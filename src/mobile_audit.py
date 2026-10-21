"""v15 手机/平板真机级审计：python3 mobile_audit.py [base] [--shots] [--scale130] [--quick]
设备：iPhone SE 375×667 / iPhone 14 390×844 / Pro Max 430×932 / Pixel 7 412×915 / 小安卓 360×640 / iPad mini 768×1024 / iPad Pro 1024×1366（isMobile+hasTouch，DPR 2–3）。
页面：今日 / d/ai / d/money / d/growth / d/all / 人物 / 人物页 / 资讯（含打开阅读窗格）/ 趋势 / 往期 / 关于。
检查：横向溢出、被截断的文字（单行 ellipsis / 横向 clip / line-clamp 隐藏内容）、手机字号下限（阅读文字 15 / 次要 13 / 元信息 12）、触控目标 44、展开后内容是否完整可见且滚入视口。--scale130 模拟系统文字放大 130%。"""
import sys,json,os
from playwright.sync_api import sync_playwright
B=next((a for a in sys.argv[1:] if a.startswith('http')),'http://127.0.0.1:8840/'); SHOTS='--shots' in sys.argv; S130='--scale130' in sys.argv
DEV=[('se',375,667,2),('i14',390,844,3),('promax',430,932,3),('pixel7',412,915,2.6),('droid360',360,640,3),('ipadmini',768,1024,2),('ipadpro',1024,1366,2)]
PG=[('today','index.html'),('ai','d/ai.html'),('money','d/money.html'),('growth','d/growth.html'),('all','d/all.html'),('people','people.html'),('person','p/karpathy.html'),('news','news.html'),('trends','trends.html'),('agents','agents.html'),('day','day/2026-10-14.html'),('about','about.html')]
if '--quick' in sys.argv: DEV=[d for d in DEV if d[0] in('se','i14')]
SCALE="""()=>{const k=1.3;document.querySelectorAll('body *').forEach(e=>{if(e.dataset.fs)return;const cs=getComputedStyle(e);e.dataset.fs=1;e.style.setProperty('font-size',(parseFloat(cs.fontSize)*k)+'px','important')})}"""
CHK=r"""(W0)=>{const W=innerWidth,out={};const vis=e=>{const r=e.getBoundingClientRect(),cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'&&!e.closest('[hidden]')};
out.ov=document.documentElement.scrollWidth>W+1?document.documentElement.scrollWidth:0;
out.wide=[...document.querySelectorAll('body *')].filter(x=>{if(!vis(x))return false;const r=x.getBoundingClientRect();return r.right>W+1&&getComputedStyle(x).position!=='fixed'&&!x.closest('.kov,.dcpop')}).slice(0,3).map(x=>x.tagName+'.'+x.className);
const clip=[],clamp=[],small=[];
document.querySelectorAll('body *').forEach(e=>{if(!vis(e))return;const cs=getComputedStyle(e);const hasText=[...e.childNodes].some(n=>n.nodeType===3&&n.textContent.trim().length>1);if(!hasText)return;
 const lc=cs.webkitLineClamp;
 if(lc&&lc!=='none'){if(e.scrollHeight>e.clientHeight+2&&!/\b(ns|gd)\b/.test(e.className))clamp.push(e.tagName+'.'+e.className+' '+JSON.stringify(e.textContent.trim().slice(0,24))+' lc='+lc)}
 else if((cs.textOverflow==='ellipsis'||cs.overflowX==='hidden'||cs.overflow==='hidden')&&cs.display!=='inline'&&e.scrollWidth>e.clientWidth+1)clip.push(e.tagName+'.'+e.className+' '+JSON.stringify(e.textContent.trim().slice(0,24))+' '+e.scrollWidth+'>'+e.clientWidth);
 const fs=parseFloat(cs.fontSize);const len=e.textContent.trim().length;
 if(len>=40&&fs<(innerWidth<=720?14.99:13.99)&&!e.closest('.kpf,footer,.ft,table,.hs,.frp')&&!/\b(tinfo|hint|ns|gd|mu)\b/.test(e.className))small.push('read '+e.tagName+'.'+e.className+':'+fs);
 else if(/\b(tinfo|hint|ns|gd|mu)\b/.test(e.className)&&fs<12.99)small.push('sec '+e.tagName+'.'+e.className+':'+fs);else if(fs<11.99)small.push('meta '+e.tagName+'.'+e.className+':'+fs)});
out.clip=clip.slice(0,6);out.clamp=clamp.slice(0,6);out.small=[...new Set(small)].slice(0,6);
const tap=[];document.querySelectorAll('a[href],button,summary,select,input').forEach(e=>{if(!vis(e)||e.disabled||e.classList.contains('skip'))return;if(e.tagName==='A'&&e.closest('p,li:not(.nr):not(.trw):not(.dh),.pt,.ft,.abt,.nrb,.lead,.pcs,.hint'))return;const r=e.getBoundingClientRect();if(r.bottom<0)return;if(r.height<43.5||r.width<43.5)tap.push((e.className||e.tagName)+':'+Math.round(r.width)+'x'+Math.round(r.height))});out.tap=[...new Set(tap)].slice(0,6);
return out}"""
res={'rows':[],'n':0}
def rec(tag,k,v):
    if v: res['rows'].append((tag,k,v)); print(tag,k,str(v)[:300],flush=True)
