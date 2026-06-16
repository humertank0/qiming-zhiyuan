#!/usr/bin/env python3
"""Build 启明志愿 promo video HTML animation."""

import base64, os

img_dir = r'E:\桌面\视频照片素材'
imgs = {}
for fname in os.listdir(img_dir):
    path = os.path.join(img_dir, fname)
    with open(path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = 'png' if path.endswith('.png') else 'jpg'
    imgs[fname] = f'data:image/{ext};base64,{b64}'

# 第一页.png 做封面
cover_key = [k for k in imgs if '第一页' in k][0] if any('第一页' in k for k in imgs) else sorted(imgs.keys())[0]
other_keys = sorted([k for k in imgs if k != cover_key])
IMG1 = imgs[cover_key]
IMG2 = imgs[other_keys[0]] if len(other_keys) > 0 else IMG1
IMG3 = imgs[other_keys[1]] if len(other_keys) > 1 else IMG1
IMG4 = imgs[other_keys[2]] if len(other_keys) > 2 else IMG1

anim_path = r'C:/Users/17625/.claude/skills/huashu-design/assets/animations.jsx'
with open(anim_path, 'r', encoding='utf-8') as f:
    anim_js = f.read()

OUT_DIR = r'E:\桌面\启明志愿\zhiyuan-video'
os.makedirs(OUT_DIR, exist_ok=True)

html = f'''<!DOCTYPE html><html lang="zh-CN">
<head><meta charset="UTF-8"><title>启明志愿</title>
<script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#000;overflow:hidden;font-family:"PingFang SC","Microsoft YaHei",sans-serif}}
#root{{width:1920px;height:1080px;position:relative;overflow:hidden}}
#preload{{position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:9999;background:#000}}
#preload img{{width:100%;height:100%;object-fit:cover}}
#preload.done{{opacity:0;transition:opacity 0.3s;pointer-events:none}}
</style></head><body>
<div id="preload"><img src="{IMG1}"/></div>
<div id="root"></div>
<script>window.__ready=true;</script>
<script type="text/babel">
{anim_js}
const{{Stage,Sprite,useTime,useSprite,Easing,interpolate}}=window.Animations;

// 0-2s: Banned video
function Banned() {{
  const{{t}}=useSprite();
  const shake=Math.sin(t*40)*(1-t)*20;
  const op=interpolate(t,[0.08,0.3],[0,1],Easing.easeOut);
  return(<div style={{{{position:'relative',width:'100%',height:'100%',background:'#000',display:'flex',alignItems:'center',justifyContent:'center'}}}}>
    <img src="{IMG1}" style={{{{position:'absolute',width:'110%',height:'110%',objectFit:'cover',transform:`translate(${{shake}}px,${{shake*0.5}}px)`,filter:'brightness(0.5)'}}}}/>
    <div style={{{{color:'#ff3b30',fontSize:80,fontWeight:900,opacity:op,textShadow:'0 0 40px rgba(255,59,48,0.6)',textAlign:'center',zIndex:10}}}}>
      高考志愿<br/>真正难的是信息差
    </div>
  </div>);
}}

// 2-4s: Still here
function StillHere() {{
  const{{t}}=useSprite();
  const op=interpolate(t,[0,0.3,1],[0,1,1],Easing.easeOut);
  return(<div style={{{{background:'linear-gradient(135deg,#1a1a2e,#16213e)',width:'100%',height:'100%',display:'flex',alignItems:'center',justifyContent:'center'}}}}>
    <div style={{{{color:'#fff',fontSize:90,fontWeight:900,opacity:op,textAlign:'center'}}}}>
      但没关系<br/><span style={{{{color:'#4cd964'}}}}>启明志愿</span>还在
    </div>
  </div>);
}}

// 4-8s: Numbers
function Numbers() {{
  const{{t}}=useSprite();
  const items=[
    {{num:'8',label:'本专著',sub:'系统方法论'}},
    {{num:'61',label:'节视频课',sub:'1500+分钟讲解'}},
    {{num:'1932',label:'页资料',sub:'整理成可用知识'}},
    {{num:'792',label:'个本科专业',sub:'梳理就业方向'}},
  ];
  const idx=Math.min(Math.floor(t*items.length),items.length-1);
  const localT=(t*items.length)%1;
  const it=items[idx];
  const sc=interpolate(Math.min(localT,0.3)/0.3,[0,0.3,1],[0.7,1.12,1],Easing.easeOut);
  const op=idx<items.length-1||localT<0.7?1:interpolate(localT,[0.7,1],[1,0],Easing.easeOut);
  return(<div style={{{{background:'#0a0a0a',width:'100%',height:'100%',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}}}}>
    <div style={{{{color:'#999',fontSize:28,marginBottom:20,letterSpacing:3}}}}>系统整理志愿填报资料</div>
    <div style={{{{color:'#ff3b30',fontSize:200,fontWeight:900,opacity:op,transform:`scale(${{sc}})`,textShadow:'0 0 50px rgba(255,59,48,0.4)'}}}}>{{it.num}}</div>
    <div style={{{{color:'#fff',fontSize:52,fontWeight:700,marginTop:10}}}}>{{it.label}}</div>
    <div style={{{{color:'#aaa',fontSize:26,marginTop:8}}}}>{{it.sub}}</div>
  </div>);
}}

// 8-11s: Agent chat demo
function ChatDemo() {{
  const{{t}}=useSprite();
  const op=interpolate(t,[0,0.15,0.85,1],[0,1,1,0],Easing.easeOut);
  return(<div style={{{{background:'#111',width:'100%',height:'100%',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}}}}>
    <div style={{{{opacity:op,width:'75%',background:'#1a1a1a',borderRadius:20,padding:45,boxShadow:'0 30px 80px rgba(0,0,0,0.6)'}}}}>
      <div style={{{{color:'#4cd964',fontSize:28,marginBottom:15}}}}>👤 湖北580分，位次28000...</div>
      <div style={{{{color:'#fff',fontSize:26,lineHeight:1.7}}}}>先问清楚：省份、位次、选科、目标。<br/>再结合家庭情况和地域偏好，<br/>给出更贴近现实的建议。</div>
    </div>
    <div style={{{{color:'#fff',fontSize:36,fontWeight:700,marginTop:25,opacity:op}}}}>先问清楚，再给建议</div>
  </div>);
}}

// 11-14s: 冲稳保 cards
function ChongWenBao() {{
  const{{t}}=useSprite();
  const op=interpolate(t,[0,0.15,0.85,1],[0,1,1,0],Easing.easeOut);
  return(<div style={{{{background:'#0a0a0a',width:'100%',height:'100%',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}}}}>
    <div style={{{{opacity:op,display:'flex',gap:25}}}}>
      <div style={{{{background:'linear-gradient(180deg,#ff3b30,#c0392b)',borderRadius:18,padding:'25px 45px',textAlign:'center'}}}}><div style={{{{color:'#fff',fontSize:18,opacity:0.7}}}}>冲</div><div style={{{{color:'#fff',fontSize:24,fontWeight:700,marginTop:8}}}}>武汉理工</div></div>
      <div style={{{{background:'linear-gradient(180deg,#ff9500,#cc7a00)',borderRadius:18,padding:'25px 45px',textAlign:'center'}}}}><div style={{{{color:'#fff',fontSize:18,opacity:0.7}}}}>稳</div><div style={{{{color:'#fff',fontSize:24,fontWeight:700,marginTop:8}}}}>湖北大学</div></div>
      <div style={{{{background:'linear-gradient(180deg,#4cd964,#34a853)',borderRadius:18,padding:'25px 45px',textAlign:'center'}}}}><div style={{{{color:'#fff',fontSize:18,opacity:0.7}}}}>保</div><div style={{{{color:'#fff',fontSize:24,fontWeight:700,marginTop:8}}}}>三峡大学</div></div>
    </div>
    <div style={{{{color:'#fff',fontSize:42,fontWeight:900,marginTop:35,opacity:op}}}}>冲稳保方向，讲清依据</div>
  </div>);
}}

// 14-16s: 风险提醒
function RiskNote() {{
  const{{t}}=useSprite();
  const sc=interpolate(t,[0,0.08,0.3,1],[0.3,1.3,1,1],Easing.easeOut);
  const op=interpolate(t,[0,0.08],[0,1],Easing.easeOut);
  return(<div style={{{{background:'#000',width:'100%',height:'100%',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}}}}>
    <div style={{{{color:'#ff3b30',fontSize:200,fontWeight:900,opacity:op,transform:`scale(${{sc}})`,textShadow:'0 0 100px rgba(255,59,48,0.5)'}}}}>慎重</div>
    <div style={{{{color:'#fff',fontSize:34,marginTop:15,opacity:op}}}}>不适合的方向，会把风险讲清楚</div>
  </div>);
}}

// 16-18s: Free
function FreeOpen() {{
  const{{t}}=useSprite();
  const op=interpolate(t,[0,0.15,0.85,1],[0,1,1,0],Easing.easeOut);
  return(<div style={{{{background:'linear-gradient(180deg,#0a0a0a,#1a1a2e)',width:'100%',height:'100%',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}}}}>
    <img src="{IMG4}" style={{{{maxWidth:'80%',maxHeight:'65%',objectFit:'contain',opacity:op,borderRadius:12,boxShadow:'0 20px 60px rgba(0,0,0,0.5)'}}}}/>
    <div style={{{{color:'#4cd964',fontSize:52,fontWeight:900,marginTop:20,opacity:op}}}}>免费 · 开源 · 普通家庭也能用</div>
  </div>);
}}

// 18-20s: Ending
function Ending() {{
  const{{t}}=useSprite();
  const op=interpolate(t,[0,0.3,1],[0,1,1],Easing.easeOut);
  return(<div style={{{{background:'#000',width:'100%',height:'100%',display:'flex',alignItems:'center',justifyContent:'center'}}}}>
    <div style={{{{color:'#fff',fontSize:70,fontWeight:900,opacity:op,textAlign:'center',letterSpacing:6}}}}>
      希望每个普通家庭<br/><span style={{{{color:'#4cd964'}}}}>少走一点弯路</span>
    </div>
  </div>);
}}

function Main() {{
  return(<Stage duration={{20}} fps={{30}}>
    <Sprite start={{0}} end={{2}}><Banned/></Sprite>
    <Sprite start={{2}} end={{4}}><StillHere/></Sprite>
    <Sprite start={{4}} end={{8}}><Numbers/></Sprite>
    <Sprite start={{8}} end={{11}}><ChatDemo/></Sprite>
    <Sprite start={{11}} end={{14}}><ChongWenBao/></Sprite>
    <Sprite start={{14}} end={{16}}><RiskNote/></Sprite>
    <Sprite start={{16}} end={{18}}><FreeOpen/></Sprite>
    <Sprite start={{18}} end={{20}}><Ending/></Sprite>
  </Stage>);
}}

const root=ReactDOM.createRoot(document.getElementById('root'));
root.render(<Main/>);
// 隐藏预加载图
setTimeout(()=>{{document.getElementById('preload').classList.add('done');}},100);
</script></body></html>'''

out_path = os.path.join(OUT_DIR, 'index.html')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'HTML written: {len(html)} chars')
print(f'Output: {out_path}')
