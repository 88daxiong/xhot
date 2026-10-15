#!/usr/bin/env python3
"""合规：检查站点展示过的帖子是否已被删除 / 变为受保护（X API v2 批量查询，每批 ≤100 个 ID）。
用法：X_BEARER_TOKEN=... python3 check_deleted.py [--days 14] [--apply]
- 默认只打印；--apply 把查不到的 ID 追加进 takedown.txt（生成器会跳过）。
- 只读、只查最近 N 天展示过的帖子，请求量 ≈ ⌈帖子数/100⌉ 次。尚未在生产流程里自动运行（见 REFRESH.md 的可选步骤）。"""
import os,sys,json,sqlite3,urllib.request,urllib.parse,datetime
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D)
tok=os.environ.get('X_BEARER_TOKEN'); days=int(sys.argv[sys.argv.index('--days')+1]) if '--days' in sys.argv else 14
if not tok: sys.exit('需要环境变量 X_BEARER_TOKEN')
import xhot_data
db=getattr(xhot_data,'db',None) or sqlite3.connect(os.path.join(D,'xhot.db'))
since=(datetime.datetime.utcnow()-datetime.timedelta(days=days)).strftime('%Y-%m-%dT%H:%M:%S')
ids=[r[0] for r in db.execute('select id from tweets where created_at>=?',(since,))]
gone=[]
for i in range(0,len(ids),100):
    q=urllib.parse.urlencode({'ids':','.join(map(str,ids[i:i+100])),'tweet.fields':'id'})
    rq=urllib.request.Request('https://api.x.com/2/tweets?'+q,headers={'Authorization':'Bearer '+tok})
    d=json.load(urllib.request.urlopen(rq))
    for er in d.get('errors',[]):
        if er.get('resource_id'): gone.append(er['resource_id'])
print(f'检查 {len(ids)} 条，查不到（已删除 / 受保护 / 账号停用）{len(gone)} 条')
for g in gone: print(g)
if '--apply' in sys.argv and gone:
    with open(os.path.join(D,'takedown.txt'),'a',encoding='utf-8') as f:
        for g in gone: f.write(f'{g}  # {datetime.date.today()} X API 查不到\n')
