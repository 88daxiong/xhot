#!/usr/bin/env python3
"""列出本次需要的 get_users_posts 调用：每行 handle user_id since_id（库里没有该账号推文时 since_id 为空）。跳过 SKIP 里的账号。"""
import json,sqlite3,os
D=os.path.dirname(os.path.abspath(__file__));db=sqlite3.connect(os.path.join(D,'xhot.db'));W=json.load(open(os.path.join(D,'watchlist.json')))
SKIP={'hecaitou'}  # 受保护账号
hs=[]
for d,v in W.items():
    if d.startswith('_'): continue
    for k,x in v.items():
        if k=='groups': [hs.extend(l) for l in x.values()]
        elif k.startswith('accounts'): hs+=x
ids=dict(db.execute('select username,user_id from followers'))
for h in dict.fromkeys(h.lower() for h in hs):
    if h in SKIP or h not in ids: continue
    s=db.execute('select cast(max(cast(id as integer)) as text) from tweets where author_id=?',(ids[h],)).fetchone()[0] or ''
    print(h,ids[h],s)
