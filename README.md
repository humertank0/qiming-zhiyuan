# 启明志愿 — Web MVP

启明志愿是一个面向高考志愿咨询场景的 Web MVP。项目目标不是替用户做最终决定，而是把省份、分数、位次、选科、专业、城市、家庭资源和就业路径放在一起分析，帮助普通家庭看清机会、风险和需要核实的数据。

当前版本以 **Debian 服务器部署** 为主，不再维护 Windows 一键启动、个人本地小白教程和宣传视频素材。

---

## 核心能力

- FastAPI 后端提供会话、配置、模型调用和静态页面服务。
- 原生 HTML/CSS/JS 前端，自动区分电脑/手机浏览器布局。
- 示例卡片通过弹窗展示本地示例，不消耗模型额度。
- 支持项目方后端 Key 调用 OpenAI-compatible 模型服务。
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

## 安全说明

- 真实 `LLM_API_KEY` 只放在 `.env`，不要提交到 Git。
- `.env` 已在 `.gitignore` 中。
- 默认后端模式下，浏览器不会收到后端模型 Key。
- 如果通过公网开放服务，别人可能消耗你的后端额度；后续建议增加访问控制、验证码或登录。
- HTTP 明文访问会暴露用户提问和回答内容，生产环境应使用 HTTPS。
- BYOK 浏览器直连模式会让用户 Key 出现在自己的浏览器环境中，默认建议关闭。

---

## 主要接口

```text
GET  /                  前端页面
GET  /api/health        健康检查
GET  /api/config        前端配置
GET  /api/providers     模型 provider 预设
POST /api/chat          后端代理对话
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
