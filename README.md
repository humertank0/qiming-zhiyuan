# 启明志愿 — Web MVP

启明志愿是一个面向高考志愿咨询场景的 Web MVP。项目目标不是替用户做最终决定，而是把省份、分数、位次、选科、专业、城市、家庭资源和就业路径放在一起分析，帮助普通家庭看清机会、风险和需要核实的数据。

当前版本以 **Debian 服务器部署** 为主，不再维护 Windows 一键启动、个人本地小白教程和宣传视频素材。

---

## 核心能力

- FastAPI 后端提供会话、配置、模型调用和静态页面服务。
- 原生 HTML/CSS/JS 前端，自动区分电脑/手机浏览器布局。
- 示例卡片通过弹窗展示本地示例，不消耗模型额度。
- 支持启明后端 Key 调用 OpenAI-compatible 模型服务。
- 可选 BYOK 浏览器直连模式，适合高级用户自行承担浏览器端 Key 风险。
- 本地录取数据库优先用于内部分析参考，不再把原始数据 dump 给用户。
- 顾问语气强调真诚、平等、诚恳，避免居高临下和短视频式劝退。

---

## 服务器快速启动

建议在 Debian 12 / Ubuntu 22.04+ 上使用 Python 3.10+。

```bash
cd /srv/qiming-zhiyuan
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`：

```env
LLM_API_KEY=你的后端模型服务密钥
LLM_BASE_URL=https://api.deepseek.com
LLM_MODEL=deepseek-chat

WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_ENABLE_BACKEND_LLM=true
WEB_ENABLE_BYOK_DIRECT=false
WEB_MAX_SESSIONS=3000
WEB_SESSION_TTL_SECONDS=7200
BACKEND_LLM_CONCURRENCY=80
LLM_REQUEST_TIMEOUT_SECONDS=45
LLM_MAX_TOKENS=1200
MAX_MESSAGE_CHARS=1200
WEB_RATE_LIMIT_ENABLED=true
```

启动：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

浏览器访问：

```text
http://服务器IP:8000
```

---

## systemd 示例

`/etc/systemd/system/qiming-zhiyuan.service`：

```ini
[Unit]
Description=Qiming Zhiyuan Web MVP
After=network.target

[Service]
Type=simple
WorkingDirectory=/srv/qiming-zhiyuan
EnvironmentFile=/srv/qiming-zhiyuan/.env
ExecStart=/srv/qiming-zhiyuan/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=3
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
```

