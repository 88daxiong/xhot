#!/usr/bin/env python3
"""v15 公开数据导出：python3 export_data.py [data]
与 v14 的区别：**不导出任何推文全文**。tweets/<handle>.json 只含 id / created_at / lang / 指标 / url；
daily/*.json 去掉 text_orig、text_orig_zh（只保留 excerpt、excerpt_zh、text_zh、gists、summary_zh 等 agent 撰写的字段）；weekly/*.json 原样复制。
不导出 raw/、xhot.db 或任何密钥。导出后自检：任何 JSON 里出现 text / text_orig* 键或超过 400 字的字符串即报错退出（防止全文泄漏）。"""
import os,sys,json,sqlite3,glob,shutil
D=os.path.dirname(os.path.abspath(__file__))
OUT=sys.argv[1] if len(sys.argv)>1 else 'data'
db=sqlite3.connect(os.path.join(D,'xhot.db')); W=json.load(open(os.path.join(D,'watchlist.json'),encoding='utf-8'))
STRIP={'text_orig','text_orig_zh','text'}
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
        for x in db.execute('select id,created_at,lang,likes,rts,replies,quotes,views,bm,url from tweets where author_id=? order by created_at desc',(uid,)):
            tw.append({'id':x[0],'created_at':x[1],'lang':x[2],'metrics':{'like':x[3],'retweet':x[4],'reply':x[5],'quote':x[6],'impression':x[7],'bookmark':x[8]},'url':x[9]})
    a['tweets_stored']=len(tw); n+=len(tw)
    dump(os.path.join(OUT,'tweets',f'{k}.json'),{'handle':k,'user_id':uid,'tweets':tw})
dump(os.path.join(OUT,'accounts.json'),{'accounts':[acc[k] for k in sorted(acc)]})
dump(os.path.join(OUT,'followers_history.json'),{'history':{k:hist[k] for k in sorted(hist)}})
def scrub(o):
    if isinstance(o,dict): return {k:scrub(v) for k,v in o.items() if k not in STRIP}
    if isinstance(o,list): return [scrub(x) for x in o]
    return o
for sub in ('daily','weekly'):
    src=glob.glob(os.path.join(D,sub,'*.json')); keep={os.path.basename(f) for f in src}
    for fp in src: dump(os.path.join(OUT,sub,os.path.basename(fp)),scrub(json.load(open(fp,encoding='utf-8'))))
    for old in glob.glob(os.path.join(OUT,sub,'*.json')):
        if os.path.basename(old) not in keep: os.remove(old)
open(os.path.join(OUT,'README.md'),'w',encoding='utf-8').write('''# XHOT 数据备份（v15：仅 ID 与指标）

由 `export_data.py` 导出，每天刷新时更新。JSON 键排序固定、缩进 2。**本目录不含任何推文全文**；推文内容请点链接回 X 查看。

- `accounts.json`：关注列表里的每个账号（handle、user_id、名字、领域/分组、是否中文号、最新粉丝数）。
- `followers_history.json`：每个账号的粉丝时间序列（北京时间 `YYYYMMDD_HHMMSS`）。
- `tweets/<handle>.json`：该账号本地存储的原创推文的 **id、created_at、lang、指标（点赞/转推/回复/引用/曝光/收藏）、url**，不含正文。
- `daily/YYYY-MM-DD.json`：每日要点（三句话、必读重点的中文概括与短摘录、一句话要点、话题/粉丝变化、更新日志）。
- `weekly/YYYY-Www.json`：每周 Top 人物的「本周要点」。

数据来源：X API。只做备份和展示，版权归原作者。
''')
# 自检：不得出现全文
bad=[]
for f in glob.glob(os.path.join(OUT,'**','*.json'),recursive=True):
    def walk(o,p=''):
        if isinstance(o,dict):
            for k,v in o.items():
                if k in STRIP: bad.append(f'{f}: key {k}')
                walk(v,p+'/'+k)
        elif isinstance(o,list):
            for x in o: walk(x,p)
        elif isinstance(o,str) and len(o)>400: bad.append(f'{f}: long string at {p} ({len(o)})')
    walk(json.load(open(f,encoding='utf-8')))
if bad: print('FAIL 全文泄漏检查：'); print('\n'.join(bad[:10])); sys.exit(1)
print('accounts',len(acc),'tweets(ids+metrics only)',n,'| 全文泄漏检查 OK')
