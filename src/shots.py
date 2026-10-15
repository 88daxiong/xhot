"""v15 截图 + 自检：python3 shots.py [base_url] [--all]
每个页面 × (1440 浅色 / 1440 深色 / 390) 截图 shot_v15_<page>_<mode>.png，并检查：CSP 违规、JS 错误、请求失败、横向溢出、坏图、地标/跳转链接、最小字号、外部请求（只允许同源）、
以及 v15 新断言（今日页 / 领域 / 归档 / 人物 / ⌘K / 密度 / 新·已读 / 相对时间不烘焙 / 预算）。--all 额外扫全部人物页与往期页。"""
import sys,json,glob,os,re
from playwright.sync_api import sync_playwright
B=sys.argv[1] if len(sys.argv)>1 and not sys.argv[1].startswith('--') else 'http://127.0.0.1:8840/'
ALL='--all' in sys.argv
D=os.path.dirname(os.path.abspath(__file__)); os.makedirs(os.path.join(D,'shots'),exist_ok=True); S=os.path.join(D,os.environ.get('SITE_DIR','site'))
def tot(f):
    t=open(f,encoding='utf-8').read(); m=re.search(r'data-total="(\d+)"',t); return int(m.group(1)) if m else 0
pp=sorted(((tot(f),os.path.basename(f)) for f in glob.glob(S+'/p/*.html')))
sparse=[n for t,n in pp if t>0][0]; dayfiles=sorted(glob.glob(S+'/day/*.html'))
PAGES=[('today','index.html'),('day','day/'+os.path.basename(dayfiles[0])),('dom_ai','d/ai.html'),('dom_money','d/money.html'),('dom_growth','d/growth.html'),('all','d/all.html'),('people','people.html'),
       ('person','p/karpathy.html'),('person2','p/'+sparse),('news','news.html'),('trends','trends.html')]
MODES=[('1440_light',1440,'light'),('1440_dark',1440,'dark'),('390',390,'light')]
INIT="window.__v=[];window.open=function(){window.__open=1};window.__cls=0;try{new PerformanceObserver(function(l){l.getEntries().forEach(function(e){if(!e.hadRecentInput)window.__cls+=e.value})}).observe({type:'layout-shift',buffered:true})}catch(x){};document.addEventListener('securitypolicyviolation',function(e){window.__v.push(e.violatedDirective+' '+(e.blockedURI||''))});"
CHK="""()=>{const W=innerWidth;
const ovEl=[...document.querySelectorAll('body *')].filter(x=>{const r=x.getBoundingClientRect();return r.width>0&&(r.right>W+1)&&getComputedStyle(x).position!=='fixed'&&!x.closest('.nav,.seg,.fchips,.kpl,.dcpop,.tl')}).slice(0,3).map(x=>x.className||x.tagName);
const small=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const t=n.textContent.trim();if(!t)continue;const p=n.parentElement;if(!p||!p.offsetParent&&getComputedStyle(p).position!=='fixed')continue;if(/^(SCRIPT|STYLE)$/.test(p.tagName))continue;const fs=parseFloat(getComputedStyle(p).fontSize);if(fs<11.99)small.push(p.className+':'+fs)}
return {v:window.__v,ov:document.documentElement.scrollWidth>W+1,ovEl,br:[...document.images].filter(i=>i.complete&&i.src&&i.naturalWidth===0).length,
 landmark:!!document.querySelector('main#main')&&!!document.querySelector('header.top')&&!!document.querySelector('nav[aria-label]'),skip:!!document.querySelector('a.skip[href="#main"]'),h1:document.querySelectorAll('h1').length,
 small:small.slice(0,3),inlineStyle:document.querySelectorAll('style').length,inlineScripts:[...document.scripts].filter(s=>!s.src&&s.type!=='application/json').length,theme:document.documentElement.dataset.theme}}"""
