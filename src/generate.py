#!/usr/bin/env python3
"""XHOT 静态站生成器（资讯合并为单一列表 · 趋势页重做 · webp 头像 · 数据新鲜度）：顶部 4 个 tab = 4 个独立页面（深链接）
  index.html 热帖 · accounts.html 账号榜 · news.html 资讯（X 新闻 + AIHOT）· trends.html 趋势（话题涨跌 + GitHub）
  p/<handle>.html 个人页；assets/ 下哈希资源：app.<h>.js、hot.<h>.json、av/<handle>.<h>.jpg
数据：xhot.db、raw/、avatars/（由 avatars_fetch.py 下载）。用法：python3 generate_v8.py [输出目录]"""
import os,sys,glob,json,re,datetime,hashlib,shutil,html as _h
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D); os.chdir(D)
from xhot_data import *
import langf
OUT=sys.argv[1] if len(sys.argv)>1 else os.path.join(D,'site')
SANS='-apple-system,BlinkMacSystemFont,system-ui,"SF Pro Text","PingFang SC","Hiragino Sans GB","Noto Sans CJK SC","Microsoft YaHei",sans-serif'
DC={'ai':'var(--ai)','money':'var(--money)','growth':'var(--growth)'}
DN={'ai':'AI','money':'搞钱','growth':'成长'}
def H8(b): return hashlib.sha1(b if isinstance(b,bytes) else b.encode()).hexdigest()[:10]
CSS=open('style.css',encoding='utf-8').read().replace('$SANS',SANS)
CSS=re.sub(r'/\*.*?\*/','',CSS,flags=re.S); CSS=re.sub(r'\s*\n\s*','',CSS)
J0=open('theme_init.js',encoding='utf-8').read().split('/*@@BODY@@*/')[0].strip()
APP=open('app.js',encoding='utf-8').read()
AD=os.path.join(OUT,'assets'); AVD=os.path.join(AD,'av'); os.makedirs(AVD,exist_ok=True)
keep=set()
def put(name,data,sub=AD):
    p=os.path.join(sub,name); keep.add(os.path.abspath(p))
    if not os.path.exists(p): open(p,'wb').write(data if isinstance(data,bytes) else data.encode('utf-8'))
JSN=f'app.{H8(APP)}.js'; put(JSN,APP)
GH0=json.load(open(sorted(glob.glob('raw/*_gh_trending.json'))[-1])) if glob.glob('raw/*_gh_trending.json') else {'repos':[]}
# ---- 头像 ----
AVF={}
from PIL import Image; import io
os.makedirs('avatars_webp',exist_ok=True)
for f in glob.glob('avatars/*.jpg'):
    h=os.path.basename(f)[:-4]; w=os.path.join('avatars_webp',h+'.webp')
    if not os.path.exists(w) or os.path.getmtime(w)<os.path.getmtime(f):
        try: im=Image.open(f); im.verify(); im=Image.open(f).convert('RGB'); im.thumbnail((96,96)); im.save(w,'WEBP',quality=78,method=6)
        except Exception as ex: print('skip avatar',h,type(ex).__name__); continue
    b=open(w,'rb').read(); n=f'{h}.{H8(b)[:8]}.webp'; put(n,b,AVD); AVF[h]=n
import base64
CSP=("default-src 'self'; script-src 'self' 'sha256-"+base64.b64encode(hashlib.sha256(J0.encode('utf-8')).digest()).decode()+"'; "
     "style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'")
HEADSEC=f'<meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin">'
def _avsrc(u,pref,eager):
    if eager=='inline': return 'data:image/webp;base64,'+base64.b64encode(open(os.path.join(AVD,AVF[u]),'rb').read()).decode()
    return f'{pref}assets/av/{AVF[u]}'
def av(u,n,cls='',pref='',eager=False):
    if eager and u in AVF: return f'<span class="av {cls}" style="--h:{hue(u)}" aria-hidden="true">{e((n or u)[:1].upper())}<img src="{_avsrc(u,pref,eager)}" alt="" width="96" height="96" fetchpriority="high"></span>'
    img=f'<img data-src="{pref}assets/av/{AVF[u]}" alt="" width="96" height="96" decoding="async">' if u in AVF else ''
    return f'<span class="av {cls}" style="--h:{hue(u)}" aria-hidden="true">{e((n or u)[:1].upper())}{img}</span>'
# ---- 账号 ----
PROF={}
for f in sorted(glob.glob('raw/*_users_*.json')):
    try:
        for u in json.load(open(f,encoding='utf-8')).get('data',[]): PROF[u['username'].lower()]=u
    except Exception: pass
ID2U={i:u for u,i in db.execute('select username,user_id from followers')}
U2ID={u:i for i,u in ID2U.items()}
def handle_case(u): return (PROF.get(u) or {}).get('username') or u
ACC={}  # u -> dict
for d in DOMS:
    cfg=W[d]; grp=[]
    if cfg.get('groups'): grp=[(g,us) for g,us in cfg['groups'].items()]
    else: grp=[('英文账号',cfg.get('accounts',[])),('中文账号',cfg.get('accounts_zh',[]))]
    for g,us in grp:
        for x in us:
            u=x.lower()
            if u in ACC: ACC[u]['doms'].append(d); continue
            s=series(u); name=s[-1][2] if s else (PROF.get(u,{}).get('name') or u)
            ACC[u]=dict(u=u,name=name,H=handle_case(u),f=s[-1][1] if s else 0,d=(s[-1][1]-s[-2][1]) if len(s)>1 else None,dom=d,doms=[d],g=g)
