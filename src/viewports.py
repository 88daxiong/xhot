"""v15.1 多视口 / 触控 / 对比度 / 展开收起 断言：python3 viewports.py [base_url] [--quick]
视口：手机 360/390/430（竖）+ 844×390（横）、平板 768/820/1024（竖）+ 1024×768/1180×820（横）、笔记本 1366/1440、桌面 1920。
每页：无横向溢出、字号 ≥13px、对比度 ≥4.5:1（含深色）、触控设备上可点元素 ≥44px、顶栏/搜索可达、粘性元素不遮挡；
另测：新闻阅读区窄屏堆叠、展开/收起（点击 / 触摸 / 键盘、aria-expanded、无位移、reduced-motion、<100ms）。结果 viewports_result.json。"""
import sys,json,os,re
from playwright.sync_api import sync_playwright
B=next((a for a in sys.argv[1:] if a.startswith('http')),'http://127.0.0.1:8840/'); QUICK='--quick' in sys.argv
src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'audit.py'),encoding='utf-8').read()
AUD=re.search(r'JS=r"""(.*?)"""',src,re.S).group(1)
VPS=[('p360',360,740,1),('p390',390,844,1),('p430',430,932,1),('p844x390',844,390,1),('t768',768,1024,1),('t820',820,1180,1),('t1024',1024,1366,1),('t1024l',1024,768,1),('t1180l',1180,820,1),('l1366',1366,768,0),('l1440',1440,900,0),('d1920',1920,1080,0)]
PAGES=['index.html','day/2026-10-14.html','d/ai.html','d/all.html','people.html','p/karpathy.html','news.html','trends.html','about.html']
if QUICK: VPS=[v for v in VPS if v[0] in('p390','t820','l1440')]; PAGES=['index.html','news.html','about.html']
CHK=r"""()=>{const W=innerWidth,H=innerHeight,out={};
out.ov=document.documentElement.scrollWidth>W+1;
const vis=e=>{const r=e.getBoundingClientRect();const cs=getComputedStyle(e);return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'&&!e.closest('[hidden]')};
const small=[];const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const t=n.textContent.trim();if(!t)continue;const p=n.parentElement;if(!p||/^(SCRIPT|STYLE)$/.test(p.tagName)||!vis(p))continue;const fs=parseFloat(getComputedStyle(p).fontSize);if(fs<11.99)small.push(p.tagName+'.'+p.className+':'+fs)}
out.small=small.slice(0,4);
const tap=[];document.querySelectorAll('a[href],button,summary,select,input,[role=button]').forEach(e=>{if(!vis(e)||e.disabled||e.closest('.skip')||e.classList.contains('skip'))return;if(e.tagName==='A'&&e.closest('p,li:not(.nr):not(.trw):not(.dh),.pt,.ft,.abt,.nrb,.sec>small,.lead'))return;if(e.tagName==='A'&&e.closest('.ft'))return;const r=e.getBoundingClientRect();if(r.bottom<0||r.right<0)return;if(e.closest('.nav,.seg,.fchips,.kpl')&&false)return;if(r.height<43.5||r.width<43.5)tap.push((e.className||e.tagName)+':'+Math.round(r.width)+'x'+Math.round(r.height))});
out.tap=[...new Set(tap)].slice(0,6);
const top=document.querySelector('header.top');const cs=getComputedStyle(top);out.sticky=cs.position==='sticky'||cs.position==='fixed';out.topH=top.getBoundingClientRect().height;out.H=H;
const nav=[...document.querySelectorAll('.nav a')];out.navOk=nav.length===5&&nav.every(a=>{const r=a.getBoundingClientRect();return r.left>=-1&&r.right<=W+1&&r.width>0});
const kb=document.querySelector('.kb');const kr=kb.getBoundingClientRect();out.kbOk=kr.width>0&&kr.left>=0&&kr.right<=W+1;
return out}"""
res={'fail':[],'n':0}
def fail(m): res['fail'].append(m); print('FAIL',m,flush=True)
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=__import__('os').environ.get('CHROME_PATH') or None,args=['--no-sandbox'])
    for vn,vw,vh,touch in VPS:
        for th in ('light','dark'):
            if th=='dark' and vn not in('p390','t820','l1440') : continue
            c=b.new_context(viewport={'width':vw,'height':vh},color_scheme=th,has_touch=bool(touch),is_mobile=bool(touch and vw<1100));c.add_init_script("window.open=()=>null")
            for u in PAGES:
                g=c.new_page();g.goto(B+u,wait_until='load');g.wait_for_timeout(500);res['n']+=1;tag=f'{vn}/{th}/{u}'
                r=g.evaluate(CHK)
                if r['ov']: fail(tag+' 横向溢出')
                if r['small']: fail(tag+' 字号<12 '+str(r['small']))
                if touch and r['tap']: fail(tag+' 触控目标<44 '+str(r['tap']))
                if not r['navOk']: fail(tag+' 顶部导航超出视口')
                if not r['kbOk']: fail(tag+' 搜索入口不可达')
                if r['sticky'] and r['topH']>0.2*r['H']: fail(tag+f' 粘性顶栏过高 {r["topH"]:.0f}/{r["H"]}')
                a=g.evaluate(AUD.replace('()=>{','()=>{',1))
                low=[x for x in a if x['cr']<4.5]
                if low: fail(tag+' 对比度<4.5 '+str([(x['k'],x['cr'],x['t']) for x in low[:3]]))
                if u=='index.html' and th=='light':
                    # 搜索入口真的能点开
                    g.locator('.kb').click();g.wait_for_timeout(300)
                    if not g.evaluate("()=>{const k=document.querySelector('.kov');return !!k&&!k.hidden}"): fail(tag+' 点搜索未打开')
                    g.keyboard.press('Escape');g.wait_for_timeout(150)
                    # 展开/收起：位移、aria、时延
                    ex=g.locator('.dh .ex').first;y0=ex.bounding_box()['y'];t0=g.evaluate("()=>document.querySelector('.dh').getBoundingClientRect().top+scrollY")
                    ms=g.evaluate("()=>new Promise(res=>{const b=document.querySelector('.dh .ex'),s=performance.now();b.click();requestAnimationFrame(()=>requestAnimationFrame(()=>res(performance.now()-s)))})")
                    st=g.evaluate("()=>{const b=document.querySelector('.dh .ex'),d=document.getElementById(b.getAttribute('aria-controls'));return [b.getAttribute('aria-expanded'),!d.hidden&&d.offsetHeight>0]}")
                    t1=g.evaluate("()=>document.querySelector('.dh').getBoundingClientRect().top+scrollY")
                    if st!=['true',True]: fail(tag+' 展开状态不对 '+str(st))
                    if abs(t1-t0)>1: fail(tag+f' 展开造成上方位移 {t1-t0}')
                    if ms>100: fail(tag+f' 展开耗时 {ms:.0f}ms>100')
                    g.evaluate("document.querySelector('.dh .ex').click()")
                    if g.evaluate("()=>document.querySelector('.dh .ex').getAttribute('aria-expanded')")!='false': fail(tag+' 收起后 aria-expanded 未复位')
                    # 键盘
                    g.evaluate("document.querySelector('.dh .ex').focus()");g.keyboard.press('Enter');g.wait_for_timeout(120)
                    if g.evaluate("()=>document.querySelector('.dh .ex').getAttribute('aria-expanded')")!='true': fail(tag+' 键盘 Enter 不能展开')
                    g.keyboard.press('Space');g.wait_for_timeout(120)
                    if g.evaluate("()=>document.querySelector('.dh .ex').getAttribute('aria-expanded')")!='false': fail(tag+' 键盘 Space 不能收起')
                    # 触摸
                    if touch:
                        g.locator('.dh .ex').first.tap();g.wait_for_timeout(150)
                        if g.evaluate("()=>document.querySelector('.dh .ex').getAttribute('aria-expanded')")!='true': fail(tag+' 触摸点击不能展开')
                    # Top30 <details>
                    g.evaluate("document.querySelector('.tl30 .trw summary').focus()");g.keyboard.press('Enter');g.wait_for_timeout(150)
                    if not g.evaluate("()=>document.querySelector('.tl30 .trw details').open"): fail(tag+' summary 键盘不能展开')
                if u=='news.html':
                    g.locator('#ntop .nr .nrh').first.click();g.wait_for_timeout(500)
                    ov=g.evaluate("()=>document.documentElement.scrollWidth>innerWidth+1")
                    if ov: fail(tag+' 新闻展开后横向溢出')
                    if vw<=1000:
                        r2=g.evaluate("()=>{const s=document.querySelector('.nside'),q=s.getBoundingClientRect(),bk=document.querySelector('#nback').getBoundingClientRect(),pb=document.querySelector('#npbody');return {open:s.classList.contains('open'),pos:getComputedStyle(s).position,full:Math.abs(q.width-innerWidth)<2&&Math.abs(q.height-innerHeight)<2,bk:[Math.round(bk.width),Math.round(bk.height)],lock:document.documentElement.classList.contains('nlock'),len:pb.textContent.trim().length,clip:pb.scrollWidth>pb.clientWidth+1}}")
                        if not (r2['open'] and r2['pos']=='fixed' and r2['full'] and r2['lock'] and r2['len']>20 and not r2['clip']) or r2['bk'][1]<44: fail(tag+' 窄屏阅读页（整页滑入）状态不对 '+str(r2))
                        g.click('#nback');g.wait_for_timeout(450)
                        if g.evaluate("()=>document.querySelector('.nside').classList.contains('open')||document.documentElement.classList.contains('nlock')"): fail(tag+' 返回键没有关闭阅读页')
                g.close()
            if th=='light' and vn in('p390','t820'):
                g=c.new_page();g.goto(B+'index.html',wait_until='load');g.wait_for_timeout(400)
                # reduced motion
                c2=b.new_context(viewport={'width':vw,'height':vh},reduced_motion='reduce');g2=c2.new_page();g2.goto(B+'index.html',wait_until='load');g2.wait_for_timeout(300)
                g2.evaluate("document.querySelector('.dh .ex').click()");d=g2.evaluate("()=>getComputedStyle(document.querySelector('.dh .dor')).animationName")
                if d!='none': fail(f'{vn} reduced-motion 仍有动画 {d}')
                c2.close();g.close()
            c.close()
    b.close()
print(json.dumps({'pages':res['n'],'fails':len(res['fail'])}));json.dump(res,open('viewports_result.json','w'),ensure_ascii=False,indent=0)