os.makedirs('_m',exist_ok=True)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=__import__('os').environ.get('CHROME_PATH') or None,args=['--no-sandbox'])
    for dn,w,h,dpr in DEV:
        c=b.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,is_mobile=True,has_touch=True);c.add_init_script("window.open=()=>null")
        for pn,u in PG:
            g=c.new_page();g.goto(B+u,wait_until='load');g.add_style_tag(content='*{content-visibility:visible!important}');g.wait_for_timeout(500);res['n']+=1;tag=f'{dn}/{pn}'+('/130' if S130 else '')
            if S130: g.evaluate(SCALE);g.wait_for_timeout(200)
            if SHOTS: g.screenshot(path=f'_m/{dn}_{pn}.png',full_page=pn in('today','ai','trends','day','about','money','growth'))
            r=g.evaluate(CHK,w)
            for k in('ov','wide','clip','clamp','small','tap'): rec(tag,k,r[k])
            if pn=='today':
                try:
                    ex=g.locator('.dh .ex').first;ex.scroll_into_view_if_needed();ex.tap();g.wait_for_timeout(500)
                    r2=g.evaluate("()=>{const b=document.querySelector('.dh .ex'),d=document.getElementById(b.getAttribute('aria-controls')),r=d.getBoundingClientRect();return {open:b.getAttribute('aria-expanded'),vis:d.offsetHeight>0,full:d.scrollHeight<=d.clientHeight+1,inview:r.top>=0&&r.top<innerHeight*0.8,ov:[...d.querySelectorAll('*')].some(x=>x.getBoundingClientRect().right>innerWidth+1),txt:[...d.querySelectorAll('.pt')].map(x=>x.scrollHeight>x.clientHeight+2)}}")
                    if r2['open']!='true' or not r2['vis'] or not r2['full'] or r2['ov'] or any(r2['txt']): rec(tag,'expand',r2)
                    if not r2['inview']: rec(tag,'expand-not-scrolled-into-view',r2)
                    if SHOTS: g.screenshot(path=f'_m/{dn}_today_expanded.png')
                    g.evaluate("()=>{document.querySelector('.tl30 .trw summary').click()}");g.wait_for_timeout(300)
                    r3=g.evaluate("()=>{const d=document.querySelector('.tl30 .trw details'),x=d.querySelector('.trx');return {open:d.open,clip:x.scrollHeight>x.clientHeight+1,ov:x.scrollWidth>x.clientWidth+1}}")
                    if not r3['open'] or r3['clip'] or r3['ov']: rec(tag,'top30-expand',r3)
                except Exception as ex: rec(tag,'expand-error',str(ex)[:120])
            if pn=='news':
                try:
                    g.locator('#ntop .nr .nrh').first.tap();g.wait_for_timeout(700)
                    r4=g.evaluate("()=>{const s=document.querySelector('.nside'),pb=document.querySelector('#npbody');return {has:s.classList.contains('open')&&pb.textContent.trim().length>20,full:!(pb.scrollWidth>pb.clientWidth+1),ov:document.documentElement.scrollWidth>innerWidth+1,pane:['block','fixed']}}")
                    rec(tag,'news-open',r4 if (not r4['has'] and not(r4['pane'] and r4['pane'][0]!='none')) or r4['ov'] or r4['full'] is False else None)
                    if SHOTS: g.screenshot(path=f'_m/{dn}_news_open.png')
                except Exception as ex: rec(tag,'news-error',str(ex)[:120])
            g.close()
        c.close()
    b.close()
