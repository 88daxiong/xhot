"""v15 模糊测试：python3 fuzz.py [种子数=6]
把随机“恶意”字符串灌进 daily / weekly JSON 的所有可写字段（摘要、译文、摘录、要点、标签、url、pin/hide、changelog…），
在临时目录里构建站点，扫描：on* 属性、多余 <script>、javascript:/data: 链接、注入的 img/iframe/svg/form、坏掉的 JSON 数据块、构建崩溃。"""
import os,sys,json,random,re,subprocess,tempfile,shutil,glob
from html.parser import HTMLParser
D=os.path.dirname(os.path.abspath(__file__)); N=int(sys.argv[1]) if len(sys.argv)>1 else 6
ATOMS=['<script>alert(1)</script>','"><img src=x onerror=alert(1)>',"'onmouseover='alert(1)",'javascript:alert(1)','</script><script>1</script>','<!--','-->','<svg onload=alert(1)>','&lt;b&gt;','&#x3c;script&#x3e;',
 '\u2028','\u2029','\u0000','\ufeff','${7*7}','{{7*7}}','`','\\','\\"','%00','data:text/html,x','https://a.com/"onfocus="x','http://[::1','@@CSS@@','@@SJ@@','@@JS:core@@','</style>','<iframe src=//evil>','<form action=//evil>','🙂','中文','x'*300,' ','\n','\r\n','<a href=javascript:1>','</div></li></ul>']
class P(HTMLParser):
    def __init__(s): super().__init__(); s.t=[]
    def handle_starttag(s,t,a): s.t.append((t,{k:(v or '') for k,v in a}))
    handle_startendtag=handle_starttag
def tags(h): p=P(); p.feed(h); return p.t
def rnd(r): return ''.join(r.choice(ATOMS) if r.random()<.45 else r.choice(['Hello ','world ','model ','agent ','中文 ','AI ','test ']) for _ in range(r.randint(1,6)))
def mutate(o,r,keys=None):
    if isinstance(o,str): return rnd(r) if r.random()<.7 else o+rnd(r)
    if isinstance(o,list): return [mutate(x,r) for x in o]
    if isinstance(o,dict): return {k:(mutate(v,r) if k not in ('post_id','id','date','week') or r.random()<.3 else v) for k,v in o.items()}
    return o
def build(out,dd,wd):
    return subprocess.run([sys.executable,os.path.join(D,'generate.py'),out],env=dict(os.environ,XHOT_DAILY_DIR=dd,XHOT_WEEKLY_DIR=wd),capture_output=True,text=True,timeout=300)
fails=0; total=0
for seed in range(N):
    r=random.Random(seed); tmp=tempfile.mkdtemp(); dd=os.path.join(tmp,'daily'); wd=os.path.join(tmp,'weekly'); os.makedirs(dd); os.makedirs(wd); out=os.path.join(tmp,'out')
    for f in glob.glob(os.path.join(D,'daily','*.json')):
        d=json.load(open(f,encoding='utf-8')); d2=mutate(d,r); d2['date']=d['date']
        for h,h0 in zip(d2.get('highlights',[]),d.get('highlights',[])): h['post_id']=h0['post_id'] if r.random()<.8 else rnd(r)
        json.dump(d2,open(os.path.join(dd,os.path.basename(f)),'w',encoding='utf-8'),ensure_ascii=False)
    for f in glob.glob(os.path.join(D,'weekly','*.json')):
        w=json.load(open(f,encoding='utf-8')); w2=mutate(w,r); json.dump(w2,open(os.path.join(wd,os.path.basename(f)),'w',encoding='utf-8'),ensure_ascii=False)
    res=build(out,dd,wd); total+=1; probs=[]
    # 构建允许“拒绝坏数据”（非 0 退出但不能是 Python 崩溃堆栈以外的静默输出）；崩溃也记为失败，便于发现未处理的输入
    if res.returncode!=0: probs.append('build crashed: '+res.stderr.strip().splitlines()[-1][:160] if res.stderr.strip() else 'build failed')
    else:
        for f in glob.glob(out+'/**/*.html',recursive=True):
            T=tags(open(f,encoding='utf-8').read()); n=os.path.relpath(f,out)
            for t,a in T:
                if any(k.lower().startswith('on') for k in a): probs.append(f'{n}: on* attr {t}')
                for k in ('href','src','action','formaction','xlink:href'):
                    v=(a.get(k) or '').strip().lower()
                    if re.match(r'(javascript|vbscript|data):',v) and not(t=='link' and a.get('rel')=='icon' and (v.startswith('data:image/svg+xml,') or v=='data:,')): probs.append(f'{n}: {k}={v[:30]}')
                if t in('iframe','object','embed','form','textarea','base','meta') and not(t=='meta'): probs.append(f'{n}: <{t}>')
                if t=='img' and a.get('src') in('x','//evil'): probs.append(f'{n}: injected img')
            sc=[a for t,a in T if t=='script' and not a.get('src') and a.get('type')!='application/json']
            if len(sc)>1 or (len(sc)==0 and 'http-equiv="refresh"' not in open(f,encoding='utf-8').read() and not n.endswith('status.html')):  probs.append(f'{n}: {len(sc)} inline scripts')
            if sum(1 for t,_ in T if t=='style')>1: probs.append(f'{n}: multiple <style>')
            txt=open(f,encoding='utf-8').read()
            if re.search(r'@@(CSS|SJ|JS)',txt): probs.append(f'{n}: placeholder leaked')
            for m in re.finditer(r'<script type="application/json"[^>]*>(.*?)</script>',txt,re.S):
                try: json.loads(m.group(1))
                except Exception: probs.append(f'{n}: bad json block')
    ok=not probs; fails+=0 if ok else 1
    print(('PASS' if ok else 'FAIL'),f'seed {seed}',('' if ok else probs[:4]))
    shutil.rmtree(tmp,ignore_errors=True)
print(f'fuzz: {total-fails}/{total} passed'); sys.exit(1 if fails else 0)
