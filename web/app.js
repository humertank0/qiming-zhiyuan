const state = {
  sessionId: localStorage.getItem('qiming_session_id') || null,
  mode: localStorage.getItem('qiming_mode') || 'backend',
  providers: [],
  config: null,
  apiKeyMemory: '',
  device: 'desktop',
};

const fallbackProviders = [
  { id: 'deepseek', label: 'DeepSeek', base_url: 'https://api.deepseek.com', model: 'deepseek-chat', requires_key: true, note: '浏览器直连是否可用取决于服务端 CORS。' },
  { id: 'qwen', label: '通义千问', base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1', model: 'qwen-plus', requires_key: true, note: '浏览器直连可能受 CORS 限制。' },
  { id: 'glm', label: '智谱 GLM', base_url: 'https://open.bigmodel.cn/api/paas/v4', model: 'glm-4', requires_key: true, note: '智谱 OpenAI-compatible 接口。浏览器直连可能受 CORS 限制。' },
  { id: 'moonshot', label: 'Moonshot', base_url: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-8k', requires_key: true, note: 'Moonshot OpenAI-compatible 接口。浏览器直连可能受 CORS 限制。' },
  { id: 'openai', label: 'OpenAI', base_url: 'https://api.openai.com/v1', model: 'gpt-4o', requires_key: true, note: 'OpenAI 官方接口通常不建议在浏览器端暴露 Key。' },
  { id: 'custom', label: '自定义 OpenAI-compatible', base_url: '', model: '', requires_key: true, note: '只填写你信任的 API 地址。' },
];

const exampleAnswers = {
  hubeiComputer: `你这情况很典型——湖北580分，2万8位次，普通家庭想靠技术找一条稳一点的路。
我说句实话，你这个分在湖北不差，但也别想985了。

方向很明确：普通家庭没资源，就优先看两条路。
第一，计算机/电子信息。靠技术能力吃饭，对家庭资源依赖相对低。
第二，电气工程。进国家电网、地方国企，稳定性更强。

冲的话——武汉理工。211，工科底子硬。你的位次冲它的计算机有点悬，但电子信息类专业组可以试试。能冲上当然很好，冲不上也正常。

稳的——湖北大学、武汉科技大。这两个在武汉本地口碑很好，580分重点看计算机、电气、电子信息相关方向。长沙理工也可以关注，原电力部的学校，电气就业有优势。

保底——武汉工程大学、三峡大学。三峡大学的电气是原电力部直属，虽然不在武汉，但就业真不差。

提醒你一句：现在计算机行业在分化。基础码农岗位在减少，大学期间必须往 AI、大数据、工程能力上靠，别只停留在课内那点基础。

这是 README 里的本地示例内容，正式填报前还要以湖北省考试院和高校招生网最新专业组数据为准。`,
  henanCivilService: `河南文科510，想考公。方向很明确，但分数确实不算高。

如果你想留在河南、也不怕背书，文科考公优先看汉语言文学、法学、思想政治教育、会计这类岗位覆盖更广的专业。英语要慎重——不是不能学，而是考公岗位相对少，除非你确实有语言优势。

冲的话——河南大学。双一流，法学和汉语言都是考公大户，但这个分数要看当年位次和专业冷热，别只看校名。

稳一点——河南师范大学。汉语言文学、思政都是强项，毕业考公考编都方便，新乡生活成本也低。

还可以看河南财经政法大学，法学、会计学都不错，而且在郑州，实习和考试信息会多一些。

保底可以看洛阳师范、河南科技学院等方向。进去之后别等大四才准备，大一大二就把行测申论的基础打起来。

提醒你：考公这件事，专业比学校重要。汉语言和法学是万金油，但也意味着竞争大，大学四年要把证书、党员、基层实践这些能加分的东西提前规划。`,
  powerGrid: `家里有电力系统资源，那电气这条路就值得认真看。

我跟你说实话，电气这个行业不是只看热不热门，它和行业资源、校招渠道、专业对口关系很大。你要是目标就是国家电网，专业尽量锁定电气工程及其自动化，别被一些名字很像、但不完全对口的专业带偏。

你这个分数可以重点分三档看：

冲——华北电力大学。保定校区或者北京校区都可以关注，电力系统认可度高，电气是核心招牌。

稳——东北电力大学、上海电力大学。这些都是原电力部直属背景，每年电网校招存在感很强。

保底——三峡大学。也是原电力部直属，分数相对没那么高，但电气就业很有特色。

计算机不是不能选，但如果你家里资源确实在电网系统，电气会更顺。资源是敲门砖，本事才是铁饭碗。进了大学该考证、该刷题、该准备校招考试，一样不能松。`,
  financeWarning: `先别急着定金融，我得先问你几个关键问题：家里有人在银行、证券、基金公司吗？有没有能带你入行的亲戚或资源？

如果没有，只是觉得金融听起来高大上、能赚钱，那我建议你慎重。

金融是典型的看起来光鲜，但普通学生进去后落差可能很大的方向。你看到的是年薪百万的基金经理，看不到的是大量普通毕业生在基层网点做柜面、销售和客户维护。

560分在河南，大概率是双非一本或者普通一本层次。这个层次学金融，毕业后要和985、211、财经强校的学生竞争，压力会很大。

如果你是普通家庭、没有金融行业资源，我更建议你看计算机、电气工程、电子信息、自动化这类更靠技术能力吃饭的方向。文科背景也可以优先看法学、汉语言、会计这类考公考编岗位更多的专业。

不是说金融一定不能学，而是普通家庭选专业要算投入产出。别只看名字好听，要看毕业后大多数人去哪。`,
  juniorCollege: `专科不是没有出路。专科选对专业，就业比很多普通本科还强。

关键是别选“名字好听但壁垒弱”的专业。专科阶段更适合选有技能门槛、有行业渠道、能考证、能进一线岗位的方向。

可以重点看三类：

第一，电力类专科。发电厂、电网基层、供电服务相关岗位，稳定性相对好。

第二，铁路类专科。比如铁道交通运营、动车组检修、供电、信号等方向，好的铁路院校校招渠道比较清楚。

第三，医护类专科。护理、医学检验、康复治疗这类，辛苦是真的，但医院和基层医疗长期有人才需求。

市场营销、行政管理、电子商务、物流管理这类专业要慎重，不是完全不能学，而是壁垒弱，专科毕业容易被动。

还有一条路要提前想：专升本。你选学校和专业时，就要看本省专升本政策、学校学习氛围、往年升本情况。专科不是终点，但第一步要选对。`,
  subjectMedicine: `想学医，选科优先看物理 + 化学 + 生物。

这个组合覆盖面最稳，尤其是临床医学、口腔医学、麻醉、医学影像这些方向，很多学校会要求物理和化学，有的还会看生物。你如果一开始就想把医学作为主线，物化生是最不容易被限制的组合。

如果你觉得生物压力太大，物理 + 化学 + 地理也可以关注，但将来报临床、口腔时一定要逐校核对选科要求，不能凭感觉。

千万别为了短期提分轻易选历史方向。选了历史，临床医学这类专业基本会被大面积挡在门外。

另外提醒你：学医是条长路。5年本科、规培、读研，周期长、强度高，35岁前未必能轻松赚钱。家里经济条件一般的话，要跟父母把时间成本说清楚。

如果你真喜欢、也能扛住长期学习，医生是越老越吃香的职业；如果只是觉得“医生稳定”，那就要再想想自己能不能接受这条路的强度。`,
};

const els = {
  messages: document.getElementById('messages'),
  composer: document.getElementById('composer'),
  messageInput: document.getElementById('messageInput'),
  sendButton: document.getElementById('sendButton'),
  resetButton: document.getElementById('resetButton'),
  byokSettings: document.getElementById('byokSettings'),
  backendModeLabel: document.getElementById('backendModeLabel'),
  byokModeLabel: document.getElementById('byokModeLabel'),
  providerSelect: document.getElementById('providerSelect'),
  baseUrlInput: document.getElementById('baseUrlInput'),
  modelInput: document.getElementById('modelInput'),
  apiKeyInput: document.getElementById('apiKeyInput'),
  rememberKeyInput: document.getElementById('rememberKeyInput'),
  testKeyButton: document.getElementById('testKeyButton'),
  testResult: document.getElementById('testResult'),
  quickPrompts: document.getElementById('quickPrompts'),
};

function detectDeviceFromUA() {
  const ua = navigator.userAgent || navigator.vendor || window.opera || '';
  const mobilePattern = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini|Mobile|HarmonyOS/i;
  const isTouchSmall = navigator.maxTouchPoints > 1 && Math.min(window.innerWidth, window.innerHeight) < 900;
  return mobilePattern.test(ua) || isTouchSmall ? 'mobile' : 'desktop';
}

function applyDeviceMode() {
  state.device = detectDeviceFromUA();
  document.documentElement.dataset.device = state.device;
  document.body.classList.toggle('device-mobile', state.device === 'mobile');
  document.body.classList.toggle('device-desktop', state.device === 'desktop');
}

function renderRichText(target, text) {
  target.textContent = '';
  const parts = String(text || '').split(/(\*\*[^*]+\*\*)/g);
  parts.forEach(part => {
    if (part.startsWith('**') && part.endsWith('**') && part.length > 4) {
      const strong = document.createElement('strong');
      strong.textContent = part.slice(2, -2);
      target.appendChild(strong);
    } else if (part) {
      target.appendChild(document.createTextNode(part));
    }
  });
}

function addMessage(role, text, extraClass = '') {
  const wrapper = document.createElement('div');
  wrapper.className = `message ${role} ${extraClass}`.trim();
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  renderRichText(bubble, text);
  wrapper.appendChild(bubble);
  els.messages.appendChild(wrapper);
  els.messages.scrollTop = els.messages.scrollHeight;
  return wrapper;
}

function setBusy(busy) {
  els.sendButton.disabled = busy;
  els.testKeyButton.disabled = busy;
  els.messageInput.disabled = busy;
}

function setMode(mode) {
  if (mode === 'byok' && state.config && state.config.byok_direct_enabled === false) {
    mode = 'backend';
  }
  state.mode = mode;
  localStorage.setItem('qiming_mode', mode);
  document.querySelectorAll('input[name="mode"]').forEach(input => {
    input.checked = input.value === mode;
  });
  els.backendModeLabel.classList.toggle('active', mode === 'backend');
  els.byokModeLabel.classList.toggle('active', mode === 'byok');
  els.byokSettings.classList.toggle('hidden', mode !== 'byok');
}

function currentProvider() {
  return state.providers.find(p => p.id === els.providerSelect.value) || state.providers[0];
}

function applyProvider(provider) {
  if (!provider) return;
  els.baseUrlInput.value = provider.base_url || '';
  els.modelInput.value = provider.model || '';
  const saved = localStorage.getItem(`qiming_api_key_${provider.id}`);
  els.apiKeyInput.value = saved || state.apiKeyMemory || '';
  els.rememberKeyInput.checked = Boolean(saved);
  els.apiKeyInput.placeholder = provider.requires_key ? '只保存在你的浏览器里' : '可留空';
  els.testResult.textContent = provider.note || '';
}

async function loadWebConfig() {
  try {
    const res = await fetch('/api/config');
    state.config = await res.json();
  } catch (_) {
    state.config = { backend_llm_enabled: true, byok_direct_enabled: false };
  }

  const byokEnabled = state.config.byok_direct_enabled !== false;
  els.byokModeLabel.classList.toggle('hidden', !byokEnabled);
  if (!byokEnabled && state.mode === 'byok') {
    state.mode = 'backend';
    localStorage.setItem('qiming_mode', 'backend');
  }
}

async function loadProviders() {
  try {
    const res = await fetch('/api/providers');
    const data = await res.json();
    state.providers = data.providers || fallbackProviders;
  } catch (_) {
    state.providers = fallbackProviders;
  }
  els.providerSelect.innerHTML = '';
  state.providers.forEach(provider => {
    const option = document.createElement('option');
    option.value = provider.id;
    option.textContent = provider.label;
    els.providerSelect.appendChild(option);
  });
  const storedProvider = localStorage.getItem('qiming_provider') || 'deepseek';
  els.providerSelect.value = state.providers.some(p => p.id === storedProvider) ? storedProvider : state.providers[0].id;
  applyProvider(currentProvider());
}

function normalizeChatCompletionsUrl(baseUrl) {
  let url = (baseUrl || '').trim();
  if (!url) throw new Error('请填写 Base URL。');
  url = url.replace(/\/+$/, '');
  if (url.endsWith('/chat/completions')) return url;
  return `${url}/chat/completions`;
}

function buildProviderHeaders(provider, apiKey) {
  const headers = { 'Content-Type': 'application/json' };
  if (provider.requires_key !== false && apiKey) {
    headers.Authorization = `Bearer ${apiKey}`;
  }
  return headers;
}

function persistKeyIfNeeded(providerId) {
  const key = els.apiKeyInput.value.trim();
  state.apiKeyMemory = key;
  if (els.rememberKeyInput.checked) {
    localStorage.setItem(`qiming_api_key_${providerId}`, key);
  } else {
    localStorage.removeItem(`qiming_api_key_${providerId}`);
  }
}

async function callProviderDirect(messages, model, temperature) {
  const provider = currentProvider();
  const apiKey = els.apiKeyInput.value.trim();
  persistKeyIfNeeded(provider.id);

  if (provider.requires_key !== false && !apiKey) {
    throw new Error('请先填写 API Key，或者切换到“使用项目方后端”。');
  }

  const url = normalizeChatCompletionsUrl(els.baseUrlInput.value);
  const body = {
    model: (els.modelInput.value || model || provider.model || '').trim(),
    messages,
    temperature: typeof temperature === 'number' ? temperature : 0.7,
  };
  if (!body.model) throw new Error('请填写模型名。');

  let res;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: buildProviderHeaders(provider, apiKey),
      body: JSON.stringify(body),
    });
  } catch (err) {
    throw new Error('请求失败：可能是 CORS、网络、HTTPS/HTTP 混合内容或服务地址错误。浏览器直连不一定被所有服务商支持。');
  }

  const raw = await res.text();
  let data;
  try { data = JSON.parse(raw); } catch (_) { data = null; }

  if (!res.ok) {
    const detail = (data && data.error && data.error.message) || (data && data.message) || raw.slice(0, 240) || res.statusText;
    if ([401, 403].includes(res.status)) throw new Error(`Key 无效或权限不足：${detail}`);
    if (res.status === 404) throw new Error(`地址或模型名可能不对：${detail}`);
    if (res.status === 402) throw new Error(`账户额度或余额不足：${detail}`);
    throw new Error(`服务商返回 ${res.status}：${detail}`);
  }

  const reply = data && data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content;
  if (!reply) throw new Error('服务商返回格式不符合 OpenAI-compatible Chat Completions。');
  return reply;
}

