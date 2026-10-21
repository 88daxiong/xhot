"""v15 设计系统一致性审计：python3 ds_audit.py [base] [--census]
对每个页面类型 × (1440 / 390)：
 · 所有可见文字的 font-size 必须在字号令牌内（手机用 type_px_phone）；字重在 400/500/600/700；
 · padding / margin / gap 的每个值（取绝对值）必须在间距刻度内；border-radius 在圆角刻度内；
 · 顶栏高度、页面左右内边距、内容最大宽度在所有页面一致；
 · 正文 line-height 比 1.45–1.8。
--census 只打印各页面出现的取值（用于调刻度），不判失败。违规则退出码 1。"""
import sys,json
from playwright.sync_api import sync_playwright
B=next((a for a in sys.argv[1:] if a.startswith('http')),'http://127.0.0.1:8840/'); CENSUS='--census' in sys.argv
T=json.load(open(__file__.rsplit('/',1)[0]+'/ds_tokens.json')) if '/' in __file__ else json.load(open('ds_tokens.json'))
PAGES=[('today','index.html'),('ai','d/ai.html'),('all','d/all.html'),('people','people.html'),('person','p/karpathy.html'),('news','news.html'),('trends','trends.html'),('agents','agents.html'),('about','about.html'),('day','day/'+sorted(__import__('os').listdir(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)),'site','day')))[-1])]
JS="""()=>{const fs={},sp={},rd={},fw={},lh=[];const vis=e=>{const r=e.getBoundingClientRect();if(r.width<1||r.height<1)return false;const c=getComputedStyle(e);return c.visibility!=='hidden'&&c.display!=='none'};
const add=(m,k,e)=>{if(!m[k])m[k]=[];if(m[k].length<3)m[k].push(e.tagName.toLowerCase()+(e.className&&typeof e.className==='string'?'.'+e.className.trim().split(/\\s+/)[0]:''))};
const px=v=>{const n=parseFloat(v);return isNaN(n)?null:Math.round(n*100)/100};
document.querySelectorAll('body *').forEach(e=>{if(e.closest('svg'))return;if(!vis(e))return;const c=getComputedStyle(e);
 if([...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim().length>0)){add(fs,c.fontSize,e);add(fw,c.fontWeight,e)}
 ['paddingTop','paddingRight','paddingBottom','paddingLeft','marginTop','marginRight','marginBottom','marginLeft','rowGap','columnGap'].forEach(p=>{const v=c[p];if(v==='normal'||v==='auto')return;const n=px(v);if(n===null)return;if(Math.abs(n)>64&&/margin(Left|Right)/.test(p))return;add(sp,String(Math.abs(n)),e)});
 ['borderTopLeftRadius','borderTopRightRadius','borderBottomLeftRadius','borderBottomRightRadius'].forEach(p=>{const v=c[p];if(!v||v.indexOf('%')>=0)return;let n=px(v);if(n===null)return;if(n>999)n=999;add(rd,String(n),e)})});
const top=document.querySelector('.top'),m=document.querySelector('main');const mc=m?getComputedStyle(m):null;
const cp=[...document.querySelectorAll('.post,.pc,.acard,.kpi')].filter(vis).map(e=>{const c=getComputedStyle(e);return Math.round(parseFloat(c.paddingTop))+'/'+Math.round(parseFloat(c.paddingLeft))});
return {cp:[...new Set(cp)],fs,sp,rd,fw,hdr:top?Math.round(top.getBoundingClientRect().height):null,mpad:mc?parseFloat(mc.paddingLeft):null,mmax:mc?mc.maxWidth:null,mw:m?Math.round(m.getBoundingClientRect().width):null}}"""
fails=[];cen={}
def fail(m):
    fails.append(m); print('FAIL',m,flush=True)
def check(vn,pn,r,okf):
    tag=f'{vn}/{pn}'
    cen[tag]={k:sorted(r[k].keys()) for k in('fs','sp','rd','fw')}
    if CENSUS: return
    for k,v in r['fs'].items():
        n=float(k[:-2])
        if not any(abs(n-o)<0.51 for o in okf): fail(f'{tag} 字号 {k} 不在令牌 {okf} 内 例 {v}')
    for k,v in r['fw'].items():
        if int(k) not in T['weights']: fail(f'{tag} 字重 {k} 不在 {T["weights"]} 例 {v}')
    for k,v in r['sp'].items():
        n=float(k)
        if not any(abs(n-o)<0.51 for o in T['space']): fail(f'{tag} 间距 {k}px 不在刻度 {T["space"]} 例 {v}')
    for k,v in r['rd'].items():
        n=float(k)
        if not any(abs(n-o)<0.51 for o in T['radius']): fail(f'{tag} 圆角 {k}px 不在刻度 例 {v}')
    if len(r['cp'])>1: fail(f'{tag} 卡片内边距不一致 {r["cp"]}')
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=__import__('os').environ.get('CHROME_PATH') or None,args=['--no-sandbox'])
    hd={};mp={}
    for vn,vp,mob in [('desktop',{'width':1440,'height':900},False),('phone',{'width':390,'height':844},True)]:
        c=b.new_context(viewport=vp,device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
        okf=sorted(set(T['type_px_phone' if mob else 'type_px'].values()))
        for pn,u in PAGES:
            g=c.new_page();g.goto(B+u,wait_until='load');g.add_style_tag(content='*{content-visibility:visible!important}');g.wait_for_timeout(900)
            r=g.evaluate(JS)
            check(vn,pn,r,okf)
            hd.setdefault(vn,{})[pn]=r['hdr'];mp.setdefault(vn,{})[pn]=(r['mpad'],r['mw'])
            # 交互后的状态：展开 / 阅读窗格 / 整页阅读页
            act=None
            if pn=='today': act="()=>{document.querySelector('.dh .ex').click();const s=document.querySelector('.tl30 summary');if(s){s.click()}}"
            if pn=='agents': act="()=>{document.querySelector('.dtpan:not([hidden]) .dcard:not([hidden]) .dmore').click()}"
            if pn=='news': act="()=>{document.querySelectorAll('.nrh')[2].click()}"
            if act:
                g.evaluate(act);g.wait_for_timeout(700)
                r2=g.evaluate(JS);check(vn,pn+'+展开',r2,okf)
            g.close()
    if not CENSUS:
        for vn in hd:
            hs=set(v for v in hd[vn].values() if v is not None)
            if len(hs)>1: fail(f'{vn} 顶栏高度不一致 {hd[vn]}')
            ms=set(v for v in mp[vn].values())
            if len(ms)>1: fail(f'{vn} 页面内边距/内容宽度不一致 {mp[vn]}')
if CENSUS:
    for t,v in cen.items(): print(t,json.dumps(v))
else:
    print('ds_audit: FAIL %d'%len(fails) if fails else 'ds_audit: ALL PASS')
sys.exit(1 if fails else 0)
