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
now=datetime.datetime.now(datetime.timezone.utc)
TOPIC=['Claude Code 和 vibe coding 的新工作流。','开源权重模型发布，open source weights。','创业公司完成融资，startup raised a round。',
       '写作习惯与 deep work 的方法。','新的 AI agents 框架上线 launch。','论文与研究 research paper 解读。','独立开发者的 MRR 增长复盘。','职业发展与 career 建议。']
TOPIC_EN=['Demo: shipping a new open source agent framework today, with Claude Code integration and MCP tools.','Demo: how we grew an indie product to 10k MRR without a team, a short thread.']; users=[]; tid=1900000000000000000
for i,h in enumerate(hs):
    uid=str(1000+i); f=random.randint(2000,3000000)
    users.append({'id':uid,'username':h,'name':h[:1].upper()+h[1:],'description':'演示账号（虚构数据）','public_metrics':{'followers_count':f,'following_count':100,'tweet_count':1000,'listed_count':0}})
    for k,ts in enumerate([now-datetime.timedelta(days=3),now-datetime.timedelta(hours=2)]):
        db.execute('insert or replace into followers values(?,?,?,?,?,?,?)',(ts.strftime('%Y%m%d_%H%M%S'),h.lower(),uid,h[:1].upper()+h[1:],f-k*random.randint(0,500),100,1000))
    for n in range(3 if i%10==9 else 30):   # 每 10 个账号有 1 个稀疏账号（测试稀疏个人页）
        tid+=random.randint(1000,99999); t=now-datetime.timedelta(hours=random.randint(1,24*28))
        lk=random.randint(5,20000)
        db.execute('insert or replace into tweets values(?,?,?,?,?,?,?,?,?,?,?,?,?)',(str(tid),uid,t.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            (TOPIC_EN[n%2] if n%3==0 else f'这是 {h} 的第 {n+1} 条演示帖子（虚构）：{TOPIC[n%len(TOPIC)]}'),lk,lk//10,lk//20,lk//50,lk*30,lk//15,
            f'https://x.com/{h}/status/{tid}','en' if n%3==0 else 'zh',now.isoformat()))
db.commit()
ts=now.strftime('%Y%m%d_%H%M%S')
json.dump({'data':users,'_label':'users_demo'},open(f'raw/{ts}_users_demo.json','w',encoding='utf-8'),ensure_ascii=False)
for d in DOMS:
    for name in (W[d].get('trend_queries') or {}):
        days=[{'start':(now-datetime.timedelta(days=6-i)).strftime('%Y-%m-%dT00:00:00.000Z'),'end':(now-datetime.timedelta(days=5-i)).strftime('%Y-%m-%dT00:00:00.000Z'),'tweet_count':random.randint(500,30000)} for i in range(7)]
        json.dump({'data':days,'_label':f'counts_{d}__{name}'},open(f'raw/{ts}_counts_{d}__{name.replace("/","_")}.json','w',encoding='utf-8'),ensure_ascii=False)
print('demo: 账号',len(hs),'帖子',db.execute('select count(*) from tweets').fetchone()[0])
# 演示日报：最近 24 小时点赞最高的 6 条为必读，前 40 条写一句话要点（真实站点由编辑撰写）
os.makedirs('daily',exist_ok=True)
_day=now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d')
_un={u['id']:u for u in users}
_top=db.execute("select id,author_id,likes,text from tweets where created_at>=? order by likes desc limit 40",((now-datetime.timedelta(hours=24)).strftime('%Y-%m-%dT%H:%M:%S'),)).fetchall()
if not os.listdir('daily') and _top:
    hl=[{'handle':_un[a]['username'],'name':_un[a]['name'],'post_id':i,'url':f'https://x.com/{_un[a]["username"]}/status/{i}','likes':lk,
         'text_zh':'演示要点：'+t[:30],'excerpt':t[:200],'tags':[],**({'excerpt_zh':'（演示译文）发布一个新的开源智能体框架。'} if t.startswith('Demo:') else {})} for i,a,lk,t in sorted(_top[:4]+[x for x in _top[4:] if x[3].startswith('Demo:')][:2],key=lambda x:-x[2])]   # 至少 2 条英文必读（测试中文译文 / EN 切换）
    json.dump({'date':_day,'summary_zh':['演示第一句：今天的重点（虚构）。','演示第二句。','演示第三句。'],'highlights':hl,
               'gists':{i:'一句话要点：'+t[:24] for i,a,lk,t in _top},'pin':[],'hide':[],'topics_zh':'','followers_zh':'','changelog':[]},
              open(f'daily/{_day}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
# 日报 / 周要点示例（仅当目录里还没有任何文件时写入；test_escape.py / fuzz.py 需要至少各一份）
for sub,sample,name in (('daily','daily.sample.json',now.astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d')),
                        ('weekly','weekly.sample.json','%d-W%02d'%now.isocalendar()[:2])):
    os.makedirs(sub,exist_ok=True)
    if not any(f.endswith('.json') for f in os.listdir(sub)):
        j=json.load(open(sample,encoding='utf-8')); j['date' if sub=='daily' else 'week']=name
        if sub=='weekly': j['people']={hs[0].lower():{'bullets':['演示要点（虚构）']}}
        json.dump(j,open(f'{sub}/{name}.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
# 资讯 / GitHub / Agent 页的演示数据（虚构，链接指向 example.com 或不存在的 demo 仓库），让所有页面和浏览器测试都有内容
iso=lambda h:(now-datetime.timedelta(hours=h)).strftime('%Y-%m-%dT%H:%M:%SZ')
ah=[{'id':f'demo{i}','title':f'演示资讯 {i+1}：开源智能体框架发布新版本','summary':f'这是第 {i+1} 条演示资讯的中文摘要，用来验证资讯页列表、阅读窗格与正文分片。\n第二段占位文字。',
     'reason':'演示推荐理由','publishedAt':iso(i*3+1),'score':100-i,'source':{'name':'Demo News'},
     'links':{'aihot':f'https://example.com/aihot/{i}','original':f'https://example.com/news/{i}'}} for i in range(24)]
json.dump({'items':ah,'_label':'aihot'},open(f'raw/{ts}_aihot.json','w',encoding='utf-8'),ensure_ascii=False)
TAGS=['agent','coding','mcp','infra','ops','fun']
repos=[{'repo':f'demo-org/demo-tool-{i}','desc':f'Demo AI developer tool number {i+1} for agents and coding workflows.','lang':['Python','TypeScript','Rust','Go'][i%4],
        'stars':5000-i*120,'today':900-i*25,'week':4000-i*90,'created':(now-datetime.timedelta(days=3+i)).strftime('%Y-%m-%d'),
        'topics':['ai','agents'],'tags':[TAGS[i%6]]} for i in range(30)]
json.dump({'repos':repos,'_label':'devtools','_fetched_at':now.isoformat()},open(f'raw/{ts}_devtools.json','w',encoding='utf-8'),ensure_ascii=False)
gh=[dict(r,url='https://github.com/'+r['repo'],ai=True) for r in repos[:20]]
json.dump({'repos':gh,'_label':'gh_trending','_fetched_at':now.isoformat()},open(f'raw/{ts}_gh_trending.json','w',encoding='utf-8'),ensure_ascii=False)
print('demo: 资讯',len(ah),'GitHub 仓库',len(repos))
