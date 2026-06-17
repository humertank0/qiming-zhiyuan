# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project overview

启明志愿 is a Debian/server-oriented Web MVP for gaokao admissions advising. It is no longer maintained as a Windows one-click or personal local CLI deployment.

Runtime path:

- `app.py` — FastAPI backend entry, static frontend mount, API routes.
- `advisor_core.py` — advisor core: env loading, provider presets, slot extraction, SQLite admissions lookup, prompt construction, LLM call, response cleanup.
- `web/` — vanilla frontend for desktop/mobile browsers.
- `system_prompt.md` — advisor behavior, data, and tone rules.
- `knowledge_base.md` — domain knowledge injected into the advisor.
- `admission_clean.db.gz` — compressed runtime admissions database; `advisor_core.ensure_admission_db()` expands it to `admission_clean.db` if needed.

Removed legacy scope:

- Windows `.bat` startup.
- personal zero-code Windows tutorials.
- promo video assets.
- old CLI entry and data-building scripts with hardcoded Windows paths.

## Copywriting and advisor tone

User-facing Chinese copy must be grounded, warm, credible, and easy to understand. The advisor must sound sincere, equal, and helpful, not superior or gleefully negative.

Avoid phrases with pressure or mockery, including:

- “我直接给你说结论，不绕弯”
- “我帮你点破”
- overusing “说白了” as a blunt put-down
- “够不着”
- “别想”
- “被带偏”
- “只能满足两个半”

Prefer:

- “这个目标可以理解”
- “我们主要看它和学校层次、专业之间怎么取舍”
- “不是不能考虑，只是要准备更稳的备选”
- “我帮你把选择拆开看”
- “最终还要以省考试院和高校招生网当年数据为准”

## Common commands

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Configure server env:

```bash
cp .env.example .env
# edit LLM_API_KEY / LLM_BASE_URL / LLM_MODEL
```

Run locally:

```bash
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Run on server:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

Smoke checks:

```bash
python -m py_compile advisor_core.py app.py
node --check web/app.js
curl http://127.0.0.1:8000/api/health
```

There is no formal pytest suite right now.

## Deployment notes

Primary target is Debian with systemd + Nginx reverse proxy.

Recommended production shape:

- bind uvicorn to `127.0.0.1:8000` behind Nginx;
- use HTTPS at Nginx;
- keep `.env` outside Git and readable only by the service user;
- set `WEB_CORS_ORIGINS` to the production origin if cross-origin access is needed;
- keep `WEB_ENABLE_BACKEND_LLM=true`;
- keep `WEB_ENABLE_BYOK_DIRECT=false` unless intentionally exposing BYOK browser-direct mode.

## Security notes

- Never commit `.env` or real API keys.
- Default backend mode does not expose `LLM_API_KEY` to browsers.
- Public deployments can consume backend quota unless access control is added.
- HTTP exposes user prompts/responses on the network; production should use HTTPS.
- BYOK mode places the user's own key in their browser runtime; do not describe it as absolutely safe.

## Data notes

`admission_clean.db.gz` is a runtime artifact and should be kept. The uncompressed `admission_clean.db` is generated locally/server-side and should not be committed.

The current `admission` table expected by `advisor_core.query_real_data()` uses:

- `school`
- `major`
- `score`
- `rank`
- `province`
- `year`

If future data rebuilding is needed, recover the deleted historical scripts from Git history and rebuild them as parameterized Debian-friendly tools rather than restoring hardcoded Windows paths into the root project.

## Important product behavior

- Example cards open a modal with local example content and must not call the API.
- Local admissions data is an internal reference for the model. Do not prepend raw `[真实录取数据]` dumps to user replies.
- If the user says they have no direction, first guide them through 2-3 possible paths and ask only a couple of key questions.
- Responses should remain conversational, not Markdown reports.
