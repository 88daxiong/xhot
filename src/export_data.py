#!/usr/bin/env python3
"""把 xhot.db 导出为 JSON 备份：<out>/tweets/<handle>.json、accounts.json、followers_history.json、README.md。
用法：python3 export_data.py [输出目录，默认 ../data]。键排序固定、缩进 2，方便看 diff。不导出 raw/ 或任何密钥。"""
import os,sys,json,sqlite3
D=os.path.dirname(os.path.abspath(__file__))
OUT=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data')
db=sqlite3.connect(os.path.join(D,'xhot.db')); W=json.load(open(os.path.join(D,'watchlist.json'),encoding='utf-8'))
def dump(p,o):
    os.makedirs(os.path.dirname(p),exist_ok=True)
    s=json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)+'\n'
    if not os.path.exists(p) or open(p,encoding='utf-8').read()!=s: open(p,'w',encoding='utf-8').write(s)
ids={u:i for u,i in db.execute('select username,user_id from followers')}
hist={}
for ts,u,uid,name,f,fg,tw in db.execute('select ts,username,user_id,name,followers,following,tweets from followers order by username,ts'):
    hist.setdefault(u,[]).append({'ts':ts,'followers':f,'following':fg,'tweets':tw})
acc={}
for dom,cfg in W.items():
    if dom.startswith('_'): continue
    grp={}
    for g,us in (cfg.get('groups') or {}).items():
        for u in us: grp.setdefault(u.lower(),g)
    for u in cfg.get('accounts',[])+cfg.get('accounts_zh',[])+[x for us in (cfg.get('groups') or {}).values() for x in us]:
        k=u.lower(); a=acc.setdefault(k,{'handle':k,'domains':[],'groups':[],'zh':False})
        if dom not in a['domains']: a['domains'].append(dom)
        if k in grp and grp[k] not in a['groups']: a['groups'].append(grp[k])
        if u in cfg.get('accounts_zh',[]): a['zh']=True
n=0
for k,a in acc.items():
    r=db.execute('select ts,name,followers from followers where username=? order by ts desc limit 1',(k,)).fetchone()
    a.update(user_id=ids.get(k),name=r[1] if r else None,followers=r[2] if r else None,followers_ts=r[0] if r else None)
    uid=ids.get(k); tw=[]
    if uid:
        for x in db.execute('select id,created_at,text,lang,likes,rts,replies,quotes,views,bm,url from tweets where author_id=? order by created_at desc',(uid,)):
            tw.append({'id':x[0],'created_at':x[1],'text':x[2],'lang':x[3],'metrics':{'like':x[4],'retweet':x[5],'reply':x[6],'quote':x[7],'impression':x[8],'bookmark':x[9]},'url':x[10]})
    a['tweets_stored']=len(tw); n+=len(tw)
    dump(os.path.join(OUT,'tweets',f'{k}.json'),{'handle':k,'user_id':uid,'tweets':tw})
dump(os.path.join(OUT,'accounts.json'),{'accounts':[acc[k] for k in sorted(acc)]})
dump(os.path.join(OUT,'followers_history.json'),{'history':{k:hist[k] for k in sorted(hist)}})
open(os.path.join(OUT,'README.md'),'w',encoding='utf-8').write('''# XHOT 数据备份

由 `export_data.py` 从 xhot.db 导出，每次刷新时更新。JSON 键排序固定、缩进 2。

- `accounts.json`：关注列表里的每个账号，包括 handle、user_id、名字、所属领域/分组、是否中文号、最新粉丝数（`followers_ts` 是快照时间）、已存推文数。
- `followers_history.json`：每个账号的粉丝时间序列（`ts`、`followers`、`following`、`tweets`），ts 是北京时间 `YYYYMMDD_HHMMSS`。
- `tweets/<handle>.json`：该账号本地存储的原创推文（最多 200 条，最新在前），字段有 id、created_at（UTC）、text（长推文是全文 note_tweet）、lang、metrics（like/retweet/reply/quote/impression/bookmark）、url。

数据来源：X API（get_users_posts、get_users_by_usernames）。只做备份和展示，版权归原作者。
''')
print('accounts',len(acc),'tweets',n)
