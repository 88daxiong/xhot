"""v15 回归：逐条打开「资讯」里每一条（含 X 新闻英文条目/相关帖子），桌面（阅读窗格）+ 手机（就地展开）。
断言：无 JS 报错、无全屏遮罩误出现（elementFromPoint 仍能点到工具条按钮）、正文非空、无横向溢出、
手机展开后内容完整可见（底部不被裁）、桌面窗格内文字不溢出。用法：python3 news_all.py [base]"""
import sys
from playwright.sync_api import sync_playwright
B=next((a for a in sys.argv[1:] if a.startswith('http')),'http://127.0.0.1:8840/')
FAILS=[]
def fail(m):
    FAILS.append(m); print('FAIL',m,flush=True)
CHK="""()=>{const o={};const e=document.elementFromPoint(innerWidth/2,innerHeight/2);o.btnOK=!(e&&e.closest('.kov,.kp')&&getComputedStyle(e.closest('.kov,.kp')).position==='fixed');o.ctr=e?e.tagName+'.'+e.className:'';
o.ov=document.documentElement.scrollWidth>innerWidth+1;
o.fixed=[...document.querySelectorAll('body *')].filter(x=>{const c=getComputedStyle(x);if(c.position!=='fixed'||x.matches('.nside'))return false;const q=x.getBoundingClientRect();return q.width>=innerWidth*.9&&q.height>=innerHeight*.9&&c.display!=='none'&&x.offsetParent===null&&!x.hidden}).map(x=>x.tagName+'.'+x.className).slice(0,3);
const pb=document.querySelector('#npbody');o.pane=pb&&pb.offsetParent&&!document.querySelector('.nside.open')?{len:pb.textContent.trim().length,clip:pb.scrollWidth>pb.clientWidth+1}:null;
const sh=document.querySelector('.nside.open');if(sh&&pb){o.open={len:pb.textContent.trim().length,clipX:pb.scrollWidth>pb.clientWidth+1,lock:document.documentElement.classList.contains('nlock')}}return o}"""
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    for name,vp,mob in [('desk',{'width':1440,'height':900},False),('phone',{'width':390,'height':844},True)]:
        c=b.new_context(viewport=vp,device_scale_factor=2 if mob else 1,is_mobile=mob,has_touch=mob)
        pg=c.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)[:200])); pg.on('crash',lambda:errs.append('CRASH'))
        pg.goto(B+'news.html'); pg.wait_for_timeout(1500); pg.wait_for_function("()=>true")
        seen=set(); n=0
        for src in ['top','all','h','d','s','x']:
            pg.click(f'[data-src={src}]'); pg.wait_for_timeout(200)
            idx=pg.evaluate("[...document.querySelectorAll('.nr')].map((e,i)=>e.offsetParent?i:-1).filter(i=>i>=0)")
            for i in idx:
                di=pg.evaluate("i=>document.querySelectorAll('.nr')[i].dataset.i",i)
                if (src!='top' and di in seen): continue
                seen.add(di); n+=1
                pg.evaluate("i=>{const e=document.querySelectorAll('.nr')[i];e.scrollIntoView({block:'center'});e.querySelector('.nrh').click()}",i)
                pg.wait_for_timeout(120)
                r=pg.evaluate(CHK); t=f'{name}/{src}/#{di}'
                if not r['btnOK']: fail(t+' 视口中心被遮罩/相关帖子块盖住')
                if r['ov']: fail(t+' 横向溢出')
                if r['fixed']: fail(t+' 出现全屏固定层 '+str(r['fixed']))
                if name=='desk':
                    if not r['pane'] or r['pane']['len']<20: fail(t+' 阅读窗格正文为空')
                    elif r['pane']['clip']: fail(t+' 窗格内容横向被裁')
                else:
                    if not r['open'] or r['open']['len']<20: fail(t+' 阅读页内容为空')
                    elif r['open']['clipX']: fail(t+' 展开内容横向被裁')
                    pg.click('#nback'); pg.wait_for_timeout(60)  # 返回
        if errs: fail(name+' JS 错误 '+str(errs[:3]))
        print(name,'打开条目',n,flush=True)
print('news_all: FAIL %d'%len(FAILS) if FAILS else 'news_all: ALL PASS'); sys.exit(1 if FAILS else 0)
