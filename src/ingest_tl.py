#!/usr/bin/env python3
"""用法: python3 ingest_tl.py <API 结果文件>... 把 get_users_posts 结果写入 tweets 表（按 id 去重），每账号保留最新 200 条。"""
import sys,json,os,sqlite3,shutil,datetime
D=os.path.dirname(os.path.abspath(__file__))
db=sqlite3.connect(os.path.join(D,'xhot.db'))
db.execute('create table if not exists tweets(id text primary key,author_id text,created_at text,text text,likes int,rts int,replies int,quotes int,views int,bm int,url text,lang text,fetched_at text)')
now=datetime.datetime.now().astimezone().isoformat();n=0;authors=set()
for f in sys.argv[1:]:
    t=open(f,encoding='utf-8').read()
    try: j=json.loads(t[t.index('{'):t.rindex('}')+1])
    except ValueError: print('skip',f);continue
    for p in (j.get('data') if isinstance(j.get('data'),list) else []):
        if 'author_id' not in p or 'created_at' not in p: continue
        m=p.get('public_metrics',{});txt=(p.get('note_tweet') or {}).get('text') or p['text']
        db.execute('insert or replace into tweets values(?,?,?,?,?,?,?,?,?,?,?,?,?)',(p['id'],p['author_id'],p['created_at'],txt,m.get('like_count',0),m.get('retweet_count',0),m.get('reply_count',0),m.get('quote_count',0),m.get('impression_count',0),m.get('bookmark_count',0),p.get('url',''),p.get('lang',''),now));n+=1;authors.add(p['author_id'])
for a in authors:
    db.execute('delete from tweets where author_id=? and id not in (select id from tweets where author_id=? order by created_at desc limit 200)',(a,a))
db.commit();print('ingested',n,'authors',len(authors),'total',db.execute('select count(*) from tweets').fetchone()[0])
