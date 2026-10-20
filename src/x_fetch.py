#!/usr/bin/env python3
"""用你自己的 X API v2 Bearer Token 抓取公开数据，写成 raw/ 下的 JSON 并入库（xhot.db）。
令牌只从环境变量 X_BEARER_TOKEN 读取，绝不写入文件或日志。

用法：
  python3 x_fetch.py full      # 完整刷新：账号资料 → 时间线（since_id 增量）→ 话题计数 → X 新闻（可选）
  python3 x_fetch.py light     # 轻量刷新：只拉最近 7 天最热的 HOT_N 个账号的时间线
  python3 x_fetch.py users | timelines | counts | news   # 单步
环境变量：X_BEARER_TOKEN（必需）、HOT_N（默认 60）、MAX_CALLS（本次调用上限，默认 400）、X_NEWS=0 跳过新闻。
限额：遇到 429 按 x-rate-limit-reset 等待后重试一次；每次调用之间至少间隔 1.1s。"""
import json,os,sys,time,sqlite3,subprocess,datetime,urllib.request,urllib.parse,urllib.error
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D); os.makedirs('raw',exist_ok=True)
API='https://api.x.com/2'; TOK=os.environ.get('X_BEARER_TOKEN','').strip()
MAX=int(os.environ.get('MAX_CALLS','400')); HOT_N=int(os.environ.get('HOT_N','60')); calls=0; last=0.0
W=json.load(open('watchlist.json',encoding='utf-8')); DOMS=[k for k in W if not k.startswith('_')]
UF='created_at,description,public_metrics,verified,profile_image_url'
TF='created_at,public_metrics,note_tweet,lang,author_id'
def get(path,params):
    global calls,last
    if calls>=MAX: raise SystemExit(f'达到本次调用上限 MAX_CALLS={MAX}')
    for attempt in (1,2):
        time.sleep(max(0,1.1-(time.time()-last))); last=time.time(); calls+=1
        r=urllib.request.Request(API+path+'?'+urllib.parse.urlencode(params),headers={'Authorization':'Bearer '+TOK,'User-Agent':'xhot-fetch'})
        try:
            with urllib.request.urlopen(r,timeout=30) as x: return json.load(x)
        except urllib.error.HTTPError as ex:
            if ex.code==429 and attempt==1:
                rs=int(ex.headers.get('x-rate-limit-reset') or time.time()+60); w=min(900,max(5,rs-int(time.time())+2))
                print(f'429 限流，等待 {w}s'); time.sleep(w); continue
            print('HTTP',ex.code,path,ex.read()[:200].decode('utf-8','ignore')); return None
def save(label,j):
    p=f'raw/_tmp_{label}.json'; json.dump(j,open(p,'w',encoding='utf-8'),ensure_ascii=False); return p
def handles():
    hs=[]
    for d in DOMS:
        for k,x in W[d].items():
            if k=='groups': [hs.extend(l) for l in x.values()]
            elif k.startswith('accounts'): hs+=x
    return list(dict.fromkeys(h.lower() for h in hs))
def users():
    hs=handles(); fs=[]
    for i in range(0,len(hs),100):
        j=get('/users/by',{'usernames':','.join(hs[i:i+100]),'user.fields':UF})
        if j: fs+=[f'users_{i//100}',save(f'users_{i//100}',j)]
    if fs: subprocess.run([sys.executable,'ingest.py']+fs,check=True)
def tl_rows():
    out=subprocess.run([sys.executable,'tl_plan.py'],capture_output=True,text=True,check=True).stdout.split('\n')
    return [l.split(' ') for l in out if l.strip()]
def hot(n):
    db=sqlite3.connect('xhot.db'); c=(datetime.datetime.utcnow()-datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S')
    return {r[0] for r in db.execute('select author_id from tweets where created_at>=? group by author_id order by sum(likes+2*rts+3*quotes+replies) desc limit ?',(c,n))}
def timelines(only=None):
    fs=[]
    for row in tl_rows():
        h,uid=row[0],row[1]; since=row[2] if len(row)>2 else ''
        if only is not None and uid not in only: continue
        p={'max_results':25,'exclude':'replies,retweets','tweet.fields':TF}
        if since: p['since_id']=since
        j=get(f'/users/{uid}/tweets',p)
        if j: fs.append(save(f'tl_{h}',j))
    if fs: subprocess.run([sys.executable,'ingest_tl.py']+fs,check=True)
def counts():
    a=[]
    for d in DOMS:
        for name,q in (W[d].get('trend_queries') or {}).items():
            j=get('/tweets/counts/recent',{'query':q,'granularity':'day'})
            if j: lab=f'counts_{d}__{name}'; a+=[lab,save(lab.replace('/','_'),j)]
    if a: subprocess.run([sys.executable,'ingest.py']+a,check=True)
def news():
    # X API v2 新闻检索（需要你的 API 套餐支持；不支持时跳过，站点仍可只用 AIHOT 资讯）
    a=[]
    for d in DOMS:
        q=W[d].get('news_query')
        if not q: continue
        j=get('/news/search',{'query':q,'max_results':20})
        if j: a+=[f'news_{d}',save(f'news_{d}',j)]
    if not a: print('X 新闻：无结果或套餐不支持，跳过'); return
    subprocess.run([sys.executable,'ingest.py']+a,check=True)
    b=[]
    for l in subprocess.run([sys.executable,'news_posts_plan.py'],capture_output=True,text=True).stdout.split('\n'):
        if not l.strip() or ' ' not in l: continue
        d,ids=l.split(' ',1)
        j=get('/tweets',{'ids':ids,'tweet.fields':TF,'expansions':'author_id','user.fields':'username,name'})
        if j: b+=[f'news_posts_{d}',save(f'news_posts_{d}',j)]
    if b: subprocess.run([sys.executable,'ingest.py']+b,check=True)
if __name__=='__main__':
    if not TOK: raise SystemExit('请先设置环境变量 X_BEARER_TOKEN（在 developer.x.com 创建 App 获取）')
    m=sys.argv[1] if len(sys.argv)>1 else 'full'
    try:
        if m in('full','users'): users()
        if m in('full','timelines'): timelines()
        if m=='light': timelines(hot(HOT_N))
        if m in('full','counts'): counts()
        if m in('full','news') and os.environ.get('X_NEWS','1')!='0': news()
    finally:
        for f in os.listdir('raw'):
            if f.startswith('_tmp_'): os.remove(os.path.join('raw',f))
        print('X API 调用次数',calls)