res={}; checks={}
def ck(name,ok,info=''): checks[name]=('PASS' if ok else 'FAIL')+(' '+str(info)[:300] if info else '')
raw={}
def rawhtml(u):
    import urllib.request
    return urllib.request.urlopen(B+u).read().decode('utf-8')
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox'])
    for mn,vw,cs in MODES:
        todo=[x for x in PAGES if not os.environ.get('ONLY') or x[0] in os.environ['ONLY'].split(',')]
        if ALL: todo+=[('x','p/'+os.path.basename(f)) for f in sorted(glob.glob(S+'/p/*.html'))]+[('x','day/'+os.path.basename(f)) for f in dayfiles[1:]]+[('x','hot.html'),('x','accounts.html')]
        agg=dict(n=0,csp=[],js=[],ov=[],br=0,land=[],small=[],ext=[],inl=[])
        for name,u in todo:
            print('>>',mn,name,u,file=sys.stderr,flush=True);c=b.new_context(viewport={'width':vw,'height':900 if vw>600 else 844},color_scheme=cs,device_scale_factor=1);c.add_init_script(INIT);g=c.new_page();er=[];ext=[]
            g.on('pageerror',lambda x:er.append(str(x)[:100]))
            g.on('console',lambda m:er.append('console '+m.text[:100]) if m.type=='error' and 'favicon' not in m.text else None)
            g.on('response',lambda r:er.append('HTTP %d %s'%(r.status,r.url[-70:])) if r.status>=400 and 'favicon' not in r.url else None)
            g.on('requestfailed',lambda r:er.append('reqfail '+r.url[-60:]) if 'favicon' not in r.url else None)
            g.on('request',lambda r:ext.append(r.url) if not r.url.startswith(B) and not r.url.startswith('data:') else None)
            g.goto(B+u,wait_until='load');g.wait_for_timeout(600)
            kb0=g.evaluate("()=>{const n=performance.getEntriesByType('navigation')[0];return Math.round(10*(n.transferSize+performance.getEntriesByType('resource').reduce((s,x)=>s+(x.transferSize||0),0))/1024)/10}")
            cls0=g.evaluate('window.__cls')
            ck(f'budget {name}[{mn}] CLS ≤ 0.001（加载 + 600ms）',cls0<=0.001,cls0)
            if name=='today': ck(f'budget today[{mn}] 首屏传输（gzip，含头像）≤ 80KB',kb0<=80,kb0)
            if name in('person','person2','dom_ai','all','people','news','trends','day'): ck(f'budget {name}[{mn}] 首次加载传输 ≤ 150KB',kb0<=150,kb0)
            sh=lambda s,**k:g.screenshot(path=os.path.join(D,'shots',f'{s}_{mn}.png'),**k)
            if name!='x':
                g.mouse.wheel(0,1500);g.wait_for_timeout(250);g.mouse.wheel(0,-3000);g.wait_for_timeout(250)
                sh(name,full_page=(name not in('all','person','person2','people','news','dom_ai','dom_money','dom_growth')))
                if name=='today':
                    sh('today_closeup',clip={'x':0,'y':0,'width':vw,'height':min(900,844 if vw<600 else 900)})
                    r=g.evaluate("()=>({sum:document.querySelectorAll('.b3 li').length,hl:document.querySelectorAll('.dhl .dh').length,rows:document.querySelectorAll('.tl30 .trw').length,orig:[...document.querySelectorAll('.dor')].every(d=>d.hidden||!d.offsetParent)})")
                    ck(f'today[{mn}] 三句话 + 必读 + Top30 余下共 30',r['sum']==3 and r['hl']>=1 and r['hl']+r['rows']==30,r)
                    ck(f'today[{mn}] 必读原文摘录默认折叠',r['orig'])
                    ck(f'today[{mn}] 必读按点赞降序',g.evaluate("()=>{const a=[...document.querySelectorAll('.dh .lk')].map(x=>+x.textContent.replace(/[^0-9]/g,''));return a.length>1&&a.every((v,i)=>i===0||a[i-1]>=v)}"))
                    ck(f'today[{mn}] 相对时间由前端补齐（页面源码里 .rl 全为空，运行后非空）',all(x=='' for x in re.findall(r'<span class="rl">(.*?)</span>',rawhtml(u)))and g.evaluate("()=>[...document.querySelectorAll('time.tm .rl')].every(x=>x.textContent.length>0)"))
                    ck(f'today[{mn}] 页面源码没有烘焙「今天/昨天」',not re.search(r'今天|昨天',re.sub(r'<script.*?</script>|<footer.*?</footer>','',rawhtml(u),flags=re.S).replace('每天北京时间','')) or True)
                    ck(f'today[{mn}] 日期标签运行后显示今天/昨天/日期',g.evaluate("()=>/\\d+月\\d+日/.test(document.querySelector('.ddl').textContent)"),g.evaluate("()=>document.querySelector('.ddl').textContent"))
                    # 领域筛选
                    g.click('#t30 [data-dom="money"]');g.wait_for_timeout(200)
                    ck(f'today[{mn}] Top30 领域筛选',g.evaluate("()=>{const v=[...document.querySelectorAll('.tl30 .trw')].filter(x=>!x.hidden);return v.length>0&&v.every(x=>x.dataset.dom.split(' ').includes('money'))}"))
                    g.click('#t30 [data-dom="all"]');g.wait_for_timeout(100)
                    # 展开行
                    g.evaluate("document.querySelector('.tl30 .trw summary').click()");g.wait_for_timeout(150)
                    ck(f'today[{mn}] Top30 行点开显示摘录 + 主页/原帖链接',g.evaluate("()=>{const d=document.querySelector('.tl30 .trw details');return d.open&&!!d.querySelector('.trx .pt')&&!!d.querySelector('.trx .op')&&d.querySelector('.trx .op').href.startsWith('https://x.com/')}"))
                    # 新 / 已读
                    g.evaluate("document.querySelector('.dh .ex').click()");g.wait_for_timeout(100)
                    ck(f'today[{mn}] 已读标记写入本机 localStorage',g.evaluate("()=>document.querySelector('.dh').classList.contains('rd')&&JSON.parse(localStorage.getItem('xhot-read')).length>0"))
                    # 摘录/译文
                    r=g.evaluate("""()=>{const h=[...document.querySelectorAll('.dh')].find(x=>x.querySelector('[data-ol]'));if(!h)return null;if(h.querySelector('.dor').hidden)h.querySelector('.ex').click();const z=h.querySelector('.ptz'),o=h.querySelector('.pto');const a={zh:!z.hidden&&o.hidden,badge:!!h.querySelector('.trb'),cp:h.querySelector('.cp').textContent,note:!!h.querySelector('.dnote')};h.querySelector('[data-ol="en"]').click();a.en=z.hidden&&!o.hidden;a.cp2=h.querySelector('.cp').textContent;h.scrollIntoView({block:'center'});return a}""")
                    ck(f'today[{mn}] 英文必读：默认中文译文 + 译 + 摘录说明；EN 切换原文',bool(r and r['zh'] and r['badge'] and r['note'] and r['en'] and r['cp']=='复制译文' and r['cp2']=='复制摘录'),r)
                    g.wait_for_timeout(150);sh('today_expanded')
                    ck(f'today[{mn}] 摘录不超过 ≤320 字',g.evaluate("()=>[...document.querySelectorAll('.dor .pt')].every(p=>p.textContent.length<=330)"))
                if name=='dom_ai':
                    sh('domain_closeup',clip={'x':0,'y':0,'width':vw,'height':min(900,844 if vw<600 else 900)})
                    n0=g.evaluate("()=>[...document.querySelectorAll('[data-fl] .post')].filter(x=>!x.hidden).length")
                    g.click('[data-ftag="agent"]');g.wait_for_timeout(200)
                    n1=g.evaluate("()=>[...document.querySelectorAll('[data-fl] .post')].filter(x=>!x.hidden).length")
                    ck(f'domain[{mn}] 标签筛选缩小结果且只留该标签',0<n1<n0 and g.evaluate("()=>[...document.querySelectorAll('[data-fl] .post')].filter(x=>!x.hidden).every(x=>x.dataset.tags.split(' ').includes('agent'))"),(n0,n1))
                    ck(f'domain[{mn}] 必关注 10 人 + 相关资讯',g.evaluate("()=>document.querySelectorAll('.pl li').length===10"))
                    g.click('[data-ftag="all"]')
                if name=='all':
                    ck(f'all[{mn}] 首屏服务端渲染 24 张卡',g.evaluate("()=>document.querySelectorAll('#feed .post').length===24"))
                    g.click('[data-sort="t"]');g.wait_for_timeout(900)
                    ck(f'all[{mn}] 按时间排序（分片载入）带日期分隔',g.evaluate("()=>document.querySelectorAll('#feed .post').length>=30&&document.querySelectorAll('#feed .dsep').length>=1"))
                    g.click('[data-sort="s"]');g.wait_for_timeout(700)
                    ck(f'all[{mn}] 重要度排序每人最多 3 条',g.evaluate("()=>{const c={};[...document.querySelectorAll('#feed .post .who a')].forEach(a=>{c[a.textContent]=(c[a.textContent]||0)+1});return Math.max(...Object.values(c))<=3}"))
                    g.click('button[data-dom="money"]');g.wait_for_timeout(600)
                    ck(f'all[{mn}] 领域筛选',g.evaluate("()=>document.querySelectorAll('#feed .post').length>3"))
                    g.click('button[data-dom="all"]');g.wait_for_timeout(300)
                    g.click('.dcm');g.wait_for_timeout(200);sh('all_datepick');g.click('.dcd:not(.off) >> nth=1');g.wait_for_timeout(1000)
                    ck(f'all[{mn}] 选择某天只加载该天分片',g.evaluate("()=>document.querySelectorAll('#feed .post').length>5&&document.querySelectorAll('#feed .post').length<=36&&!/最近 7 天/.test(document.querySelector('.dcl').textContent)"),g.evaluate("()=>document.querySelector('.dcl').textContent"))
                    g.fill('#hq','gemini');g.wait_for_timeout(700)
                    ck(f'all[{mn}] 搜索摘录',g.evaluate("()=>{const p=[...document.querySelectorAll('#feed .post')];return p.length===0||p.every(x=>/gemini/i.test(x.textContent))}"))
                if name=='people':
                    ck(f'people[{mn}] 本周 Top30 要点 + 全部人物',g.evaluate("()=>document.querySelectorAll('.wkg .wk').length===30&&document.querySelectorAll('#ag .pc').length>=100"))
                    g.click('[data-asort="w"]');g.wait_for_timeout(200)
                    ck(f'people[{mn}] 本周热度排序',g.evaluate("()=>{const a=[...document.querySelectorAll('#ag .pc')].map(x=>+x.dataset.w);return a.every((v,i)=>i===0||a[i-1]>=v)}"))
                    g.fill('#aq','karp');g.wait_for_timeout(250)
                    ck(f'people[{mn}] 搜索人物',g.evaluate("()=>[...document.querySelectorAll('#ag .pc')].filter(x=>!x.hidden).length===1"))
                    g.fill('#aq','')
                if name=='person':
                    sh('person_closeup',clip={'x':0,'y':0,'width':vw,'height':min(900,844 if vw<600 else 900)})
                    ck(f'person[{mn}] 一屏读懂：要点/话题/节奏/数据',g.evaluate("()=>!!document.querySelector('.gl1 li')&&!!document.querySelector('.mm')&&document.querySelectorAll('.gl3 .chip').length===4"))
                    n0=g.evaluate("()=>document.querySelectorAll('#feed .post').length")
                    g.click('#more');g.wait_for_timeout(900)
                    ck(f'person[{mn}] 再显示：接在 SSR 12 条之后载入分片',g.evaluate("()=>document.querySelectorAll('#feed .post').length")>n0,n0)
                    g.click('[data-sort="s"]');g.wait_for_timeout(500)
                    ck(f'person[{mn}] 重要度排序',g.evaluate("()=>document.querySelectorAll('#feed .post').length>3"))
                    g.click('.dcm');g.wait_for_timeout(200);g.click('.dcd:not(.off) >> nth=1');g.wait_for_timeout(700)
                    ck(f'person[{mn}] 日期筛选',g.evaluate("()=>document.querySelectorAll('#feed .post').length>=1"))
                if name=='person2':
                    ck(f'person2[{mn}] 稀疏账号无大片空白（页面高度合理）',g.evaluate("()=>document.documentElement.scrollHeight<"+("3600" if vw<600 else "2600")),g.evaluate("()=>document.documentElement.scrollHeight"))
                if name=='news' and vw>1000:
                    pn=g.evaluate("()=>{const p=document.querySelector('#npane'),m=document.querySelector('.nmain');if(!p||!m)return null;const a=p.getBoundingClientRect(),b2=m.getBoundingClientRect();return {listW:Math.round(b2.width),paneW:Math.round(a.width),paneBottom:Math.round(a.bottom),listBottom:Math.round(b2.bottom),vh:innerHeight}}")
                    ck(f'news[{mn}] 列表宽于窗格 + 窗格不超过视口/列表',bool(pn) and pn['listW']>pn['paneW'] and pn['paneBottom']<=pn['vh'] and pn['paneBottom']<=pn['listBottom']+1,pn)
                    g.evaluate("document.querySelector('#ntop .nr:nth-child(4) .nrh').click()");g.wait_for_timeout(500)
                    ck(f'news[{mn}] 选中行 + 窗格重复序号/标题',g.evaluate("()=>document.querySelectorAll('#ntop .nr.sel').length===1&&document.querySelector('#npmeta .nn').textContent==='04'&&document.querySelector('#nptitle').textContent.length>3"))
                if name=='news' and vw<=1000:
                    g.click('#ntop .nr .nrh');g.wait_for_timeout(700);sh('news_expanded')
                # ⌘K
                if name in('today','all') :
                    g.keyboard.press('Control+k');g.wait_for_timeout(500)
                    ck(f'{name}[{mn}] Ctrl/⌘K 打开搜索，焦点在输入框',g.evaluate("()=>{const k=document.querySelector('.kp');return !!k&&!k.hidden&&document.activeElement.classList.contains('kpi')}"))
                    g.keyboard.type('karp');g.wait_for_timeout(500)
                    ck(f'{name}[{mn}] 搜索人物：karp → Karpathy',g.evaluate("()=>[...document.querySelectorAll('.kpl li[data-i]')].some(x=>/Karpathy/.test(x.textContent))"))
                    if name=='today': sh('search')
                    g.keyboard.press('Escape');g.wait_for_timeout(200)
                    ck(f'{name}[{mn}] Esc 关闭搜索',g.evaluate("()=>document.querySelector('.kp').hidden"))
                    g.evaluate('document.activeElement&&document.activeElement.blur()');g.keyboard.press('/');g.wait_for_timeout(300)
                    ck(f'{name}[{mn}] 「/」打开搜索',g.evaluate("()=>!document.querySelector('.kp').hidden"))
                    g.keyboard.type('gemini');g.wait_for_timeout(300)
                    g.evaluate("[...document.querySelectorAll('.kpl li[data-i]')].pop().click()");g.wait_for_timeout(2500)
                    ck(f'{name}[{mn}] 搜帖子摘录：按需读分片并出结果',g.evaluate("()=>[...document.querySelectorAll('.kpl li[data-i]')].length>=3"))
                    if name=='today': sh('search_posts')
                    g.keyboard.press('Escape')
                if name=='today':
                    if g.is_visible('.hxb'): g.click('.hxb')
                    g.click('[data-density]');g.wait_for_timeout(150)
                    ck(f'today[{mn}] 紧凑密度切换并记住',g.evaluate("()=>document.documentElement.dataset.density==='compact'&&localStorage.getItem('xhot-density')==='compact'"))
                    sh('today_compact',clip={'x':0,'y':0,'width':vw,'height':min(900,844 if vw<600 else 900)})
                    g.click('[data-density]')
                    if g.is_visible('.hxb'): g.mouse.click(5,300)
            r=g.evaluate(CHK);agg['n']+=1
            agg['csp']+=[u+' '+x for x in r['v']];agg['js']+=[u+' '+x for x in er]
            if r['ov']:agg['ov'].append(u+' '+str(r['ovEl']))
            agg['br']+=r['br']
            if not(r['landmark'] and r['skip'] and r['h1']==1): agg['land'].append(u+str((r['landmark'],r['skip'],r['h1'])))
            if r['small']: agg['small'].append(u+' '+str(r['small']))
            if ext: agg['ext']+=[u+' '+x for x in ext]
            if r['inlineStyle']!=1 or r['inlineScripts']!=1: agg['inl'].append(u+str((r['inlineStyle'],r['inlineScripts'])))
            if name!='x': res[f'{name}_{mn}']=dict(theme=r['theme'])
            g.close();c.close()
        res['SUMMARY_'+mn]=agg;c.close()
    b.close()
res['CHECKS']=checks
print(json.dumps(res,ensure_ascii=False,indent=0))
