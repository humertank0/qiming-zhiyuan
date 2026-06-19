# 启明志愿

把高考志愿里的信息差，讲清楚一点。

启明志愿是一个面向普通家庭的高考志愿咨询辅助项目。它不会替你拍板，也不会承诺“保证录取”，而是把省份、分数、位次、选科、专业、城市、家庭情况和就业目标放在一起看，帮你更清楚地判断：哪些机会值得争取，哪些风险需要提前看见，哪些数据必须回到官方渠道核实。

项目目前是一个可部署的 Web 版本，让学生和家长直接用浏览器咨询。

---

## 它想解决什么问题

很多家庭填志愿时会遇到几个现实问题：

- 只看分数，不知道位次和专业组更关键。
- 只看学校名，不知道专业、城市和就业路径差异很大。
- 只听热门专业，却没想清楚家庭资源、学习能力和行业周期。
- 网上信息很多，但真假、年份、批次、地区经常混在一起。
- 机构话术容易制造焦虑，普通家庭很难判断哪些建议是真的适合自己。

启明志愿希望做的是：

> 用更真诚、平等、接地气的方式，把志愿选择里的机会、风险和信息差讲清楚。

---

## 它怎么帮助填志愿

### 1. 先理解你的真实情况

它会尽量识别这些信息：

- 省份
- 分数
- 位次
- 选科
- 想去的城市
- 感兴趣或排斥的专业
- 家庭资源
- 就业、考公、考研、稳定、高薪等目标

比如你可以直接问：

```text
湖北物理类580分，位次28000，普通家庭，想去武汉学计算机，怎么选？
```

也可以问：

```text
河南文科510分，家在县城，想考公务员，能去哪个学校？
```

或者：

```text
河北物理690分，家里亲戚在电力系统，想进国家电网，怎么选学校？
```

---

### 2. 不只给学校清单，还会讲取舍

启明志愿不会只扔给你一堆院校名字。它会尽量解释：

- 为什么这个方向适合或不适合你；
- 哪些学校可以冲；
- 哪些选择更稳；
- 保底应该注意什么；
- 专业和就业之间有什么关系；
- 普通家庭需要避开什么坑；
- 哪些数据还需要去考试院或高校招生网核实。

例如对“普通家庭想学金融”，它不会只说“金融热门”，而会提醒：金融对学校层次、城市机会和家庭资源要求较高，普通家庭需要认真考虑投入产出。

对“想进国家电网”，它会优先把目标映射到电气、电力相关院校和招聘路径，而不是泛泛推荐热门专业。

---

### 3. 数据只展示强相关内容

项目内置了本地录取数据，但不会把数据库原始表格直接倒给用户。

当前规则是：只有在存在强约束时，才展示具体录取参考，比如：

- 明确位次；
- 明确学校；
- 明确专业；
- 明确职业目标，并能映射到专业方向，比如“国家电网 / 电力系统 → 电气”。

如果用户只说：

```text
河北物理690分，普通家庭，怎么选学校？
```

系统不会随便列一堆分数附近的学校表格，因为那样很容易混入无关批次、无关专业或不可比数据。它会先提示需要补充位次、专业方向或城市偏好。

同时，这些不可比数据会被过滤：

- 高职单招
- 对口招生
- 艺术类
- 体育类
- 中职 / 职教 / 技能类
- 专升本
- 高分段下明显不相关的职业 / 专科院校

---

### 4. 搜索只作辅助核验

启明志愿会在涉及最新政策、招生计划、投档线、学校评价等问题时尝试联网补充信息，但搜索结果不会直接照单全收。

搜索结果会经过：

- 来源可信度判断；
- 省份、学校、专业、年份等相关性匹配；
- 官方来源优先；
- 低相关网页过滤。

优先参考：

- 省教育考试院；
- 教育部 / 阳光高考；
- 高校本科招生网；
- 较可信的教育信息平台。

如果没有找到足够强相关、可信的公开来源，它会明确说明“未核验到足够数据”，而不是编造分数、位次或政策变化。

---

## 适合谁使用

### 适合

- 普通家庭想先理清志愿方向；
- 不知道该优先看学校、专业还是城市；
- 想判断某个专业是否适合自己的家庭情况；
- 想围绕就业、考公、考研、稳定等目标做取舍；
- 想先看一版思路，再去官方渠道核实数据。

### 不适合

- 想让 AI 直接替你决定最终志愿；
- 希望得到“保证录取”的确定答案；
- 不愿意再核对考试院和高校招生网；
- 把 AI 回答当成唯一依据。

---

## 使用时应该怎么问

越具体越好。建议包含：

