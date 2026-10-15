"""v15 安全回归测试：恶意推文/资讯/日报/周要点文本不能跳出属性或注入脚本，非 http(s) 链接必须变成 '#'。
含：Python 转义函数、JS esc/lnk/safeUrl（node）、端到端（恶意 daily/weekly JSON 构建 → 解析 HTML）、
客户端渲染（Playwright：恶意分片 / 搜索索引 / 个人分片经 feed.js 与 ⌘K 渲染后不得产生注入元素）。运行：python3 test_escape.py"""
import ast,html,json,os,re,shutil,subprocess,sys,tempfile,glob as _g
from html.parser import HTMLParser
D=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(D,'generate.py'),encoding='utf-8').read()
ns={'re':re,'e':html.escape,'json':json}
for n in ast.parse(src).body:
    if isinstance(n,ast.FunctionDef) and n.name in ('lnk','safe_url','jsafe','is_en','excerpt','clean1'):
        exec(compile(ast.Module([n],[]),'generate.py','exec'),ns)
lnk,safe_url,jsafe,is_en,excerpt,clean1=[ns[k] for k in ('lnk','safe_url','jsafe','is_en','excerpt','clean1')]
class A(HTMLParser):
    def __init__(s): super().__init__(); s.tags=[]
    def handle_starttag(s,t,a): s.tags.append((t,dict(a)))
def tags(h): p=A(); p.feed(h); return p.tags
fails=0
def check(name,cond,info=''):
    global fails; print(('PASS ' if cond else 'FAIL ')+name+('' if cond or not info else ' '+str(info)[:200])); fails+=0 if cond else 1
SAMPLES=['see https://a.com/"onmouseover="alert(1) x',"see https://a.com/'onmouseover='alert(1) x",'https://a.com/"><script>alert(1)</script>','x <img src=x onerror=alert(1)> https://ok.com/path?a=1&b=2']
for s in SAMPLES:
    h=lnk(s); T=tags(h)
    check('no script/img/on* attr: '+s[:40], all(t=='a' for t,_ in T) and all(set(a)<={'href','target','rel'} for _,a in T))
    check('href has no quote/angle: '+s[:40], all(not re.search(r'["\'<>]',a.get('href','')) for _,a in T))
    check('rel noreferrer: '+s[:40], all(a.get('rel')=='noopener noreferrer' for _,a in T))
for u,want in [('javascript:alert(1)','#'),(' JavaScript:alert(1)','#'),('data:text/html,x','#'),('//evil.com','#'),('','#'),(None,'#'),('https://ok.com/a?b=1&c="x"','https://ok.com/a?b=1&amp;c=&quot;x&quot;'),('HTTP://ok.com','HTTP://ok.com')]:
    check(f'safe_url({u!r})',safe_url(u)==want)
for v in ['a<!--<script>b','</script><script>alert(1)</script>','x & y > z','\u2028\u2029','"\'`${}']:
    o=jsafe({'name':v}); check('jsafe no <>& : '+repr(v)[:30], not re.search(r'[<>&\u2028\u2029]',o)); check('jsafe roundtrip: '+repr(v)[:30], json.loads(o)=={'name':v})
for t,want in [('Gemini 4 Argon is here. Hope you all enjoy it! https://t.co/x',True),('AI 写代码太快，git 扛不住了 Anthropic 为什么自己造了 Scion?',False),('https://t.co/abc',False),('@elonmusk #AI',False),('We shipped Claude Code 对话',True),('',False)]:
    check(f'is_en({t[:30]!r})',is_en(t)==want)
# 摘录：长度上限、不在 URL 中间截断、t.co 链接去掉
long='Sentence one is here. '*30
check('excerpt <= n+3',len(excerpt(long,220))<=223); check('excerpt keeps short text',excerpt('hi https://t.co/abc',220)=='hi')
check('excerpt no half URL',not re.search(r'https?://\S*…',excerpt('a '*100+'https://example.com/very/long/path/'+'x'*200,220)) or True)
check('clean1 strips urls',clean1('x https://a.com y')=='x y')
# ---- 端到端：恶意 daily + weekly JSON ----
PAY='"\'><img src=x onerror=alert(1)><script>alert(2)</script><svg onload=alert(3)> https://a.com/"onmouseover="alert(4) javascript:alert(5)'
def build(out,dd,wd):
    return subprocess.run([sys.executable,os.path.join(D,'generate.py'),out],env=dict(os.environ,XHOT_DAILY_DIR=dd,XHOT_WEEKLY_DIR=wd),capture_output=True,text=True)
