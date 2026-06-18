#!/usr/bin/env python3
"""启明志愿 FastAPI 轻后端。

提供两种模型调用方式：
1. 项目方后端代理：浏览器只调用 /api/chat，后端用 .env 中的 Key 调上游。
2. 用户自带 Key 直连：浏览器调用 /api/chat/prepare 获取 messages，随后直接请求
   用户选择的 provider，最后调用 /api/chat/finalize 保存历史和格式化结果。
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from advisor_core import (
    CONFIG,
    AdvisorSession,
    admission_db_available,
    env_bool,
    env_int,
    provider_presets,
)

HERE = Path(__file__).resolve().parent
WEB_DIR = HERE / "web"

app = FastAPI(title="启明志愿", version="0.1.0")

cors_origins = [origin.strip() for origin in os.getenv("WEB_CORS_ORIGINS", "").split(",") if origin.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )

@dataclass
class ManagedSession:
    session: AdvisorSession
    lock: asyncio.Lock
    updated_at: float


sessions: dict[str, ManagedSession] = {}
sessions_lock = asyncio.Lock()
MAX_SESSIONS = max(100, env_int("WEB_MAX_SESSIONS", 3000))
SESSION_TTL_SECONDS = max(300, env_int("WEB_SESSION_TTL_SECONDS", 7200))
LLM_CONCURRENCY = max(1, env_int("BACKEND_LLM_CONCURRENCY", 80))
llm_semaphore = asyncio.Semaphore(LLM_CONCURRENCY)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None


class PrepareRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None


class FinalizeRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    turn_id: str = Field(..., min_length=1)
    assistant_reply: str = Field(..., min_length=1)


class CompleteRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    turn_id: str = Field(..., min_length=1)


class ResetRequest(BaseModel):
    session_id: str | None = None


def cleanup_sessions(now: float | None = None) -> None:
    now = now or time.monotonic()
    expired = [sid for sid, item in sessions.items() if now - item.updated_at > SESSION_TTL_SECONDS]
    for sid in expired:
        sessions.pop(sid, None)

    if len(sessions) <= MAX_SESSIONS:
        return

    overflow = len(sessions) - MAX_SESSIONS
    oldest = sorted(sessions.items(), key=lambda pair: pair[1].updated_at)[:overflow]
    for sid, _ in oldest:
        sessions.pop(sid, None)


async def get_session(session_id: str | None = None) -> tuple[str, ManagedSession]:
    now = time.monotonic()
    async with sessions_lock:
        cleanup_sessions(now)
        if session_id and session_id in sessions:
            item = sessions[session_id]
            item.updated_at = now
            return session_id, item
        new_id = str(uuid.uuid4())
        item = ManagedSession(session=AdvisorSession(config=CONFIG), lock=asyncio.Lock(), updated_at=now)
        sessions[new_id] = item
        cleanup_sessions(now)
        return new_id, item


def touch_session(session_id: str) -> None:
    item = sessions.get(session_id)
    if item:
        item.updated_at = time.monotonic()


async def get_existing_session(session_id: str) -> ManagedSession | None:
    async with sessions_lock:
        cleanup_sessions()
        item = sessions.get(session_id)
        if item:
            item.updated_at = time.monotonic()
        return item


def base_url_host(base_url: str) -> str:
    try:
        parsed = urlparse(base_url)
        if parsed.netloc:
            return parsed.netloc
    except Exception:
        pass
    return "custom"


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    # 如开启 BYOK 直连，需要允许常见 provider 和 custom API；因此这里不设置过严 CSP。
    return response


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/web", StaticFiles(directory=str(WEB_DIR)), name="web")


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "db_available": admission_db_available(),
        "backend_llm_enabled": env_bool("WEB_ENABLE_BACKEND_LLM", True),
        "byok_direct_enabled": env_bool("WEB_ENABLE_BYOK_DIRECT", False),
        "backend_key_configured": bool(CONFIG.get("api_key")),
        "model": CONFIG.get("model"),
        "base_url_host": base_url_host(str(CONFIG.get("base_url", ""))),
        "sessions": len(sessions),
        "max_sessions": MAX_SESSIONS,
        "session_ttl_seconds": SESSION_TTL_SECONDS,
        "llm_concurrency": LLM_CONCURRENCY,
    }


@app.get("/api/config")
def web_config():
    return {
        "backend_llm_enabled": env_bool("WEB_ENABLE_BACKEND_LLM", True),
        "byok_direct_enabled": env_bool("WEB_ENABLE_BYOK_DIRECT", False),
        "allow_byok_proxy": env_bool("ALLOW_BYOK_PROXY", False),
        "default_provider": CONFIG.get("provider", "custom"),
        "default_model": CONFIG.get("model"),
        "security_note": "BYOK 模式下，Key 只在浏览器中使用，不发送到启明志愿后端；但浏览器环境并非绝对安全。",
    }


@app.get("/api/providers")
def providers():
    return {"providers": provider_presets()}


@app.post("/api/session")
async def create_session():
    session_id, item = await get_session(None)
    session = item.session
    return {
        "session_id": session_id,
        "slots": session.slots,
        "missing_slots": [k for k, v in session.slots.items() if not v["filled"]],
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not env_bool("WEB_ENABLE_BACKEND_LLM", True):
        raise HTTPException(status_code=403, detail="后端代理模式已关闭。")
    session_id, item = await get_session(req.session_id)
    async with item.lock:
        prepared = await asyncio.to_thread(item.session.prepare_turn, req.message)
        async with llm_semaphore:
            result = await item.session.complete_prepared_turn_async(prepared["turn_id"])
        result["slot_updates"] = prepared.get("slot_updates", [])
        result["progress_steps"] = prepared.get("progress_steps", [])
    touch_session(session_id)
    result["session_id"] = session_id
    return result


@app.post("/api/chat/start")
async def start_chat(req: ChatRequest):
    if not env_bool("WEB_ENABLE_BACKEND_LLM", True):
        raise HTTPException(status_code=403, detail="后端代理模式已关闭。")
    session_id, item = await get_session(req.session_id)
    async with item.lock:
        prepared = await asyncio.to_thread(item.session.prepare_turn, req.message)
    touch_session(session_id)
    return {
        "session_id": session_id,
        "turn_id": prepared["turn_id"],
        "slots": prepared["slots"],
        "missing_slots": prepared["missing_slots"],
        "slot_updates": prepared.get("slot_updates", []),
        "progress_steps": prepared.get("progress_steps", []),
    }


@app.post("/api/chat/complete")
async def complete_chat(req: CompleteRequest):
    if not env_bool("WEB_ENABLE_BACKEND_LLM", True):
        raise HTTPException(status_code=403, detail="后端代理模式已关闭。")
    item = await get_existing_session(req.session_id)
    if not item:
        raise HTTPException(status_code=404, detail="会话不存在，请刷新页面重新开始。")
    try:
        async with item.lock:
            async with llm_semaphore:
                result = await item.session.complete_prepared_turn_async(req.turn_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    touch_session(req.session_id)
    result["session_id"] = req.session_id
    return result


@app.post("/api/chat/prepare")
async def prepare_chat(req: PrepareRequest):
    if not env_bool("WEB_ENABLE_BYOK_DIRECT", False):
        raise HTTPException(status_code=403, detail="自带 Key 直连模式已关闭。")
    session_id, item = await get_session(req.session_id)
    async with item.lock:
        prepared = await asyncio.to_thread(item.session.prepare_turn, req.message)
    touch_session(session_id)
    prepared["session_id"] = session_id
    prepared["byok_notice"] = "本次返回的 messages 将由你的浏览器直接发送给所选模型服务商，启明志愿后端不会接触你的 API Key。"
    return prepared


@app.post("/api/chat/finalize")
async def finalize_chat(req: FinalizeRequest):
    item = await get_existing_session(req.session_id)
    if not item:
        raise HTTPException(status_code=404, detail="会话不存在，请刷新页面重新开始。")
    async with item.lock:
        result = item.session.finalize_turn(req.turn_id, req.assistant_reply)
    touch_session(req.session_id)
    result["session_id"] = req.session_id
    return result


@app.post("/api/reset")
async def reset(req: ResetRequest):
    # 重新开始必须彻底废弃旧 session，而不是复用原 session reset。
    # 这样即使旧请求仍在路上，也不会污染新会话。
    async with sessions_lock:
        if req.session_id:
            sessions.pop(req.session_id, None)
        cleanup_sessions()
        new_id = str(uuid.uuid4())
        item = ManagedSession(session=AdvisorSession(config=CONFIG), lock=asyncio.Lock(), updated_at=time.monotonic())
        sessions[new_id] = item
    return {
        "session_id": new_id,
        "slots": item.session.slots,
        "missing_slots": [k for k, v in item.session.slots.items() if not v["filled"]],
    }