```text
省份 + 分数 + 位次 + 选科 + 专业/城市偏好 + 家庭情况 + 未来目标
```

示例：

```text
湖北物理类580分，位次28000，普通家庭，想去武汉学计算机，怎么选？
```

```text
河南文科510分，家在县城，想考公务员，专业和学校怎么取舍？
```

```text
河北物理600分，家里亲戚在电力系统，想进国家电网，应该看哪些学校和专业？
```

如果你暂时没想法，也可以直接说：

```text
湖北物理580分，普通家庭，没什么想法，帮我先理一下方向。
```

这时系统会先帮你缩小方向，而不是一上来堆学校清单。

---

## 项目原则

### 真诚、平等、诚恳

启明志愿不希望用居高临下的语气吓唬用户，也不制造焦虑。

它会尽量做到：

- 先接住用户的目标；
- 再分析现实约束；
- 把机会和风险讲清楚；
- 不用短视频式“点破”“别想”“够不着”等压迫表达。

### 不替用户做最终决定

志愿填报是家庭决策。启明志愿只能帮你看清信息、提出问题、整理思路，最终仍要结合当年招生计划、省考试院规则和家庭实际情况决定。

### 不编造确定数字

没有本地数据或可信公开来源支持时，系统应该明确说数据不足，而不是为了显得专业编出分数线、位次或招生计划。

### 保护公益项目成本

项目是纯公益、为爱发电。公网部署时会有基础限流和安全拦截，避免后端模型额度被恶意消耗。

---

## 当前功能

- Web 聊天咨询界面；
- 电脑 / 手机浏览器自动适配；
- 本地示例弹窗，不消耗模型额度；
- 启明后端模型模式，用户不用填写 Key；
- 可选 BYOK 模式，高级用户可以使用自己的模型 Key；
- 本地录取数据强相关查询；
- 过程卡片展示系统识别了什么、查了什么；
- 回答完成后过程自动折叠，可手动展开；
- 模型异常输出自动拦截和重试；
- 基础内容安全和限流保护；

---

## 安全与边界


- 违法、危险、隐私侵犯、索要系统提示 / 密钥、诱导访问内网或本地文件的请求会被拒绝。
- AI 输出会经过基础安全检查，但仍可能存在错误、过时或遗漏。
- 所有志愿结果都必须以省教育考试院、高校招生网和当年官方招生计划为准。

---

## 开源与维护者

本项目由 **幻影** 发起维护，定位是纯公益志愿咨询辅助工具。

GitHub：

```text
https://github.com/humertank0/qiming-zhiyuan
```

欢迎查看代码、反馈问题，也欢迎一起改进。

---

## 部署说明

如果你只是想了解项目，可以先看上面的产品说明。

如果你要自己部署，建议使用 Debian 12 / Ubuntu 22.04+，Python 3.10+。

### 快速启动

```bash
cd /srv/qiming-zhiyuan
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，至少填写：

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

访问：

```text
http://服务器IP:8000
```

健康检查：

```bash
curl http://127.0.0.1:8000/api/health
```

---

## 常用生产配置

```env
WEB_MAX_SESSIONS=3000
WEB_SESSION_TTL_SECONDS=7200
BACKEND_LLM_CONCURRENCY=40
LLM_REQUEST_TIMEOUT_SECONDS=45
LLM_MAX_TOKENS=1200
MAX_MESSAGE_CHARS=1200
WEB_RATE_LIMIT_ENABLED=true
WEB_CHAT_RATE_LIMIT_PER_MINUTE=6
WEB_CHAT_RATE_LIMIT_PER_HOUR=60
WEB_SESSION_RATE_LIMIT_PER_HOUR=30
```

如果通过公网开放服务，建议：

- 使用 HTTPS；
- 放在 Nginx / Cloudflare 后面；
- 不要提交 `.env`；
- 控制后端模型并发和每分钟请求数；
- 先单机部署，稳定后再考虑 Redis 或多机。

---

## systemd 示例

`/etc/systemd/system/qiming-zhiyuan.service`：

```ini
[Unit]
Description=Qiming Zhiyuan Web
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

    client_max_body_size 1m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

生产环境建议配置 HTTPS，并在 `.env` 里限制跨域来源：

```env
WEB_CORS_ORIGINS=https://your-domain.example
```

---

## 项目结构

```text
├── app.py                # FastAPI Web 后端入口
├── advisor_core.py       # 顾问核心逻辑、槽位、数据查询、搜索、安全和模型调用
├── web/                  # 原生前端页面
│   ├── index.html
│   ├── app.js
│   ├── styles.css
│   └── assets/
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
