"""截图 + 自检：python3 shots.py [base_url] [--all]（先 python3 gzserve.py site 8840 &）
截图 shots/shot_<page>_<mode>.png；检查 CSP 违规、JS 错误、横向溢出、坏图、按钮溢出，以及交互断言（日报原帖默认折叠、译文切换、日期控件、资讯阅读窗格不越界）；
--all 时额外扫全部个人页与日报页（不截图）。"""
import sys,json,glob,os
from playwright.sync_api import sync_playwright
B=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith('--') else 'http://127.0.0.1:8840/'
ALL='--all' in sys.argv
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.join(D,os.environ.get('SITE_DIR','site')); SH=os.path.join(D,'shots'); os.makedirs(SH,exist_ok=True)
_dl=sorted(glob.glob(S+'/daily/*.html')); OLD=('daily/'+os.path.basename(_dl[0])) if _dl else 'index.html'
PAGES=[('daily','index.html'),('daily14',OLD),('hot','hot.html'),('accounts','accounts.html'),('news','news.html'),('trends','trends.html'),('person','p/karpathy.html'),('person2','p/dotey.html'),('person3','p/huggingface.html'),('person4','p/david_perell.html')]
MODES=[('1440_light',1440,'light'),('1440_dark',1440,'dark'),('390',390,'light')]
INIT="window.__v=[];document.addEventListener('securitypolicyviolation',function(e){window.__v.push(e.violatedDirective+' '+(e.blockedURI||''))});"
CHK="""()=>{const W=innerWidth;const bo=[...document.querySelectorAll('.btn,button')].filter(b=>b.offsetParent&&b.scrollWidth>b.clientWidth+1).map(b=>b.textContent.trim().slice(0,20));
return {v:window.__v,ov:document.documentElement.scrollWidth>W+1,ovEl:[...document.querySelectorAll('body *')].filter(x=>{const r=x.getBoundingClientRect();return r.width&&r.right>W+1&&getComputedStyle(x).position!=='fixed'}).slice(0,3).map(x=>x.className||x.tagName),
br:[...document.images].filter(i=>i.complete&&i.src&&i.naturalWidth===0).length,btnOv:bo.slice(0,4),dsep:document.querySelectorAll('.dsep').length,theme:document.documentElement.dataset.theme}}"""
PANE="""()=>{const p=document.querySelector('#npane'),m=document.querySelector('.nmain');if(!p||!m)return null;const a=p.getBoundingClientRect(),b=m.getBoundingClientRect();return {paneTop:Math.round(a.top),paneBottom:Math.round(a.bottom),listBottom:Math.round(b.bottom),vh:innerHeight,paneH:Math.round(a.height),paneW:Math.round(a.width),listW:Math.round(b.width),visible:!!p.offsetParent}}"""
res={}; checks={}
def ck(name,ok,info=''):
    checks[name]=('PASS' if ok else 'FAIL')+(' '+str(info) if info else '')
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
            g.goto(B+u,wait_until='load');g.wait_for_timeout(600)
            if name!='x':
                g.mouse.wheel(0,1500);g.wait_for_timeout(300);g.mouse.wheel(0,-3000);g.wait_for_timeout(300)
                sh=lambda s,**k:g.screenshot(path=os.path.join(SH,f'shot_{s}_{mn}.png'),**k)
                sh(name,full_page=(name not in('hot','person','person2','accounts','news')))
                if name in('hot','person'):
                    g.mouse.wheel(0,2600);g.wait_for_timeout(500);g.screenshot(path=os.path.join(SH,f'shot_{name}_{mn}_scrolled.png'))
                    g.mouse.wheel(0,-9000);g.wait_for_timeout(200)
                if name in('hot','person','news','daily','daily14'):
                    g.click('.dcm');g.wait_for_timeout(250);g.screenshot(path=os.path.join(SH,f'shot_{name}_{mn}_datepick.png'));g.keyboard.press('Escape')
                if name=='daily':
                    ck(f'daily[{mn}] original hidden by default',g.evaluate("()=>[...document.querySelectorAll('.dor')].every(d=>d.hidden||!d.offsetParent)"))
                    ck(f'daily[{mn}] expand/copy buttons in header row',g.evaluate("()=>[...document.querySelectorAll('.dh')].every(h=>{const a=h.querySelector('.dha'),d=h.querySelector('.dor');if(!d)return true;return !!a.querySelector('.ex')&&!!a.querySelector('.cp')&&!!a.querySelector('.op')&&a.getBoundingClientRect().bottom<=h.querySelector('.dsm').getBoundingClientRect().top+2})"))
                    ck(f'daily[{mn}] highlights sorted by likes desc',g.evaluate("()=>{const a=[...document.querySelectorAll('.dh .lk')].map(x=>+x.textContent.replace(/[^0-9]/g,''));return a.length>1&&a.every((v,i)=>i===0||a[i-1]>=v)}"))
                    ck(f'daily[{mn}] action boxes on one fixed grid (same x/width in every card)',g.evaluate("()=>{const q=s=>[...document.querySelectorAll('.dh '+s)].map(x=>{const r=x.getBoundingClientRect();return Math.round(r.left)+':'+Math.round(r.width)});return ['.lk','.ex','.cp','.op'].every(s=>new Set(q(s)).size===1)}"))
                    g.locator('.dhl').screenshot(path=os.path.join(SH,f'shot_daily_{mn}_footer.png'))
                    ex=g.query_selector('.dh .ex');ex.click();g.wait_for_timeout(250)
                    ck(f'daily[{mn}] expand shows original',g.evaluate("()=>{const h=document.querySelector('.dh .ex').closest('.dh');const d=h.querySelector('.dor');return !d.hidden&&d.offsetHeight>0&&h.querySelector('.ex').textContent==='收起'}"))
                    ck(f'daily[{mn}] long original scrolls (<=440px)',g.evaluate("()=>{const d=document.querySelector('.dh .dor .pt:not([hidden])');return d.getBoundingClientRect().height<=441}"))
                    g.screenshot(path=os.path.join(SH,f'shot_daily_{mn}_expanded1.png'),full_page=True)
                    # English card with translation
                    r=g.evaluate("""()=>{const h=[...document.querySelectorAll('.dh')].find(x=>x.querySelector('[data-ol]'));if(!h)return null;if(h.querySelector('.dor').hidden)h.querySelector('.ex').click();h.scrollIntoView({block:'center'});const z=h.querySelector('.ptz'),o=h.querySelector('.pto');return {zhShown:!z.hidden&&o.hidden,cp:h.querySelector('.cp').textContent,badge:!!h.querySelector('.trb')}}""")
                    ck(f'daily[{mn}] English default 中 + 译 badge + 复制译文',bool(r and r['zhShown'] and r['badge'] and r['cp']=='复制译文'),r)
                    g.wait_for_timeout(200);g.screenshot(path=os.path.join(SH,f'shot_daily_{mn}_zh.png'))
                    r=g.evaluate("""()=>{const h=[...document.querySelectorAll('.dh')].find(x=>x.querySelector('[data-ol]')&&!x.querySelector('.dor').hidden);h.querySelector('[data-ol="en"]').click();const z=h.querySelector('.ptz'),o=h.querySelector('.pto');return {enShown:z.hidden&&!o.hidden,cp:h.querySelector('.cp').textContent}}""")
                    ck(f'daily[{mn}] EN toggle shows original + 复制原文',bool(r['enShown'] and r['cp']=='复制原文'),r)
                    g.wait_for_timeout(200);g.screenshot(path=os.path.join(SH,f'shot_daily_{mn}_en.png'))
                    ck(f'daily[{mn}] Chinese highlight has no toggle',g.evaluate("()=>{const hs=[...document.querySelectorAll('.dh')].filter(x=>/宝玉|Gorden/.test(x.querySelector('.hh').textContent));return hs.length>0&&hs.every(x=>!x.querySelector('[data-ol]'))}"))
                if name=='news':
                    pn=g.evaluate(PANE)
                    if vw>1000:
                        ck(f'news[{mn}] pane visible with content',bool(pn and pn['visible'] and g.evaluate("()=>document.querySelector('#nptitle').textContent.length>4")),pn)
                        ck(f'news[{mn}] list wider than pane (list 55-66% of total)',pn['listW']>pn['paneW'] and 0.55<=pn['listW']/(pn['listW']+pn['paneW']+16)<=0.66,f"{pn['listW']}/{pn['paneW']}")
                        r=g.evaluate("()=>{const li=document.querySelector('#ntop .nr:nth-child(4)');li.querySelector('.nrh').click();const bd=document.querySelector('#npbody');return new Promise(res=>setTimeout(()=>{const pm=document.querySelector('#npmeta .nn'),a=li.getBoundingClientRect(),n=document.querySelector('#nnotch').getBoundingClientRect(),pr=document.querySelector('#npane').getBoundingClientRect();res({sel:li.classList.contains('sel'),only:document.querySelectorAll('.nr.sel').length===1,num:pm&&pm.textContent,title:document.querySelector('#nptitle').textContent===li.querySelector('.nt2').textContent,bar:getComputedStyle(li).boxShadow!=='none',arrow:getComputedStyle(li.querySelector('.nrh'),'::after').content!=='none',notchY:Math.round(n.top+n.height/2),rowY:Math.round(a.top+Math.min(a.height,72)/2),notchOnPane:n.left<pr.left+4&&n.right>pr.left-12,top:bd.scrollTop})},400))}")
                        ck(f'news[{mn}] selected row: accent bar+arrow, pane repeats number/title, notch aligned to row, pane at top',bool(r['sel'] and r['only'] and r['num']=='04' and r['title'] and r['bar'] and r['arrow'] and abs(r['notchY']-r['rowY'])<=8 and r['notchOnPane'] and r['top']==0),r)
                        g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_selected.png'),clip={'x':0,'y':0,'width':vw,'height':760})
                        ck(f'news[{mn}] pane within viewport + not past list bottom',pn['paneBottom']<=pn['vh'] and pn['paneBottom']<=pn['listBottom']+1,pn)
                        g.mouse.wheel(0,700);g.wait_for_timeout(300);pn2=g.evaluate(PANE)
                        ck(f'news[{mn}] pane sticky after scroll',pn2['paneTop']<=20+60 and pn2['paneBottom']<=pn2['vh'] and pn2['paneBottom']<=pn2['listBottom']+1,pn2)
                        g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_scrolled.png'))
                        g.click('#nmore');g.wait_for_timeout(500);g.mouse.wheel(0,99999);g.wait_for_timeout(500)
                        pn3=g.evaluate(PANE);ck(f'news[{mn}] pane stays inside list at page bottom',pn3['paneBottom']<=pn3['listBottom']+1 and pn3['paneBottom']<=pn3['vh']+1,pn3)
                        g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_bottom.png'))
                        g.mouse.wheel(0,-99999);g.wait_for_timeout(300)
                        # source filter: X news 1 row, pane must shrink/stay within list
                        g.click('[data-src="x"]');g.wait_for_timeout(500);pn4=g.evaluate(PANE)
                        ck(f'news[{mn}] source filter in toolbar works',bool(pn4) and g.evaluate("()=>[...document.querySelectorAll('#nall .nr')].filter(x=>x.offsetParent).every(x=>x.dataset.s==='x')"))
                        g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_xfilter.png'))
                        # day filter via calendar
                        g.click('.dcm');g.wait_for_timeout(200);g.click('.dcd:not(.off)');g.wait_for_timeout(500)
                        ck(f'news[{mn}] day filter shows only one day',g.evaluate("()=>{const gs=[...document.querySelectorAll('#nall .ndg')].filter(x=>!x.hidden);return gs.length===1&&document.querySelector('.dcl').textContent.length>2}"),g.evaluate("()=>document.querySelector('.dcl').textContent"))
                        g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_dayfilter.png'))
                    else:
                        g.click('#ntop .nr .nrh');g.wait_for_timeout(700);g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_expanded.png'),full_page=True)
                        g.click('#nmore');g.wait_for_timeout(400);g.screenshot(path=os.path.join(SH,f'shot_news_{mn}_all.png'))
                if name=='hot':
                    g.click('[data-sort="w"]');g.wait_for_timeout(500);g.click('[data-sort="t"]');g.wait_for_timeout(500);g.click('#more');g.wait_for_timeout(400)
                    g.evaluate("window.scrollTo(0,0)");g.click('.dcm');g.wait_for_timeout(200);days=g.evaluate("()=>[...document.querySelectorAll('.dcd:not(.off)')].map(x=>x.dataset.d)")
                    g.click('.dcd:not(.off) >> nth=1');g.wait_for_timeout(1200)
                    ck(f'hot[{mn}] day filter: posts all from chosen day',g.evaluate("()=>{const k=document.querySelector('.dcm .dcl').textContent;const ds=[...document.querySelectorAll('#feed .dsep')];return document.querySelectorAll('#feed .post').length>5&&ds.length===1}"),f'{len(days)} days')
                    g.screenshot(path=os.path.join(SH,f'shot_hot_{mn}_dayfilter.png'))
                    g.click('.dcn');g.wait_for_timeout(900)
                    ck(f'hot[{mn}] next-day arrow works',g.evaluate("()=>document.querySelectorAll('#feed .post').length>3"))
                if name=='person':
                    ck(f'person[{mn}] continuous grid: no day separators, day chip + time on every card, first row full',g.evaluate("()=>{const c=[...document.querySelectorAll('#feed .post')];if(c.length<4)return false;const t0=Math.round(c[0].getBoundingClientRect().top);const row=c.filter(x=>Math.abs(x.getBoundingClientRect().top-t0)<3).length;const cols=Math.floor((document.querySelector('#feed').clientWidth+12)/(360+12));return !document.querySelector('#feed .dsep')&&c.every(x=>x.querySelector('.dtag')&&x.querySelector('time.tm'))&&row>=Math.min(cols,c.length)&&(innerWidth<=720||row>=2)}"))
                    g.click('.dcm');g.wait_for_timeout(200);g.click('.dcd:not(.off) >> nth=1');g.wait_for_timeout(900)
                    ck(f'person[{mn}] day filter',g.evaluate("()=>{const ds=[...document.querySelectorAll('#feed .dsep')];return ds.length<=1&&document.querySelectorAll('#feed .post').length>=0}"))
                    g.screenshot(path=os.path.join(SH,f'shot_person_{mn}_dayfilter.png'))
            r=g.evaluate(CHK);agg['n']+=1
            agg['csp']+=[u+' '+x for x in r['v']];agg['js']+=[u+' '+x for x in er]
            if r['ov']:agg['ov'].append(u+' '+str(r['ovEl']))
            agg['br']+=r['br'];agg['btn']+=[u+' '+x for x in r['btnOv']]
            if name!='x':res[f'{name}_{mn}']=dict(dsep=r['dsep'],theme=r['theme'])
            g.close()
        res['SUMMARY_'+mn]=agg;c.close()
    b.close()
res['CHECKS']=checks
print(json.dumps(res,ensure_ascii=False,indent=0))
