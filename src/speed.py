"""冷启动测速：python3 speed.py <base_url> [label]；每页 无节流 + Fast 3G（CDP），记录 FCP/LCP/load/传输字节/请求数"""
import sys,os,json
from playwright.sync_api import sync_playwright
B=sys.argv[1]; PAGES=['index.html','accounts.html','news.html','trends.html','p/karpathy.html']
F3G=dict(offline=False,latency=562.5,downloadThroughput=1.44e6/8*.9,uploadThroughput=675e3/8*.9)
out={}
with sync_playwright() as p:
    b=p.chromium.launch(**({'executable_path':os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}))
    for net in ('none','fast3g'):
        for pg_ in PAGES:
            for vw in (1440,390):
                c=b.new_context(viewport={'width':vw,'height':900});pg=c.new_page();cdp=c.new_cdp_session(pg);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
                if net=='fast3g': cdp.send('Network.emulateNetworkConditions',F3G)
                pg.add_init_script("window.__lcp=0;new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lcp=e.startTime}).observe({type:'largest-contentful-paint',buffered:true})")
                pg.goto(B+pg_,wait_until='load',timeout=120000);pg.wait_for_timeout(1500 if net=='fast3g' else 300)
                r=pg.evaluate("()=>{const n=performance.getEntriesByType('navigation')[0],rs=performance.getEntriesByType('resource');const f=performance.getEntriesByName('first-contentful-paint')[0];return {fcp:Math.round(f?f.startTime:0),lcp:Math.round(window.__lcp),load:Math.round(n.loadEventEnd),kb:Math.round((rs.reduce((s,x)=>s+(x.transferSize||0),0)+n.transferSize)/1024),req:rs.length+1}}")
                out[f'{net}|{pg_}|{vw}']=r;c.close()
    b.close()
print(json.dumps(out))
