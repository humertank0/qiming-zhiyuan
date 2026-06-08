#!/usr/bin/env python3
"""Build the promotional video HTML animation."""

import base64, os, sys

# Read images
img_dir = r'E:\桌面\视频照片素材'
imgs = {}
for fname in sorted(os.listdir(img_dir)):
    path = os.path.join(img_dir, fname)
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = 'png' if path.endswith('.png') else 'jpg'
    imgs[fname] = f'data:image/{ext};base64,{b64}'
    print(f'Loaded {fname}: {len(b64)/1024:.0f}KB')

names = sorted(imgs.keys())
IMG_SCIFI = imgs[names[0]]
IMG_SCR1 = imgs[names[1]] if len(imgs) > 1 else ''
IMG_SCR2 = imgs[names[2]] if len(imgs) > 2 else ''
IMG_GH = imgs[names[3]] if len(imgs) > 3 else ''

# Read animations.jsx
anim_path = r'C:/Users/17625/.claude/skills/huashu-design/assets/animations.jsx'
with open(anim_path, 'r', encoding='utf-8') as f:
    anim_js = f.read()

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>雪峰Agent 宣传视频</title>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:#000; overflow:hidden; font-family:'PingFang SC','Microsoft YaHei',sans-serif; user-select:none; }}
#root {{ width:1920px; height:1080px; position:relative; overflow:hidden; }}
.big-red {{ color:#ff3b30; font-weight:900; text-shadow:0 0 80px rgba(255,59,48,0.6); }}
.centered {{ display:flex; align-items:center; justify-content:center; width:100%; height:100%; }}
</style>
</head>
<body>
<div id="root"></div>
<script>window.__ready = true;</script>
<script type="text/babel">
{anim_js}

const {{ Stage, Sprite, useTime, useSprite, Easing, interpolate }} = window.Animations;

const IMG_SCIFI = "{IMG_SCIFI}";
const IMG_SCR1 = "{IMG_SCR1}";
const IMG_SCR2 = "{IMG_SCR2}";
const IMG_GH = "{IMG_GH}";

function FullImage({{ src, brightness, scale, offsetX, offsetY }}) {{
  const s = scale || 1;
  const ox = offsetX || 0;
  const oy = offsetY || 0;
  const b = brightness || 1;
  return (
    <img src={{src}} style={{{{
      position:'absolute', top:0, left:0, width:'100%', height:'100%',
      objectFit:'cover', transform:`scale(${{s}}) translate(${{ox}}px,${{oy}}px)`,
      filter:`brightness(${{b}})`
    }}}} />
  );
}}

// 0-3s: Opening
function OpeningShock() {{
  const {{ t }} = useSprite();
  const shakeX = Math.sin(t * 40) * (1 - t) * 25;
  const shakeY = Math.cos(t * 35) * (1 - t) * 15;
  const scale = 1 + (1 - t) * 0.1;
  const redOp = interpolate(t, [0.05, 0.2], [0, 1], Easing.easeOut);
  const textScale = interpolate(t, [0.05, 0.15], [0.5, 1], Easing.easeOut);
  return (
    <div style={{{{ position:'relative', width:'100%', height:'100%' }}}}>
      <img src={{IMG_SCIFI}} style={{{{
        position:'absolute', top:0, left:0, width:'110%', height:'110%',
        objectFit:'cover', transform:`scale(${{scale}}) translate(${{shakeX}}px,${{shakeY}}px)`,
        filter:`brightness(0.6)`
      }}}} />
      <div style={{{{ position:'absolute', top:'40%', left:'50%', transform:`translate(-50%,-50%) scale(${{textScale}})`, textAlign:'center', zIndex:10 }}}}>
        <div style={{{{ color:'#ff3b30', fontSize:140, fontWeight:900, opacity:redOp,
          textShadow:'0 0 60px rgba(255,59,48,0.8), 0 0 120px rgba(255,59,48,0.4)' }}}}>
          不可以！绝对不可以！
        </div>
      </div>
    </div>
  );
}}

// 3-5s: Warm
function WarmMsg() {{
  const {{ t }} = useSprite();
  const opacity = interpolate(t, [0, 0.3, 1], [0, 1, 1], Easing.easeOut);
  const y = interpolate(t, [0, 1], [40, 0], Easing.easeOut);
  return (
    <div style={{{{ background:'linear-gradient(135deg, #2d1b69 0%, #c0392b 100%)', width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center' }}}}>
      <div style={{{{ color:'#fff', fontSize:100, fontWeight:900, opacity, transform:`translateY(${{y}}px)` }}}}>
        高中毕业生有福了
      </div>
    </div>
  );
}}

// 5-14s: Numbers Jump (LONGER - core selling point)
function NumbersJump() {{
  const {{ t }} = useSprite();
  const items = [
    {{ num:'8', label:'本专著', sub:'雪峰老师原版著作', extra:'从就业看专业 · 手把手报志愿 · 考研通关攻略' }},
    {{ num:'61', label:'节视频课', sub:'1500+分钟专业讲解', extra:'高考志愿填报 · 大学专业详解 · 避坑指南' }},
    {{ num:'1932', label:'页资料', sub:'全部学进脑子', extra:'OCR提取 · 逐页分析 · 结构化整理' }},
    {{ num:'792', label:'个本科专业', sub:'挨个分析就业出路', extra:'12大学科门类全覆盖' }},
  ];
  const idx = Math.min(Math.floor(t * items.length), items.length - 1);
  const localT = (t * items.length) % 1;
  const item = items[idx];
  const scale = interpolate(Math.min(localT, 0.3) / 0.3, [0, 0.3, 1], [0.7, 1.12, 1], Easing.easeOut);
  const opacity = idx < items.length - 1 || localT < 0.7 ? 1 : interpolate(localT, [0.7, 1], [1, 0], Easing.easeOut);
  const extraOpacity = interpolate(localT, [0.15, 0.35], [0, 1], Easing.easeOut);

  return (
    <div style={{{{ background:'#0a0a0a', width:'100%', height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}}}>
      <div style={{{{ color:'#999', fontSize:30, marginBottom:30, letterSpacing:4, opacity:1, fontWeight:300 }}}}>
        它蒸馏了雪峰老师的知识体系
      </div>
      <div style={{{{ color:'#ff3b30', fontSize:220, fontWeight:900, opacity, transform:`scale(${{scale}})`, textShadow:'0 0 60px rgba(255,59,48,0.4)', transition:'all 0.4s ease-out' }}}}>
        {{item.num}}
      </div>
      <div style={{{{ color:'#fff', fontSize:56, fontWeight:700, marginTop:15, opacity }}}}>
        {{item.label}}
      </div>
      <div style={{{{ color:'#ccc', fontSize:30, marginTop:10, opacity }}}}>
        {{item.sub}}
      </div>
      <div style={{{{ color:'#888', fontSize:22, marginTop:25, opacity:extraOpacity, letterSpacing:2 }}}}>
        {{item.extra}}
      </div>
    </div>
  );
}}

// 9-12s: Agent Flow - show agent screenshot
function AgentFlow() {{
  const {{ t }} = useSprite();
  const opacity = interpolate(t, [0, 0.15, 0.85, 1], [0, 1, 1, 0], Easing.easeOut);
  const y = interpolate(t, [0, 1], [30, 0], Easing.easeOut);
  return (
    <div style={{{{ background:'#111', width:'100%', height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}}}>
      <div style={{{{ opacity, transform:`translateY(${{y}}px)`, width:'80%', background:'#1a1a1a', borderRadius:20, padding:50, boxShadow:'0 30px 80px rgba(0,0,0,0.6)' }}}}>
        <div style={{{{ color:'#4cd964', fontSize:32, marginBottom:20 }}}}>👤 湖北物理580分，位次28000...</div>
        <div style={{{{ color:'#fff', fontSize:28, lineHeight:1.8 }}}}>
          你这情况很典型——普通家庭想靠技术吃饭。<br/>
          我说句实话，你这个分在湖北不差。<br/>
          冲的话——武汉理工。稳的——湖北大学。<br/>
          保底——武汉工程大学、三峡大学。
        </div>
      </div>
      <div style={{{{ color:'#fff', fontSize:38, fontWeight:700, marginTop:30, opacity, textShadow:'0 2px 10px rgba(0,0,0,0.8)' }}}}>
        先追着你问清楚底细，再给方案
      </div>
    </div>
  );
}}

// 12-15s: Output
function ResultOutput() {{
  const {{ t }} = useSprite();
  const opacity = interpolate(t, [0, 0.15, 0.85, 1], [0, 1, 1, 0], Easing.easeOut);
  const scale = interpolate(t, [0, 0.15, 0.5, 1], [0.9, 1, 1, 0.95], Easing.easeOut);
  return (
    <div style={{{{ background:'#0a0a0a', width:'100%', height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}}}>
      <div style={{{{ opacity, transform:`scale(${{scale}})`, display:'flex', gap:30 }}}}>
        <div style={{{{ background:'linear-gradient(180deg, #ff3b30 0%, #c0392b 100%)', borderRadius:20, padding:'30px 50px', textAlign:'center' }}}}>
          <div style={{{{ color:'#fff', fontSize:20, opacity:0.7 }}}}>🔴 冲</div>
          <div style={{{{ color:'#fff', fontSize:26, fontWeight:700, marginTop:10 }}}}>武汉理工大学</div>
        </div>
        <div style={{{{ background:'linear-gradient(180deg, #ff9500 0%, #cc7a00 100%)', borderRadius:20, padding:'30px 50px', textAlign:'center' }}}}>
          <div style={{{{ color:'#fff', fontSize:20, opacity:0.7 }}}}>🟡 稳</div>
          <div style={{{{ color:'#fff', fontSize:26, fontWeight:700, marginTop:10 }}}}>湖北大学</div>
        </div>
        <div style={{{{ background:'linear-gradient(180deg, #4cd964 0%, #34a853 100%)', borderRadius:20, padding:'30px 50px', textAlign:'center' }}}}>
          <div style={{{{ color:'#fff', fontSize:20, opacity:0.7 }}}}>🟢 保</div>
          <div style={{{{ color:'#fff', fontSize:26, fontWeight:700, marginTop:10 }}}}>三峡大学</div>
        </div>
      </div>
      <div style={{{{ color:'#fff', fontSize:44, fontWeight:900, marginTop:40, opacity }}}}>
        冲稳保三档，一口气全给你
      </div>
    </div>
  );
}}

// 15-17s: Dont Touch
function DontTouch() {{
  const {{ t }} = useSprite();
  const scale = interpolate(t, [0, 0.08, 0.3, 1], [0.3, 1.3, 1, 1], Easing.easeOut);
  const opacity = interpolate(t, [0, 0.08], [0, 1], Easing.easeOut);
  return (
    <div style={{{{ background:'#000', width:'100%', height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}}}>
      <div style={{{{ color:'#ff3b30', fontSize:220, fontWeight:900, opacity, transform:`scale(${{scale}})`, textShadow:'0 0 100px rgba(255,59,48,0.5), 0 0 200px rgba(255,59,48,0.3)' }}}}>
        别碰
      </div>
      <div style={{{{ color:'#fff', fontSize:36, marginTop:20, opacity }}}}>
        不适合你的专业，它真敢说别碰
      </div>
    </div>
  );
}}

// 17-19s: GitHub screenshot
function GitHubFree() {{
  const {{ t }} = useSprite();
  const opacity = interpolate(t, [0, 0.1, 0.9, 1], [0, 1, 1, 0], Easing.easeOut);
  const scale = interpolate(t, [0, 0.15, 0.7, 1], [0.95, 1.02, 1.02, 0.98], Easing.easeOut);
  return (
    <div style={{{{ background:'#0a0a0a', width:'100%', height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center' }}}}>
      <img src={{IMG_GH}} style={{{{
        maxWidth:'85%', maxHeight:'75%', objectFit:'contain',
        opacity, transform:`scale(${{scale}})`,
        borderRadius:12, boxShadow:'0 20px 60px rgba(0,0,0,0.5)'
      }}}} />
      <div style={{{{ color:'#fff', fontSize:44, fontWeight:900, marginTop:25, opacity, textShadow:'0 2px 10px rgba(0,0,0,0.8)' }}}}>
        免费 · 开源 · 拿去用
      </div>
    </div>
  );
}}

// 19-20s: Ending
function Ending() {{
  const {{ t }} = useSprite();
  const opacity = interpolate(t, [0, 0.3, 1], [0, 1, 1], Easing.easeOut);
  return (
    <div style={{{{ background:'#000', width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center' }}}}>
      <div style={{{{ color:'#fff', fontSize:130, fontWeight:900, opacity, letterSpacing:10 }}}}>
        雪峰 agent
      </div>
      <div style={{{{ position:'absolute', bottom:50, right:60, color:'rgba(255,255,255,0.25)', fontSize:14, fontFamily:'monospace', letterSpacing:2 }}}}>
        Created by Huashu-Design
      </div>
    </div>
  );
}}

// Main
function MainScene() {{
  return (
    <Stage duration={{25}} fps={{30}}>
      <Sprite start={{0}} end={{3}}><OpeningShock /></Sprite>
      <Sprite start={{3}} end={{5}}><WarmMsg /></Sprite>
      <Sprite start={{5}} end={{14}}><NumbersJump /></Sprite>
      <Sprite start={{14}} end={{17}}><AgentFlow /></Sprite>
      <Sprite start={{17}} end={{20}}><ResultOutput /></Sprite>
      <Sprite start={{20}} end={{22}}><DontTouch /></Sprite>
      <Sprite start={{22}} end={{24}}><GitHubFree /></Sprite>
      <Sprite start={{24}} end={{25}}><Ending /></Sprite>
    </Stage>
  );
}}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<MainScene />);
</script>
</body>
</html>'''

out_path = r'E:\桌面\张雪峰agent\xuefeng-promo-video\index.html'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nDone! HTML written to: {out_path}')
print(f'Size: {len(html)} chars')
