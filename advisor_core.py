#!/usr/bin/env python3
"""启明志愿核心顾问逻辑。

Web (`app.py`) 复用这里的配置、槽位、数据库查询、
搜索、prompt 构造和 OpenAI-compatible 调用。这里不处理 FastAPI 路由，
"""

from __future__ import annotations

import copy
import gzip
import json
import os
import re
import shutil
import sqlite3
import uuid
import urllib.parse
import urllib.request
from typing import Any

from openai import AsyncOpenAI, OpenAI

HERE = os.path.dirname(os.path.abspath(__file__))
KNOWLEDGE_BASE_PATH = os.path.join(HERE, "knowledge_base.md")
SYSTEM_PROMPT_PATH = os.path.join(HERE, "system_prompt.md")
DB_PATH = os.path.join(HERE, "admission_clean.db")
GZ_PATH = os.path.join(HERE, "admission_clean.db.gz")
SEARCH_ENGINE = "https://www.baidu.com/s?wd="
DEFAULT_MAX_HISTORY_MESSAGES = 20


def load_dotenv(path: str) -> None:
    """简单的 .env 加载器，不依赖第三方库。"""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                key, val = key.strip(), val.strip()
                if key not in os.environ:
                    os.environ[key] = val


load_dotenv(os.path.join(HERE, ".env"))


PRESETS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "requires_key": True,
        "note": "DeepSeek OpenAI-compatible 接口。浏览器直连是否可用取决于服务端 CORS。",
    },
    "qwen": {
        "label": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus",
        "requires_key": True,
        "note": "阿里云 DashScope OpenAI-compatible 模式。浏览器直连可能受 CORS 限制。",
    },
    "glm": {
        "label": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4",
        "requires_key": True,
        "note": "智谱 OpenAI-compatible 接口。浏览器直连可能受 CORS 限制。",
    },
    "moonshot": {
        "label": "Moonshot",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
        "requires_key": True,
        "note": "Moonshot OpenAI-compatible 接口。浏览器直连可能受 CORS 限制。",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o",
        "requires_key": True,
        "note": "OpenAI 官方接口通常不建议在浏览器端暴露 Key。",
    },
    "custom": {
        "label": "自定义 OpenAI-compatible",
        "base_url": "",
        "model": "",
        "requires_key": True,
        "note": "只填写你信任的 API 地址；自定义地址会收到你的 Key 和对话内容。",
    },
}


def provider_presets() -> list[dict[str, Any]]:
    return [
        {"id": key, **value}
        for key, value in PRESETS.items()
    ]


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", "关闭"}


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def normalize_base_url(base_url: str) -> str:
    """兼容用户把完整 chat/completions 地址填进 LLM_BASE_URL 的情况。"""
    url = (base_url or "").strip().rstrip("/")
    if url.endswith("/chat/completions"):
        url = url[: -len("/chat/completions")]
    return url


def resolve_config(model_override: str | None = None, enable_search: bool | None = None) -> dict[str, Any]:
    """解析后端代理模式配置，支持 provider preset 或显式 OpenAI-compatible 地址。"""
    provider = os.getenv("LLM_PROVIDER", "").lower()
    if provider in PRESETS and provider != "custom":
        preset = PRESETS[provider]
        base_url = os.getenv("LLM_BASE_URL", str(preset["base_url"]))
        model = os.getenv("LLM_MODEL", str(preset["model"]))
    else:
        base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
        model = os.getenv("LLM_MODEL", "deepseek-chat")

    return {
        "provider": provider or "custom",
        "base_url": normalize_base_url(base_url),
        "api_key": os.getenv("LLM_API_KEY", ""),
        "model": model_override or model,
        "max_tokens": None,
        "temperature": 0.7,
        "enable_search": env_bool("ENABLE_SEARCH", True) if enable_search is None else enable_search,
        "max_history_messages": max(2, env_int("MAX_HISTORY_MESSAGES", DEFAULT_MAX_HISTORY_MESSAGES)),
    }


CONFIG = resolve_config()
_ASYNC_CLIENTS: dict[tuple[str, str], AsyncOpenAI] = {}


def get_async_client(base_url: str, api_key: str) -> AsyncOpenAI:
    """复用异步 HTTP client，减少高并发下反复建连的开销。"""
    normalized = normalize_base_url(base_url)
    key = (normalized, api_key)
    client = _ASYNC_CLIENTS.get(key)
    if client is None:
        client = AsyncOpenAI(base_url=normalized, api_key=api_key)
        _ASYNC_CLIENTS[key] = client
    return client


def load_file(path: str) -> str:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


SHARED_KNOWLEDGE_BASE = load_file(KNOWLEDGE_BASE_PATH)
SHARED_SYSTEM_PROMPT = load_file(SYSTEM_PROMPT_PATH)


