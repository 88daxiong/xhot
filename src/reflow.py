"""整页回流耗时（CPU 4x）：python3 reflow.py <base_url>；改 body 字号强制整页重排，取中位数（ms）"""
import os,sys,json
from playwright.sync_api import sync_playwright
B=sys.argv[1]
JS="""()=>{const t=[];for(let i=0;i<9;i++){document.body.style.fontSize=(14+(i%2)*.01)+'px';const a=performance.now();document.body.offsetHeight;t.push(performance.now()-a)}document.body.style.fontSize='';t.sort((a,b)=>a-b);return Math.round(t[4]*10)/10}"""
out={}
with sync_playwright() as p:
    b=p.chromium.launch(**({'executable_path':os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}))
    for pg_ in ['index.html','hot.html','accounts.html','news.html','trends.html','p/karpathy.html']:
        for vw in (1440,390):
            c=b.new_context(viewport={'width':vw,'height':900});pg=c.new_page();cdp=c.new_cdp_session(pg);pg.goto(B+pg_,wait_until='load');pg.wait_for_timeout(800)
            cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});out[f'{pg_}|{vw}']=pg.evaluate(JS);c.close()
    b.close()
print(json.dumps(out))
