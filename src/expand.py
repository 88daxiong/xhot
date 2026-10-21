"""展开回归：python3 expand.py [base_url]
全站每张帖子卡片（.post / 必读 .dh / Top30 与 Agent 列表行 details）和每个 GitHub 条目（趋势页 button.grow、Agent 卡片）都必须有可用的展开入口；
1440 / 1024 / 768 / 390 × Chromium + WebKit，抽样点开（首 / 中 / 末）并收起；个人页「再显示」载入的帖子也要能展开。另测 768 下今日 / 日报页 CLS ≤ 0.001。"""
import sys,os,glob,json
from playwright.sync_api import sync_playwright
B=next((a for a in sys.argv[1:] if a.startswith('http')),'http://127.0.0.1:8840/')
D=os.path.dirname(os.path.abspath(__file__)); S=os.path.join(D,os.environ.get('SITE_DIR','site'))
day='day/'+sorted(os.path.basename(x) for x in glob.glob(os.path.join(S,'day','*.html')))[-1]
PG=['index.html',day,'d/ai.html','d/all.html','p/karpathy.html','trends.html','agents.html']
W=[1440,1024,768,390]; R={}; bad=0
def ck(k,ok,v=''):
    global bad; R[k]=('PASS ' if ok else 'FAIL ')+str(v); bad+=0 if ok else 1
