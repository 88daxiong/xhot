#!/usr/bin/env python3
"""读取 raw/ 中每个 label 的最新快照 + xhot.db，生成自包含的 index.html（浅色编辑风，支持深色模式）。"""
import json, glob, os, sqlite3, html, datetime, hashlib
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
W=json.load(open('watchlist.json',encoding='utf-8'))
DOMS=[k for k in W if not k.startswith('_')]
SHORT={'ai':'AI','money':'搞钱','growth':'个人成长'}
TZ=datetime.timezone(datetime.timedelta(hours=8)); NOW=datetime.datetime.now(TZ)
e=html.escape
def latest(label):
    fs=sorted(glob.glob(f'raw/*_{label}.json')); return json.load(open(fs[-1],encoding='utf-8')) if fs else None
def latest_prefix(p):
    out={}
    for f in sorted(glob.glob(f'raw/*_{p}*.json')):
        out[os.path.basename(f).split('_',2)[2][:-5]]=json.load(open(f,encoding='utf-8'))
    return out
def fmt(n):
    if n is None: return '-'
    if n>=1e8: return f'{n/1e8:.2f}亿'
    if n>=1e4: return f'{n/1e4:.1f}万'
    return f'{n:,}'
def dt(s):
    try: return datetime.datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(TZ)
    except Exception: return None
