"""截图 + 自检：python3 shots.py [base_url]（默认 http://127.0.0.1:8765/，需先在 site/ 下 python3 -m http.server 8765）。截图写入 shots/。"""
import sys,os,json
OUTD=os.path.join(os.path.dirname(os.path.abspath(__file__)),'shots');os.makedirs(OUTD,exist_ok=True)
from playwright.sync_api import sync_playwright
B=sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1:8765/'
J=[('index.html', 'hot_1440_light', 'light', 1440), ('index.html', 'hot_1440_dark', 'dark', 1440), ('index.html', 'hot_390', 'light', 390), ('accounts.html', 'accounts_1440_light', 'light', 1440), ('accounts.html', 'accounts_1440_dark', 'dark', 1440), ('accounts.html', 'accounts_390', 'light', 390), ('news.html', 'news_1440_light', 'light', 1440), ('news.html', 'news_1440_dark', 'dark', 1440), ('news.html', 'news_390', 'light', 390), ('trends.html', 'trends_1440_light', 'light', 1440), ('trends.html', 'trends_1440_dark', 'dark', 1440), ('trends.html', 'trends_390', 'light', 390), ('p/karpathy.html', 'person_1440_light', 'light', 1440), ('p/karpathy.html', 'person_1440_dark', 'dark', 1440), ('p/karpathy.html', 'person_390', 'light', 390)]
CHK='''()=>{const r={};const de=document.documentElement;r.hOverflow=de.scrollWidth>de.clientWidth+1;
const bad=[];document.querySelectorAll('.btn,.seg button,.nav a,.xb').forEach(b=>{if(b.offsetParent===null)return;if(b.scrollWidth>b.clientWidth+1)bad.push(b.textContent.trim())});r.btnOverflow=bad.slice(0,5);
const hs=[];document.querySelectorAll('.post').forEach(p=>{const op=p.querySelector('.op'),cp=p.querySelector('.cp');if(op&&cp&&Math.abs(op.getBoundingClientRect().height-cp.getBoundingClientRect().height)>.5)hs.push(1);
 const pb=p.getBoundingClientRect(),ob=op&&op.getBoundingClientRect();if(ob&&(ob.right>pb.right+.5))hs.push(2)});r.btnMisaligned=hs.length;
const rows={};document.querySelectorAll('#feed .post, .ng .post').forEach(p=>{const b=p.getBoundingClientRect();const k=Math.round(b.top);(rows[k]=rows[k]||[]).push(Math.round(b.height))});r.unequalRows=Object.values(rows).filter(a=>Math.max(...a)-Math.min(...a)>1).length;r.cards=document.querySelectorAll('#feed .post, .ng .post').length;
r.avLoaded=document.querySelectorAll('.av img:not([data-src])').length;r.avatarsBroken=[...document.querySelectorAll('.av img:not([data-src])')].filter(i=>i.complete&&i.naturalWidth===0).length;
const n=performance.getEntriesByType('navigation')[0];r.ttfb=Math.round(n.responseStart);r.dcl=Math.round(n.domContentLoadedEventEnd);r.load=Math.round(n.loadEventEnd);
const fcp=performance.getEntriesByName('first-contentful-paint')[0];r.fcp=fcp?Math.round(fcp.startTime):null;r.bytes=performance.getEntriesByType('resource').reduce((s,x)=>s+(x.transferSize||0),0)+(n.transferSize||0);return r}'''
res={}
with sync_playwright() as p:
    b=p.chromium.launch(**({'executable_path':os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}))
    for u,o,t,w in J:
        c=b.new_context(viewport={'width':w,'height':900 if w>500 else 844},device_scale_factor=1 if w>500 else 2);pg=c.new_page()
        errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.add_init_script(f"localStorage.setItem('xhot-theme','{t}')");pg.goto(B+u,wait_until='load');pg.wait_for_timeout(700)
        r=pg.evaluate(CHK);r['jsErrors']=errs;res[o]=r
        pg.screenshot(path=os.path.join(OUTD,f'shot_{o}.png'),full_page=('trends' in o or 'person' in o or w<500))
        c.close()
    c=b.new_context(viewport={'width':1440,'height':900});pg=c.new_page();pg.goto(B+'news.html');pg.wait_for_timeout(400)
    r0=pg.evaluate("[document.querySelectorAll('.nw').length, document.querySelectorAll('.nw .ex:not([hidden])').length, document.querySelectorAll('.kp').length]")
    pg.click('.nw .ex:not([hidden])');pg.wait_for_timeout(200);r1=pg.evaluate("document.querySelector('.nw.open .nbc').scrollHeight")
    pg.screenshot(path=os.path.join(OUTD,'shot_news_expanded.png'))
    res['interact']=dict(cards_expandable_keyposts=r0,expanded_height=r1)
    b.close()
print(json.dumps(res,ensure_ascii=False,indent=1))