NT=db.execute('select count(*) from tweets').fetchone()[0]
def heat(r): return r[4]+2*r[5]+3*r[7]+r[6]+(r[9] or 0)
WEEK=(NOW-datetime.timedelta(days=7)).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
def jdt(s): return dt(s).astimezone(TZ).strftime('%m-%d %H:%M')
def fullt(s): return dt(s).astimezone(TZ).strftime('%Y-%m-%d %H:%M')
def safe_url(u):
    """只保留 http(s) 链接，其它（javascript:/data: 等）一律替换成 '#'；结果已转义"""
    u=str(u or '').strip()
    return e(u) if re.match(r'(?i)https?://',u) else '#'
def lnk(t): return re.sub(r'https?://[^\s<&"\']+',lambda m:f'<a href="{m.group(0)}" target="_blank" rel="noopener noreferrer">{re.sub("^https?://","",m.group(0))}</a>',e(t))
def isw(t): return t>=WEEK
def card(r,a,pref='',showwho=True):
    """r=[id,t,text,like,rt,reply,quote,view,heat,url]  与 app.js card() 一致"""
    t=r[2]; lg=len(t)>150 or t.count('\n')>4
    who=(f'<header>{av(a["u"],a["name"],"",pref)}<div class="who"><a href="{pref}p/{a["u"]}.html">{e(a["name"])}</a><small>@{e(a["H"])}</small></div><div class="pm"><span class="heat" title="热度 = 赞 + 2×转 + 3×引用 + 评论 + 收藏">🔥 {fmt(r[8])}</span><time datetime="{r[1]}" title="{fullt(r[1])}">{jdt(r[1])}</time></div></header>' if showwho
         else f'<header><span class="tag">{"近一周" if isw(r[1]) else "更早"}</span><div class="who"></div><div class="pm"><span class="heat" title="热度 = 赞 + 2×转 + 3×引用 + 评论 + 收藏">🔥 {fmt(r[8])}</span><time datetime="{r[1]}" title="{fullt(r[1])}">{jdt(r[1])}</time></div></header>')
    return (f'<article class="post" style="--dc:{DC[a["dom"]]}" data-k="{r[0]}">{who}<div class="pt ptc">{lnk(t)}</div><footer><div class="act">'
      f'<button class="btn ex" type="button" aria-expanded="false"{"" if lg else " hidden"}>展开</button><button class="btn cp" type="button">复制原文</button><a class="btn op" href="{safe_url(r[9] or f'https://x.com/{a["H"]}/status/{r[0]}')}" target="_blank" rel="noopener noreferrer">在 X 打开 ↗</a></div>'
      f'<div class="met"><span title="点赞"><i aria-hidden="true">♥</i>{fmt(r[3])}</span><span title="转发"><i aria-hidden="true">⇄</i>{fmt(r[4])}</span><span title="评论"><i aria-hidden="true">💬</i>{fmt(r[5])}</span><span title="浏览"><i aria-hidden="true">👁</i>{fmt(r[7])}</span></div></footer></article>')
