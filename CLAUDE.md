# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

启明志愿 is a lightweight Python 3.10+ CLI advisor for Chinese gaokao admissions planning, derived from https://github.com/ziqihe10-droid/xuefeng-agent. It combines:

- an OpenAI-compatible chat client in `agent.py`,
- local prompt and domain knowledge files (`system_prompt.md`, `knowledge_base.md`),
- a compressed SQLite admissions database (`admission_clean.db.gz`) that is expanded on first run,
- optional live web search for fresh admissions/school information.

The user-facing docs are primarily Chinese: `README.md`, `TUTORIAL.md`, `小白教程-零基础也能用.md`, examples, and marketing/video scripts.

## Copywriting style

User-facing Chinese copy should be grounded and easy to understand, but not overly rustic, aggressive, or short-video-like. Prefer plain, warm, credible wording around “打破信息差 / 看清选择 / 讲清机会和风险”. Avoid exaggerated phrases, coarse jokes, and fear-driven marketing language.

## Common commands

Install the runtime dependencies documented by the project:

```bash
pip install openai pywin32
```

`pywin32` is only used for Windows clipboard support in the `/paste` command. On non-Windows environments, the core agent path only needs the OpenAI-compatible client.

Configure a local API key before running the agent:

```bash
cp .env.example .env
# edit .env and set LLM_API_KEY plus either LLM_PROVIDER or LLM_BASE_URL/LLM_MODEL
```

Run the interactive CLI:

```bash
python agent.py
```

Inside the CLI, supported slash commands are implemented in `agent.py`: `/paste`, `/slots`, `/reset`, `/quit`.

Run lightweight smoke checks:

```bash
python gaokao_data.py          # exercises the standalone realtime search helper
python -m py_compile agent.py gaokao_data.py real_data.py build_real_db.py build_all_provinces.py clean_data.py verify_provinces.py
```

There is no formal automated test suite or pytest configuration in this repository right now, so there is no existing “single test” command. For targeted validation, run the relevant script directly or add focused tests before relying on `pytest` conventions.

For data-building work, install the Excel dependencies first:

```bash
pip install xlrd openpyxl
```

Before running data import/cleanup scripts, inspect and update their hardcoded Windows paths (`DATA_DIR`, `SRC`, `DST`, `DB_PATH`). Several scripts currently point at desktop paths such as `E:\桌面\...` rather than repository-relative files:

```bash
python build_real_db.py
python build_all_provinces.py
python clean_data.py
python verify_provinces.py
```

## Runtime architecture

`agent.py` is the main application and contains most runtime behavior:

1. Loads `.env` with a small built-in dotenv reader.
2. Resolves provider presets from `LLM_PROVIDER` (`deepseek`, `qwen`, `glm`, `moonshot`, `openai`, `ollama`) or explicit `LLM_BASE_URL`/`LLM_MODEL`.
3. Auto-decompresses `admission_clean.db.gz` to `admission_clean.db` if the uncompressed DB is missing, then opens SQLite.
4. Tracks consultation slots in the global `SLOTS` mapping: province, score/rank, subject, interest, region, family, goal.
5. Builds each LLM system message from `system_prompt.md`, the full `knowledge_base.md`, search notes, and current slot state.
6. On each user turn, tries local SQLite admissions lookup first, then web search when `should_search()` triggers, then calls the OpenAI-compatible chat completion API.
7. Cleans Markdown-ish formatting from the model response before printing.

The README/docstring mention `python agent.py --model ...` and `python agent.py --no-search`, but current `agent.py` does not parse command-line arguments. Prefer `.env`/environment configuration unless adding real argparse support.

## Data flow and database notes

The runtime database path is repository-local `admission_clean.db`; the committed artifact is `admission_clean.db.gz`. The expected `admission` table used by `query_real_data()` has these queried fields:

- `school`
- `major`
- `score`
- `rank`
- `province`
- `year`

`build_real_db.py` and `build_all_provinces.py` parse `.xls`/`.xlsx` files into SQLite, while `clean_data.py` filters noisy rows into a cleaner DB. These scripts are operational utilities, not part of the normal CLI startup path, and they require path review before use.

`gaokao_data.py` is a standalone Baidu-based realtime admissions search helper. `agent.py` imports it defensively, but the main chat path also has its own `web_search()` implementation.

## Prompt and product behavior

The advisor persona and response constraints live in `system_prompt.md`; the domain methods and school/major knowledge live in `knowledge_base.md`. Changes to either file directly affect model behavior without code changes.

Important product constraints from the prompt files:

- precise admissions numbers must come from the local database, official/user-provided data, or clearly marked search results;
- if data is missing or uncertain, the advisor should say so rather than inventing scores/ranks;
- final advisor replies are intended to sound like natural Chinese conversation, not Markdown reports;
- consultation should collect enough user context before giving detailed school/major recommendations.

## Repository structure worth knowing

- `agent.py` — main interactive CLI, provider config, slot extraction, DB lookup, web search, LLM call.
- `system_prompt.md` — advisor persona, safety/data rules, conversation style.
- `knowledge_base.md` — large gaokao planning knowledge base injected into the model.
- `admission_clean.db.gz` — compressed admissions database used at runtime.
- `gaokao_data.py` — standalone realtime search helper.
- `build_real_db.py`, `build_all_provinces.py`, `clean_data.py`, `real_data.py`, `verify_provinces.py` — data import/cleanup/validation utilities with hardcoded local paths.
- `examples/demo_conversation.md` — realistic manual prompts for smoke testing behavior.
- `zhiyuan-video/` — promotional HTML/video assets; independent from the CLI runtime.

## Existing agent/tooling context

`.cursor/rules.md` and `.devin/rules.md` are generated Trellis pointers. The repository is Trellis-tracked; if using that workflow, relevant commands include:

```bash
trellis status
trellis seed
trellis log
```

The generated Trellis context points to `.trellis/agents/AGENTS.md` for additional Trellis-specific operating context. Root `AGENTS.md` already contains broader repository guidelines; keep this `CLAUDE.md` aligned if those guidelines change.