async function testConnection() {
  els.testResult.textContent = '正在测试...';
  try {
    const reply = await callProviderDirect([{ role: 'user', content: 'hi' }], els.modelInput.value, 0.1);
    els.testResult.textContent = `连接成功：${reply.slice(0, 30) || 'OK'}`;
  } catch (err) {
    els.testResult.textContent = err.message;
  }
}

function looksLikeInvalidOutput(text) {
  return /<\s*\/?\s*tool_call\b|<\s*function\s*=|<\s*parameter\s*=|<\s*\/\s*function\s*>/i.test(String(text || ''));
}

function addProcessMessage() {
  const wrapper = document.createElement('div');
  wrapper.className = 'message assistant process';
  const bubble = document.createElement('div');
  bubble.className = 'bubble process-bubble';

  const title = document.createElement('div');
  title.className = 'process-title';
  title.textContent = '正在处理你的问题';

  const toggleButton = document.createElement('button');
  toggleButton.type = 'button';
  toggleButton.className = 'process-toggle-btn';
  toggleButton.textContent = '收起过程';

  const header = document.createElement('div');
  header.className = 'process-header';
  header.append(title, toggleButton);

  const list = document.createElement('div');
  list.className = 'process-list';

  const actions = document.createElement('div');
  actions.className = 'process-actions';

  bubble.append(header, list, actions);
  wrapper.appendChild(bubble);
  els.messages.appendChild(wrapper);
  els.messages.scrollTop = els.messages.scrollHeight;

  let tick = 0;
  let baseTitle = '正在处理你的问题';
  let latestSteps = [];
  const timer = window.setInterval(() => {
    if (wrapper.classList.contains('done') || wrapper.classList.contains('failed')) return;
    tick = (tick + 1) % 4;
    title.textContent = `${baseTitle}${'.'.repeat(tick)}`;
  }, 450);

  toggleButton.addEventListener('click', () => {
    wrapper.classList.toggle('collapsed');
    toggleButton.textContent = wrapper.classList.contains('collapsed') ? '查看过程' : '收起过程';
  });

  function setSteps(steps) {
    latestSteps = Array.isArray(steps) ? steps : [];
    list.innerHTML = '';
    latestSteps.forEach(step => {
      const item = document.createElement('div');
      item.className = `process-step ${step.status || 'running'}`;
      const dot = document.createElement('span');
      dot.className = 'process-dot';
      const content = document.createElement('div');
      const stepTitle = document.createElement('strong');
      stepTitle.textContent = step.title || '处理中';
      const detail = document.createElement('small');
      detail.textContent = step.detail || '';
      content.append(stepTitle, detail);
      if (Array.isArray(step.items) && step.items.length) {
        const itemList = document.createElement('ul');
        itemList.className = 'process-detail-list';
        step.items.forEach(text => {
          const li = document.createElement('li');
          li.textContent = text;
          itemList.appendChild(li);
        });
        content.appendChild(itemList);
      }
      item.append(dot, content);
      list.appendChild(item);
    });
    els.messages.scrollTop = els.messages.scrollHeight;
  }

  setSteps([
    { title: '接收问题', status: 'done', detail: '已经收到你的描述。' },
    { title: '识别信息和查询数据', status: 'running', detail: '正在识别省份、分数、位次，并查询本地录取数据库。' },
  ]);

  return {
    wrapper,
    setSteps,
    setTitle(nextTitle) {
      baseTitle = nextTitle;
      title.textContent = nextTitle;
    },
    finish(extraSteps) {
      const finalSteps = (extraSteps || latestSteps).map(step => ({
        ...step,
        status: step.status === 'running' ? 'done' : step.status,
      }));
      setSteps(finalSteps);
      window.clearInterval(timer);
      title.textContent = '分析完成';
      wrapper.classList.add('done', 'collapsed');
      toggleButton.textContent = '查看过程';
    },
    fail(message, onRetry) {
      window.clearInterval(timer);
      title.textContent = '这次生成没成功';
      wrapper.classList.add('failed');
      wrapper.classList.remove('collapsed');
      toggleButton.textContent = '收起过程';
      setSteps([{ title: '需要重试', status: 'error', detail: message }]);
      actions.innerHTML = '';
      if (typeof onRetry === 'function') {
        const retryButton = document.createElement('button');
        retryButton.type = 'button';
        retryButton.className = 'process-retry-btn';
        retryButton.textContent = '重新生成';
        retryButton.addEventListener('click', onRetry);
        actions.appendChild(retryButton);
      }
    },
  };
}