def pick(n): return sorted({0,n//2,n-1}) if n else []
VIS="e=>!!e&&!e.hidden&&e.getBoundingClientRect().height>0&&getComputedStyle(e).display!='none'"
def posts(g,tag):
    n=g.locator('.post').count(); m=g.locator('.post .ex2').count()
    ck(f'{tag} 每张帖子卡片都有展开按钮',n==m,f'{m}/{n}')
    for i in pick(n):
        c=g.locator('.post').nth(i); b=c.locator('.ex2'); b.evaluate("e=>e.scrollIntoView({block:'center'})"); g.wait_for_timeout(60); b.click(); g.wait_for_timeout(320)
        ok=b.get_attribute('aria-expanded')=='true' and c.locator('.pxd').evaluate(VIS) and c.locator('.pxd dd').count()>=2
        b.click(); g.wait_for_timeout(320); ok=ok and b.get_attribute('aria-expanded')=='false' and c.locator('.pxd').evaluate('e=>e.hidden')
        ck(f'{tag} 帖子 #{i} 展开 / 收起',ok)
    return n
with sync_playwright() as p:
    for eng in ('chromium','webkit'):
        b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH') or None,args=['--no-sandbox']) if eng=='chromium' else p.webkit.launch()
        for w in W:
            for pg in PG:
                tag=f'{eng}[{w}] {pg}'; g=b.new_page(viewport={'width':w,'height':900}); err=[]; g.on('pageerror',lambda x:err.append(str(x)))
                g.goto(B+pg); g.add_style_tag(content='html,*{scroll-behavior:auto!important}'); g.wait_for_timeout(300)   # WebKit 平滑滚动下 scroll_into_view 后坐标会过期
                posts(g,tag)
                n=g.locator('.dh').count(); m=g.locator('.dh .ex').count(); ck(f'{tag} 每张必读卡片都有展开按钮',n==m,f'{m}/{n}')
                for i in pick(n):
                    c=g.locator('.dh').nth(i); x=c.locator('.ex'); x.evaluate("e=>e.scrollIntoView({block:'center'})"); g.wait_for_timeout(60); x.click(); g.wait_for_timeout(320)
                    ok=x.get_attribute('aria-expanded')=='true' and c.locator('.dor').evaluate(VIS); x.click(); g.wait_for_timeout(320)
                    ck(f'{tag} 必读 #{i} 展开 / 收起',ok and x.get_attribute('aria-expanded')=='false')
                n=g.locator('details:has(> .trx)').count()
                for i in pick(n):
                    d=g.locator('details:has(> .trx)').nth(i); sm=d.locator('summary'); sm.evaluate("e=>e.scrollIntoView({block:'center'})"); g.wait_for_timeout(60); sm.click(); g.wait_for_timeout(320)
                    ok=d.evaluate('e=>e.open') and d.locator('.trx').evaluate(VIS) and d.locator('.trx .act a, .trx .act button').count()>=1
                    if i==0: sm.focus(); g.keyboard.press('Enter'); g.wait_for_timeout(320)
                    else: sm.click(); g.wait_for_timeout(320)
                    ck(f'{tag} 列表行 #{i} 展开 / 收起（含键盘）',ok and not d.evaluate('e=>e.open'))
                n=g.locator('.gl li').count(); m=g.locator('.gl li > button.grow[aria-expanded] + .gxd').count()
                if pg=='trends.html': ck(f'{tag} 每个 GitHub 条目都可展开',n==m and n>0,f'{m}/{n}')
                for i in pick(m):
                    li=g.locator('.gl li').nth(i); gb=li.locator('button.grow'); gb.evaluate("e=>e.scrollIntoView({block:'center'})"); g.wait_for_timeout(60); gb.click(); g.wait_for_timeout(700)
                    ok=gb.get_attribute('aria-expanded')=='true' and li.locator('.gxd').evaluate(VIS) and li.locator('.gxd .gmt').count()==1 and li.locator('.gxd a[href^="https://github.com/"]').count()==1 and li.locator('.gxd .cpy').count()==1
                    gb.click(); g.wait_for_timeout(320); ck(f'{tag} GitHub #{i} 展开详情 / 收起',ok and li.locator('.gxd').evaluate('e=>e.hidden'))
                if pg=='agents.html':
                    n=g.locator('.dcard').count(); m=g.locator('.dcard .dmore').count(); ck(f'{tag} 每张 Agent 卡片都有详情入口',n==m and n>0,f'{m}/{n}')
                    c=g.locator('.dcard .dmore').first; c.click(); g.wait_for_timeout(500)
                    ok=g.locator('.dsh').evaluate(VIS) if g.locator('.dsh').count() else False
                    g.keyboard.press('Escape'); g.wait_for_timeout(200); ck(f'{tag} Agent 卡片详情打开',ok)
                if pg.startswith('p/') and g.locator('#more').count() and g.locator('#more').is_visible():
                    n0=g.locator('.post').count(); g.locator('#more').click(); g.wait_for_timeout(700)
                    n1=g.locator('.post').count(); ck(f'{tag} 再显示载入新帖',n1>n0,f'{n0}->{n1}')
                    c=g.locator('.post').nth(n1-1); bb=c.locator('.ex2'); ok=bb.count()==1
                    if ok: bb.evaluate("e=>e.scrollIntoView({block:'center'})"); g.wait_for_timeout(60); bb.click(); g.wait_for_timeout(320); ok=c.locator('.pxd').evaluate(VIS)
                    ck(f'{tag} 再显示的帖子可展开',ok)
                ck(f'{tag} 无 JS 错误',not err,err[:1]); g.close()
        b.close()
    b=p.chromium.launch(executable_path=os.environ.get('CHROME_PATH') or None,args=['--no-sandbox'])
    for w in (721,768,900,1024,1100):
        for pg in ('index.html',day):
            g=b.new_page(viewport={'width':w,'height':900})
            g.add_init_script("window.__c=0;new PerformanceObserver(l=>l.getEntries().forEach(e=>{if(!e.hadRecentInput)window.__c+=e.value})).observe({type:'layout-shift',buffered:true})")
            g.goto(B+pg); g.wait_for_timeout(900); c=g.evaluate('window.__c'); ck(f'CLS[{w}] {pg} ≤ 0.001',c<=0.001,round(c,4)); g.close()
    b.close()
json.dump(R,open(os.path.join(D,'expand_result.json'),'w'),ensure_ascii=False,indent=1)
for k,v in R.items():
    if v.startswith('FAIL'): print(k,v)
print('expand:','ALL PASS' if not bad else f'{bad} FAIL',f'({len(R)} checks)')