启用：

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now qiming-zhiyuan
sudo systemctl status qiming-zhiyuan
```

---

## Nginx 反代示例

```nginx
server {
    listen 80;
    server_name your-domain.example;

    client_max_body_size 2m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

生产环境建议配置 HTTPS，并在 `.env` 里限制跨域来源：

```env
WEB_CORS_ORIGINS=https://your-domain.example
```

---

## 并发与容量配置

当前后端已按多人在线做基础改造：

- FastAPI 接口使用异步路径，后端模型调用使用 `AsyncOpenAI`，避免单个模型请求阻塞整个 worker。
- 内存会话带 TTL 和最大容量，避免长期运行时会话无限增长。
- 同一会话内用锁串行处理，避免用户连续点击导致上下文错乱。
- 全局模型并发用信号量限制，避免 1000 人同时在线时把上游模型服务打爆。
- 应用内提供轻量 IP/session 限流、输入长度限制和模型超时保护，适合单进程公益项目先上线。

关键环境变量：

```env
WEB_MAX_SESSIONS=3000          # 单个进程最多保留多少个会话
WEB_SESSION_TTL_SECONDS=7200   # 会话多久未使用后过期
BACKEND_LLM_CONCURRENCY=80     # 单个进程同时调用上游模型的最大请求数
LLM_REQUEST_TIMEOUT_SECONDS=45 # 单次模型生成超时时间
LLM_MAX_TOKENS=1200            # 单次模型回答最大输出 token
MAX_MESSAGE_CHARS=1200         # 用户单次输入最大字符数
WEB_CHAT_RATE_LIMIT_PER_MINUTE=6
MAX_HISTORY_MESSAGES=20        # 每个会话保留的历史消息数
```

如果目标是 1000 人同时在线，建议先按这个思路部署：

- 1 个 uvicorn 进程可以承载大量空闲在线用户；真正需要控制的是同时生成回复的人数。
- `BACKEND_LLM_CONCURRENCY` 不要盲目设到 1000，要按模型服务商 QPS、token 速率和服务器带宽来定。
- 如果要开多个 worker，由于当前会话存在进程内存里，需要在 Nginx 做粘性会话，或者后续把会话迁到 Redis。
- 生产环境建议加访问控制、限流和日志监控，否则公网用户可能消耗后端额度。

多 worker 示例：

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --workers 4
```

多 worker 时 Nginx upstream 建议使用 `ip_hash`，确保同一用户的 `/api/chat/start` 和 `/api/chat/complete` 尽量落在同一个 worker：

```nginx
upstream qiming_backend {
    ip_hash;
    server 127.0.0.1:8000;
}
```

如果后续要做真正的水平扩展，下一步应该把 `sessions` 从进程内存迁到 Redis。

---

## 搜索和数据相关性

- 本地录取库只在存在强约束时展示具体条目：明确位次、具体学校、具体专业/职业方向之一。
- 高职单招、对口、艺体、中职、职教、专升本等不可比数据会被过滤。
- 联网搜索只作为辅助核验：搜索引擎用于发现候选网页，进入模型前还会按可信域名和问题相关性评分。
- 优先使用考试院、教育部/阳光高考、高校招生网等官方来源；低相关网页不会展示，也不会作为确定依据。
- 找不到强相关公开来源时，系统会明确说明未核验到足够数据，不能编造分数、位次或招生计划。

关键搜索配置：

```env
SEARCH_TRUSTED_DOMAINS=moe.gov.cn,chsi.com.cn,gaokao.chsi.com.cn,edu.cn,gov.cn,eol.cn,gaokao.cn
SEARCH_MIN_RELEVANCE=6
SEARCH_MAX_RESULTS=5
SEARCH_MAX_QUERIES=4
SEARCH_TIMEOUT_SECONDS=5
SEARCH_MAX_PAGE_BYTES=300000
```

---

## 安全说明

- 真实 `LLM_API_KEY` 只放在 `.env`，不要提交到 Git。
- `.env` 已在 `.gitignore` 中。
- 默认后端模式下，浏览器不会收到后端模型 Key。
- 如果通过公网开放服务，别人可能消耗你的后端额度；后续建议增加访问控制、验证码或登录。
- HTTP 明文访问会暴露用户提问和回答内容，生产环境应使用 HTTPS。
- BYOK 浏览器直连模式会让用户 Key 出现在自己的浏览器环境中，默认建议关闭。
- 违法、危险、隐私侵犯、索要系统提示/密钥、诱导访问内网或本地文件的请求会被拒绝。
- BYOK 回复必须经过 `/api/chat/finalize` 的后端格式化和安全检查；如果保存/检查失败，前端不会直接展示原始模型回复。
- 当前限流是进程内内存实现，适合单机单进程；如果开启多 worker、多机器，建议迁移到 Redis 限流和 Redis session。

---

## 主要接口

```text
GET  /                  前端页面
GET  /api/health        健康检查
GET  /api/config        前端配置
GET  /api/providers     模型 provider 预设
POST /api/chat          后端代理对话（兼容旧调用）
POST /api/chat/start    识别信息、查数据并返回动态过程步骤
POST /api/chat/complete 调用后端模型生成回复
POST /api/chat/prepare  BYOK 直连前的上下文准备
POST /api/chat/finalize BYOK 回复落库与格式化
POST /api/reset         重置会话
```

---

## 项目结构

```text
├── app.py                # FastAPI Web 后端入口
├── advisor_core.py       # 顾问核心逻辑、配置、槽位、数据查询、模型调用
├── web/                  # 原生前端
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── knowledge_base.md     # 志愿填报知识库
├── system_prompt.md      # 顾问行为与语气规则
├── admission_clean.db.gz # 压缩录取数据库，首次运行自动解压
├── requirements.txt      # Python 依赖
├── .env.example          # 环境变量模板
├── CLAUDE.md             # 开发协作说明
└── LICENSE
```

---

## 本地开发

```bash
source .venv/bin/activate
uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

常用检查：

```bash
python -m py_compile advisor_core.py app.py
node --check web/app.js
curl http://127.0.0.1:8000/api/health
```

---

## 免责声明

本工具仅供决策参考，不构成任何形式的专业志愿填报建议。AI 生成内容可能存在错误、过时或不准确。最终志愿填报决定必须以省教育考试院、高校招生网和当年官方招生计划为准。