async function sendBackend(message, processView) {
  const startRes = await fetch('/api/chat/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: state.sessionId, message }),
  });
  const started = await startRes.json();
  if (!startRes.ok) throw new Error(started.detail || '后端准备上下文失败。');

  state.sessionId = started.session_id;
  localStorage.setItem('qiming_session_id', state.sessionId);
  if (processView) {
    processView.setSteps(started.progress_steps || []);
    processView.setTitle('正在生成志愿建议');
  }

  const completeRes = await fetch('/api/chat/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: state.sessionId, turn_id: started.turn_id }),
  });
  const completed = await completeRes.json();
  if (!completeRes.ok) throw new Error(completed.detail || '后端生成回复失败。');
  if (looksLikeInvalidOutput(completed.reply) || completed.invalid_output_blocked) {
    throw new Error(completed.reply || '模型输出格式不对，请重新生成。');
  }
  if (processView && completed.retry_count > 0) {
    const retrySteps = (started.progress_steps || []).map(step => ({ ...step, status: step.status === 'running' ? 'done' : step.status }));
    retrySteps.push({
      title: '自动重试模型输出',
      status: 'done',
      detail: `检测到模型输出了工具调用格式，已自动重试 ${completed.retry_count} 次。`,
    });
    processView.setSteps(retrySteps);
  }
  return completed.reply;
}

