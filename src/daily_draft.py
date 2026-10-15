#!/usr/bin/env python3
"""日报素材：python3 daily_draft.py [YYYY-MM-DD] > /tmp/daily_draft.json
窗口 = 该日 08:00（北京时间）往前 24 小时（若是今天则截至最新抓取）。输出候选：
  posts   热度前 20（每人 1 条，只含中/英）：handle,name,id,url,likes,heat,created_at,text(前 400 字),text_orig(原帖全文，直接抄进日报 highlights[].text_orig),
          is_english(英文帖=true：入选 highlights 时必须再写 text_orig_zh = text_orig 的完整中文翻译；中文帖不需要)
  topics  话题最近一日条数 vs 前几日均值的涨跌（取窗口结束前最新一次计数）
  followers 粉丝变化前后各 6（与约 24 小时前的快照比）
刷新流程用它写 daily/YYYY-MM-DD.json（中文摘要由刷新人工/助手撰写），不直接发布。"""
import sys,os,json,glob,sqlite3,datetime,re,html
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D); sys.path.insert(0,D)
import langf
def is_english(t):
    """去掉链接 / @ / # 后几乎没有汉字、且有足够的拉丁字母 → 英文帖（与 generate.py 的 is_en 同一规则）"""
    t=re.sub(r'https?://\S+|[@#]\w+','',t or ''); cj=len(re.findall(r'[\u3400-\u9fff]',t)); la=len(re.findall(r'[A-Za-z]',t))
    return la>=12 and cj<=max(2,0.05*(cj+la))
TZ=datetime.timezone(datetime.timedelta(hours=8))
day=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now(TZ).strftime('%Y-%m-%d')
end=datetime.datetime.strptime(day+' 09:00','%Y-%m-%d %H:%M').replace(tzinfo=TZ); end=min(end,datetime.datetime.now(TZ))
start=end-datetime.timedelta(hours=25)
db=sqlite3.connect('xhot.db')
idm={}
for uid,u,n in db.execute('select user_id,username,name from followers order by ts'): idm[uid]=(u,n)
Z=lambda t:t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
posts=[];seen=set()
for r in db.execute('select id,author_id,created_at,text,likes,rts,replies,quotes,bm,url,lang from tweets where created_at>=? and created_at<? order by likes+2*rts+3*quotes+replies+coalesce(bm,0) desc',(Z(start),Z(end))):
    if r[1] not in idm or r[1] in seen or not langf.ok(r[3],r[10]): continue
    seen.add(r[1]); u,n=idm[r[1]]
    posts.append(dict(handle=u,name=n,id=r[0],url=r[9] or f'https://x.com/{u}/status/{r[0]}',likes=r[4],heat=r[4]+2*r[5]+3*r[7]+r[6]+(r[8] or 0),created_at=r[2],text=html.unescape(r[3])[:400],text_orig=html.unescape(r[3]),is_english=is_english(html.unescape(r[3]))))
    if len(posts)>=20: break
ts_end=end.strftime('%Y%m%d_%H%M%S')
snaps=[t for (t,) in db.execute('select distinct ts from followers where ts<=? order by ts',(ts_end,))]
fol=[]
if len(snaps)>=2:
    b=snaps[-1]; tgt=(datetime.datetime.strptime(b,'%Y%m%d_%H%M%S')-datetime.timedelta(hours=24)).strftime('%Y%m%d_%H%M%S')
    a=min(snaps[:-1],key=lambda t:abs(int(t[:8]+t[9:])-int(tgt[:8]+tgt[9:])))
    A={u:(f,n) for u,f,n in db.execute('select username,followers,name from followers where ts=?',(a,))}
    for u,f,n in db.execute('select username,followers,name from followers where ts=?',(b,)):
        if u in A: fol.append(dict(handle=u,name=n,delta=f-A[u][0],followers=f))
    fol.sort(key=lambda x:-x['delta']); fol=dict(window=[a,b],up=fol[:6],down=fol[::-1][:6])
tp=[]
by={}
for f in glob.glob('raw/*_counts_*__*.json'):
    b=os.path.basename(f); ts=b[:15]
    if ts>ts_end: continue
    lab=b[16:-5].replace('counts_','',1); dom,name=lab.split('__',1)
    if (dom,name) not in by or ts>by[(dom,name)][0]: by[(dom,name)]=(ts,f)
for (dom,name),(ts,f) in by.items():
    d=json.load(open(f,encoding='utf-8')).get('data',[]); v=[x['tweet_count'] for x in d[1:-1]] if len(d)>3 else [x['tweet_count'] for x in d]
    if len(v)<2: continue
    prev=sum(v[:-1])/len(v[:-1]); tp.append(dict(dom=dom,name=name,last=v[-1],change_pct=round((v[-1]/prev-1)*100,1) if prev else 0,ratio=round(v[-1]/prev,2) if prev else 0,ts=ts))
tp.sort(key=lambda x:-x['change_pct'])
print(json.dumps(dict(date=day,window=[start.isoformat(),end.isoformat()],posts=posts,topics=tp,followers=fol),ensure_ascii=False,indent=1))