def jdump(o): return json.dumps(o,ensure_ascii=False,separators=(',',':'))  # 独立 .json 文件用（不嵌入 HTML）
def jsafe(o):
    """嵌入 <script type=application/json> 的 JSON：转义 < > & 与 U+2028/2029，防止 </script>、<!-- 等打断解析"""
    return (json.dumps(o,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e')
            .replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029'))
THEME='<div class="tg" role="group" aria-label="主题"><button type="button" data-set-theme="light" aria-label="浅色">☀</button><button type="button" data-set-theme="dark" aria-label="深色">☾</button><button type="button" data-set-theme="auto">自动</button></div>'
TABS=[('index.html','🔥 热帖'),('accounts.html','👤 账号榜'),('news.html','📰 资讯'),('trends.html','📈 趋势')]
def _fa(lab):
    fs=sorted(glob.glob(f'raw/*_{lab}.json'))
    if not fs: return None
    j=json.load(open(fs[-1],encoding='utf-8')); t=j.get('_fetched_at') if isinstance(j,dict) else None
    if t: return datetime.datetime.fromisoformat(t).astimezone(TZ)
    return datetime.datetime.strptime('_'.join(os.path.basename(fs[-1]).split('_')[:2]),'%Y%m%d_%H%M%S').replace(tzinfo=TZ)
def _ts(t): return t.strftime('%m-%d %H:%M') if t else '—'
_tw=db.execute('select max(fetched_at) from tweets').fetchone()[0]; _fo=db.execute('select max(ts) from followers').fetchone()[0]
FRESH=dict(tweets=datetime.datetime.fromisoformat(_tw).astimezone(TZ) if _tw else None,
  followers=datetime.datetime.strptime(_fo,'%Y%m%d_%H%M%S').replace(tzinfo=TZ) if _fo else None,
  news=_fa('news_ai'),aihot=_fa('aihot'),gh=datetime.datetime.fromisoformat(GH0['_fetched_at']).astimezone(TZ) if GH0.get('_fetched_at') else None,
  counts=max([x for x in [_fa(k) for k in [f.split('_',2)[2][:-5] for f in glob.glob('raw/*_counts_*.json')]] if x] or [None]) if glob.glob('raw/*_counts_*.json') else None)
FRL={'tweets':'推文','followers':'粉丝','news':'X 新闻','aihot':'AIHOT','gh':'GitHub','counts':'话题计数'}
PAGEF={'index.html':['tweets'],'accounts.html':['followers'],'news.html':['aihot','news'],'trends.html':['counts','gh'],'':['tweets','followers']}
def _cnt(lab,key='data'):
    j=latest(lab) or {}; v=j.get(key) if isinstance(j,dict) else None
    return len(v) if isinstance(v,(list,dict)) else 0
NACC=None
def health():
    rows=[('tweets','推文时间线',f'{NT:,} 条 · 每账号 ≤200',26),('followers','账号资料/粉丝',f'{len(ACC)} 账号 · {db.execute("select count(distinct ts) from followers").fetchone()[0]} 次快照',26),
          ('counts','话题计数',f'{len(glob.glob("raw/*_counts_*.json"))} 个文件',26),('news','X 新闻',f'{sum(_cnt("news_"+d) for d in DOMS)} 条 · 相关帖 {len(NP)}',26),
          ('aihot','AIHOT',f'精选 {_cnt("aihot","items")} · 热点 {_cnt("aihot_hot","items")}',26),('gh','GitHub Trending',f'{len(GHR)} 个 AI/开发仓库',26)]
    out='';bad=0
    for k,lab,c,lim in rows:
        t=FRESH.get(k); age=(NOW-t).total_seconds()/3600 if t else 999
        stt='ok' if age<=lim else ('warn' if age<=48 else 'bad'); bad+=stt!='ok'
        out+=f'<tr class="{stt}"><td><i></i>{lab}</td><td>{_ts(t)}</td><td>{"—" if age>=999 else (f"{age:.1f} 小时前" if age>=1 else f"{age*60:.0f} 分钟前")}</td><td>{c}</td></tr>'
    return bad,f'<table class="hs"><thead><tr><th>数据源</th><th>最近抓取</th><th>距今</th><th>规模</th></tr></thead><tbody>{out}</tbody></table><p class="hsn">刷新计划：每天 1 次（北京时间 07:58）。超过 26 小时标黄、超过 48 小时标红。生成于 {NOW.strftime("%m-%d %H:%M")}。</p>'
def fresh(cur):
    ks=PAGEF.get(cur,['tweets']); bad,tbl=health()
    ts=[FRESH[k] for k in ks if FRESH.get(k)]; old=min(ts) if ts else None; age=(NOW-old).total_seconds()/3600 if old else 99
    cls='bad' if age>48 else 'warn' if age>26 else 'ok'
    lab=f'数据 {_ts(old)}' if old else '数据 —'
    return f'<details class="fr {cls}"><summary title="点击查看各数据源状态"><i></i>{lab}{f"<b>{bad} 项待更新</b>" if bad else ""}</summary><div class="frp"><h3>数据健康</h3>{tbl}</div></details>'
def page(title,body,cur,pref='',head=''):
    nav=''.join(f'<a href="{pref}{h}"{" aria-current=page" if h==cur else ""}>{t}</a>' for h,t in TABS)
    return (f'<!doctype html><html lang="zh-CN" data-theme="light" data-pref="auto"><head><meta charset="utf-8">{HEADSEC}<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#7c3aed"><title>{e(title)}</title><script>{J0}</script><style>{CSS}</style><script src="{pref}assets/{JSN}" defer></script>{head}</head><body>'
      f'<header class="top"><div class="bar"><a class="lg" href="{pref}index.html"><i>⚡</i>XHOT<span>X 热点雷达</span></a><nav class="nav" aria-label="栏目">{nav}</nav><span class="sp0"></span>{fresh(cur)}{THEME}</div></header>'
      f'<div class="wrap">{body}<footer class="ft">数据：X API · <a href="https://aihot.news" target="_blank" rel="noopener noreferrer">aihot.news</a> · <a href="https://github.com/trending" target="_blank" rel="noopener noreferrer">GitHub Trending</a> · 热度 = 赞 + 2×转 + 3×引用 + 评论 + 收藏 · 生成于 {NOW.strftime("%Y-%m-%d %H:%M")} 北京时间</footer></div></body></html>')
def domseg(withall=True):
    b=('<button type="button" data-dom="all" class="on" aria-pressed="true">全部</button>' if withall else '')
    return '<div class="seg" role="group" aria-label="领域">'+b+''.join(f'<button type="button" data-dom="{d}" style="--dc:{DC[d]}" aria-pressed="false"><i class="dot"></i>{DN[d]}</button>' for d in DOMS)+'</div>'
SORTSEG='<div class="seg" role="group" aria-label="排序"><button type="button" data-sort="w" class="on" aria-pressed="true">近一周热度</button><button type="button" data-sort="g" aria-pressed="false">全局热度</button><button type="button" data-sort="t" aria-pressed="false">时间</button></div>'
# ---- 热帖 ----
CAP=3; NL=150; PRE=36
def overview(P,us):
    """热帖页顶部 10 秒速览：最近一次抓取新增、24 小时最热、粉丝涨最多、话题涨最快、AIHOT 头条"""
    mx=db.execute('select max(fetched_at) from tweets').fetchone()[0]
    newn=0
    if mx:
        cut=(datetime.datetime.fromisoformat(mx)-datetime.timedelta(minutes=45)).isoformat()
        newn=db.execute('select count(*) from tweets where fetched_at>=?',(cut,)).fetchone()[0]
    d24=(NOW-datetime.timedelta(hours=24)).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    p24=[p for p in P if p[1]>=d24]; top=max(p24 or P,key=lambda p:p[8]) if P else None
    fg=max([a for a in ACC.values() if a['d']],key=lambda a:a['d'],default=None)
    TT=[(x,d) for d in DOMS for x in DATA[d]['trends']]; tp=max(TT,key=lambda z:z[0]['g'],default=None)
    hh=AH_HOT[0] if AH_HOT else None
    def k(lbl,val,sub,href='',ext=False,dc='var(--ac)'):
        tag='a' if href else 'div'; at=f' href="{safe_url(href) if ext else e(href)}"'+(' target="_blank" rel="noopener noreferrer"' if ext else '') if href else ''
        return f'<{tag} class="ov"{at} style="--dc:{dc}"><span class="kl">{lbl}</span><b class="kv">{val}</b><span class="ks">{sub}</span></{tag}>'
    p7=[p for p in P if isw(p[1])]
    cards=[k('24 小时新帖',f'{len(p24)} 条',f'近一周 {len(p7)} 条 · 来自 {len({p[10] for p in p24})} 个账号','index.html#sort=t')]
    if top:
        a=ACC[us[top[10]]]; cards.append(k('24 小时最热' if p24 else '最热',e(a['name']),f'🔥 {fmt(top[8])} · {e(short(re.sub(r"https?://\S+","",top[2]).replace(chr(10)," ").strip() or "（链接/媒体）",28))}',top[9],True,DC[a['dom']]))
    if fg: cards.append(k('粉丝涨最多',e(fg['name']),f'<b class="up">+{fg["d"]:,}</b> 较上次 · {fmt(fg["f"])} 粉丝',f'p/{fg["u"]}.html','',DC[fg['dom']]))
    if tp: cards.append(k('话题涨最快',e(tp[0]['name']),f'<b class="{"up" if tp[0]["g"]>=0 else "dn"}">{tp[0]["g"]:+.0f}%</b> · {DN[tp[1]]} · 昨日 {fmt(tp[0]["last"])} 条','trends.html','',DC[tp[1]]))
    if hh: cards.append(k('AIHOT 头条',e(short(hh['title'],22)),f'{hh.get("sourceCount",0)} 个信源报道','news.html#src=h','',"var(--g2)"))
    return '<div class="ovs" aria-label="速览">'+''.join(cards)+'</div>'
def hot():
    rows=[]
    for r in db.execute('select id,created_at,text,likes,rts,replies,quotes,views,bm,url,lang,author_id from tweets order by created_at desc'):
        u=ID2U.get(r[11])
        if u not in ACC or not langf.ok(r[2],r[10]): continue
        rows.append(([r[0],r[1],_h.unescape(r[2]),r[3],r[4],r[5],r[6],r[7],r[3]+2*r[4]+3*r[6]+r[5]+(r[8] or 0),r[9] or f'https://x.com/{ACC[u]["H"]}/status/{r[0]}'],u))
    us=list(dict.fromkeys(u for _,u in rows)); ui={u:i for i,u in enumerate(us)}
    P=[r+[ui[u]] for r,u in rows]
    def lst(dom,mode):
        idx=[i for i,p in enumerate(P) if dom=='all' or dom in ACC[us[p[10]]]['doms']]
        if mode=='w': idx=sorted([i for i in idx if isw(P[i][1])],key=lambda i:-P[i][8])
        elif mode=='g': idx=sorted(idx,key=lambda i:-P[i][8])
        out=[];c={}
        for i in idx:
            a=P[i][10]; c[a]=c.get(a,0)+1
            if c[a]>CAP: continue
            out.append(i)
            if len(out)>=NL: break
        return out
    L={d:{m:lst(d,m) for m in 'wgt'} for d in ['all']+DOMS}
    used=sorted({i for d in L.values() for l in d.values() for i in l}); remap={o:n for n,o in enumerate(used)}
    PP=[P[i] for i in used]; LL={d:{m:[remap[i] for i in l] for m,l in v.items()} for d,v in L.items()}
    UU=[[u,ACC[u]['name'],ACC[u]['H'],ACC[u]['dom'],AVF.get(u,''),hue(u)] for u in us]
    def slim(p): return p[:9]+['' if p[9]==f'https://x.com/{UU[p[10]][2]}/status/{p[0]}' else p[9]]+p[10:]  # url 可还原则省略
    data=jdump({'P':[slim(p) for p in PP],'U':UU,'L':LL}); hn=f'hot.{H8(data)}.json'; put(hn,data)
    first=''.join(card(PP[i][:10],ACC[us[PP[i][10]]]) for i in LL['all']['w'][:PRE])
    nw=len(LL['all']['w'])
    ov=overview(P,us)
    body=(f'{ov}<div class="tools"><h1>热帖</h1>{SORTSEG}{domseg()}<input type="search" id="hq" aria-label="搜索热帖" placeholder="搜索内容 / 账号…" autocomplete="off" spellcheck="false" style="flex:0 1 220px"><span class="sp"></span><span class="cnt" id="cnt" aria-live="polite">近一周 {nw} 条 · 每人最多 {CAP} 条</span></div>'
          f'<div id="feed" class="grid" data-src="assets/{hn}" data-pre="{PRE}">{first}</div><button id="more" class="more" type="button"{"" if nw>PRE else " hidden"}>再显示 36 条</button>')
    return page('XHOT · 热帖',body,'index.html',head='')
# ---- 账号榜 ----
def accounts():
    global _ec
    _ec=0
    sec=''
    for d in DOMS:
        gs=list(dict.fromkeys(a['g'] for a in ACC.values() if a['dom']==d))
        for g in gs:
            al=sorted([a for a in ACC.values() if a['dom']==d and a['g']==g],key=lambda a:-a['f'])
            sec+=f'<h2 class="gh2" data-dom="{d}" data-g="1"><i class="dot" style="--dc:{DC[d]}"></i>{DN[d]} · {e(g)} <span>{len(al)}</span></h2>'
            for a in al:
                dv='' if a['d'] is None else f'<span class="dv {"up" if a["d"]>0 else "dn" if a["d"]<0 else ""}">{"+" if a["d"]>0 else ""}{a["d"]:,} 较上次</span>'
                sec+=(f'<a class="acard" href="p/{a["u"]}.html" style="--dc:{DC[d]}" data-dom="{d}" data-f="{a["f"]}" data-d="{a["d"] or 0}" data-q="{e((a["name"]+" "+a["u"]).lower())}">{av(a["u"],a["name"],"l",eager=("inline" if (_ec:=_ec+1)<=24 else False))}'
                      f'<span class="an"><b>{e(a["name"])}</b><small>@{e(a["H"])}</small></span><span class="af"><span class="tag">{DN[d]}</span><span class="fv">{fmt(a["f"])} 粉丝</span>{dv}</span></a>')
    body=(f'<div class="tools"><h1>账号榜</h1>{domseg()}<div class="seg" role="group" aria-label="排序"><button type="button" data-asort="grp" class="on" aria-pressed="true">按分组</button><button type="button" data-asort="f" aria-pressed="false">粉丝数</button><button type="button" data-asort="d" aria-pressed="false">粉丝变化</button></div>'
          f'<input type="search" id="aq" aria-label="搜索账号" placeholder="搜索账号…" autocomplete="off" spellcheck="false"><span class="sp"></span><span class="cnt" id="acnt">{len(ACC)} 个账号 · 点卡片看主页</span><span class="hint" title="粉丝变化 = 最近一次抓取 vs 上一次抓取">变化 = 本次 vs 上次抓取</span></div><div id="ag" class="agrid">{sec}</div>')
    return page('XHOT · 账号榜',body,'accounts.html')
# ---- 资讯 ----
GH=GH0
GHR=sorted([r for r in GH['repos'] if r['ai'] and langf.script_ok(r['desc'])],key=lambda r:-r['today'])[:20]
def norm(t): return re.sub(r'[\W_]+','',t.lower())[:24]
def src(it): return ((it.get('source') or {}).get('name') or '').split('（')[0]
def paras(t): return ''.join(f'<p>{lnk(x.strip())}</p>' for x in re.split(r'\n\s*\n|\n',t or '') if x.strip())
def ago(s): return rel(s) if s else ''
def tt(s): return f'{jdt(s)}（{rel(s)}）' if s and dt(s) else ''
NP={}
for d in DOMS:
    j=latest(f'news_posts_{d}') or {}
    us={u['id']:u for u in (j.get('includes') or {}).get('users',[])}
    for p in j.get('data',[]):
        u=us.get(p.get('author_id'),{}); t=_h.unescape((p.get('note_tweet') or {}).get('text') or p.get('text',''))
        if langf.ok(t,p.get('lang')): NP[p['id']]=dict(t=t,u=u.get('username','?'),n=u.get('name',''),m=p.get('public_metrics',{}),url=f"https://x.com/{u.get('username','i')}/status/{p['id']}")
STORIES=(latest('aihot_stories') or {}).get('items',{})
def kp(ids):
    out=''
    for i in list(dict.fromkeys(ids))[:3]:
        p=NP.get(i)
        if not p: continue
        out+=f'<blockquote class="kp"><a class="kh" href="{safe_url(p["url"])}" target="_blank" rel="noopener noreferrer"><b>{e(p["n"])}</b> @{e(p["u"])} · ♥ {fmt(p["m"].get("like_count",0))}</a>{paras(p["t"])}</blockquote>'
    return f'<div class="kps"><h4>相关帖子</h4>{out}</div>' if out else ''
def news_items():
    items=[]
    for it in AH_HOT:
        stv=STORIES.get(it['id']) or {}
        rp=''.join(f'<li><a href="{safe_url((r.get("links") or {}).get("original") or (r.get("links") or {}).get("aihot",""))}" target="_blank" rel="noopener noreferrer">{e(r["title"])}</a> <small>{e(src(r))}</small></li>' for r in (stv.get('reports') or [])[:5])
        body=paras(stv.get('digest',''))+(f'<div class="kps"><h4>各方报道（{stv.get("sourceCount",it.get("sourceCount",""))} 个信源）</h4><ul class="rps">{rp}</ul></div>' if rp else '')
        if not body: continue
        L=it.get('links') or {}
        items.append(dict(t=it['title'],s='h',sl='AIHOT 热点',m=f'{it.get("sourceCount",0)} 个信源 · {tt(it.get("latestAt",""))}',body=body,links=[('AIHOT 综述',(stv.get('links') or {}).get('aihot') or L.get('aihot','')),('原文',L.get('original',''))],chk=it['title']))
    if AH_DAILY:
        for sec in AH_DAILY.get('sections',[]):
            for it in sec['items']:
                L=it.get('links') or {}
                items.append(dict(t=it['title'],s='d',sl='AIHOT 日报',m=(src(it) or sec['label'])+' · 日报 '+AH_DAILY.get('date',''),body=paras(it.get('summary','')),links=[('AIHOT',L.get('aihot') or AH_DAILY['links']['aihot']),('原文',L.get('original',''))],chk=it['title']))
    pool=AH_SEL[:20]+[x for d in DOMS if d!='ai' for x in DATA[d]['ex']]
    for it in pool:
        L=it.get('links') or {}
        body=paras(it.get('summary',''))+(f'<p class="why"><b>推荐理由</b>{e(it["reason"])}</p>' if it.get('reason') else '')
        items.append(dict(t=it['title'],s='s',sl='AIHOT 精选',m=src(it)+(' · '+tt(it.get('publishedAt',''))) if it.get('publishedAt') else src(it),body=body,links=[('AIHOT 全文译文',L.get('aihot','')),('原文',L.get('original',''))],chk=it['title']))
    xs=[]
    for d in DOMS:
        for n in (latest(f'news_{d}') or {}).get('data',[])[:15]:
            body=(f'<p class="hook">{e(n["hook"])}</p>' if n.get('hook') else '')+paras(n.get('summary',''))+kp([x['post_id'] for x in n.get('cluster_posts_results',[])])
            xs.append(dict(t=n.get('name',''),s='x',sl='X 新闻',m='更新 '+tt(n.get('updated_at','')),u=n.get('updated_at',''),body=body,links=[('在 X 查看',n.get('url',''))],chk=n.get('name','')+n.get('summary','')))
    items+=sorted(xs,key=lambda x:x['u'],reverse=True)  # X 新闻（英文）在后，按更新时间新→旧
    seen=set(); out=[]
    for it in items:
        k=norm(it['t'])
        if not langf.script_ok(it['chk']) or not k or k in seen: continue
        seen.add(k); out.append(it)
    return out
NPRE=12  # 资讯首屏直出正文的卡片数，其余正文进 assets/news.<hash>.json 按需加载
def ncard(n,lz=None):
    lk=''.join(f'<a class="btn" href="{safe_url(u)}" target="_blank" rel="noopener noreferrer">{e(t)} ↗</a>' for t,u in n['links'] if u)
    return (f'<article class="post nw s-{n["s"]}" data-s="{n["s"]}"><header class="nh"><span class="src {n["s"]}">{n["sl"]}</span><span class="nm">{e(n["m"])}</span></header>'
            f'<h3 class="nt">{e(n["t"])}</h3>{f'<div class="nb nbc" data-lz="{lz}"></div>' if lz is not None else f'<div class="nb nbc">{n["body"]}</div>'}<footer><div class="act"><button class="btn ex" type="button" aria-expanded="false">展开</button>{lk}</div></footer></article>')
def news():
    N=news_items(); c={k:sum(1 for n in N if n['s']==k) for k in 'hdsx'}
    nz=sum(c[k] for k in 'hds')
    nbd=jdump([n['body'] for n in N[NPRE:]]); nbn=f'news.{H8(nbd)}.json'; put(nbn,nbd)
    seg=('<div class="seg" role="group" aria-label="来源"><button type="button" data-src="all" class="on" aria-pressed="true">全部 '+str(len(N))+'</button>'
         +''.join(f'<button type="button" data-src="{k}" aria-pressed="false">{l} {c[k]}</button>' for k,l in (('h','AIHOT 热点'),('d','AIHOT 日报'),('s','AIHOT 精选'),('x','X 新闻 · 英文')) if c[k])+'</div>')
    body=(f'<div class="tools"><h1>资讯</h1>{seg}<span class="sp"></span><span class="hint">中文 AIHOT {nz} 条在前 · 英文 X 新闻 {c["x"]} 条在后 · 卡片内读全文</span></div>'
          f'<div class="grid ng" id="ng" data-src="assets/{nbn}">{"".join(ncard(n,None if i<NPRE else i-NPRE) for i,n in enumerate(N))}</div><div class="empty" id="nempty" hidden>这个来源暂无内容</div>')
    return page('XHOT · 资讯',body,'news.html')
def spark(vals,w=72,h=22):
    if len(vals)<2: return ''
    pts=sparkpath(vals,w,h); up=vals[-1]>=sum(vals[:-1])/len(vals[:-1])
    lx,ly=pts.split()[-1].split(',')
    return f'<svg class="spk {"up" if up else "dn"}" viewBox="0 0 {w} {h}" width="{w}" height="{h}" aria-hidden="true"><polyline points="{pts}"/><circle cx="{lx}" cy="{ly}" r="2.2"/></svg>'
def trows(L,mx,tag=False):
    out=''
    for i,(x,d) in enumerate(L,1):
        g=x['g']; w=min(100,abs(g)/mx*100) if mx else 0
        t=f'<span class="tag" style="--dc:{DC[d]}">{DN[d]}</span>' if tag else ''
        out+=(f'<li><a class="trow" href="{turl(x)}" target="_blank" rel="noopener noreferrer" title="{e(x["name"])}：昨日 {x["last"]:,} 条，较前几日均值 {g:+.0f}%"><span class="rk">{i}</span><span class="tn">{e(x["name"])}{t}</span>'
              f'{spark(x["vals"])}<span class="tc">{fmt(x["last"])}</span><span class="tb"><i class="{"up" if g>=0 else "dn"}" style="width:{w:.0f}%"></i></span><span class="tg2 {"up" if g>=0 else "dn"}">{g:+.0f}%</span></a></li>')
    return out or '<li class="empty">暂无话题数据</li>'
TH='<div class="th"><span>#</span><span>话题</span><span>近 6 日</span><span>昨日条数</span><span>较均值</span></div>'
def trends():
    T=[(x,'ai') for x in DATA['ai']['trends']]
    M=sorted([(x,d) for d in DOMS if d!='ai' for x in DATA[d]['trends']],key=lambda z:-z[0]['g'])
    mx=max([abs(x['g']) for x,_ in T+M] or [1])
    up=[z for z in T+M if z[0]['g']>=0]; top=max(T+M,key=lambda z:z[0]['g']) if T+M else None; bot=min(T+M,key=lambda z:z[0]['g']) if T+M else None
    gtop=GHR[0] if GHR else None
    kp_=[('追踪话题',f'{len(T+M)}',f'{len(up)} 个上升 · {len(T+M)-len(up)} 个下降'),
         ('涨最快',e(top[0]['name']) if top else '—',f'<b class="up">{top[0]["g"]:+.0f}%</b> · {DN[top[1]]}' if top else ''),
         ('跌最多',e(bot[0]['name']) if bot else '—',f'<b class="dn">{bot[0]["g"]:+.0f}%</b> · {DN[bot[1]]}' if bot else ''),
         ('GitHub 今日最热',e(gtop['repo'].split('/')[-1]) if gtop else '—',f'+{gtop["today"]:,} ★ 今日' if gtop else '')]
    kpis='<div class="kpis">'+''.join(f'<div class="kpi"><span class="kl">{a}</span><b class="kv">{b}</b><span class="ks">{c}</span></div>' for a,b,c in kp_)+'</div>'
    gmx=max([r['today'] for r in GHR[:12]] or [1])
    gl=''.join(f'<li><a class="grow" href="{safe_url(r["url"])}" target="_blank" rel="noopener noreferrer"><span class="rk">{i}</span><span class="gm"><b class="gn"><span class="go">{e(r["repo"].split("/")[0])}/</span>{e(r["repo"].split("/")[-1])}</b><span class="gd">{e(r["desc"])}</span><span class="gx">{(f"<i class=ld style=--h:{hue(r[chr(108)+chr(97)+chr(110)+chr(103)])}></i>"+e(r["lang"])) if r["lang"] else ""}<span>★ {fmt(r["stars"])}</span></span></span><span class="gt"><b>+{r["today"]:,}</b><span class="tb"><i class="up" style="width:{(r["today"]/gmx)**.5*100:.0f}%"></i></span><small>今日 ★</small></span></a></li>' for i,r in enumerate(GHR[:12],1))
    # hot=''.join(f'<li><a class="hrow" href="{e((it.get("links") or {}).get("aihot",""))}" target="_blank" rel="noopener noreferrer"><span class="rk">{i}</span><span class="hn">{e(it["title"])}</span><span class="hc">{it.get("sourceCount",0)} 信源</span></a></li>' for i,it in enumerate(AH_HOT[:10],1))
    body=(f'<div class="tools"><h1>趋势</h1><span class="hint">话题 = X 上相关帖子每日条数（get_posts_counts_recent），涨跌 = 昨日 vs 前几日均值 · 点行在 X 搜索</span></div>{kpis}'
          f'<div class="tcols"><div class="tstack"><section class="panel big" style="--dc:{DC["ai"]}"><h2><i class="dot"></i>AI 话题涨跌<small>{len(T)} 个 · 按涨幅排序</small></h2>{TH}<ul class="list tl">{trows(T,mx)}</ul></section>'
          f'<section class="panel" style="--dc:{DC["money"]}"><h2><i class="dot" style="--dc:{DC["money"]}"></i><i class="dot" style="--dc:{DC["growth"]}"></i>搞钱 + 个人成长<small>{len(M)} 个话题</small></h2>{TH}<ul class="list tl">{trows(M,mx,True)}</ul></section></div>'
          f'<section class="panel big" style="--dc:#0ea5e9"><h2>GitHub 技术趋势<small>AI / 开发工具 · 今日新增 ★（条长按平方根缩放）</small></h2><ul class="list gl">{gl}</ul></section></div>'
          '')
    return page('XHOT · 趋势',body,'trends.html')
# ---- 个人页 ----
def person(u):
    a=ACC[u]; pr=PROF.get(u,{}); uid=U2ID.get(u)
    rows=[]
    if uid:
        for r in db.execute('select id,created_at,text,likes,rts,replies,quotes,views,bm,url,lang from tweets where author_id=? order by created_at desc limit 200',(uid,)):
            rows.append([r[0],r[1],_h.unescape(r[2]),r[3],r[4],r[5],r[6],r[7],r[3]+2*r[4]+3*r[6]+r[5]+(r[8] or 0),r[9] or f'https://x.com/{a["H"]}/status/{r[0]}',1 if langf.ok(r[2],r[10]) else 0])
    nother=sum(1 for r in rows if not r[10])
    okr=[r for r in rows if r[10]]
    wk=sorted([r for r in okr if isw(r[1])],key=lambda r:-r[8]); mode='w' if len(wk)>=6 else 'g'
    first=(wk if mode=='w' else sorted(okr,key=lambda r:-r[8]))[:12]
    data=jdump([r[:9]+['' if r[9]==f'https://x.com/{a["H"]}/status/{r[0]}' else r[9]]+r[10:] for r in rows]); jn=f'{u}.{H8(data)}.json'
    for old in glob.glob(os.path.join(OUT,'p',f'{u}.*.json')):
        if os.path.basename(old)!=jn: os.remove(old)
    open(os.path.join(OUT,'p',jn),'w',encoding='utf-8').write(data)
    dl='—' if a['d'] is None else f'{a["d"]:+,}'
    bio=f'<p class="bio">{e(pr["description"])}</p>' if pr.get('description') else ''
    tog=f'<label class="tgl"><input type="checkbox" id="alll"> 显示全部语言（另 {nother} 条）</label>' if nother else ''
    seg=SORTSEG if mode=='w' else SORTSEG.replace('data-sort="w" class="on" aria-pressed="true"','data-sort="w" aria-pressed="false"').replace('data-sort="g" aria-pressed="false"','data-sort="g" class="on" aria-pressed="true"')
    tags=''.join(f'<span class="tag" style="--dc:#fff">{DN[d]}</span>' for d in a['doms'])
    feed=''.join(card(r,a,'../',False) for r in first) if okr else '<div class="empty">这个账号暂时没有可显示的推文：可能是受保护账号，或者近期没有发原创帖。</div>'
    body=(f'<section class="phc">{av(u,a["name"],"xl","../")}<div style="min-width:0"><h1>{e(a["name"])}<small translate="no">@{e(a["H"])}</small>{tags}</h1>{bio}</div><div class="chips"><div class="chip"><b>{fmt(a["f"])}</b><span>粉丝</span></div><div class="chip"><b>{dl}</b><span>较上次</span></div><div class="chip"><b>{len(rows)}</b><span>已存推文</span></div><a class="xb" href="https://x.com/{e(a["H"])}" target="_blank" rel="noopener noreferrer">在 X 查看 ↗</a></div></section>'
          f'<div class="tools">{seg}<input id="q" type="search" aria-label="搜索推文" placeholder="搜索 {e(a["name"])} 的推文…" autocomplete="off" spellcheck="false" style="flex:1 1 240px">{tog}<span class="cnt" id="cnt" aria-live="polite">{("近一周 "+str(len(wk))+" 条") if mode=="w" else ("近一周仅 "+str(len(wk))+" 条，默认按全局热度")}</span></div>'
          f'<div id="feed" class="grid" data-pre="{len(first)}" data-mode="{mode}">{feed}</div><button id="more" class="more" type="button" hidden>再显示</button>'
          f'<script type="application/json" id="tw-meta">{jsafe({"name":a["name"],"handle":a["H"],"u":u,"dom":a["dom"],"av":AVF.get(u,""),"h":hue(u),"src":jn,"week":WEEK})}</script>')
    return page(f'{a["name"]} (@{a["H"]}) · XHOT',body,'',pref='../')
os.makedirs(os.path.join(OUT,'p'),exist_ok=True)
for fn,fnc in (('index.html',hot),('accounts.html',accounts),('news.html',news),('trends.html',trends)):
    open(os.path.join(OUT,fn),'w',encoding='utf-8').write(fnc())
for u in ACC: open(os.path.join(OUT,'p',f'{u}.html'),'w',encoding='utf-8').write(person(u))
for sub in (AD,AVD):
    for f in os.listdir(sub):
        p=os.path.abspath(os.path.join(sub,f))
        if os.path.isfile(p) and p not in keep: os.remove(p)
print('xhot: 4 tab pages +',len(ACC),'person pages; avatars',len(AVF),'; tweets',NT)