async function sendByok(message) {
  const prepareRes = await fetch('/api/chat/prepare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: state.sessionId, message }),
  });
  const prepared = await prepareRes.json();
  if (!prepareRes.ok) throw new Error(prepared.detail || '后端准备上下文失败。');

  state.sessionId = prepared.session_id;
  localStorage.setItem('qiming_session_id', state.sessionId);

  const assistantReply = await callProviderDirect(prepared.messages, els.modelInput.value || prepared.model_suggestion, prepared.temperature);

  const finalizeRes = await fetch('/api/chat/finalize', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: state.sessionId, turn_id: prepared.turn_id, assistant_reply: assistantReply }),
  });
  const finalized = await finalizeRes.json();
  if (!finalizeRes.ok) {
    addMessage('assistant', assistantReply);
    throw new Error(finalized.detail || '回复已生成，但保存会话失败。');
  }
  return finalized.reply;
}

async function sendMessage(text, options = {}) {
  const message = text.trim();
  if (!message) return;
  const showUser = options.showUser !== false;
  if (showUser) addMessage('user', message);
  els.messageInput.value = '';
  setBusy(true);
  const processView = addProcessMessage();
  try {
    const reply = state.mode === 'byok' ? await sendByok(message) : await sendBackend(message, processView);
    processView.finish();
    addMessage('assistant', reply);
  } catch (err) {
    const errorText = err.message || String(err);
    processView.fail(errorText, () => sendMessage(message, { showUser: false }));
    addMessage('assistant', errorText, 'error');
  } finally {
    setBusy(false);
    els.messageInput.focus();
  }
}

