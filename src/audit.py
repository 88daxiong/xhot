"""v15 可读性审计：python3 audit.py [base_url] [--theme light|dark|both] [pages...]
逐页（1440 + 390，浅色 + 深色）收集所有可见文字：字号、字重、行高、WCAG 对比度（前景 vs 有效背景，渐变取最差色标，半透明按祖先逐层合成），
输出：字号分布、过细字重、低于 4.5:1 的元素（按类名聚合）。也被 shots.py 的断言复用。"""
import sys,json,os
from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8840/'; pages=[]
for a in sys.argv[1:]:
    if a.startswith('http'): B=a
    elif not a.startswith('--'): pages.append(a)
pages=pages or ['index.html','day/2026-10-14.html','d/ai.html','d/all.html','people.html','p/karpathy.html','news.html','trends.html']
JS=r"""()=>{
function parse(c){const m=c.match(/rgba?\(([^)]+)\)/);if(!m)return null;const p=m[1].split(/[ ,\/]+/).filter(Boolean).map(Number);return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}}
function over(f,b){const a=f.a;return {r:f.r*a+b.r*(1-a),g:f.g*a+b.g*(1-a),b:f.b*a+b.b*(1-a),a:1}}
function lum(c){const f=v=>{v/=255;return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4)};return 0.2126*f(c.r)+0.7152*f(c.g)+0.0722*f(c.b)}
function cr(a,b){const x=lum(a),y=lum(b);return (Math.max(x,y)+0.05)/(Math.min(x,y)+0.05)}
const root=getComputedStyle(document.documentElement);
function bgs(el){ // 返回可能的背景色列表（渐变取各色标）
  let stack=[];let e=el;
  while(e&&e.nodeType===1){const cs=getComputedStyle(e);const bc=parse(cs.backgroundColor);const bi=cs.backgroundImage;
    let stops=[];if(bi&&bi!=='none'){(bi.match(/rgba?\([^)]+\)/g)||[]).forEach(s=>{const p=parse(s);if(p)stops.push(p)})}
    stack.push({bc,stops});if(bc&&bc.a===1&&!stops.length)break;e=e.parentElement}
  let bases=[parse(getComputedStyle(document.body).backgroundColor)||{r:255,g:255,b:255,a:1}];if(bases[0].a<1)bases=[over(bases[0],{r:255,g:255,b:255,a:1})];
  for(let i=stack.length-1;i>=0;i--){const L=stack[i];let nb=[];
    for(const base of bases){let cur=base;if(L.bc&&L.bc.a>0)cur=over(L.bc,cur);
      if(L.stops.length){for(const s of L.stops)nb.push(over(s,cur))}else nb.push(cur)}
    bases=nb}
  return bases}
const out=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;const seen=new Set();
while(n=w.nextNode()){const t=n.textContent.trim();if(!t)continue;const p=n.parentElement;if(!p||/^(SCRIPT|STYLE|NOSCRIPT)$/.test(p.tagName))continue;
  const r=p.getBoundingClientRect();if(r.width<2||r.height<2)continue;const cs=getComputedStyle(p);if(cs.visibility==='hidden'||cs.display==='none'||+cs.opacity===0)continue;
  let o=1,e=p;while(e&&e!==document.body){o*=+getComputedStyle(e).opacity;e=e.parentElement}
  if(p.closest('[hidden],[aria-hidden=true],[disabled],.dis'))continue;if(r.right<=0||r.bottom<=0||r.left<-50)continue;
  const fg=parse(cs.color);const B=bgs(p);let worst=99;for(const b of B){const f=over({r:fg.r,g:fg.g,b:fg.b,a:fg.a*o},b);worst=Math.min(worst,cr(f,b))}
  const key=p.tagName+'.'+(p.className||'')+'|'+cs.fontSize+'|'+cs.fontWeight;if(seen.has(key))continue;seen.add(key);
  out.push({k:p.tagName+'.'+String(p.className||'').slice(0,40),t:t.slice(0,16),fs:parseFloat(cs.fontSize),fw:+cs.fontWeight,lh:cs.lineHeight==='normal'?0:parseFloat(cs.lineHeight)/parseFloat(cs.fontSize),ls:cs.letterSpacing,cr:+worst.toFixed(2),ff:cs.fontFamily.slice(0,30)})}
return out}"""
res={};
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=(os.environ.get('CHROME_PATH') or None),args=['--no-sandbox'])
    for th in ('light','dark'):
        for vw in (1440,390):
            for u in pages:
                c=b.new_context(viewport={'width':vw,'height':900 if vw>600 else 844},color_scheme=th);g=c.new_page();g.goto(B+u,wait_until='load');g.wait_for_timeout(700)
                res[f'{u}|{th}|{vw}']=g.evaluate(JS);c.close()
json.dump(res,open('audit_v15.json','w'),ensure_ascii=False)
import collections
fs=collections.Counter();low=collections.defaultdict(list);thin=set();lh=[]
for k,v in res.items():
    for x in v:
        fs[x['fs']]+=1
        if x['cr']<4.5: low[(x['k'],x['fs'])].append((k,x['cr'],x['t']))
        if x['fw']<400: thin.add((x['k'],x['fw']))
print('字号分布',sorted(fs.items()))
print('字重<400',sorted(thin)[:10])
print('对比度<4.5 的元素种类',len(low))
for (k,f),v in sorted(low.items(),key=lambda z:min(a[1] for a in z[1]))[:40]: print(f'  {k} {f}px  min={min(a[1] for a in v)}  例 {v[0][0]} {v[0][2]!r}  ×{len(v)}')
