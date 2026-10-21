"""v15 卡片头部 / 动作区回归：python3 card_layout_v15.py [base]
页面：今日 / 最新往期 / d/ai / d/all / 人物页 × 宽度 1440 / 1280 / 1024 / 768 / 390 × Chromium + WebKit。
断言：卡片头部作者名不换行（单行）；同一卡片内按钮 / 链接 / 点赞数 / 作者区互不重叠；
今日页桌面两栏布局占满内容宽度（右栏右边缘贴齐内容区，无空第三列）。"""
import sys,os,glob
from playwright.sync_api import sync_playwright
B=next((a for a in sys.argv[1:] if a.startswith('http')),'http://127.0.0.1:8840/')
D=os.path.dirname(os.path.abspath(__file__))
days=sorted(os.path.basename(f) for f in glob.glob(os.path.join(D,'site','day','*.html')))
PAGES=['index.html','d/ai.html','d/all.html','p/karpathy.html']+(['day/'+days[-1]] if days else [])
W=[1440,1280,1024,768,390]
JS="""()=>{const bad=[];const R=e=>e.getBoundingClientRect();
const vis=e=>{const r=R(e);return r.width>0&&r.height>0&&getComputedStyle(e).visibility!=='hidden'};
const ov=(a,b)=>!(a.right<=b.left+0.5||b.right<=a.left+0.5||a.bottom<=b.top+0.5||b.bottom<=a.top+0.5);
document.querySelectorAll('.dh,.post,.trw').forEach((c,ci)=>{if(!vis(c)||ci>40)return;
 [c.querySelector('.hh b,.who a,.who b,.trh b'),innerWidth>720?c.querySelector('.hh small'):null].forEach(nm=>{
 if(nm&&vis(nm)){const lh=parseFloat(getComputedStyle(nm).lineHeight)||parseFloat(getComputedStyle(nm).fontSize)*1.5;const rg=document.createRange();rg.selectNodeContents(nm);const ts=[...rg.getClientRects()].filter(x=>x.width>0).map(x=>x.top);if(ts.length&&Math.max(...ts)-Math.min(...ts)>lh*0.6)bad.push('作者名换行 '+nm.textContent.trim().slice(0,20))}})
 const els=[...c.querySelectorAll(':scope .btn,:scope .cpy,:scope .lk,:scope .hh,:scope .who,:scope .op')].filter(e=>vis(e)&&!e.closest('[hidden],.dor,.trx'));
 for(let i=0;i<els.length;i++)for(let j=i+1;j<els.length;j++){const a=els[i],b=els[j];if(a.contains(b)||b.contains(a))continue;if(ov(R(a),R(b)))bad.push('重叠 '+(a.className||a.tagName)+' × '+(b.className||b.tagName))}});
const g=document.querySelector('.dly .dgrid');if(g&&innerWidth>1000){const s=g.querySelector('.dside'),r=R(g);if(s&&Math.abs(R(s).right-r.right)>2)bad.push('两栏未占满宽度 右栏右边缘 '+Math.round(R(s).right)+' vs '+Math.round(r.right))}
return [...new Set(bad)].slice(0,6)}"""
F=[]
with sync_playwright() as p:
    for eng in ('chromium','webkit'):
        b=p.chromium.launch(executable_path=__import__('os').environ.get('CHROME_PATH') or None,args=['--no-sandbox']) if eng=='chromium' else p.webkit.launch()
        for w in W:
            ctx=b.new_context(viewport={'width':w,'height':900},**({'has_touch':True} if w<=768 else {}))
            g=ctx.new_page()
            for pg in PAGES:
                g.goto(B+pg); g.wait_for_timeout(300)
                r=g.evaluate(JS)
                if r: F.append(f'{eng}/{w}/{pg}: {r}'); print('FAIL',F[-1],flush=True)
            ctx.close()
        b.close()
print('card_layout:',('FAIL %d'%len(F)) if F else 'ALL PASS')
sys.exit(1 if F else 0)