function scrollToChat() {
  const chat = document.getElementById('chat');
  if (chat) chat.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function createElement(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text) el.textContent = text;
  return el;
}

function getExampleModal() {
  let modal = document.getElementById('exampleModal');
  if (modal) return modal;

  modal = document.createElement('div');
  modal.id = 'exampleModal';
  modal.className = 'example-modal hidden';
  Object.assign(modal.style, {
    position: 'fixed',
    inset: '0',
    zIndex: '1000',
    display: 'none',
    placeItems: 'center',
    padding: '20px',
  });
  modal.setAttribute('role', 'dialog');
  modal.setAttribute('aria-modal', 'true');
  modal.setAttribute('aria-labelledby', 'exampleModalTitle');
  modal.innerHTML = `
    <div class="example-modal-backdrop" data-close-example="true"></div>
    <section class="example-modal-card">
      <header class="example-modal-header">
        <div>
          <div class="example-modal-kicker">示例怎么问</div>
          <h2 id="exampleModalTitle"></h2>
          <p>先看一个完整问法和回答，再改成你自己的情况。</p>
        </div>
        <button type="button" class="example-close-btn" data-close-example="true" aria-label="关闭示例">×</button>
      </header>
      <div class="example-modal-body"></div>
      <footer class="example-modal-footer">
        <button type="button" class="example-secondary-btn" data-close-example="true">先自己看看</button>
        <button type="button" class="example-primary-btn">填入聊天框，我改一改</button>
      </footer>
    </section>
  `;
  document.body.appendChild(modal);
  modal.addEventListener('click', event => {
    if (event.target.closest('[data-close-example]')) closeExampleModal();
  });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !modal.classList.contains('hidden')) closeExampleModal();
  });
  return modal;
}

