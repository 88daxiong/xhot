"""运行时性能剖析：python3 prof.py <base_url> [out.json]；CPU 4x 节流，测长任务、DOM 数、样式/布局/脚本耗时、滚动掉帧、交互延迟"""
import os,sys,json
from playwright.sync_api import sync_playwright
B=sys.argv[1]; OUT=sys.argv[2] if len(sys.argv)>2 else None
PAGES=['index.html','hot.html','accounts.html','news.html','trends.html','p/karpathy.html']
INIT="""window.__lt=[];try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lt.push(Math.round(e.duration))}).observe({type:'longtask',buffered:true})}catch(e){}
window.__lcp=0;try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lcp=e.startTime}).observe({type:'largest-contentful-paint',buffered:true})}catch(e){}"""
# 滚动：每帧滚 60px，共 40 帧，记录帧间隔
SCROLL="""async()=>{const d=[];let last=performance.now();const el=document.scrollingElement;const mx=el.scrollHeight-innerHeight;
for(let i=0;i<60;i++){el.scrollTop=Math.min(mx,i*Math.max(40,mx/60));await new Promise(r=>requestAnimationFrame(r));const n=performance.now();d.push(n-last);last=n}
el.scrollTop=0;await new Promise(r=>requestAnimationFrame(r));d.sort((a,b)=>a-b);const t=d.reduce((a,b)=>a+b,0);return {avg:Math.round(t/d.length*10)/10,p95:Math.round(d[Math.floor(d.length*.95)]),max:Math.round(d[d.length-1]),slow:d.filter(x=>x>50).length}}"""
# 点击后到下一帧绘制完成的耗时
def inter(pg,sel,n=1,pre=None):
    r=[]
    for i in range(n):
        t=pg.evaluate("""async(s)=>{const el=document.querySelectorAll(s)[0];if(!el)return -1;const t0=performance.now();el.click();await new Promise(r=>requestAnimationFrame(()=>setTimeout(r,0)));return Math.round(performance.now()-t0)}""",sel)
        r.append(t)
    return r
out={}
with sync_playwright() as p:
    b=p.chromium.launch(**({'executable_path':os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}))
    for vw in (1440,390):
        for pgn in PAGES:
            c=b.new_context(viewport={'width':vw,'height':900},device_scale_factor=2 if vw==390 else 1);pg=c.new_page();cdp=c.new_cdp_session(pg)
            cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});cdp.send('Performance.enable')
            pg.add_init_script(INIT)
            pg.goto(B+pgn,wait_until='load');pg.wait_for_timeout(1200)
            m={x['name']:x['value'] for x in cdp.send('Performance.getMetrics')['metrics']}
            r=pg.evaluate("()=>({lt:window.__lt,lcp:Math.round(window.__lcp),dom:document.getElementsByTagName('*').length,html:document.documentElement.outerHTML.length})")
            r['tbt']=sum(max(0,x-50) for x in r['lt']);r['nlt']=len(r['lt']);r['maxlt']=max(r['lt'] or [0]);del r['lt']
            r['script']=round(m['ScriptDuration']*1000);r['layout']=round(m['LayoutDuration']*1000);r['style']=round(m['RecalcStyleDuration']*1000);r['task']=round(m['TaskDuration']*1000)
            r['scroll']=pg.evaluate(SCROLL)
            key=f'{vw}|{pgn}'
            if pgn=='news.html' and vw==1440:
                r['click_news']=inter(pg,'#ntop .nr:nth-child(3) .nrh');r['click_news2']=inter(pg,'#ntop .nr:nth-child(5) .nrh')
                r['src_all']=inter(pg,'button[data-src="all"]');r['src_h']=inter(pg,'button[data-src="h"]')
            if pgn=='news.html' and vw==390: r['click_news']=inter(pg,'#ntop .nr .nrh')
            if pgn=='index.html':
                r['expand']=inter(pg,'.dh .ex');
            if pgn=='hot.html':
                r['sort_g']=inter(pg,'[data-sort="g"]');r['sort_t']=inter(pg,'[data-sort="t"]');r['dom_ai']=inter(pg,'button[data-dom="ai"]');r['more']=inter(pg,'#more')
            if pgn=='accounts.html':
                r['sort_f']=inter(pg,'[data-asort="f"]');r['dom_ai']=inter(pg,'button[data-dom="ai"]')
            if pgn.startswith('p/'):
                r['sort']=inter(pg,'[data-sort="g"]')
            out[key]=r;c.close()
    b.close()
s=json.dumps(out,ensure_ascii=False)
if OUT: open(OUT,'w').write(s)
for k,v in out.items(): print(k,json.dumps(v,ensure_ascii=False))