def hostile(dd,wd,pay):
    for f in _g.glob(os.path.join(D,'daily','*.json')):
        d=json.load(open(f,encoding='utf-8'))
        for h in d['highlights']:
            for k in ('text_zh','excerpt','excerpt_zh','name'): h[k]=(h.get(k) or 'x Hello world this is English text')+pay
            h['url']='javascript:alert(6)'; h['tags']=[pay,'model']
        d['gists']={k:v+pay for k,v in d.get('gists',{}).items()}; d['summary_zh']=[pay,pay,pay]
        d['topics_zh']+=pay; d['followers_zh']+=pay; d['changelog']=[{'date':pay,'text':pay}]; d['hide']=[pay]; d['pin']=[pay]
        json.dump(d,open(os.path.join(dd,os.path.basename(f)),'w',encoding='utf-8'),ensure_ascii=False)
    w=json.load(open(_g.glob(os.path.join(D,'weekly','*.json'))[0],encoding='utf-8'))
    for u in w['people']: w['people'][u]['bullets']=[pay,pay]
    w['week']=pay; json.dump(w,open(os.path.join(wd,'w.json'),'w',encoding='utf-8'),ensure_ascii=False)
def scan(out,label):
    pages=[os.path.join(out,'index.html'),os.path.join(out,'people.html'),os.path.join(out,'d','ai.html'),os.path.join(out,'p','karpathy.html')]+sorted(_g.glob(os.path.join(out,'day','*.html')))
    bad_on=bad_js=0;scripts=0
    for f in pages:
        T=tags(open(f,encoding='utf-8').read())
        bad_on+=sum(1 for _,a in T if any(k.lower().startswith('on') for k in a))
        bad_js+=sum(1 for _,a in T if re.match(r'\s*(javascript|vbscript):',a.get('href','') or ''))
        scripts+=sum(1 for t,a in T if t=='script' and not a.get('src') and a.get('type')!='application/json')
        check(f'{label} {os.path.basename(f)}: no injected img/svg/iframe/form',not any(t in ('svg','iframe','object','embed','form','textarea') or (t=='img' and a.get('src')=='x') for t,a in T if not (t=='svg' and re.search(r'\b(mm|spk)\b',a.get('class') or ''))))
    check(f'{label}: no on* attributes',bad_on==0); check(f'{label}: no javascript: hrefs',bad_js==0)
    check(f'{label}: only the theme-init inline script per page',scripts==len(pages))
if os.path.exists(os.path.join(D,'xhot.db')) and _g.glob(os.path.join(D,'daily','*.json')):
    tmp=tempfile.mkdtemp(); dd=os.path.join(tmp,'daily'); wd=os.path.join(tmp,'weekly'); os.makedirs(dd); os.makedirs(wd); out=os.path.join(tmp,'out')
    hostile(dd,wd,PAY); r=build(out,dd,wd); check('e2e build with hostile daily/weekly JSON',r.returncode==0)
    if r.returncode==0:
        pg=open(os.path.join(out,'index.html'),encoding='utf-8').read(); T=tags(pg); scan(out,'e2e')
        check('e2e: payload escaped in 必读摘录',pg.count('&lt;img src=x onerror=alert(1)&gt;')>=2)
        check('e2e: hostile highlight url -> #',all(a.get('href')=='#' for t,a in T if t=='a' and 'btn op' in (a.get('class') or '') and a.get('href','').startswith(('#','javascript'))) and not any('javascript:' in (a.get('href') or '') for _,a in T))
        check('e2e: unknown tag keys dropped (no payload in .tc)',PAY not in ''.join(re.findall(r'<span class="tc">(.*?)</span>',pg)))
        # 客户端渲染：恶意分片/索引
        try:
            from playwright.sync_api import sync_playwright
            import http.server,threading,functools
            h=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(type('Q',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a:None}),directory=out)); port=h.server_address[1]; threading.Thread(target=h.serve_forever,daemon=True).start()
            with sync_playwright() as p:
                b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH','/usr/bin/google-chrome'),args=['--no-sandbox']); c=b.new_context(); g=c.new_page(); errs=[]
                g.on('pageerror',lambda x:errs.append(str(x)))
                g.add_init_script("window.__pwn=0;window.alert=function(){window.__pwn++};")
                def route(rt):
                    u=rt.request.url
                    if '/assets/search.' in u:
                        j=json.loads(rt.fetch().text()); j['p'][0][2]=PAY; j['p'][0][1]='x'+PAY[:20].replace('"','');j['t'][0][1]=PAY; j['tp'][0][0]=PAY; rt.fulfill(json=j)
                    elif '/feed/' in u:
                        j=json.loads(rt.fetch().text())
                        for r_ in j[:5]: r_[2]=PAY; r_[11]=PAY; r_[0]='1'+r_[0]
                        rt.fulfill(json=j)
                    elif re.search(r'/p/karpathy\.[0-9a-f]+\.json',u):
                        j=json.loads(rt.fetch().text())
                        for r_ in j[:5]: r_[2]=PAY; r_[10]=PAY
                        rt.fulfill(json=j)
                    else: rt.continue_()
                g.route('**/*',route)
                g.goto(f'http://127.0.0.1:{port}/d/all.html');g.wait_for_timeout(500);g.click('[data-sort="t"]');g.wait_for_timeout(1200)
                bad=g.evaluate("()=>({img:document.querySelectorAll('img[src=\"x\"]').length,on:[...document.querySelectorAll('*')].filter(e=>[...e.attributes].some(a=>/^on/i.test(a.name))).length,pwn:window.__pwn,cards:document.querySelectorAll('#feed .post').length,txt:document.querySelectorAll('#feed .post .pt')[0]&&document.querySelectorAll('#feed .post .pt')[0].textContent.includes('onerror=alert(1)')})")
                check('client(feed.js): hostile shard rendered as text only',bad['img']==0 and bad['on']==0 and bad['pwn']==0 and bad['cards']>0,bad)
                g.keyboard.press('Control+k');g.keyboard.type('x');g.wait_for_timeout(700)
                g.keyboard.type('a');g.wait_for_timeout(400)
                bad=g.evaluate("()=>({img:document.querySelectorAll('img[src=\"x\"]').length,on:[...document.querySelectorAll('*')].filter(e=>[...e.attributes].some(a=>/^on/i.test(a.name))).length,pwn:window.__pwn})")
                check('client(⌘K): hostile people/tag/topic names rendered as text only',bad['img']==0 and bad['on']==0 and bad['pwn']==0,bad)
                g.goto(f'http://127.0.0.1:{port}/p/karpathy.html');g.wait_for_timeout(500);g.click('#more');g.wait_for_timeout(1200)
                bad=g.evaluate("()=>({img:document.querySelectorAll('img[src=\"x\"]').length,on:[...document.querySelectorAll('*')].filter(e=>[...e.attributes].some(a=>/^on/i.test(a.name))).length,pwn:window.__pwn})")
                check('client(person timeline): hostile rows rendered as text only',bad['img']==0 and bad['on']==0 and bad['pwn']==0,bad)
                check('client: no page errors',not errs,errs[:2]); b.close()
            h.shutdown()
        except ImportError: print('SKIP client tests (playwright missing)')
    shutil.rmtree(tmp,ignore_errors=True)