# ---- 回归：帖子卡片摘录不得压住标签/按钮；折叠的摘录点「展开」/点卡片能展开（Chromium + WebKit/Safari 引擎）----
PJS="""()=>{const R=e=>e.getBoundingClientRect(),bad=[];[...document.querySelectorAll('.post')].filter(p=>p.offsetParent&&!p.hidden).slice(0,40).forEach(p=>{const t=p.querySelector('.pt');if(!t)return;
 const cs=getComputedStyle(t),rg=document.createRange();rg.selectNodeContents(t);const rs=[...rg.getClientRects()].filter(r=>r.height>0);
 const tb=cs.overflow==='visible'?Math.max(R(t).bottom,...rs.map(r=>r.bottom)):R(t).bottom;
 if(cs.overflow==='visible'&&rs.length&&Math.max(...rs.map(r=>r.bottom))>R(t).bottom+2)bad.push('text-outside-box '+p.dataset.k);
 [p.querySelector('.tcs'),p.querySelector('footer')].forEach(x=>{if(x&&tb>R(x).top+1)bad.push('overlap '+x.className+' '+p.dataset.k)})});return bad}"""
with sync_playwright() as p:
    for eng in ('chromium','webkit'):
        try: b=(p.chromium.launch(executable_path=__import__('os').environ.get('CHROME_PATH') or None,args=['--no-sandbox']) if eng=='chromium' else p.webkit.launch())
        except Exception as ex: print('SKIP webkit（无法启动）',str(ex)[:80]) if eng=='webkit' else rec('engine','launch',str(ex)[:80]); continue
        for vw,mob in ((390,True),(820,True),(1440,False)):
            c=b.new_context(viewport={'width':vw,'height':900},is_mobile=mob and eng=='chromium',has_touch=mob)
            for u in ('p/karpathy.html','index.html','d/ai.html','d/all.html'):
                g=c.new_page();tag=f'{eng}{vw}/{u}'
                try:
                    g.goto(B+u,wait_until='load');g.wait_for_timeout(700);res['n']+=1
                    bad=g.evaluate(PJS); rec(tag,'post-overlap',bad[:3] if bad else None)
                    if g.locator('.post .ex2').count():
                        r=g.evaluate("()=>{const b=[...document.querySelectorAll('.post .ex2')].find(x=>x.offsetParent);if(!b)return null;const p=b.closest('.post'),t=p.querySelector('.pt');const h0=t.getBoundingClientRect().height;b.click();return new Promise(ok=>setTimeout(()=>{const h1=t.getBoundingClientRect().height;const o1=p.classList.contains('open');p.querySelector('.pt').click();setTimeout(()=>ok({o1,grow:h1>=h0,closed:!p.classList.contains('open')}),400)},400))}")
                        rec(tag,'post-expand',r if r and not(r['o1'] and r['grow'] and r['closed']) else None)
                        bad2=g.evaluate("()=>{document.querySelectorAll('.post .pt.clp').forEach(t=>t.closest('.post').classList.add('open'));return 1}") and g.evaluate(PJS)
                        rec(tag,'post-overlap-open',bad2[:3] if bad2 else None)
                except Exception as ex: rec(tag,'post-error',str(ex)[:120])
                g.close()
            c.close()
        b.close()
json.dump(res,open('mobile_audit_v15_result.json','w'),ensure_ascii=False,indent=0);print('checked',res['n'],'issues',len(res['rows']))
