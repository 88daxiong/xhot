#!/usr/bin/env python3
"""离线演示数据：不需要任何令牌，生成一份虚构的 xhot.db + raw/ 快照，用来验证生成器与测试能跑通。
内容全部是占位文字（不是任何真实帖子）。用法：python3 demo_seed.py && python3 generate.py
注意：会覆盖当前目录下的 xhot.db 与 raw/*_demo_* 文件，不要在有真实数据的目录里运行。"""
import json,os,sqlite3,datetime,random
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D); os.makedirs('raw',exist_ok=True)
random.seed(7); W=json.load(open('watchlist.json',encoding='utf-8')); DOMS=[k for k in W if not k.startswith('_')]
hs=[]
for d in DOMS:
    for k,x in W[d].items():
        if k=='groups': [hs.extend(l) for l in x.values()]
        elif k.startswith('accounts'): hs+=x
hs=list(dict.fromkeys(hs))
if os.path.exists('xhot.db'): os.remove('xhot.db')
db=sqlite3.connect('xhot.db')
db.execute('create table if not exists followers(ts text, username text, user_id text, name text, followers integer, following integer, tweets integer, primary key(ts,username))')
db.execute('create table if not exists tweets(id text primary key,author_id text,created_at text,text text,likes int,rts int,replies int,quotes int,views int,bm int,url text,lang text,fetched_at text)')
now=datetime.datetime.now(datetime.timezone.utc); users=[]; tid=1900000000000000000
for i,h in enumerate(hs):
    uid=str(1000+i); f=random.randint(2000,3000000)
    users.append({'id':uid,'username':h,'name':h,'description':'演示账号（虚构数据）','public_metrics':{'followers_count':f,'following_count':100,'tweet_count':1000,'listed_count':0}})
    for k,ts in enumerate([now-datetime.timedelta(days=3),now-datetime.timedelta(hours=2)]):
        db.execute('insert or replace into followers values(?,?,?,?,?,?,?)',(ts.strftime('%Y%m%d_%H%M%S'),h.lower(),uid,h,f-k*random.randint(0,500),100,1000))
    for n in range(30):
        tid+=random.randint(1000,99999); t=now-datetime.timedelta(hours=random.randint(1,24*28))
        lk=random.randint(5,20000)
        db.execute('insert or replace into tweets values(?,?,?,?,?,?,?,?,?,?,?,?,?)',(str(tid),uid,t.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            f'这是 {h} 的第 {n+1} 条演示帖子：AI 智能体、开源模型与创业的占位文字。Demo post about agents and open models.',lk,lk//10,lk//20,lk//50,lk*30,lk//15,
            f'https://x.com/{h}/status/{tid}','zh',now.isoformat()))
db.commit()
ts=now.strftime('%Y%m%d_%H%M%S')
json.dump({'data':users,'_label':'users_demo'},open(f'raw/{ts}_users_demo.json','w',encoding='utf-8'),ensure_ascii=False)
for d in DOMS:
    for name in (W[d].get('trend_queries') or {}):
        days=[{'start':(now-datetime.timedelta(days=6-i)).strftime('%Y-%m-%dT00:00:00.000Z'),'end':(now-datetime.timedelta(days=5-i)).strftime('%Y-%m-%dT00:00:00.000Z'),'tweet_count':random.randint(500,30000)} for i in range(7)]
        json.dump({'data':days,'_label':f'counts_{d}__{name}'},open(f'raw/{ts}_counts_{d}__{name.replace("/","_")}.json','w',encoding='utf-8'),ensure_ascii=False)
print('demo: 账号',len(hs),'帖子',db.execute('select count(*) from tweets').fetchone()[0])
# 日报 / 周要点示例（仅当目录里还没有任何文件时写入；test_escape.py / fuzz.py 需要至少各一份）
for sub,sample,name in (('daily','daily.sample.json',now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d')),
                        ('weekly','weekly.sample.json','%d-W%02d'%now.isocalendar()[:2])):
    os.makedirs(sub,exist_ok=True)
    if not any(f.endswith('.json') for f in os.listdir(sub)):
        j=json.load(open(sample,encoding='utf-8')); j['date' if sub=='daily' else 'week']=name
        if sub=='weekly': j['people']={hs[0].lower():{'bullets':['演示要点（虚构）']}}
        json.dump(j,open(f'{sub}/{name}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