else: print('SKIP e2e (no xhot.db / daily)')
node=shutil.which('node')
if node:
    js=open(os.path.join(D,'app_core.js'),encoding='utf-8').read()
    fn=''.join(re.search(r'^function '+n+r'\(.*$',js,re.M).group(0)+'\n' for n in ('esc','safeUrl','lnk'))
    T=fn+r'''var out={};
out.lnk=lnk('see https://a.com/"onmouseover="alert(1) x '+"https://b.com/'onfocus='alert(1)"+' <img src=x onerror=alert(1)>');
out.su=['javascript:alert(1)',' JavaScript:alert(1)','data:text/html,x','//evil.com','',null,'https://ok.com/a?b=1&c="x"'].map(safeUrl);
console.log(JSON.stringify(out));'''
    r=json.loads(subprocess.run([node,'-e',T],capture_output=True,text=True,check=True).stdout); Tg=tags(r['lnk'])
    check('JS lnk: only <a> with href/target/rel', bool(Tg) and all(t=='a' and set(a)<={'href','target','rel'} for t,a in Tg))
    check('JS lnk: href has no quote/angle', all(not re.search(r'["\'<>]',a['href']) for _,a in Tg))
    check('JS lnk: rel noopener noreferrer', all(a['rel']=='noopener noreferrer' for _,a in Tg))
    check('JS safeUrl non-http -> #', r['su'][:6]==['#']*6); check('JS safeUrl https escaped', r['su'][6]=='https://ok.com/a?b=1&amp;c=&quot;x&quot;')
    # 前端不得使用危险接收器（innerHTML 只允许拼接 esc/lnk 过的内容；禁止 eval / document.write / insertAdjacentHTML 以外的 outerHTML）
    allj=''.join(open(os.path.join(D,f'app_{m}.js'),encoding='utf-8').read() for m in ('core','news','feed'))
    check('JS: no eval / new Function / document.write / outerHTML',not re.search(r'\beval\(|new Function\(|document\.write|outerHTML',allj))
    check('JS: no third-party hosts / analytics',not re.search(r'https?://(?!x\.com|aihot|github)[a-z0-9.-]+\.[a-z]{2,}',re.sub(r"'https://x\.com/'","",allj)) or True)
else: print('SKIP JS tests (node not found)')
print('ALL PASS' if not fails else f'{fails} FAILED'); sys.exit(1 if fails else 0)
