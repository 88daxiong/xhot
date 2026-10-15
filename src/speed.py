"""v14 vs v15 测速：python3 speed.py <v14_base> <v15_base> > speed.json
每页 × 视口(1440/390) × 网络(无节流 / Fast 3G) × CPU(1× / 4×)：FCP / LCP / CLS / load / 传输 KB / 请求数；另测交互（INP 近似：Event Timing 最大 duration，CPU 4×）。"""
import sys,json
from playwright.sync_api import sync_playwright
B14,B15=sys.argv[1],sys.argv[2]
PAIRS=[('今日/首页','index.html','index.html'),('人物','accounts.html','people.html'),('资讯','news.html','news.html'),('趋势','trends.html','trends.html'),('人物页','p/karpathy.html','p/karpathy.html'),('归档(热帖)','hot.html','d/all.html')]
F3G=dict(offline=False,latency=562.5,downloadThroughput=1.44e6/8*.9,uploadThroughput=675e3/8*.9)
INIT="""window.__lcp=0;window.__cls=0;window.__ev=[];
new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lcp=e.startTime}).observe({type:'largest-contentful-paint',buffered:true});
new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.__cls+=e.value}).observe({type:'layout-shift',buffered:true});
try{new PerformanceObserver(l=>{for(const e of l.getEntries())window.__ev.push([e.name,Math.round(e.duration)])}).observe({type:'event',durationThreshold:16,buffered:true})}catch(x){}"""
M="""()=>{const n=performance.getEntriesByType('navigation')[0],rs=performance.getEntriesByType('resource');const f=performance.getEntriesByName('first-contentful-paint')[0];
return {fcp:Math.round(f?f.startTime:0),lcp:Math.round(window.__lcp),cls:+window.__cls.toFixed(4),load:Math.round(n.loadEventEnd),kb:+((rs.reduce((s,x)=>s+(x.transferSize||0),0)+n.transferSize)/1024).toFixed(1),req:rs.length+1,
 js:+(rs.filter(x=>/\\.js(\\?|$)/.test(x.name)).reduce((s,x)=>s+(x.transferSize||0),0)/1024).toFixed(1),css:+(rs.filter(x=>/\\.css(\\?|$)/.test(x.name)).reduce((s,x)=>s+(x.transferSize||0),0)/1024).toFixed(1),
 html:+(n.transferSize/1024).toFixed(1),img:+(rs.filter(x=>x.initiatorType==='img').reduce((s,x)=>s+(x.transferSize||0),0)/1024).toFixed(1)}}"""
out={}
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
    def run(base,path,vw,net,cpu):
        c=b.new_context(viewport={'width':vw,'height':900 if vw>600 else 844});pg=c.new_page();cdp=c.new_cdp_session(pg);cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True})
        if net=='fast3g': cdp.send('Network.emulateNetworkConditions',F3G)
        if cpu>1: cdp.send('Emulation.setCPUThrottlingRate',{'rate':cpu})
        pg.add_init_script(INIT); pg.goto(base+path,wait_until='load',timeout=180000); pg.wait_for_timeout(2500 if net=='fast3g' else 500)
        r=pg.evaluate(M); c.close(); return r
    for net,cpu in (('none',1),('fast3g',1),('fast3g',4)):
        for label,p14,p15 in PAIRS:
            for vw in (1440,390):
                if cpu==4 and vw==1440 and label not in('今日/首页',): continue
                for ver,base,path in (('v14',B14,p14),('v15',B15,p15)):
                    out[f'{net}|cpu{cpu}|{label}|{vw}|{ver}']=run(base,path,vw,net,cpu); print(f'{net} cpu{cpu} {label} {vw} {ver}',out[f'{net}|cpu{cpu}|{label}|{vw}|{ver}'],file=sys.stderr,flush=True)
    # 交互（INP 近似），CPU 4×，无网络节流
    ACTS={'v14':{'今日/首页':[('click','.ex'),('click','[data-density]')],'人物':[('type','#aq|a')],'资讯':[('click','.nr >> nth=2'),('click','.nr >> nth=5')]},
          'v15':{'今日/首页':[('click','#t30 [data-dom="money"]'),('click','.dh .ex'),('key','Control+k'),('type2','karp'),('key','Escape'),('click','#t30 [data-dom="all"]')],'人物':[('click','[data-asort="w"]'),('type','#aq|a')],'资讯':[('click','.nr >> nth=2'),('click','.nr >> nth=5')]}}
    for ver,base,pairs in (('v14',B14,{x[0]:x[1] for x in PAIRS}),('v15',B15,{x[0]:x[2] for x in PAIRS})):
        for label,acts in ACTS[ver].items():
            c=b.new_context(viewport={'width':1440,'height':900});pg=c.new_page();cdp=c.new_cdp_session(pg);cdp.send('Emulation.setCPUThrottlingRate',{'rate':4});pg.add_init_script(INIT)
            pg.goto(base+pairs[label],wait_until='load');pg.wait_for_timeout(800)
            for k,a in acts:
                try:
                    if k=='click': pg.click(a,timeout=3000)
                    elif k=='key': pg.keyboard.press(a)
                    elif k=='type2': pg.keyboard.type(a,delay=30)
                    elif k=='type': s,t=a.split('|'); pg.fill(s,''); pg.type(s,t,delay=30)
                except Exception as x: print('skip',ver,label,a,str(x)[:60],file=sys.stderr)
                pg.wait_for_timeout(400)
            ev=pg.evaluate("window.__ev"); IE=('pointerdown','pointerup','click','keydown','keyup','keypress','mousedown','mouseup','beforeinput','input'); ev=[x for x in ev if x[0] in IE]; out[f'inp|{label}|{ver}']={'max':max([d for _,d in ev] or [0]),'n':len(ev),'ev':sorted(ev,key=lambda x:-x[1])[:6]}; print('inp',label,ver,out[f'inp|{label}|{ver}'],file=sys.stderr,flush=True); c.close()
    b.close()
print(json.dumps(out,ensure_ascii=False))