function renderAnswerBlock(text) {
  const block = createElement('div', 'example-answer-block');
  const lines = text.split('\n').map(line => line.trim()).filter(Boolean);

  lines.forEach(line => {
    const match = line.match(/^(冲(?:的话)?|稳(?:的|一点)?|保底(?:可以)?|提醒你一句|提醒你|第一|第二|第三|如果|不是说|千万别)(——|，|：)?(.+)?$/);
    if (match) {
      const row = createElement('div', 'example-answer-line highlighted');
      const tag = createElement('span', 'example-answer-tag', match[1]);
      const content = createElement('span', 'example-answer-text', `${match[2] || ''}${match[3] || ''}`.trim());
      row.append(tag, content);
      block.appendChild(row);
      return;
    }
    block.appendChild(createElement('p', 'example-answer-line', line));
  });

  return block;
}

function renderExampleAnswer(answer) {
  const wrapper = createElement('div', 'example-answer-wrap');
  answer.split(/\n{2,}/).map(part => part.trim()).filter(Boolean).forEach(part => {
    wrapper.appendChild(renderAnswerBlock(part));
  });
  return wrapper;
}

function closeExampleModal() {
  const modal = document.getElementById('exampleModal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.style.display = 'none';
  document.body.classList.remove('modal-open');
}

function showLocalExample(button) {
  const card = button.closest('.case-card');
  const prompt = button.dataset.prompt || '';
  const answer = exampleAnswers[button.dataset.exampleKey] || '这个案例暂无本地示例答案。你可以把自己的情况发到下方对话框，我再帮你分析。';
  const titleEl = card ? card.querySelector('h3') : null;
  const kickerEl = card ? card.querySelector('.case-kicker') : null;
  const title = titleEl ? titleEl.textContent : '示例';
  const kicker = kickerEl ? kickerEl.textContent : '示例怎么问';
  const modal = getExampleModal();

  modal.querySelector('.example-modal-kicker').textContent = kicker;
  modal.querySelector('#exampleModalTitle').textContent = title;

  const body = modal.querySelector('.example-modal-body');
  body.innerHTML = '';

  const questionCard = createElement('section', 'example-question-card');
  questionCard.append(
    createElement('div', 'example-section-label', '示例问题'),
    createElement('div', 'example-question-text', prompt),
  );

  const answerCard = createElement('section', 'example-answer-card');
  answerCard.append(
    createElement('div', 'example-section-label', '示例回答'),
    renderExampleAnswer(answer),
  );

  body.append(questionCard, answerCard);

  const fillButton = modal.querySelector('.example-primary-btn');
  fillButton.onclick = () => {
    els.messageInput.value = prompt;
    closeExampleModal();
    scrollToChat();
    els.messageInput.focus();
  };

  modal.classList.remove('hidden');
  modal.style.display = 'grid';
  document.body.classList.add('modal-open');
}

async function resetSession() {
  try {
    await fetch('/api/reset', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId }),
    });
  } catch (_) {
    // 即便后端失败，也先清空前端显示，用户下一轮会自动新建/恢复会话。
  }
  els.messages.innerHTML = '';
  addMessage('assistant', '已重新开始。你可以重新告诉我省份、分数、位次、选科和目标。');
}

