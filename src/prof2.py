"""滚动期间主线程/光栅耗时（CDP tracing）：python3 prof2.py <base_url> [out.json]；CPU 4x，1440 视口，每页滚到底再回顶"""
import sys,json,os,tempfile
from playwright.sync_api import sync_playwright
B=sys.argv[1]; OUT=sys.argv[2] if len(sys.argv)>2 else None
PAGES=['index.html','hot.html','accounts.html','news.html','trends.html','p/karpathy.html']
SCROLL="""async()=>{const el=document.scrollingElement;const mx=el.scrollHeight-innerHeight;for(let k=0;k<2;k++){for(let i=0;i<=60;i++){el.scrollTop=(k?mx-i*mx/60:i*mx/60);await new Promise(r=>requestAnimationFrame(r))}}el.scrollTop=0;return mx}"""
NAMES={'UpdateLayoutTree','Layout','PrePaint','Paint','Layerize','Commit','RasterTask','FunctionCall','EventDispatch','UpdateLayer','CompositeLayers','HitTest'}
out={}
with sync_playwright() as p:
    b=p.chromium.launch(**({'executable_path':os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}))
    for pgn in PAGES:
        c=b.new_context(viewport={'width':1440,'height':900});pg=c.new_page();cdp=c.new_cdp_session(pg)
        pg.goto(B+pgn,wait_until='load');pg.wait_for_timeout(1500)
        cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        f=tempfile.mktemp(suffix='.json')
        b.start_tracing(page=pg,path=f,categories=['devtools.timeline','disabled-by-default-devtools.timeline','cc','gpu','viz'])
        mx=pg.evaluate(SCROLL)
        b.stop_tracing()
        ev=json.load(open(f));ev=ev['traceEvents'] if isinstance(ev,dict) else ev;os.remove(f)
        agg={}
        for e in ev:
            if e.get('ph')=='X' and e.get('name') in NAMES: agg[e['name']]=agg.get(e['name'],0)+e.get('dur',0)/1000
        out[pgn]={'scrollH':mx,**{k:round(v) for k,v in sorted(agg.items())}}
        c.close()
    b.close()
for k,v in out.items(): print(k,json.dumps(v))
if OUT: json.dump(out,open(OUT,'w'))
