#!/usr/bin/env python3
"""用法: python3 ingest.py <label> <API 结果文件> [<label> <file> ...]
截取文件中第一个 { 到最后一个 } 之间的 JSON（允许前后有说明文字），保存为 raw/<时间戳>_<label>.json，并把 users_* 写入 SQLite 粉丝时间序列。"""
import sys, json, os, sqlite3, datetime
D=os.path.dirname(os.path.abspath(__file__)); RAW=os.path.join(D,'raw')
ts=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
db=sqlite3.connect(os.path.join(D,'xhot.db'))
db.execute('create table if not exists followers(ts text, username text, user_id text, name text, followers integer, following integer, tweets integer, primary key(ts,username))')
a=sys.argv[1:]
for label,f in zip(a[0::2],a[1::2]):
    t=open(f,encoding='utf-8').read(); j=json.loads(t[t.index('{'):t.rindex('}')+1])
    j['_fetched_at']=datetime.datetime.now().astimezone().isoformat(); j['_label']=label
    out=os.path.join(RAW,f'{ts}_{label}.json'); json.dump(j,open(out,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    if label.startswith('users_'):
        for u in j.get('data',[]):
            m=u['public_metrics']; db.execute('insert or replace into followers values(?,?,?,?,?,?,?)',(ts,u['username'].lower(),u['id'],u['name'],m['followers_count'],m['following_count'],m['tweet_count']))
    print('saved',out)
db.commit()