def rel(s):
    d=dt(s)
    if not d: return ''
    m=int((NOW-d).total_seconds()//60)
    return '刚刚' if m<1 else f'{m} 分钟前' if m<60 else f'{m//60} 小时前' if m<1440 else f'{m//1440} 天前'
def avatar(user,name):
    h=int(hashlib.md5(user.encode()).hexdigest()[:6],16)%360
    ch=(name or user or '?').strip()[:1].upper()
    return f'<span class="av" style="--h:{h}">{e(ch)}</span>'
db=sqlite3.connect('xhot.db')
nsnap=db.execute('select count(distinct ts) from followers').fetchone()[0]
def series(u): return db.execute('select ts,followers,name from followers where username=? order by ts',(u.lower(),)).fetchall()
def eng(m): return m.get('like_count',0)+2*m.get('retweet_count',0)+3*m.get('quote_count',0)+m.get('reply_count',0)+m.get('bookmark_count',0)
def posts(dom,cfg):
    zh={a.lower() for a in cfg.get('accounts_zh',[])}; seen={}
    for lab in [f'watch_{dom}',f'watch_{dom}_zh']+[f'watch_{dom}_g{i}' for i in range(1,10)]+[f'search_{dom}_en',f'search_{dom}_zh']:
        j=latest(lab)
        if not j: continue
        users={u['id']:u for u in j.get('includes',{}).get('users',[])}
        for p in j.get('data',[]):
            u=users.get(p.get('author_id'),{}); m=p.get('public_metrics',{}); un=u.get('username','?')
            full=html.unescape((p.get('note_tweet') or {}).get('text') or p['text'])
            seen[p['id']]=dict(text=full,user=un,name=u.get('name',''),t=p.get('created_at',''),m=m,score=eng(m),
              url=f"https://x.com/{un}/status/{p['id']}",zh=un.lower() in zh or lab.endswith('_zh'),watch=lab.startswith('watch'))
    out=[];per={}
    for p in sorted(seen.values(),key=lambda x:-x['score']):
        if per.get(p['user'],0)>=2: continue
        per[p['user']]=per.get(p['user'],0)+1; out.append(p)
        if len(out)>=18: break
    return out
def spark(vals,w=132,h=36):
    mx=max(vals) or 1; mn=min(vals); rng=(mx-mn) or 1; n=len(vals)
    pts=[(i*w/(n-1), h-3-(v-mn)/rng*(h-6)) for i,v in enumerate(vals)]
    line=' '.join(f'{x:.1f},{y:.1f}' for x,y in pts)
    area=f'0,{h} '+line+f' {w},{h}'
    lx,ly=pts[-1]
    return f'<svg viewBox="0 0 {w} {h}" class="spark" preserveAspectRatio="none"><polygon points="{area}" class="sa"/><polyline points="{line}" class="sl"/><circle cx="{lx:.1f}" cy="{ly:.1f}" r="2.6" class="sd"/></svg>'
def trends(dom):
    out=[]
    for lab,j in latest_prefix(f'counts_{dom}__').items():
        d=j.get('data',[]); full=[x['tweet_count'] for x in d[1:-1]] if len(d)>3 else [x['tweet_count'] for x in d]
        if len(full)<2: continue
        last=full[-1]; prev=sum(full[:-1])/len(full[:-1]); g=(last/prev-1)*100 if prev else 0
        out.append(dict(name=lab.split('__',1)[1],last=last,g=g,total=j.get('meta',{}).get('total_tweet_count'),vals=full))
    return sorted(out,key=lambda x:-x['g'])
aih=(latest('aihot') or {}).get('items',[])[:10]
def news_items(dom):
    items=[dict(title=n.get('name',''),sum=(n.get('hook') or n.get('summary') or ''),url=n.get('url',''),meta='X 热点 · '+rel(n.get('updated_at',''))) for n in ((latest(f'news_{dom}') or {}).get('data',[])[:6])]
    if dom=='ai':
        items=[dict(title=it.get('title',''),sum=it.get('summary') or '',url=(it.get('links') or {}).get('aihot') or 'https://aihot.news',meta='AIHOT · '+((it.get('source') or {}).get('name','')).split('（')[0]) for it in aih[:6]]+items
    return items

def data(dom):
    cfg=W[dom]; accs=[]
    for a in dict.fromkeys(cfg['accounts']+cfg.get('accounts_zh',[])):
        s=series(a)
        if s: accs.append(dict(u=a,f=s[-1][1],d=(s[-1][1]-s[-2][1]) if len(s)>1 else None,name=s[-1][2],zh=a in cfg.get('accounts_zh',[])))
    accs.sort(key=lambda x:-x['f'])
    groups=None
    if cfg.get('groups'):
        by={a['u']:a for a in accs}; groups=[(g,[by[u] for u in sorted(us,key=lambda u:-by[u]['f']) if u in by]) for g,us in cfg['groups'].items()]
    return dict(trends=trends(dom),posts=posts(dom,cfg),accs=accs,news=news_items(dom),groups=groups,ex=excerpts(dom))
AH_HOT=(latest('aihot_hot') or {}).get('items',[])[:10]
AH_SEL=sorted((latest('aihot') or {}).get('items',[]),key=lambda x:-(x.get('score') or 0))
AH_DAILY=(latest('aihot_daily') or {}).get('report')
AH_TOPICS=(latest('aihot_topics') or {}).get('items',[])
AH_MODELS=(latest('aihot_models') or {}).get('items',[])[:10]
AH_POOL=(latest('aihot_pool') or {}).get('items',[])
KW={'money':['营收','收入','变现','融资','估值','创业','独立开发','出海','定价','订阅','商业化','付费','赚钱','创作者','SaaS','ARR','一人公司','副业','startup','revenue'],
    'growth':['学习','习惯','效率','思考方式','认知','职业','成长','写作','阅读','心理','工作方式','焦虑','人生','生产力','productivity','注意力']}
def ahlink(it): return (it.get('links') or {}).get('aihot') or 'https://aihot.news'
def excerpts(dom):
    if dom=='ai': return [x for x in AH_SEL if x['id'] not in {h['id'] for h in AH_HOT}][:9]
    kws=KW.get(dom,[]); seen=set(); out=[]
    for it in sorted(AH_POOL,key=lambda x:(-(1 if x.get('selected') else 0),-(x.get('score') or 0))):
        t=(it.get('title') or '')+(it.get('summary') or '')
        if it['id'] in seen or not any(k.lower() in t.lower() for k in kws): continue
        seen.add(it['id']); out.append(it)
        if len(out)>=9: break
    return out
DATA={d:data(d) for d in DOMS}
def short(t,n): return t if len(t)<=n else t[:n].rstrip()+'…'
def turl(t): return 'https://x.com/search?q='+e(t['name'].replace('·',' OR '))+'&f=live'
def sparkpath(vals,w,h):
    mx=max(vals);mn=min(vals);r=(mx-mn) or 1;n=len(vals)
    return ' '.join(f'{i*w/(n-1):.1f},{h-2-(v-mn)/r*(h-4):.1f}' for i,v in enumerate(vals))
def hue(u): return int(hashlib.md5(u.encode()).hexdigest()[:6],16)%360
