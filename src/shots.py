"""截图 + 自检：python3 shots.py [base_url] [--all]（先 python3 gzserve.py site 8840 &）
截图 shots/shot_<page>_<mode>.png；检查 CSP 违规、JS 错误、横向溢出、坏图、按钮溢出；--all 时额外扫全部个人页与日报页（不截图）。"""
import sys,json,glob,os
from playwright.sync_api import sync_playwright
B=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith('--') else 'http://127.0.0.1:8840/'
ALL='--all' in sys.argv
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.join(D,'site'); SH=os.path.join(D,'shots'); os.makedirs(SH,exist_ok=True)
_dl=sorted(glob.glob(S+'/daily/*.html')); OLD=('daily/'+os.path.basename(_dl[0])) if _dl else 'index.html'
PAGES=[('daily','index.html'),('daily14',OLD),('hot','hot.html'),('accounts','accounts.html'),('news','news.html'),('trends','trends.html'),('person','p/karpathy.html'),('person2','p/dotey.html')]
MODES=[('1440_light',1440,'light'),('1440_dark',1440,'dark'),('390',390,'light')]
INIT="window.__v=[];document.addEventListener('securitypolicyviolation',function(e){window.__v.push(e.violatedDirective+' '+(e.blockedURI||''))});"
CHK="""()=>{const W=innerWidth;const bo=[...document.querySelectorAll('.btn,button')].filter(b=>b.offsetParent&&b.scrollWidth>b.clientWidth+1).map(b=>b.textContent.trim().slice(0,20));
return {v:window.__v,ov:document.documentElement.scrollWidth>W+1,ovEl:[...document.querySelectorAll('body *')].filter(x=>{const r=x.getBoundingClientRect();return r.width&&r.right>W+1&&getComputedStyle(x).position!=='fixed'}).slice(0,3).map(x=>x.className||x.tagName),
br:[...document.images].filter(i=>i.complete&&i.src&&i.naturalWidth===0).length,btnOv:bo.slice(0,4),dsep:document.querySelectorAll('.dsep').length,theme:document.documentElement.dataset.theme}}"""
res={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox'])
    for mn,vw,cs in MODES:
        c=b.new_context(viewport={'width':vw,'height':900},color_scheme=cs,device_scale_factor=1);c.add_init_script(INIT)
        todo=list(PAGES)
        if ALL: todo+=[('x','p/'+os.path.basename(f)) for f in sorted(glob.glob(S+'/p/*.html'))]+[('x','daily/'+os.path.basename(f)) for f in sorted(glob.glob(S+'/daily/*.html'))]
        agg=dict(n=0,csp=[],js=[],ov=[],br=0,btn=[])
        for name,u in todo:
            g=c.new_page();er=[];g.on('pageerror',lambda x:er.append(str(x)[:100]))
            g.on('console',lambda m:er.append('console '+m.text[:100]) if m.type=='error' and 'favicon' not in m.text else None)
            g.on('requestfailed',lambda r:er.append('reqfail '+r.url[-60:]) if 'favicon' not in r.url else None)
            g.goto(B+u,wait_until='load');g.wait_for_timeout(500)
            if name!='x':
                g.mouse.wheel(0,1500);g.wait_for_timeout(300);g.mouse.wheel(0,-3000);g.wait_for_timeout(300)
                g.screenshot(path=os.path.join(SH,f'shot_{name}_{mn}.png'),full_page=(name not in('hot','person','person2','accounts')))
                if name in('hot','person'):
                    g.mouse.wheel(0,2600);g.wait_for_timeout(500);g.screenshot(path=os.path.join(SH,f'shot_{name}_{mn}_scrolled.png'))
                if name=='news':
                    g.click('#ntop .nr .nrh');g.wait_for_timeout(700);g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_expanded.png'))
                    g.click('#nmore');g.wait_for_timeout(400);g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_all.png'))
                if name=='hot':
                    g.click('[data-sort="w"]');g.wait_for_timeout(500);g.click('[data-sort="t"]');g.wait_for_timeout(500);g.click('#more');g.wait_for_timeout(400)
            r=g.evaluate(CHK);agg['n']+=1
            agg['csp']+=[u+' '+x for x in r['v']];agg['js']+=[u+' '+x for x in er]
            if r['ov']:agg['ov'].append(u+' '+str(r['ovEl']))
            agg['br']+=r['br'];agg['btn']+=[u+' '+x for x in r['btnOv']]
            if name!='x':res[f'{name}_{mn}']=dict(dsep=r['dsep'],theme=r['theme'])
            g.close()
        res['SUMMARY_'+mn]=agg;c.close()
    b.close()
print(json.dumps(res,ensure_ascii=False,indent=0))