def ensure_admission_db() -> bool:
    """确保本地录取数据库可用，必要时从 gzip 压缩包解压。"""
    if os.path.exists(DB_PATH):
        return True
    if not os.path.exists(GZ_PATH):
        return False
    try:
        with gzip.open(GZ_PATH, "rb") as gz:
            with open(DB_PATH, "wb") as f:
                shutil.copyfileobj(gz, f)
        return os.path.exists(DB_PATH)
    except Exception:
        return False


def admission_db_available() -> bool:
    return ensure_admission_db()


def extract_score(msg: str) -> int | None:
    match = re.search(r"(\d{3})\s*分", msg)
    return int(match.group(1)) if match else None


def extract_rank(msg: str) -> int | None:
    patterns = [
        r"(?:位次|排名|排位|名次)\s*(?:大概|约|是|为|在|[:：])?\s*(\d{4,8})",
        r"(\d{4,8})\s*(?:位|名)",
    ]
    for pattern in patterns:
        match = re.search(pattern, msg)
        if match:
            return int(match.group(1))
    return None


def extract_major_keyword(user_msg: str) -> str | None:
    if any(word in user_msg for word in ["国家电网", "电网", "电力系统", "电力行业"]):
        return "电气"
    subject_only_words = {"物理", "历史", "化学", "生物", "数学", "地理"}
    for kw in MAJOR_KEYWORDS:
        if kw not in user_msg:
            continue
        if kw in subject_only_words:
            explicit_major = re.search(rf"(想学|学|专业|喜欢|考虑|方向|{kw}学)\s*[^，。；,;]{{0,8}}{kw}|{kw}学", user_msg)
            subject_context = re.search(rf"{kw}\s*(类|组|方向)?\s*(考生|考了|\d{{3}}分|类)", user_msg)
            if not explicit_major or subject_context:
                continue
        return kw
    return None


def query_real_data(
    province: str | None = None,
    school_keyword: str | None = None,
    major_keyword: str | None = None,
    max_rank: int | None = None,
    score: int | None = None,
    limit: int = 20,
) -> list[dict[str, Any]] | None:
    """查询真实录取数据库。每次查询单独打开只读连接，避免 Web 多线程复用连接。"""
    if not ensure_admission_db():
        return None

    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        curs = conn.cursor()
        conditions: list[str] = []
        params: list[Any] = []
        if not (province or school_keyword or major_keyword or max_rank or score):
            return None

        if province:
            conditions.append("province LIKE ?")
            params.append(f"%{province}%")
        if school_keyword:
            conditions.append("school LIKE ?")
            params.append(f"%{school_keyword}%")
        if major_keyword:
            conditions.append("major LIKE ?")
            params.append(f"%{major_keyword}%")
        conditions.append("(school LIKE '%大学%' OR school LIKE '%学院%' OR school LIKE '%学校%' OR school LIKE '%职业%' OR school LIKE '%专科%')")
        conditions.append("length(school) <= 40")
        conditions.append("score IS NOT NULL AND score > 0")
        # 高职单招、对口招生、艺体类等分数体系和普通高考不可直接比较，不能混入常规志愿参考。
        for pattern in ["%单招%", "%对口%", "%艺术%", "%体育%", "%中职%", "%职教%", "%技能%", "%专升本%"]:
            conditions.append("(source IS NULL OR source NOT LIKE ?)")
            params.append(pattern)
        # 高分段普通本科咨询里，专科/高职院校通常是脏数据或不可比数据；指定学校查询时不强行过滤。
        if score and score >= 580 and not school_keyword:
            conditions.append("school NOT LIKE '%职业%'")
            conditions.append("school NOT LIKE '%专科%'")
        if score:
            conditions.append("score >= ? AND score <= ?")
            params.extend([max(1, score - 45), score + 35])
        order_sql = "year DESC, rank ASC"
        order_params: list[Any] = []
        if max_rank:
            low = max(1, max_rank - 15000)
            high = max_rank + 30000
            conditions.append("rank IS NOT NULL AND rank > 0")
            conditions.append("rank >= ? AND rank <= ?")
            params.extend([low, high])
            order_sql = "year DESC, ABS(rank - ?) ASC, rank ASC"
            order_params.append(max_rank)
        elif score:
            order_sql = "year DESC, ABS(score - ?) ASC, score DESC"
            order_params.append(score)
        if not conditions:
            return None

        where = " AND ".join(conditions)
        query_sql = (
            "SELECT school, major, score, rank, province, year "
            f"FROM admission WHERE {where} ORDER BY {order_sql} LIMIT ?"
        )
        params.extend(order_params)
        params.append(limit)
        curs.execute(query_sql, params)
        rows = curs.fetchall()
        if not rows:
            return None
        result: list[dict[str, Any]] = []
        seen_rows: set[tuple[Any, ...]] = set()
        for r in rows:
            key = (r[0], r[1], r[2], r[3], r[4], r[5])
            if key in seen_rows:
                continue
            seen_rows.add(key)
            result.append({"school": r[0], "major": r[1], "score": r[2], "rank": r[3], "province": r[4], "year": r[5]})
        return result
    except Exception:
        return None
    finally:
        if conn is not None:
            conn.close()