function bindEvents() {
  document.querySelectorAll('input[name="mode"]').forEach(input => {
    input.addEventListener('change', () => setMode(input.value));
  });

  if (els.providerSelect) {
    els.providerSelect.addEventListener('change', () => {
      const provider = currentProvider();
      localStorage.setItem('qiming_provider', provider.id);
      applyProvider(provider);
    });
  }

  if (els.apiKeyInput) {
    els.apiKeyInput.addEventListener('input', () => {
      state.apiKeyMemory = els.apiKeyInput.value.trim();
    });
  }

  if (els.rememberKeyInput) {
    els.rememberKeyInput.addEventListener('change', () => {
      persistKeyIfNeeded(currentProvider().id);
    });
  }

  if (els.testKeyButton) els.testKeyButton.addEventListener('click', testConnection);

  document.querySelectorAll('button[data-example-key]').forEach(button => {
    button.addEventListener('click', event => {
      event.preventDefault();
      event.stopPropagation();
      showLocalExample(button);
    });
  });

  els.composer.addEventListener('submit', event => {
    event.preventDefault();
    sendMessage(els.messageInput.value);
  });

  els.messageInput.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage(els.messageInput.value);
    }
  });

  els.resetButton.addEventListener('click', resetSession);
  window.addEventListener('resize', applyDeviceMode);
}

async function init() {
  applyDeviceMode();
  await loadWebConfig();
  bindEvents();
  setMode(state.mode === 'byok' ? 'byok' : 'backend');
  await loadProviders();
}

init();