DEFAULT_SLOTS = {
    "province": {"label": "省份", "filled": False, "value": ""},
    "score_rank": {"label": "分数/位次", "filled": False, "value": ""},
    "subject": {"label": "选科", "filled": False, "value": ""},
    "interest": {"label": "专业兴趣/厌恶", "filled": False, "value": ""},
    "region": {"label": "地域偏好", "filled": False, "value": ""},
    "family": {"label": "家庭资源", "filled": False, "value": ""},
    "goal": {"label": "核心诉求", "filled": False, "value": ""},
}


def new_slots() -> dict[str, dict[str, Any]]:
    return copy.deepcopy(DEFAULT_SLOTS)


def filled_slots(slots: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {k: v for k, v in slots.items() if v["filled"]}


def missing_slots(slots: dict[str, dict[str, Any]]) -> list[str]:
    return [k for k, v in slots.items() if not v["filled"]]


def slots_summary(slots: dict[str, dict[str, Any]]) -> str:
    lines = []
    for v in slots.values():
        status = "[OK]" if v["filled"] else "[ ]"
        lines.append(f"  {status} {v['label']}: {v['value'] if v['filled'] else '(未填)'}")
    return "\n".join(lines)


def _fill_slot(slots: dict[str, dict[str, Any]], key: str, value: str, updates: list[str], label: str) -> None:
    if not slots[key]["filled"]:
        slots[key]["value"] = value
        slots[key]["filled"] = True
        updates.append(f"{label}→{value}")


def extract_slots_from_message(msg: str, slots: dict[str, dict[str, Any]]) -> list[str]:
    """从用户消息中自动提取槽位信息，更新当前会话自己的 slots。"""
    updates: list[str] = []

    provinces = [
        "北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林",
        "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南",
        "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西",
        "甘肃", "青海", "台湾", "内蒙古", "广西", "西藏", "宁夏", "新疆",
    ]
    for p in provinces:
        if p in msg:
            _fill_slot(slots, "province", p, updates, "省份")
            break

    score = extract_score(msg)
    rank = extract_rank(msg)
    if score and not slots["score_rank"]["filled"]:
        _fill_slot(slots, "score_rank", f"{score}分", updates, "分数")
    if rank:
        rank_text = f"位次{rank}"
        if not slots["score_rank"]["filled"]:
            _fill_slot(slots, "score_rank", rank_text, updates, "位次")
        elif rank_text not in slots["score_rank"]["value"]:
            slots["score_rank"]["value"] += " / " + rank_text
            updates.append(f"位次→{rank}")

    for subj in ["物化生", "物化地", "物化政", "物生政", "史政地", "史政生", "史地生", "物理", "历史", "理科", "文科"]:
        if subj in msg:
            _fill_slot(slots, "subject", subj, updates, "选科")
            break

    for r in ["省内", "本省", "离家近", "北上广", "江浙沪", "北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "南京", "西安"]:
        if r in msg:
            _fill_slot(slots, "region", r, updates, "地域")
            break

    for fw in ["电力", "电网", "铁路", "医生", "教师", "老师", "做生意", "公务员", "烟草", "石油", "普通家庭", "普通工薪", "没资源"]:
        if fw in msg:
            _fill_slot(slots, "family", fw, updates, "家庭")
            break

    for g in ["就业", "考公", "考研", "稳定", "高薪", "赚钱", "深造", "出国"]:
        if g in msg:
            _fill_slot(slots, "goal", g, updates, "诉求")
            break

    for interest in ["计算机", "软件", "人工智能", "电气", "电子", "通信", "临床", "口腔", "护理", "法学", "会计", "金融", "汉语言", "师范", "铁路", "医学"]:
        if interest in msg:
            _fill_slot(slots, "interest", interest, updates, "兴趣")
            break

    return updates


def is_consultation_intent(msg: str) -> bool:
    keywords = [
        "高考", "志愿", "选专业", "报学校", "报志愿", "填志愿", "选科",
        "分科", "考研", "选学校", "大学", "专业", "就业", "考公",
        "能报", "能上", "推荐", "建议", "帮忙看", "帮我选",
    ]
    return any(kw in msg for kw in keywords)


def web_search(query: str, max_results: int = 5) -> list[str]:
    """搜索并抓取网页。当前先复用轻量百度抓取，后续可替换为更稳定的搜索服务。"""
    results: list[str] = []
    try:
        url = SEARCH_ENGINE + urllib.parse.quote(query)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        urls = re.findall(r'href="(https?://[^"]+)"', html)
        valid_urls = [u for u in urls if "baidu.com" not in u and len(u) > 30][:max_results + 3]

        for target_url in valid_urls:
            if len(results) >= max_results:
                break
            try:
                page_req = urllib.request.Request(target_url, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                with urllib.request.urlopen(page_req, timeout=8) as page_resp:
                    page_html = page_resp.read().decode("utf-8", errors="ignore")
                clean = re.sub(r"<script[^>]*>.*?</script>", "", page_html, flags=re.DOTALL)
                clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL)
                clean = re.sub(r"<[^>]+>", " ", clean)
                clean = re.sub(r"\s+", " ", clean).strip()
                if len(clean) > 100:
                    results.append(clean[:600])
            except Exception:
                continue

        if not results:
            snippets = re.findall(r'<span class="content-right_[^"]*">(.*?)</span>', html)
            for s in snippets[:max_results]:
                clean = re.sub(r"<[^>]+>", "", s).strip()
                if len(clean) > 20:
                    results.append(clean)

        return results if results else ["(搜索无结果)"]
    except Exception as e:
        return [f"(搜索异常: {e})"]


def should_search(msg: str) -> bool:
    triggers = [
        "今年", "最新", "2026", "2025", "最近", "现在",
        "分数线", "录取分", "投档线", "招生计划", "录取",
        "政策", "变化", "改革", "新规", "就业率", "就业前景",
        "薪资", "月薪", "年薪", "排名", "第几名", "怎么样", "好不好",
        "能上", "能报", "能进", "稳不稳", "冲不冲", "多少分",
        "什么专业", "一本", "二本", "985", "211", "王牌专业",
        "优势", "缺点", "劣势", "值得", "推荐吗", "评价", "口碑",
        "好不好考", "难不难",
    ]
    return any(t in msg for t in triggers)


def soften_tone(text: str) -> str:
    replacements = {
        "我直接给你说结论，不绕弯。": "我先把大致判断说清楚。",
        "我先直接给你说结论，不绕弯。": "我先把大致判断说清楚。",
        "你这个分数我先直接给你说结论，不绕弯。": "我先把大致判断说清楚。",
        "我帮你点破": "我帮你拆开看",
        "说白了": "换个更清楚的说法",
        "够不着": "距离会比较大",
        "别想": "不太现实",
        "被北京带偏": "容易只看到北京的吸引力",
        "被热门专业带偏": "容易只看到热门专业的吸引力",
        "只能最多满足两个半": "很难三方面都完全满足",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def cleanup_format(text: str) -> str:
    if not text:
        return text
    text = soften_tone(text)
    text = re.sub(r"^\s*[-—]{3,}\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[\.、]\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def extract_chat_content(resp: Any) -> str:
    """从 OpenAI-compatible 响应中提取 assistant 文本，兼容少数代理返回 dict/string。"""
    if isinstance(resp, str):
        raw = resp.strip()
        if raw.startswith("{") or raw.startswith("["):
            try:
                return extract_chat_content(json.loads(raw))
            except json.JSONDecodeError:
                pass
        if raw:
            return raw
        raise ValueError("模型服务返回了空字符串。")

    if isinstance(resp, dict):
        choices = resp.get("choices")
    else:
        choices = getattr(resp, "choices", None)

    if choices:
        choice = choices[0]
        if isinstance(choice, dict):
            message = choice.get("message") or {}
            if isinstance(message, dict):
                content = _content_to_text(message.get("content"))
            else:
                content = _content_to_text(getattr(message, "content", ""))
            if content:
                return content
            text = _content_to_text(choice.get("text"))
            if text:
                return text
        else:
            message = getattr(choice, "message", None)
            content = _content_to_text(getattr(message, "content", "")) if message else ""
            if content:
                return content
            text = _content_to_text(getattr(choice, "text", ""))
            if text:
                return text

    raise ValueError(f"模型服务返回格式不符合 OpenAI-compatible Chat Completions：{type(resp).__name__}")


def is_invalid_model_output(text: str) -> bool:
    if not text:
        return True
    patterns = [
        r"<\s*tool_call\b",
        r"<\s*/\s*tool_call\s*>",
        r"<\s*function\s*=",
        r"<\s*parameter\s*=",
        r"</\s*function\s*>",
        r"</\s*parameter\s*>",
        r"^\s*\{\s*\"tool",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE) for pattern in patterns)


def retry_instruction(reason: str) -> dict[str, str]:
    return {
        "role": "system",
        "content": (
            f"【重新生成要求】上一轮输出不合格：{reason}。"
            "你没有任何可调用工具，绝对不能输出 <tool_call>、<function>、<parameter>、JSON tool call 或 XML。"
            "请直接用自然中文回答用户；保留少量 **重点** 加粗；如果数据不足，就明确说明并给出下一步核实建议。"
        ),
    }


MAJOR_KEYWORDS = [
    "计算机", "软件", "电气", "机械", "土木", "临床", "口腔", "法学", "会计", "金融",
    "物联网", "人工智能", "大数据", "电子", "通信", "自动化", "材料", "化工", "生物",
    "医学", "护理", "师范", "英语", "日语", "新闻", "设计", "美术", "音乐", "体育",
    "汉语言", "思政", "马克思", "数学", "物理", "化学", "历史", "地理",
]


def needs_direction_guidance(msg: str) -> bool:
    no_direction_words = ["没什么想法", "没有想法", "没想法", "没方向", "不知道", "不清楚", "都行", "无所谓", "迷茫"]
    return any(word in msg for word in no_direction_words)


class AdvisorSession:
    def __init__(self, config: dict[str, Any] | None = None):
        self.config = dict(config or CONFIG)
        self.knowledge_base = SHARED_KNOWLEDGE_BASE
        self.system_prompt = SHARED_SYSTEM_PROMPT
        self.conversation: list[dict[str, str]] = []
        self.slots = new_slots()
        self.pending_turns: dict[str, dict[str, Any]] = {}

    def _build_system_message(self) -> str:
        search_note = ""
        if self.config["enable_search"]:
            search_note = "\n\n【联网搜索已启用。遇到最新政策/分数线/就业数据等问题时，请结合搜索信息，并提醒用户以官方来源核实。】"

        return f"""{self.system_prompt}

{search_note}

【知识库参考】
{self.knowledge_base or ""}

【当前用户信息采集状态】
{slots_summary(self.slots)}

请在回答时：
1. 语气必须诚恳、平等、真诚。先接住用户的目标，再分析取舍；不要居高临下，不要幸灾乐祸。
2. 每次回复要突出重点：允许用少量 `**重点**` 加粗关键结论、风险边界、推荐方向和最后追问；不要整篇都加粗。
3. 避免这些句式：我直接给你说结论、不绕弯、我帮你点破、说白了、够不着、别想、被带偏、只能满足两个半。
4. 如果用户信息不全，追问缺失的槽位（用自然的方式，不要像填表）。
5. 如果用户明确说“没想法/不知道/都行”，先做方向引导：用 2-3 条可选路径帮他缩小范围，再问 2 个关键问题；不要一上来堆学校清单。
6. 如果信息已经足够（至少省份+分数/位次+核心诉求），给出冲稳保推荐。
7. 遇到需要最新数据时，提示用户建议查官方渠道，或结合搜索信息回答。
8. 保持接地气但不土味，把机会、风险和需要核实的数据讲清楚。Web 首轮回复尽量控制在 800 字以内。"""

    def _find_school(self, user_msg: str) -> str | None:
        for m in re.finditer(r"(?:大学|学院)", user_msg):
            end = m.end()
            for start in range(max(0, end - 12), end - 1):
                candidate = user_msg[start:end]
                if len(candidate) >= 3 and any("一" <= c <= "鿿" for c in candidate):
                    if query_real_data(school_keyword=candidate, limit=1):
                        return candidate
        fallback = re.findall(r"[一-鿿]{2,8}(?:大学|学院)", user_msg)
        return fallback[-1] if fallback else None

    def _build_real_data_message(self, user_msg: str) -> tuple[str | None, str | None]:
        prov_match = re.findall(r"(北京|天津|上海|重庆|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|广西|海南|四川|贵州|云南|陕西|甘肃|青海|西藏|宁夏|新疆|内蒙古)", user_msg)
        school = self._find_school(user_msg)
        prov = prov_match[0] if prov_match else self.slots.get("province", {}).get("value", "")
        rank = extract_rank(user_msg)
        score = extract_score(user_msg)
        major_kw = extract_major_keyword(user_msg)

        if not (prov or school):
            return None, None

        # 只有存在强约束时才查询并暴露录取条目：具体学校、专业/职业目标映射，或明确位次。
        # 只有省份+分数时，直接列相近分数表容易混入无关专业/批次，反而误导用户。
        if not (school or major_kw or rank):
            return None, None

        real_data = query_real_data(prov, school, major_kw, rank, score=score, limit=30)
        if not real_data and school:
            real_data = query_real_data(school_keyword=school, major_keyword=major_kw, max_rank=rank, score=score, limit=30)
        if not real_data and school and major_kw:
            real_data = query_real_data(province=prov, school_keyword=school, max_rank=rank, score=score, limit=30)
        if not real_data and school:
            real_data = query_real_data(school_keyword=school, max_rank=rank, score=score, limit=50)
        if not real_data:
            return None, None

        data_prov = real_data[0].get("province", prov)
        lines = [f"【真实录取数据 · {data_prov}】"]
        for d in real_data:
            extras = []
            if d.get("year"):
                extras.append(f"{d['year']}年")
            if d.get("score") and d["score"] > 1:
                extras.append(f"最低{d['score']}分")
            if d.get("rank"):
                extras.append(f"位次{d['rank']}")
            extra_str = " / ".join(extras)
            major_value = str(d.get("major") or "")
            major_is_code = bool(re.fullmatch(r"[A-Z][A-Z0-9]*\d{2,}", major_value))
            major_str = f" · {major_value}" if major_value and major_value != d["school"] and not major_is_code else ""
            lines.append(f"· {d['school']}{major_str} — {extra_str}")

        search_hint = "\n".join(lines[:20])
        data_summary = "\n".join(lines[:15])
        if prov and prov not in str(data_prov):
            warning = f"\n\n注意：{prov}暂无该学校录取数据，以上为{data_prov}省数据，仅作参考。"
            search_hint += warning
            data_summary += warning
        return search_hint, data_summary

    def _public_query_context(self, user_msg: str) -> dict[str, Any]:
        prov_match = re.findall(r"(北京|天津|上海|重庆|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|广西|海南|四川|贵州|云南|陕西|甘肃|青海|西藏|宁夏|新疆|内蒙古)", user_msg)
        return {
            "province": prov_match[0] if prov_match else self.slots.get("province", {}).get("value", "") or "未明确",
            "score": extract_score(user_msg) or "未明确",
            "rank": extract_rank(user_msg) or "未明确",
            "major": extract_major_keyword(user_msg) or "未限定具体专业",
            "school": self._find_school(user_msg) or "未指定学校",
        }

    def _public_data_items(self, data_summary: str | None, limit: int = 6) -> list[str]:
        if not data_summary:
            return []
        items: list[str] = []
        for line in data_summary.split("\n"):
            line = line.strip()
            if not line.startswith("· "):
                continue
            items.append(line[2:])
            if len(items) >= limit:
                break
        return items

    def _format_query_context_items(self, context: dict[str, Any]) -> list[str]:
        return [
            f"省份：{context['province']}",
            f"分数：{context['score']}",
            f"位次：{context['rank']}",
            f"专业关键词：{context['major']}",
            f"指定学校：{context['school']}",
        ]

    def prepare_turn(self, user_msg: str) -> dict[str, Any]:
        if is_consultation_intent(user_msg):
            updates = extract_slots_from_message(user_msg, self.slots)
        else:
            updates = []

        messages: list[dict[str, str]] = [{"role": "system", "content": self._build_system_message()}]
        messages.extend(self.conversation)
        messages.append({"role": "user", "content": user_msg})
        public_query_context = self._public_query_context(user_msg)

        if updates:
            hint = f"(系统自动识别到: {', '.join(updates)}。请在回复中确认并追问缺失信息。)"
            messages.append({"role": "system", "content": hint})

        if needs_direction_guidance(user_msg):
            messages.append({
                "role": "system",
                "content": "【对话策略】用户现在没明确专业/职业方向。请不要直接输出长篇学校清单，也不要把本地数据整段贴出来。先用简短语言给出 2-3 条大方向（如技术就业、稳定体制、城市优先），说明各自适合什么人，最后只问 2 个最关键的问题，帮助用户下一轮选择。",
            })

        search_results = None
        search_hint = None
        data_summary = None
        if admission_db_available():
            search_hint, data_summary = self._build_real_data_message(user_msg)
            if data_summary:
                messages.append({"role": "system", "content": f"【本地录取数据参考】\n{data_summary}\n\n这些数据只给你内部参考：不要原样整段贴给用户，不要说成是用户贴的数据。回答时只提炼成定位和少量例子；如果显示跨省警告，必须先说明该省暂无数据，以下为其他省参考。所有具体分数/位次都提醒以考试院和高校招生网为准。"})
                search_results = "real_data_used"

        web_info = None
        web_queries: list[str] = []
        if self.config["enable_search"] and should_search(user_msg):
            search_query = user_msg[:120]
            query1 = search_query + " 录取 位次 site:gaokao.cn OR site:eol.cn"
            query2 = search_query + " 分数线 教育考试院 OR 招生网"
            web_queries = [query1, query2]
            web_results1 = web_search(query1, max_results=5)
            web_results2 = web_search(query2, max_results=5)
            all_web = (web_results1 or []) + (web_results2 or [])
            seen: set[str] = set()
            unique_web: list[str] = []
            for r in all_web:
                key = r[:50]
                if key not in seen and len(r) > 30:
                    seen.add(key)
                    unique_web.append(r)
            if unique_web:
                web_info = "\n".join(f"· {r[:250]}" for r in unique_web[:8])
                messages.append({"role": "system", "content": f"【网上搜索到的信息·综合{len(unique_web)}条】\n{web_info}\n\n请根据以上公开信息交叉验证，给出综合分析。必须明确标注根据网上公开信息综合分析。不准把模糊信息说成确定数字；如果多条信息矛盾，要指出。"})
                if not search_results:
                    search_results = "web_only"

        if not search_results:
            messages.append({"role": "system", "content": "【数据边界】数据库和搜索均未找到该学校/专业在该省的录取数据。必须明确告诉用户没有数据，建议查省考试院官网或学校招生网。禁止编造任何数字。"})

        turn_id = str(uuid.uuid4())
        progress_steps = [
            {
                "title": "识别基础信息",
                "status": "done",
                "detail": "；".join(updates) if updates else "已读取你的问题，继续结合上下文判断。",
                "items": self._format_query_context_items(public_query_context),
            }
        ]
        if data_summary:
            data_lines = [line for line in data_summary.split("\n") if line.startswith("· ")]
            progress_steps.append({
                "title": "查询本地录取数据库",
                "status": "done",
                "detail": f"已查询 admission_clean.db，命中 {len(data_lines)} 条强相关参考数据。",
                "items": self._public_data_items(data_summary),
            })
        else:
            has_anchor = any([
                public_query_context["rank"] != "未明确",
                public_query_context["major"] != "未限定具体专业",
                public_query_context["school"] != "未指定学校",
            ])
            progress_steps.append({
                "title": "查询本地录取数据库",
                "status": "done",
                "detail": "本地库没有命中足够相关的数据，回答会提醒以官方数据核实。" if has_anchor else "已跳过具体院校条目展示：缺少位次、专业/职业方向或指定学校，避免把无关表格当参考。",
                "items": [
                    f"查询省份：{public_query_context['province']}",
                    f"位次/分数：{public_query_context['rank']} / {public_query_context['score']}",
                    f"专业关键词：{public_query_context['major']}",
                    "展示规则：只公开强相关院校/专业条目，不展示仅按分数扫出的无关表格。",
                ],
            })
        if web_info:
            progress_steps.append({
                "title": "补充公开信息",
                "status": "done",
                "detail": "已尝试抓取公开网页信息，作为辅助参考。",
                "items": web_queries,
            })
        elif self.config["enable_search"] and should_search(user_msg):
            progress_steps.append({
                "title": "补充公开信息",
                "status": "done",
                "detail": "已尝试联网补充，但没有拿到足够稳定的信息。",
                "items": web_queries,
            })
        else:
            progress_steps.append({
                "title": "补充公开信息",
                "status": "skipped",
                "detail": "这轮优先使用本地知识库和录取数据，没有触发联网搜索。",
                "items": ["未触发原因：问题不涉及明显的最新政策、分数线或学校评价关键词。"],
            })
        progress_steps.append({
            "title": "生成志愿建议",
            "status": "running",
            "detail": "正在把分数、位次、地域和专业诉求整理成自然回答。",
        })
        turn_context = {
            "user_msg": user_msg,
            "messages": messages,
            "search_results": search_results,
            "search_hint": search_hint,
            "web_info": web_info,
            "progress_steps": progress_steps,
        }
        self.pending_turns[turn_id] = turn_context

        return {
            "turn_id": turn_id,
            "messages": messages,
            "temperature": self.config["temperature"],
            "model_suggestion": self.config["model"],
            "slots": copy.deepcopy(self.slots),
            "missing_slots": missing_slots(self.slots),
            "slot_updates": updates,
            "progress_steps": copy.deepcopy(progress_steps),
        }

    def complete_prepared_turn(self, turn_id: str) -> dict[str, Any]:
        turn_context = self.pending_turns.get(turn_id)
        if not turn_context:
            raise ValueError("会话轮次不存在或已经完成，请重新发送。")
        messages = turn_context.get("messages")
        if not isinstance(messages, list):
            raise ValueError("会话上下文不完整，请重新发送。")

        retry_count = 0
        working_messages = list(messages)
        for attempt in range(3):
            try:
                assistant_reply = self.complete_with_backend(working_messages)
            except Exception as e:
                assistant_reply = f"出错了：{e}\n请检查后端 .env 里的 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 是否正确。"
                break

            if not is_invalid_model_output(assistant_reply):
                break

            retry_count += 1
            if attempt >= 2:
                assistant_reply = "这次模型返回了工具调用格式，我没有把那段内容直接展示给你。可以点下面的“重新生成”，我会再按自然中文回答重试一次。"
                break
            working_messages.append(retry_instruction("模型输出了工具调用/XML，而不是自然语言回答"))

        result = self.finalize_turn(turn_id, assistant_reply)
        result["turn_id"] = turn_id
        result["retry_count"] = retry_count
        result["invalid_output_blocked"] = retry_count > 0 and "工具调用格式" in assistant_reply
        return result

    async def complete_prepared_turn_async(self, turn_id: str) -> dict[str, Any]:
        turn_context = self.pending_turns.get(turn_id)
        if not turn_context:
            raise ValueError("会话轮次不存在或已经完成，请重新发送。")
        messages = turn_context.get("messages")
        if not isinstance(messages, list):
            raise ValueError("会话上下文不完整，请重新发送。")

        retry_count = 0
        working_messages = list(messages)
        for attempt in range(3):
            try:
                assistant_reply = await self.complete_with_backend_async(working_messages)
            except Exception as e:
                assistant_reply = f"出错了：{e}\n请检查后端 .env 里的 LLM_API_KEY / LLM_BASE_URL / LLM_MODEL 是否正确。"
                break

            if not is_invalid_model_output(assistant_reply):
                break

            retry_count += 1
            if attempt >= 2:
                assistant_reply = "这次模型返回了工具调用格式，我没有把那段内容直接展示给你。可以点下面的“重新生成”，我会再按自然中文回答重试一次。"
                break
            working_messages.append(retry_instruction("模型输出了工具调用/XML，而不是自然语言回答"))

        result = self.finalize_turn(turn_id, assistant_reply)
        result["turn_id"] = turn_id
        result["retry_count"] = retry_count
        result["invalid_output_blocked"] = retry_count > 0 and "工具调用格式" in assistant_reply
        return result

    async def complete_with_backend_async(self, messages: list[dict[str, str]]) -> str:
        client = get_async_client(str(self.config["base_url"]), str(self.config["api_key"]))
        kwargs: dict[str, Any] = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config["temperature"],
        }
        if self.config["max_tokens"] is not None:
            kwargs["max_tokens"] = self.config["max_tokens"]
        resp = await client.chat.completions.create(**kwargs)
        return extract_chat_content(resp)

    def complete_with_backend(self, messages: list[dict[str, str]]) -> str:
        client = OpenAI(base_url=normalize_base_url(str(self.config["base_url"])), api_key=self.config["api_key"])
        kwargs: dict[str, Any] = {
            "model": self.config["model"],
            "messages": messages,
            "temperature": self.config["temperature"],
        }
        if self.config["max_tokens"] is not None:
            kwargs["max_tokens"] = self.config["max_tokens"]
        resp = client.chat.completions.create(**kwargs)
        return extract_chat_content(resp)

    def finalize_turn(self, turn_id: str, assistant_reply: str) -> dict[str, Any]:
        turn_context = self.pending_turns.pop(turn_id, None)
        if not turn_context:
            reply = cleanup_format(assistant_reply)
            return {
                "reply": reply,
                "slots": copy.deepcopy(self.slots),
                "missing_slots": missing_slots(self.slots),
                "slot_updates": [],
            }

        reply = cleanup_format(assistant_reply)
        search_results = turn_context.get("search_results")
        search_hint = turn_context.get("search_hint")
        web_info = turn_context.get("web_info")

        # 本地录取数据和搜索结果只作为模型内部参考，不再原样拼到用户回复前面。
        # 否则 Web 聊天会变成生硬的数据 dump，用户体验很差。

        self.conversation.append({"role": "user", "content": turn_context["user_msg"]})
        self.conversation.append({"role": "assistant", "content": reply})
        max_history = int(self.config.get("max_history_messages", DEFAULT_MAX_HISTORY_MESSAGES))
        self.conversation = self.conversation[-max_history:]

        return {
            "reply": reply,
            "slots": copy.deepcopy(self.slots),
            "missing_slots": missing_slots(self.slots),
            "slot_updates": [],
        }

    def chat(self, user_msg: str) -> dict[str, Any]:
        prepared = self.prepare_turn(user_msg)
        result = self.complete_prepared_turn(prepared["turn_id"])
        result["slot_updates"] = prepared.get("slot_updates", [])
        result["progress_steps"] = prepared.get("progress_steps", [])
        return result

    async def chat_async(self, user_msg: str) -> dict[str, Any]:
        prepared = self.prepare_turn(user_msg)
        result = await self.complete_prepared_turn_async(prepared["turn_id"])
        result["slot_updates"] = prepared.get("slot_updates", [])
        result["progress_steps"] = prepared.get("progress_steps", [])
        return result

    def reset(self) -> None:
        self.conversation = []
        self.slots = new_slots()
        self.pending_turns = {}


def test_connection(config: dict[str, Any] | None = None) -> tuple[bool, str]:
    cfg = config or CONFIG
    try:
        client = OpenAI(base_url=normalize_base_url(str(cfg["base_url"])), api_key=cfg["api_key"])
        resp = client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=5,
        )
        return True, extract_chat_content(resp)
    except Exception as e:
        return False, str(e)
