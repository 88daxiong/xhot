#!/usr/bin/env python3
"""XHOT v15 生成器（任务导向重构）：今日 · 领域 · 人物 · 资讯 · 趋势 + ⌘K 搜索
  index.html 今日（最新一期） · day/<date>.html 往期 · d/<ai|money|growth|all>.html 领域/归档 · people.html 人物目录 · p/<handle>.html 人物页
  news.html 资讯 · trends.html 趋势；hot.html / accounts.html / daily/<date>.html 为旧链接跳转页
  assets/：style.<h>.css · core/news/feed.<h>.js · search.<h>.json · av/ 头像；feed/<day>.<h>.json 按天分片；p/<handle>.<h>.json 个人分片
  公开数据策略（TEXT_MODE=excerpt，默认）：站点与 data/ 只含帖子 ID、指标、短摘录（≤220 字，日报必读 ≤320 字）+ 中文要点 + 原帖链接，不含推文全文。
  用法：python3 generate.py [输出目录]"""
import os,sys,glob,json,re,datetime,hashlib,shutil,math,html as _h,base64,io,statistics
D=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,D); os.chdir(D)
from xhot_data import *
import langf
_e0=e
def e(t): return _e0(t).replace('@@','&#64;&#64;')   # 内容里的 @@ 不能被当成构建占位符
OUT=sys.argv[1] if len(sys.argv)>1 else os.path.join(D,'site')
TEXT_MODE=os.environ.get('XHOT_TEXT_MODE','excerpt')   # excerpt（默认）| full（用户日后批准才改）
EXC,EXCH=(220,320) if TEXT_MODE=='excerpt' else (4000,8000)
SANS='-apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",system-ui,"Noto Sans CJK SC","Microsoft YaHei",sans-serif'   # Mac 优先 -apple-system / PingFang SC / Helvetica Neue
DC={'ai':'var(--ai)','money':'var(--money)','growth':'var(--growth)'}
DN={'ai':'AI','money':'搞钱','growth':'成长'}
def H8(b): return hashlib.sha1(b if isinstance(b,bytes) else b.encode()).hexdigest()[:10]
os.makedirs(OUT,exist_ok=True)
AD=os.path.join(OUT,'assets'); AVD=os.path.join(AD,'av')
EMIT=set()
def write(rel,data):
    p=os.path.join(OUT,rel); os.makedirs(os.path.dirname(p),exist_ok=True); b=data if isinstance(data,bytes) else data.encode('utf-8')
    EMIT.add(os.path.abspath(p))
    if not os.path.exists(p) or open(p,'rb').read()!=b: open(p,'wb').write(b)
def put(name,data,sub=AD): write(os.path.relpath(os.path.join(sub,name),OUT),data)

GH0=json.load(open(sorted(glob.glob('raw/*_gh_trending.json'))[-1])) if glob.glob('raw/*_gh_trending.json') else {'repos':[]}
# ---- 头像 ----
AVF={}; AVS={}   # AVF = 96px（大头像）, AVS = 64px q66（列表/卡片小头像，约 0.6 KB）
from PIL import Image; import io
os.makedirs('avatars_webp',exist_ok=True)
for f in glob.glob('avatars/*.jpg'):
    h=os.path.basename(f)[:-4]; w=os.path.join('avatars_webp',h+'.webp')
    if not os.path.exists(w) or os.path.getmtime(w)<os.path.getmtime(f):
        try: im=Image.open(f); im.verify(); im=Image.open(f).convert('RGB'); im.thumbnail((96,96)); im.save(w,'WEBP',quality=78,method=6)
        except Exception as ex: print('skip avatar',h,type(ex).__name__); continue
    b=open(w,'rb').read(); n=f'{h}.{H8(b)[:8]}.webp'; put(n,b,AVD); AVF[h]=n
    w2=os.path.join('avatars_webp',h+'.s.webp')
    if not os.path.exists(w2) or os.path.getmtime(w2)<os.path.getmtime(f):
        im=Image.open(f).convert('RGB'); im.thumbnail((64,64)); im.save(w2,'WEBP',quality=66,method=6)
    b2=open(w2,'rb').read(); n2=f'{h}.s.{H8(b2)[:8]}.webp'; put(n2,b2,AVD); AVS[h]=n2

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
WD='一二三四五六日'
def dkey(s): return dt(s).strftime('%Y-%m-%d')
def dlab(k):
    t=NOW.strftime('%Y-%m-%d'); y=(NOW-datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    return f'{int(k[5:7])}月{int(k[8:])}日'
def dsub(k): d=datetime.datetime.strptime(k,'%Y-%m-%d'); return f'{d.month}月{d.day}日 周{WD[d.weekday()]}'
def dsep(k):
    sub=dsub(k); sub=sub if dlab(k) in ('今天','昨天') else sub.split(' ')[1]
    return f'<div class="dsep" data-d="{k}"><b>{dlab(k)}</b><span>{sub}</span></div>'
def dchip(k):
    return f'{dlab(k)} · {dsub(k).split(" ")[1]}'
def relt(s): return ''   # 相对时间由前端补（页面不烘焙「x 小时前」）
def tmh(s): return f'<time class="tm" datetime="{e(s)}" title="{fullt(s)}"><b>{dt(s).strftime("%H:%M")}</b><span class="rl">{relt(s)}</span></time>'
def withdays(rows,fn):
    """按北京时间日期插入吸顶分隔条（时间排序用）"""
    out=[];last=None
    for r in rows:
        k=dkey(r[1])
        if k!=last: out.append(dsep(k)); last=k
        out.append(fn(r))

def jdump(o): return json.dumps(o,ensure_ascii=False,separators=(',',':'))  # 独立 .json 文件用（不嵌入 HTML）
def jsafe(o):
    """嵌入 <script type=application/json> 的 JSON：转义 < > & 与 U+2028/2029，防止 </script>、<!-- 等打断解析"""
    return (json.dumps(o,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e')
            .replace('&','\\u0026').replace('\u2028','\\u2028').replace('\u2029','\\u2029').replace('@@','\\u0040\\u0040'))

def tools(title,mid='',right='',info='',h='h1'):
    """统一工具条：左标题 · 中筛选 · 右日期 + 排序；info 是下方一行小字"""
    return (f'<div class="tools"><{h}>{title}</{h}><div class="tmid">{mid}</div><div class="tright">{right}</div></div>'+(f'<div class="tinfo">{info}</div>' if info else '')+('<i id="rdy" hidden></i>' if h=='h1' else ''))
def dfull(k):
    d=datetime.datetime.strptime(k,'%Y-%m-%d'); return f'{d.month}月{d.day}日 周{WD[d.weekday()]}'
def dctl(days,mode='state',cur='',href='',alllab='全部日期'):
    """统一日期控件：‹ [📅 日期 ▾] ›。state = 页内筛选（空 = 全部日期）；nav = 跳转到 href 模板（{d}）。days 为有数据的日期（新→旧）"""
    days=[k for k in days if re.fullmatch(r'\d{4}-\d\d-\d\d',k)]
    if mode=='nav':
        i=days.index(cur) if cur in days else -1
        pv=f'<a class="dcb dcp" href="{e(href.replace("{d}",days[i+1]))}" rel="prev" aria-label="更早一天">‹</a>' if 0<=i<len(days)-1 else '<span class="dcb dcp dis" aria-disabled="true">‹</span>'
        nx=f'<a class="dcb dcn" href="{e(href.replace("{d}",days[i-1]))}" rel="next" aria-label="更新一天">›</a>' if i>0 else '<span class="dcb dcn dis" aria-disabled="true">›</span>'
        lab=dfull(cur) if cur else '选择日期'
    else:
        pv='<button type="button" class="dcb dcp" aria-label="更早一天"'+('' if days else ' disabled')+'>‹</button>'
        nx='<button type="button" class="dcb dcn" aria-label="更新一天" disabled>›</button>'
        lab=alllab
    return (f'<div class="dctl" data-mode="{mode}" data-all="{e(alllab)}" data-days="{",".join(days)}"'+(f' data-cur="{cur}"' if cur else '')+(f' data-href="{e(href)}"' if href else '')+f'>{pv}'
            f'<button type="button" class="dcm" aria-haspopup="dialog" aria-expanded="false"><i aria-hidden="true">📅</i><span class="dcl">{lab}</span><i class="dcv" aria-hidden="true"></i></button>{nx}</div>')

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
# 构建时钟 = 最新一次数据抓取时间（不是墙上时钟）：同一份数据重复构建得到逐字节相同的页面，没有数据变化的页面不会被改写；
# 「x 小时前 / 数据是否过期」全部交给前端按真实当前时间判断。
_fv=[v for v in FRESH.values() if v]
if _fv: NOW=max(_fv)
WEEK=(NOW-datetime.timedelta(days=7)).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
FRL={'tweets':'推文','followers':'粉丝','news':'X 新闻','aihot':'AIHOT','gh':'GitHub','counts':'话题计数'}
PAGEF={'today':['tweets','followers','counts'],'dom':['tweets'],'ppl':['followers','tweets'],'news':['aihot','news'],'trends':['counts','gh'],'trend':['counts','gh'],'':['tweets','followers']}
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
        out+=f'<tr class="{stt}"><td><i></i>{lab}</td><td>{_ts(t)}</td><td>{('—' if not t else '<time class="tm" datetime="'+Zs(t)+'Z"><span class="rl"></span></time>')}</td><td>{c}</td></tr>'
    return bad,f'<table class="hs"><thead><tr><th>数据源</th><th>最近抓取</th><th>距今</th><th>规模</th></tr></thead><tbody>{out}</tbody></table><p class="hsn">刷新计划：每天 1 次（北京时间 07:58）。超过 26 小时标黄、超过 48 小时标红。数据抓取于 {NOW.strftime("%m-%d %H:%M")}。</p>'
def fresh(cur):
    ks=PAGEF.get(cur,['tweets']); bad,tbl=health()
    ts=[FRESH[k] for k in ks if FRESH.get(k)]; old=min(ts) if ts else None; age=(NOW-old).total_seconds()/3600 if old else 99
    cls='ok'   # 过期颜色由前端按真实时间改（data-t）
    lab=f'数据 {_ts(old)}' if old else '数据 —'
    return f'<details class="fr {cls}"{(" data-t=\""+Zs(old)+"Z\"") if old else ""}><summary title="点击查看各数据源状态"><i></i>{lab}{f"<b>{bad} 项待更新</b>" if bad else ""}</summary><div class="frp"><h3>数据健康</h3>{tbl}</div></details>'

# ======================= v15 新增：评分 / 标签 / 摘录 / 帖子表 =======================
import statistics
JS_MODS={}   # 模块名 -> 源码
def av(u,n,cls='',pref='',eager=False):
    ch=e((n or u)[:1].upper()); lz='' if eager else ' loading="lazy"'
    big=cls in('l','xl'); F=AVF if big else AVS; px=96 if big else 64
    img=f'<img src="{pref}assets/av/{F[u]}" alt="" width="{px}" height="{px}" decoding="async"{lz}>' if u in F else ''
    return f'<span class="av {cls}" style="--h:{hue(u)}" aria-hidden="true">{ch}{img}</span>'
TAGS=[('model','模型','ai',r'\b(gpt-?\d\w*|gemini|claude|llama|qwen|deepseek|kimi|mistral|gro[k]|llm|benchmarks?|reasoning|fine-?tun\w*|models?|opus|sonnet|haiku)\b|模型|推理|基准|微调'),
 ('agent','智能体','ai',r'\bagents?\b|\bmcp\b|agentic|智能体|工作流|workflows?|computer use|subagents?'),
 ('code','编程','ai',r'claude code|codex|cursor|copilot|vibe coding|\bcoding\b|\bide\b|编程|代码|\bcli\b|devin|windsurf|replit|\bgithub\b'),
 ('oss','开源','ai',r'open[- ]?source|open[- ]?weights?|开源|hugging ?face|github\.com|apache 2|mit license'),
 ('product','产品发布','ai',r'\blaunch\w*|\breleased?\b|introducing|rolling out|now available|announc\w+|发布|上线|推出|新功能|available today|\bv\d+(\.\d+)?\b'),
 ('research','研究','ai',r'\bpaper\b|arxiv|\bresearch\w*|\bstudy\b|论文|研究|实验|\bsota\b|datasets?|alignment|interpretab\w+'),
 ('chips','算力芯片','ai',r'\bgpus?\b|nvidia|\btpus?\b|\bchips?\b|semiconductor|data ?cent(er|re)s?|\bcompute\b|算力|芯片|显卡|数据中心|h100|b200'),
 ('policy','监管安全','ai',r'regulat\w+|\bpolicy\b|\bsafety\b|eu ai act|legislat\w+|congress|government|export control|监管|安全|法案|政策|合规|版权|copyright|lawsuit|诉讼'),
 ('startup','创业','money',r'startups?|founders?|\bsaas\b|\bmrr\b|\barr\b|revenue|bootstrapp\w*|创业|创始人|营收|商业化|一人公司|盈利|\byc\b|y combinator'),
 ('creator','创作者','money',r'creators?|youtube|newsletter|audience|followers|创作者|博主|涨粉|流量|短视频|\bviral\b'),
 ('funding','融资投资','money',r'funding|valuation|\bipo\b|invest\w*|\bvcs?\b|融资|估值|投资|上市|series [a-d]\b|raised \$|\$\d+(\.\d+)?\s?[mb]\b'),
 ('indie','独立开发','money',r'indie|solopreneur|side project|\bship(ped|ping)?\b|build in public|出海|独立开发|副业|pricing|定价|订阅|subscription|stripe'),
 ('habit','习惯效率','growth',r'habits?|productivity|\bfocus\b|routine|\bsleep\b|discipline|习惯|效率|专注|自律|精力|时间管理|早起|健身|deep work'),
 ('write','写作阅读','growth',r'\bwriting\b|\bessays?\b|clarity|communicat\w+|storytelling|写作|表达|文章|笔记|沟通|阅读|\breading\b|\bbooks?\b'),
 ('career','职业认知','growth',r'career|\bjobs?\b|hiring|\blearn(ing)?\b|\bskills?\b|mindset|advice|decisions?|职业|认知|学习|成长|思考|人生|焦虑|面试|晋升')]
TAGL={k:l for k,l,_,_ in TAGS}; TAGD={k:d for k,_,d,_ in TAGS}
TAGRX=[(k,re.compile(rx,re.I)) for k,_,_,rx in TAGS]
def tags_of(t):
    t=re.sub(r'https?://\S+','',t or ''); return [k for k,rx in TAGRX if rx.search(t)][:2]
def tcs(ks,cls='tc'): return ''.join(f'<span class="{cls}">{e(TAGL[k])}</span>' for k in ks if k in TAGL)
def excerpt(t,n):
    t=re.sub(r'https?://t\.co/\w+','',t or ''); t=re.sub(r'[ \t]+\n','\n',t); t=re.sub(r'\n{3,}','\n\n',t).strip()
    t=re.sub(r'[ \t]{2,}',' ',t)
    if len(t)<=n: return t
    cut=t[:n]; m=max(cut.rfind(x) for x in ('。','！','？','.\n','. ','! ','? ','\n\n','；'))
    if m>=n*0.55: return cut[:m+1].rstrip()+' …'
    m=max(cut.rfind(' '),cut.rfind('，'),cut.rfind('、'))
    return (cut[:m] if m>=n*0.7 else cut).rstrip(' ,，、')+'…'
def is_en(t):
    t=re.sub(r'https?://\S+|[@#]\w+','',t or ''); cj=len(re.findall(r'[\u3400-\u9fff]',t)); la=len(re.findall(r'[A-Za-z]',t))
    return la>=12 and cj<=max(2,0.05*(cj+la))
def clean1(t,n=96):
    t=re.sub(r'https?://\S+','',t or ''); t=re.sub(r'\s+',' ',t).strip(); return t if len(t)<=n else t[:n].rstrip(' ,，、。')+'…'
def xlink(h,i): return f'https://x.com/{h}/status/{i}'
def zts(s): return s[:19]+'Z'     # 精简 UTC 时间戳
# ---- 帖子表（内存里有全文，只为评分/标签/摘录；公开产物只写摘录） ----
POSTS=[]; PBY={}
TAKEDOWN=set(l.split('#')[0].strip().lower() for l in open('takedown.txt',encoding='utf-8')) if os.path.exists('takedown.txt') else set()   # 帖子 ID / 账号 handle，一行一个：已删除、受保护或被要求撤下的内容
TAKEDOWN.discard('')
for u,a in ACC.items():
    uid=U2ID.get(u)
    if not uid: continue
    rows=[]
    for r in db.execute('select id,created_at,text,likes,rts,replies,quotes,views,bm,lang from tweets where author_id=? order by created_at desc',(uid,)):
        if str(r[0]) in TAKEDOWN or u.lower() in TAKEDOWN: continue
        t=_h.unescape(r[2] or '')
        if not langf.ok(t,r[9]): continue
        ex=excerpt(t,EXC)
        if len(re.sub(r'https?://\S+|\s','',t))<4: continue    # 纯链接/媒体帖不进榜
        rows.append(dict(id=r[0],u=u,ts=r[1],t=t,ex=ex,like=r[3],rt=r[4],reply=r[5],quote=r[6],view=r[7],bm=r[8] or 0,heat=r[3]+2*r[4]+3*r[6]+r[5]+(r[8] or 0),en=is_en(t),tags=tags_of(t)))
    base=statistics.median([x['heat'] for x in rows[:30]]) if len(rows)>=5 else 50
    for x in rows:
        # 重要度 0-100：绝对热度（对数）+ 相对本人常态（对数比，限幅），规则可复现；日报由流程撰写者做最终复核（pin/hide/必读）
        s=6*math.log1p(x['heat'])+10*max(-1,min(2.5,math.log((x['heat']+20)/(base+20))))
        x['score']=int(max(0,min(100,round(s)))); POSTS.append(x); PBY[x['id']]=x
POSTS.sort(key=lambda p:-p['score'])
def pdom(p): return ACC[p['u']]['dom']
def Zs(t): return t.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
def win(k):
    end=datetime.datetime.strptime(k+' 09:00','%Y-%m-%d %H:%M').replace(tzinfo=TZ); end=min(end,NOW)
    return Zs(end-datetime.timedelta(hours=25)),Zs(end)
def inwin(k): a,b=win(k); return [p for p in POSTS if a<=p['ts'][:19]<b]
def rank(rows,n,per=2,hide=(),pin=()):
    out=[];cnt={};seen=set()
    pr=[PBY[i] for i in pin if i in PBY and i not in hide]
    for p in pr+[p for p in rows if p['id'] not in pin]:
        if p['id'] in hide or p['id'] in {x['id'] for x in out}: continue
        k=re.sub(r'\W+','',p['t'].lower())[:28]
        if k in seen: continue
        if cnt.get(p['u'],0)>=per and p['id'] not in pin: continue
        seen.add(k); cnt[p['u']]=cnt.get(p['u'],0)+1; out.append(p)
        if len(out)>=n: break
    return out
for a in ACC.values():
    ps=[p for p in POSTS if p['u']==a['u']]
    a['p7']=[p for p in ps if p['ts'][:19]>=WEEK]
    a['top3']=sum(sorted([p['score'] for p in a['p7']],reverse=True)[:3])
    a['last']=max(ps,key=lambda p:p['score'] if p['ts'][:19]>=WEEK else -1,default=None) if ps else None
# ---- 周要点（刷新流程每周一撰写）----
WK={}
_wf=sorted(glob.glob(os.path.join(os.environ.get('XHOT_WEEKLY_DIR') or 'weekly','*.json')))
if _wf:
    try: WK=json.load(open(_wf[-1],encoding='utf-8'))
    except Exception: WK={}
def wk_people():
    ex={x.lower() for x in WK.get('exclude',[])}
    return sorted([a for a in ACC.values() if a['u'] not in ex],key=lambda a:-a['top3'])[:30]

# ======================= 页面外壳 / 卡片 =======================
J0=("(function(){var d=document.documentElement,t,s;try{t=localStorage.getItem('xhot-theme');s=localStorage.getItem('xhot-density')}catch(e){}"
    "t=(t==='light'||t==='dark')?t:'auto';d.setAttribute('data-pref',t);d.setAttribute('data-theme',t==='auto'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):t);if(s==='compact')d.setAttribute('data-density','compact')})();")
CSP=("default-src 'self'; script-src 'self' 'sha256-"+base64.b64encode(hashlib.sha256(J0.encode('utf-8')).digest()).decode()+"'; "
     "style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'none'; connect-src 'self'; media-src 'none'; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'")
HEADSEC=f'<meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin">'
THEME='<div class="tg" role="group" aria-label="主题"><button type="button" data-set-theme="light" aria-label="浅色">☀</button><button type="button" data-set-theme="dark" aria-label="深色">☾</button><button type="button" data-set-theme="auto">自动</button></div>'
NAVT=[('index.html','今日','today'),('d/ai.html','领域','dom'),('people.html','人物','ppl'),('news.html','资讯','news'),('trends.html','趋势','trend')]
CURM={'news.html':'news','trends.html':'trend','index.html':'today'}
def page(title,body,cur,pref='',head='',mods=(),desc='XHOT：每天 10 分钟，看完 X 上 AI / 搞钱 / 成长领域的重点。'):
    cur=CURM.get(cur,cur)
    nav=''.join(f'<a href="{pref}{h}"{" aria-current=page" if c==cur else ""}>{t}</a>' for h,t,c in NAVT)
    js=''.join(f'<script src="{pref}assets/@@JS:{m}@@" defer></script>' for m in ('core',)+tuple(mods))
    return (f'<!doctype html><html lang="zh-CN" data-theme="light" data-pref="auto" data-p="{pref}" data-sj="@@SJ@@"><head><meta charset="utf-8">{HEADSEC}<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22%3E%3Ctext y=%22.9em%22 font-size=%2290%22%3E%E2%9A%A1%3C/text%3E%3C/svg%3E">'
      f'<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><meta name="theme-color" content="#7c3aed"><link rel="expect" href="#rdy" blocking="render"><meta name="description" content="{e(desc)}"><title>{e(title)}</title>'
      f'<script>{J0}</script>@@CSS@@{js}{head}</head><body><a class="skip" href="#main">跳到正文</a>'
      f'<header class="top"><div class="bar"><a class="lg" href="{pref}index.html"><i aria-hidden="true">⚡</i>XHOT<span>X 热点雷达</span></a><nav class="nav" aria-label="栏目">{nav}</nav><span class="sp0"></span>'
      f'<button class="kb" type="button" data-kp aria-haspopup="dialog" aria-label="搜索（快捷键 ⌘K 或 /）"><i aria-hidden="true">⌕</i><span>搜索</span><kbd>⌘K</kbd></button>'
      f'<button class="hxb" type="button" aria-expanded="false" aria-controls="hx" aria-label="设置：主题、密度、数据状态">⚙</button><div class="hx" id="hx">{fresh(cur)}'
      f'<button class="tgb" type="button" data-density aria-pressed="false" title="切换信息密度">紧凑</button>{THEME}</div></div></header>'
      f'<main id="main" class="wrap">{body}<footer class="ft"><p>XHOT 是独立的个人项目，与 X Corp.、AIHOT、GitHub 无隶属或背书关系。帖子版权归原作者；站内只有短摘录，全文请点「在 X 打开」。中文要点与译文由 AI 自动整理，仅供参考，以原文为准。</p><p><a href="{pref}about.html">关于 · 数据来源 · 免责声明</a> · <a href="https://github.com/88daxiong/xhot/issues" target="_blank" rel="noopener noreferrer">反馈 / 撤下请求（GitHub Issues）</a> · 数据抓取于 {NOW.strftime("%Y-%m-%d %H:%M")} 北京时间</p></footer></main></body></html>')
PAGES={}
def emit(rel,html): PAGES[rel]=html
MET=lambda p:(f'<div class="met"><span title="点赞"><i aria-hidden="true">♥</i>{fmt(p["like"])}</span><span title="转发"><i aria-hidden="true">⇄</i>{fmt(p["rt"])}</span><span title="评论"><i aria-hidden="true">💬</i>{fmt(p["reply"])}</span><span title="浏览"><i aria-hidden="true">👁</i>{fmt(p["view"])}</span></div>')
def post_html(p,pref='',who=True,eager=False):
    a=ACC[p['u']]; dom=pdom(p); H=a['H']
    meta=f'<div class="pm"><span class="heat" title="热度 = 赞 + 2×转 + 3×引用 + 评论 + 收藏">🔥 {fmt(p["heat"])}</span>{tmh(p["ts"])}</div>'
    hd=(f'<header>{av(p["u"],a["name"],"",pref,eager)}<div class="who"><a href="{pref}p/{p["u"]}.html">{e(a["name"])}</a><small>@{e(H)}</small></div>{meta}</header>' if who
        else f'<header><span class="tag dtag" data-d="{dkey(p["ts"])}">{dchip(dkey(p["ts"]))}</span><div class="who"></div>{meta}</header>')
    lang=' lang="en"' if p['en'] else ''
    tg=f'<div class="tcs">{tcs(p["tags"])}</div>' if p['tags'] else ''
    return (f'<article class="post fi" style="--dc:{DC[dom]}" data-k="{p["id"]}" data-ts="{zts(p["ts"])}" data-dom="{" ".join(a["doms"])}" data-tags="{" ".join(p["tags"])}">{hd}<div class="pt"{lang}>{lnk(p["ex"])}</div>{tg}'
            f'<footer>{MET(p)}<div class="act"><button class="btn cp" type="button" data-l="复制摘录">复制摘录</button><a class="btn op" href="{safe_url(xlink(H,p["id"]))}" target="_blank" rel="noopener noreferrer">在 X 打开 ↗</a></div></footer></article>')
def seg_dom(cur_attr='button',withall=True,allhref=None):
    b=('<button type="button" data-dom="all" class="on" aria-pressed="true">全部</button>' if withall else '')
    return '<div class="seg" role="group" aria-label="领域">'+b+''.join(f'<button type="button" data-dom="{d}" style="--dc:{DC[d]}" aria-pressed="false"><i class="dot"></i>{DN[d]}</button>' for d in DOMS)+'</div>'
def seg_links(cur,pref=''):
    items=[(d,DN[d],f'{pref}d/{d}.html') for d in DOMS]+[('all','全部归档',f'{pref}d/all.html')]
    return '<nav class="seg" aria-label="领域">'+''.join(f'<a href="{h}" class="{"on" if k==cur else ""}"'+(' aria-current="page"' if k==cur else '')+(f' style="--dc:{DC[k]}"' if k in DC else '')+f'>{("<i class=dot></i>" if k in DC else "")}{t}</a>' for k,t,h in items)+'</nav>'
def tag_chips(keys,counts=None):
    return ('<div class="fchips" role="group" aria-label="标签筛选"><button type="button" class="on" data-ftag="all" aria-pressed="true">全部标签</button>'
            +''.join(f'<button type="button" data-ftag="{k}" aria-pressed="false">{e(TAGL[k])}{f"<small>{counts[k]}</small>" if counts and k in counts else ""}</button>' for k in keys)+'</div>')
def minimap(vals,w=112,h=28):
    mx=max(vals) or 1; n=len(vals); bw=w/n
    return f'<svg class="mm" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="近 {n} 天发帖节奏">'+''.join(f'<rect x="{i*bw+1:.1f}" y="{h-max(2,v/mx*h):.1f}" width="{bw-2:.1f}" height="{max(2,v/mx*h):.1f}" rx="1.5"/>' for i,v in enumerate(vals))+'</svg>'

GH=GH0
GHR=sorted([r for r in GH['repos'] if r['ai'] and langf.script_ok(r['desc'])],key=lambda r:-r['today'])[:20]
def plain(t,n=96):
    t=re.sub(r'https?://\S+','',t or ''); t=re.sub(r'[#*>`_]+','',t); t=re.sub(r'\s+',' ',t).strip()
    return short(t,n)
def norm(t): return re.sub(r'[\W_]+','',t.lower())[:24]
def src(it): return ((it.get('source') or {}).get('name') or '').split('（')[0]
def paras(t): return ''.join(f'<p>{lnk(x.strip())}</p>' for x in re.split(r'\n\s*\n|\n',t or '') if x.strip())
def ago(s): return rel(s) if s else ''
def tt(s): return jdt(s) if s and dt(s) else ''
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
        items.append(dict(t=it['title'],s='h',sl='AIHOT 热点',m=f'{it.get("sourceCount",0)} 个信源 · {tt(it.get("latestAt",""))}',sm=plain(stv.get('digest','')),ts=it.get('latestAt',''),body=body,links=[('AIHOT 综述',(stv.get('links') or {}).get('aihot') or L.get('aihot','')),('原文',L.get('original',''))],chk=it['title']))
    if AH_DAILY:
        for sec in AH_DAILY.get('sections',[]):
            for it in sec['items']:
                L=it.get('links') or {}
                items.append(dict(t=it['title'],s='d',sl='AIHOT 日报',m=(src(it) or sec['label'])+' · 日报 '+AH_DAILY.get('date',''),sm=plain(it.get('summary','')),ts=AH_DAILY.get('generatedAt') or (AH_DAILY.get('date','')+'T08:00:00+08:00'),body=paras(it.get('summary','')),links=[('AIHOT',L.get('aihot') or AH_DAILY['links']['aihot']),('原文',L.get('original',''))],chk=it['title']))
    pool=AH_SEL[:20]+[x for d in DOMS if d!='ai' for x in DATA[d]['ex']]
    for it in pool:
        L=it.get('links') or {}
        body=paras(it.get('summary',''))+(f'<p class="why"><b>推荐理由</b>{e(it["reason"])}</p>' if it.get('reason') else '')
        items.append(dict(sm=plain(it.get('summary','') or it.get('reason','')),ts=it.get('publishedAt',''),t=it['title'],s='s',sl='AIHOT 精选',m=src(it)+(' · '+tt(it.get('publishedAt',''))) if it.get('publishedAt') else src(it),body=body,links=[('AIHOT 全文译文',L.get('aihot','')),('原文',L.get('original',''))],chk=it['title']))
    xs=[]
    for d in DOMS:
        for n in (latest(f'news_{d}') or {}).get('data',[])[:15]:
            body=(f'<p class="hook">{e(n["hook"])}</p>' if n.get('hook') else '')+paras(n.get('summary',''))+kp([x['post_id'] for x in n.get('cluster_posts_results',[])])
            xs.append(dict(sm=plain(n.get('hook') or n.get('summary','')),ts=n.get('updated_at',''),t=n.get('name',''),s='x',sl='X 新闻',m='更新 '+tt(n.get('updated_at','')),u=n.get('updated_at',''),body=body,links=[('在 X 查看',n.get('url',''))],chk=n.get('name','')+n.get('summary','')))
    items+=sorted(xs,key=lambda x:x['u'],reverse=True)  # X 新闻（英文）在后，按更新时间新→旧
    seen=set(); out=[]
    for it in items:
        k=norm(it['t'])
        if not langf.script_ok(it['chk']) or not k or k in seen: continue
        seen.add(k); out.append(it)
    return out
NTOP={'h':4,'s':5,'d':2,'x':2}   # 资讯默认「精选」各来源配额（中文 AIHOT 在前）
NORD={'h':0,'s':1,'d':2,'x':3}
def nkey(n):
    d=dt(n.get('ts') or '')
    return d.strftime('%Y-%m-%d') if d else '0000-00-00'
def ntop(N):
    pick=[];q=dict(NTOP)
    for k in 'hsdx':
        pick+=[i for i,n in enumerate(N) if n['s']==k][:q[k]]
    if len(pick)<12: pick+=[i for i in range(len(N)) if i not in pick][:12-len(pick)]
    return pick
def nmeta(n):
    t=dt(n.get('ts') or '')
    tm=f'<time class="tm" datetime="{e(n["ts"])}"><b>{t.strftime("%H:%M")}</b><span class="rl">{relt(n["ts"])}</span></time>' if t else ''
    return f'<span class="src {n["s"]}">{n["sl"]}</span>{tm}'
def nrow(n,i,sel=False):
    return (f'<li class="nr{" sel" if sel else ""}" data-s="{n["s"]}" data-i="{i}"><button class="nrh" type="button" aria-expanded="false">'
            f'<span class="nrm">{nmeta(n)}</span>'
            f'<span class="nrt"><b class="nt2">{e(n["t"])}</b><span class="ns">{e(n["sm"])}</span></span><i class="chev" aria-hidden="true"></i></button>'
            f'<div class="nrb" hidden></div></li>')
def nbody(n):
    lk=''.join(f'<a class="btn" href="{safe_url(u)}" target="_blank" rel="noopener noreferrer">{e(t)} ↗</a>' for t,u in n['links'] if u)
    return f'<div class="nb">{n["body"]}</div><div class="act">{lk}<span class="nm">{e(n["m"])}</span></div>'
NEWS=None
def news():
    global NEWS
    N=news_items(); NEWS=N; c={k:sum(1 for n in N if n['s']==k) for k in 'hdsx'}
    TOP=ntop(N)
    nbd=jdump([nbody(n) for n in N]); nbn=f'news.{H8(nbd)}.json'; put(nbn,nbd)
    SL=(('h','AIHOT 热点'),('d','AIHOT 日报'),('s','AIHOT 精选'),('x','X 新闻 · 英文'))
    seg=('<div class="seg" role="group" aria-label="来源筛选"><button type="button" data-src="top" class="on" aria-pressed="true">⭐ 精选 '+str(len(TOP))+'</button>'
         '<button type="button" data-src="all" aria-pressed="false">全部 '+str(len(N))+'</button>'
         +''.join(f'<button type="button" data-src="{k}" aria-pressed="false">{l} {c[k]}</button>' for k,l in SL if c[k])+'</div>')
    order=sorted(range(len(N)),key=lambda i:(nkey(N[i]),-NORD[N[i]['s']],N[i].get('ts') or ''),reverse=True)
    groups=[];last=None
    for i in order:
        k=nkey(N[i])
        if k!=last: groups.append((k,[])); last=k
        groups[-1][1].append(i)
    allh=''.join(f'<div class="ndg" data-d="{k}">{dsep(k) if k!="0000-00-00" else "<div class=dsep><b>更早</b></div>"}<ol class="nl">{"".join(nrow(N[i],i) for i in ids)}</ol></div>' for k,ids in groups)
    days=[k for k,_ in groups if k!='0000-00-00']
    f0=TOP[0] if TOP else None
    aside=('<aside class="nside" aria-label="阅读窗格"><section class="panel nrp" id="npane"><i class="nnotch" id="nnotch" aria-hidden="true"></i>'
           '<div class="nrpm" id="npmeta">'+('<span class="nn">01</span>'+nmeta(N[f0]) if f0 is not None else '')+'</div>'
           '<div class="nrph"><span class="nrpt" id="nptitle">'+(e(N[f0]['t']) if f0 is not None else '阅读窗格')+'</span></div>'
           '<div class="nrpb" id="npbody">'+(nbody(N[f0]) if f0 is not None else '<p class="nph" id="nhint">点左侧任意标题，全文在这里打开；列表位置不变，可以连续点着读。</p>')+'</div></section></aside>')
    body=(tools('资讯',seg,dctl(days),f'<span class="hint">精选 = AIHOT 热点 / 精选优先 {len(TOP)} 条 · 点标题读全文 · 中文 AIHOT 在前 · X 新闻为英文</span>')+
          f'<div class="nlay" id="ng" data-body="assets/{nbn}"><div class="nmain">'
          f'<section id="ntop" class="nsec2"><ol class="nl">{"".join(nrow(N[i],i,j==0) for j,i in enumerate(TOP))}</ol>'
          f'<button id="nmore" class="more" type="button">展开更多 · 按日期看全部 {len(N)} 条</button></section>'
          f'<section id="nall" class="nsec2" hidden>{allh}</section><div class="empty" id="nempty" hidden>这个来源 / 日期暂无内容</div></div>{aside}</div>')
    return page('XHOT · 资讯',body,'news',mods=('news',))
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
    body=(tools('趋势','<span class="hint">话题 = X 上相关帖子每日条数，涨跌 = 昨日 vs 前几日均值 · 点行在 X 搜索</span>')+f'{kpis}'
          f'<div class="tcols"><div class="tstack"><section class="panel big" style="--dc:{DC["ai"]}"><h2><i class="dot"></i>AI 话题涨跌<small>{len(T)} 个 · 按涨幅排序</small></h2>{TH}<ul class="list tl">{trows(T,mx)}</ul></section>'
          f'<section class="panel" style="--dc:{DC["money"]}"><h2><i class="dot" style="--dc:{DC["money"]}"></i><i class="dot" style="--dc:{DC["growth"]}"></i>搞钱 + 个人成长<small>{len(M)} 个话题</small></h2>{TH}<ul class="list tl">{trows(M,mx,True)}</ul></section></div>'
          f'<section class="panel big" style="--dc:#0ea5e9"><h2>GitHub 技术趋势<small>AI / 开发工具 · 今日新增 ★（条长按平方根缩放）</small></h2><ul class="list gl">{gl}</ul></section></div>'
          '')
    return page('XHOT · 趋势',body,'trends.html')
# ---- 个人页 ----

# ======================= 日报数据（刷新流程撰写）=======================
DAYD=os.environ.get('XHOT_DAILY_DIR') or os.path.join(D,'daily')
def _ids(x): return [str(i) for i in (x or []) if re.fullmatch(r'\d{5,25}',str(i))]
def _dok(d):
    if not isinstance(d,dict) or not re.fullmatch(r'\d{4}-\d\d-\d\d',str(d.get('date',''))): return None
    hl=[]
    for h in d.get('highlights') or []:
        if not isinstance(h,dict) or not re.fullmatch(r'[A-Za-z0-9_]{1,30}',str(h.get('handle',''))): continue
        pid=str(h.get('post_id') or ''); pid=pid if re.fullmatch(r'\d{5,25}',pid) else ''
        p=PBY.get(pid)
        og=str(h.get('excerpt') or '') or (excerpt(str(h.get('text_orig') or ''),EXCH) if h.get('text_orig') else '') or (excerpt(p['t'],EXCH) if p else '')
        likes=h.get('likes') if isinstance(h.get('likes'),int) else (p['like'] if p else None)
        hl.append(dict(handle=h['handle'],name=str(h.get('name') or h['handle']),text=str(h.get('text_zh') or ''),pid=pid,
            url=str(h.get('url') or (xlink(h['handle'],pid) if pid else f"https://x.com/{h['handle']}")),likes=likes,orig=og[:EXCH+40],orig_zh=str(h.get('excerpt_zh') or '')[:EXCH*3],
            tags=[k for k in (h.get('tags') or tags_of(og)) if k in TAGL][:2]))
    hl.sort(key=lambda x:-(x['likes'] if x['likes'] is not None else -1))
    cl=[]
    for c in d.get('changelog') or []:
        if isinstance(c,str): cl.append(('',c))
        elif isinstance(c,dict) and c.get('text'): cl.append((str(c.get('date') or ''),str(c['text'])))
    g={str(k):str(v)[:140] for k,v in (d.get('gists') or {}).items() if re.fullmatch(r'\d{5,25}',str(k))} if isinstance(d.get('gists'),dict) else {}
    sm=[str(x)[:140] for x in (d.get('summary_zh') or []) if isinstance(x,str) and x.strip()][:3] if isinstance(d.get('summary_zh'),list) else []
    return dict(date=d['date'],hl=hl,topics=str(d.get('topics_zh') or ''),fol=str(d.get('followers_zh') or ''),cl=cl,gists=g,summary=sm,hide=_ids(d.get('hide')),pin=_ids(d.get('pin')))
DAYS=[]
for fp in sorted(glob.glob(os.path.join(DAYD,'*.json'))):
    try: x=_dok(json.load(open(fp,encoding='utf-8')))
    except Exception as ex: print('skip daily',os.path.basename(fp),type(ex).__name__); x=None
    if x: DAYS.append(x)
DAYS.sort(key=lambda x:x['date'])
def day_top(d):
    k=d['date']; rows=inwin(k); pins=[h['pid'] for h in d['hl'] if h['pid']]+d['pin']
    top=rank(rows,30,2,d['hide'],pins)
    hs={h['pid'] for h in d['hl']}
    return top,[p for p in top if p['id'] not in hs]
for _d in DAYS[-2:]:
    _t,_r=day_top(_d)
    if len(_d['summary'])!=3: print('WARN 三句话不是 3 条:',_d['date'],len(_d['summary']))
    _m=[p['id'] for p in _r if p['en'] and p['id'] not in _d['gists']]
    if _m: print('WARN 缺英文一句话要点 gists:',_d['date'],len(_m),'条',_m[:5])
    for _h in _d['hl']:
        if _h['orig'] and is_en(_h['orig']) and not _h['orig_zh']: print('WARN 缺译文 excerpt_zh:',_d['date'],_h['handle'])

# ---- 草稿模式：XHOT_DRAFT=YYYY-MM-DD → 只打印当天候选（规则评分 Top 40）后退出，不写站点 ----
if os.environ.get('XHOT_DRAFT'):
    _k=os.environ['XHOT_DRAFT']; _d=next((x for x in DAYS if x['date']==_k),None) or dict(date=_k,hl=[],hide=[],pin=[],gists={})
    _rows=rank(inwin(_k),40,2,_d['hide'],_d['pin'])
    print(json.dumps([dict(id=p['id'],handle=ACC[p['u']]['H'],name=ACC[p['u']]['name'],url=xlink(ACC[p['u']]['H'],p['id']),likes=p['like'],heat=p['heat'],score=p['score'],domain=pdom(p),tags=p['tags'],
          is_english=p['en'],created_at=p['ts'],excerpt=excerpt(p['t'],EXCH),has_gist=p['id'] in _d.get('gists',{})) for p in _rows],ensure_ascii=False,indent=1)); sys.exit(0)
def gist_of(p,G):
    g=G.get(p['id'])
    if g: return g,False
    return clean1(p['ex'],100),p['en']

# ---- 周要点草稿模式：XHOT_WEEKLY=1 → 打印本周 Top 30 人物及其最热 3 帖摘录后退出 ----
if os.environ.get('XHOT_WEEKLY'):
    _o=[]
    for a in wk_people():
        _t=sorted(a['p7'],key=lambda p:-p['score'])[:3]
        _o.append(dict(handle=a['H'],name=a['name'],domains=a['doms'],followers=a['f'],week_posts=len(a['p7']),top=[dict(id=p['id'],likes=p['like'],score=p['score'],is_english=p['en'],excerpt=excerpt(p['t'],200)) for p in _t]))
    iso=NOW.isocalendar(); print(json.dumps(dict(week=f'{iso[0]}-W{iso[1]:02d}',people=_o),ensure_ascii=False,indent=1)); sys.exit(0)
# ---- 今日页 ----
def dhl(h,pref,n=0,k=''):
    u=h['handle'].lower(); a=ACC.get(u)
    who=(f'<a class="hh" href="{pref}p/{u}.html">{av(u,a["name"],"",pref,n<6)}<b>{e(a["name"])}</b><small>@{e(a["H"])}</small></a>' if a
         else f'<a class="hh" href="{safe_url("https://x.com/"+h["handle"])}" target="_blank" rel="noopener noreferrer"><b>{e(h["name"])}</b><small>@{e(h["handle"])}</small></a>')
    lk=f'<a class="btn op" href="{safe_url(h["url"])}" target="_blank" rel="noopener noreferrer">原帖 ↗</a>'
    lv=f'<span class="lk">♥ {fmt(h["likes"])}</span>' if h['likes'] is not None else '<span class="lk"></span>'
    og,oz=h['orig'],h['orig_zh']; ex=cp=ob=''
    if og:
        zh=bool(oz) and is_en(og); did=f'o{k}-{n}'
        ex=f'<button class="btn ex" type="button" aria-expanded="false" aria-controls="{did}">展开</button>'
        cp=f'<button class="btn cp" type="button" data-l="{"复制译文" if zh else "复制摘录"}">{"复制译文" if zh else "复制摘录"}</button>'
        if zh:
            hd=('<div class="dorh"><span class="dlab">原帖摘录</span><span class="trb" title="中文为译文，仅供参考，以原文为准">译</span>'
                '<div class="seg sm" role="group" aria-label="语言"><button type="button" data-ol="zh" class="on" aria-pressed="true">中</button><button type="button" data-ol="en" aria-pressed="false">EN</button></div></div>')
            tx=f'<div class="pt ptz" lang="zh-CN">{lnk(oz)}</div><div class="pt pto" lang="en" hidden>{lnk(og)}</div>'
        else:
            hd='<div class="dorh"><span class="dlab">原帖摘录</span></div>'; tx=f'<div class="pt pto">{lnk(og)}</div>'
        ob=f'<div class="dor" id="{did}" hidden>{hd}{tx}<p class="dnote">摘录自原帖，全文请点「原帖 ↗」。</p></div>'
    p=PBY.get(h['pid']); ts=f' data-ts="{zts(p["ts"])}"' if p else ''
    return f'<li class="dh fi" style="--dc:{DC[a["dom"]] if a else "var(--ac)"}" data-dom="{" ".join(a["doms"]) if a else ""}" data-tags="{" ".join(h["tags"])}" data-k="{e(str(h["pid"]))}"{ts}>{who}<div class="dha">{lv}{ex}{cp}{lk}</div><p class="dsm">{e(h["text"])}</p>{("<div class=tcs>"+tcs(h["tags"])+"</div>") if h["tags"] else ""}{ob}</li>'
def t30row(p,rk,G,pref,eager=False):
    a=ACC[p['u']]; dom=pdom(p); g,en=gist_of(p,G)
    return (f'<li class="trw fi" style="--dc:{DC[dom]}" data-dom="{" ".join(a["doms"])}" data-tags="{" ".join(p["tags"])}" data-ts="{zts(p["ts"])}" data-k="{p["id"]}"><details><summary><span class="rk">{rk}</span>{av(p["u"],a["name"],"s",pref,eager)}'
            f'<span class="trbd"><span class="trh"><b>{e(a["name"])}</b><small>@{e(a["H"])}</small>{tcs(p["tags"])}</span><span class="trg">{"<i class=en>EN</i>" if en else ""}{e(g)}</span></span><span class="trm">🔥 {fmt(p["heat"])}</span></summary>'
            f'<div class="trx"><div class="pt"{" lang=en" if p["en"] else ""}>{lnk(p["ex"])}</div><div class="act"><a class="btn" href="{pref}p/{p["u"]}.html">看 {e(a["name"])} 主页</a><button class="btn cp" type="button" data-l="复制摘录">复制摘录</button><a class="btn op" href="{safe_url(xlink(a["H"],p["id"]))}" target="_blank" rel="noopener noreferrer">在 X 打开 ↗</a></div></div></details></li>')
def mini_trends():
    T=[(x,d) for d in DOMS for x in DATA[d]['trends']]; T.sort(key=lambda z:-z[0]['g'])
    pick=T[:4]+[z for z in T[::-1][:2] if z[0]['g']<0]
    return ''.join(f'<li><a href="{turl(x)}" target="_blank" rel="noopener noreferrer"><span class="tn">{e(x["name"])}<i class="tag" style="--dc:{DC[d]}">{DN[d]}</i></span><b class="{"up" if x["g"]>=0 else "dn"}">{x["g"]:+.0f}%</b></a></li>' for x,d in pick)
def mini_fol(pref=''):
    L=[a for a in ACC.values() if a['d']]; L.sort(key=lambda a:-a['d'])
    pick=L[:3]+[a for a in L[::-1][:2] if a['d']<0]
    return ''.join(f'<li><a href="{pref}p/{a["u"]}.html">{av(a["u"],a["name"],"s",pref)}<span class="tn">{e(a["name"])}</span><b class="{"up" if a["d"]>0 else "dn"}">{a["d"]:+,}</b></a></li>' for a in pick)
def today_page(i,pref):
    d=DAYS[i]; k=d['date']; latest=i==len(DAYS)-1
    top,rest=day_top(d); G=d['gists']
    hl=''.join(dhl(h,pref,n,k) for n,h in enumerate(d['hl']))
    mins=max(3,round(2+(sum(len(x) for x in d['summary'])+sum(len(h['text']) for h in d['hl'])+sum(len(gist_of(p,G)[0]) for p in rest))/320))
    brief=(f'<section class="brief" aria-label="今日三句话"><h2>今天一眼看完</h2><ol class="b3">'+''.join(f'<li>{e(x)}</li>' for x in d['summary'])+'</ol></section>') if d['summary'] else ''
    dom_cnt={x:sum(1 for p in rest if x in ACC[p['u']]['doms']) for x in DOMS}
    chips=('<div class="seg" role="group" aria-label="领域"><button type="button" data-dom="all" class="on" aria-pressed="true">全部 '+str(len(rest))+'</button>'
           +''.join(f'<button type="button" data-dom="{x}" style="--dc:{DC[x]}" aria-pressed="false"><i class="dot"></i>{DN[x]} {dom_cnt[x]}</button>' for x in DOMS if dom_cnt[x])+'</div>')
    rows=''.join(t30row(p,j,G,pref,j<=3) for j,p in enumerate(rest,len(d['hl'])+1))
    news5=''
    if latest and NEWS:
        tops=ntop(NEWS)[:5]
        news5=('<section class="panel dsec"><h2>资讯头条 <a class="more2" href="'+pref+'news.html">全部资讯 →</a></h2><ol class="dn">'
               +''.join(f'<li><a href="{pref}news.html#n={j}"><span class="src {NEWS[j]["s"]}">{NEWS[j]["sl"]}</span><b>{e(NEWS[j]["t"])}</b></a></li>' for j in tops)+'</ol></section>')
    cl=('<details class="panel dsec dcl"><summary>更新日志 <small>'+str(len(d['cl']))+' 条</small></summary><ul>'+''.join(f'<li>{f"<time>{e(dd)}</time>" if dd else ""}{e(t)}</li>' for dd,t in d['cl'])+'</ul></details>') if d['cl'] else ''
    dates=[x['date'] for x in reversed(DAYS)]
    side_t=f'<section class="panel dsec"><h2>话题涨跌 <a class="more2" href="{pref}trends.html">趋势 →</a></h2>'+(f'<ul class="mt">{mini_trends()}</ul>' if latest else '')+(f'<p>{e(d["topics"])}</p>' if d['topics'] else '')+'</section>'
    side_f=f'<section class="panel dsec"><h2>粉丝变化 <a class="more2" href="{pref}people.html#sort=d">人物 →</a></h2>'+(f'<ul class="mt mf">{mini_fol(pref)}</ul>' if latest else '')+(f'<p>{e(d["fol"])}</p>' if d['fol'] else '')+'</section>'
    mid=f'<span class="ddl" data-d="{k}">{dsub(k)}</span>'+('<span class="dnew">最新</span>' if latest else '')+'<span class="hint">每天北京时间 08:00 更新 · 过去 24 小时</span>'
    body=(f'<div id="daily" class="dly" data-day="{k}">'+tools('今日',mid,dctl(dates,'nav',k,pref+'day/{d}.html'),f'约 {mins} 分钟读完 · 必读 {len(d["hl"])} 条 + 更多 {len(rest)} 条 = 今日 Top {len(top)} <span class="newc" id="newc" hidden></span>')+brief+
          f'<div class="dgrid"><div class="dmain"><section class="sec"><h2>必读 <small>{len(d["hl"])} 条 · 按点赞</small></h2><ol class="dhl">{hl}</ol></section>'
          f'<section class="sec" id="t30"><div class="sech"><h2>更多值得看 <small>Top 30 余下 {len(rest)} 条 · 点开看摘录</small></h2>{chips}</div><ol class="tl30" data-fl>{rows}</ol><p class="empty" hidden>这个领域今天没有更多入选。</p></section></div>'
          f'<aside class="dside">{side_t}{side_f}{news5}{cl}</aside></div></div>')
    return page(f'XHOT · 今日 {k}',body,'today',pref=pref,desc=(d['summary'][0] if d['summary'] else 'XHOT 今日'))
# ---- 领域页 ----
DOMD={'ai':'模型、智能体、编程工具、芯片与监管——AI 圈这一周的重点。','money':'创业、创作者、融资与独立开发——能落地赚钱的信号。','growth':'习惯、写作、职业与认知——长期复利的方法。'}
def dom_posts(d,days=7):
    cut=Zs(NOW-datetime.timedelta(days=days))
    return [p for p in POSTS if d in ACC[p['u']]['doms'] and p['ts'][:19]>=cut]
def domain_page(d):
    rows=dom_posts(d); 
    if len(rows)<12: rows=dom_posts(d,14)
    top=rank(rows,24,2)
    cnt={}
    for p in rows:
        for t in p['tags']:
            if TAGD[t]==d or True: cnt[t]=cnt.get(t,0)+1
    keys=[k for k,_,dd,_ in TAGS if dd==d]+[k for k,_,dd,_ in TAGS if dd!=d and cnt.get(k,0)>=3]
    keys=[k for k in keys if cnt.get(k,0)>0][:9]
    cards=''.join(post_html(p,'../',True,j<4) for j,p in enumerate(top))
    ppl=sorted([a for a in ACC.values() if d in a['doms']],key=lambda a:-(a['top3']+3*math.log10(max(a['f'],10))))[:10]
    pl=''.join(f'<li><a href="../p/{a["u"]}.html">{av(a["u"],a["name"],"s","../")}<span class="tn"><b>{e(a["name"])}</b><small>{fmt(a["f"])} 粉丝{"" if not a["d"] else f" · {a["d"]:+,}"}</small></span></a></li>' for a in ppl)
    tr=DATA[d]['trends']; mx=max([abs(x['g']) for x in tr] or [1])
    trl=trows([(x,d) for x in sorted(tr,key=lambda x:-x['g'])[:8]],mx)
    nl=''
    if NEWS:
        idx=[j for j,n in enumerate(NEWS) if n['s']=='h'][:5] if d=='ai' else [j for j,n in enumerate(NEWS) if any(w.lower() in (n['t']+n['sm']).lower() for w in KW.get(d,[]))][:5]
        nl=''.join(f'<li><a href="../news.html#n={j}"><span class="src {NEWS[j]["s"]}">{NEWS[j]["sl"]}</span><b>{e(NEWS[j]["t"])}</b></a></li>' for j in idx)
    nsec=f'<section class="panel dsec"><h2>相关资讯 <a class="more2" href="../news.html">全部 →</a></h2><ol class="dn">{nl}</ol></section>' if nl else ''
    nu=len({p['u'] for p in rows})
    body=(tools(DN[d],seg_links(d,'../'),'',f'{DOMD[d]} 近 {"7" if len(dom_posts(d))>=12 else "14"} 天 {len(rows)} 条帖子 · 来自 {nu} 位 · 每人最多 2 条')+
          f'<div class="dgrid"><div class="dmain"><section class="sec"><div class="sech"><h2>本周最重要 <small>Top {len(top)} · 重要度排序</small></h2>{tag_chips(keys,cnt)}</div><div class="grid" data-fl>{cards}</div><p class="empty" hidden>没有符合这个标签的帖子。</p></section></div>'
          f'<aside class="dside"><section class="panel dsec"><h2>必关注 {len(ppl)} 人 <a class="more2" href="../people.html#dom={d}">全部 →</a></h2><ul class="pl">{pl}</ul></section>'
          f'<section class="panel dsec"><h2>话题涨跌 <a class="more2" href="../trends.html">趋势 →</a></h2><ul class="list tl">{trl}</ul></section>{nsec}</aside></div>')
    return page(f'XHOT · {DN[d]}',body,'dom',pref='../',desc=DOMD[d])
# ---- 全部归档（旧「热帖」）----
FEEDDAYS=[]
def feed_shards():
    by={}
    for p in POSTS: by.setdefault(dkey(p['ts']),[]).append(p)
    out=[]
    for k in sorted(by,reverse=True):
        if len(by[k])<8 or len(out)>=30: continue
        rows=sorted(by[k],key=lambda p:-p['score'])[:200]
        data=jdump([[p['id'],zts(p['ts']),p['ex'],p['like'],p['rt'],p['reply'],p['quote'],p['view'],p['heat'],p['score'],p['u'],','.join(p['tags']),1 if p['en'] else 0] for p in rows])
        h=H8(data); put(f'{k}.{h}.json',data,os.path.join(OUT,'feed')); out.append([k,h,len(by[k])])
    return out
def all_page():
    rows=dom_posts('ai',7)+dom_posts('money',7)+dom_posts('growth',7)
    seen=set(); rr=[]
    for p in sorted(rows,key=lambda p:-p['score']):
        if p['id'] not in seen: seen.add(p['id']); rr.append(p)
    top=rank(rr,24,3)
    cards=''.join(post_html(p,'../',True,j<4) for j,p in enumerate(top))
    days=[x[0] for x in FEEDDAYS]
    mid=(seg_dom()+'<input type="search" id="hq" aria-label="搜索帖子" placeholder="搜索摘录 / 人物…" autocomplete="off" spellcheck="false">')
    srt='<div class="seg" role="group" aria-label="排序"><button type="button" data-sort="s" class="on" aria-pressed="true">重要度</button><button type="button" data-sort="t" aria-pressed="false">时间</button></div>'
    body=(tools('全部归档',mid,dctl(days,'state','','',alllab='最近 7 天')+srt,'按天分片加载 · 站内只存摘录，全文请点「在 X 打开」')+
          '<div class="tinfo"><span id="cnt" aria-live="polite">最近 7 天 · 重要度排序 · 每人最多 3 条</span></div>'
          f'<div id="feed" class="grid" data-pre="{len(top)}">{cards}</div><button id="more" class="more" type="button">再显示</button>')
    return page('XHOT · 全部归档',body,'dom',pref='../',head='',mods=('feed',),desc='全部帖子归档：按天、按领域、按重要度浏览。')
# ---- 人物 ----
def pgist(a):
    b=((WK.get('people') or {}).get(a['u']) or {}).get('bullets') or []
    if b: return str(b[0])[:90],False
    p=a['last']
    if p and p['ts'][:19]>=WEEK: return clean1(p['ex'],80),p['en']
    return '本周没有新帖',False
def people_page():
    sec=[];n=0
    for a in sorted(ACC.values(),key=lambda a:-a['f']):
        g,en=pgist(a); n+=1
        dv='' if a['d'] is None else f'<span class="dv {"up" if a["d"]>0 else "dn" if a["d"]<0 else ""}">{"+" if a["d"]>0 else ""}{a["d"]:,}</span>'
        tg=sorted({t for p in a['p7'] for t in p['tags']},key=lambda t:-sum(1 for p in a['p7'] if t in p['tags']))[:2]
        sec.append(f'<a class="pc fi" href="p/{a["u"]}.html" style="--dc:{DC[a["dom"]]}" data-dom="{" ".join(a["doms"])}" data-f="{a["f"]}" data-d="{a["d"] or 0}" data-w="{a["top3"]}" data-q="{e((a["name"]+" "+a["u"]).lower())}">{av(a["u"],a["name"],"l","",n<=12)}'
                   f'<span class="an"><b>{e(a["name"])}</b><small>@{e(a["H"])}</small></span><span class="af">{"".join(f"<span class=tag style=--dc:{DC[x]}>{DN[x]}</span>" for x in a["doms"])}<span class="fv">{fmt(a["f"])}</span>{dv}</span>'
                   f'<span class="pcs">{"<i class=en>EN</i>" if en else ""}{e(g)}</span></a>')
    wp=wk_people(); wl=''
    for j,a in enumerate(wp):
        b=((WK.get('people') or {}).get(a['u']) or {}).get('bullets') or []
        if not b:
            g,en=pgist(a); b=[g]
        li=''.join(f'<li>{e(str(x)[:100])}</li>' for x in b[:2])
        wl+=f'<li class="wk fi" data-dom="{" ".join(a["doms"])}"><a class="wkh" href="p/{a["u"]}.html">{av(a["u"],a["name"],"",'',j<6)}<b>{e(a["name"])}</b><small>@{e(a["H"])}</small></a><ul>{li}</ul></li>'
    wkh=WK.get('week','')
    body=(tools('人物',seg_dom()+'<input type="search" id="aq" aria-label="搜索人物" placeholder="搜索人物…" autocomplete="off" spellcheck="false">',
                '<div class="seg" role="group" aria-label="排序"><button type="button" data-asort="f" class="on" aria-pressed="true">粉丝数</button><button type="button" data-asort="w" aria-pressed="false">本周热度</button><button type="button" data-asort="d" aria-pressed="false">粉丝变化</button></div>',
                f'<span id="acnt">{len(ACC)} 人</span> · 点卡片看他这周说了什么')+
          f'<section class="sec wks"><h2>本周关注 Top 30 <small>{e(wkh)} · 每周一更新要点 · 按本周最热 3 帖得分</small></h2><ol class="wkg">{wl}</ol></section>'
          f'<section class="sec"><h2>全部人物 <small>{len(ACC)}</small></h2><div id="ag" class="agrid" data-fl="p">{"".join(sec)}</div><p class="empty" hidden>没有匹配的人物。</p></section>')
    return page('XHOT · 人物',body,'ppl',desc='追踪的 AI / 搞钱 / 成长领域人物与他们本周说了什么。')
def person(u):
    a=ACC[u]; pr=PROF.get(u,{}); H=a['H']
    ps=[p for p in POSTS if p['u']==u]; ps.sort(key=lambda p:p['ts'],reverse=True)
    rows=[[p['id'],zts(p['ts']),p['ex'],p['like'],p['rt'],p['reply'],p['quote'],p['view'],p['heat'],p['score'],','.join(p['tags']),1 if p['en'] else 0] for p in ps]
    data=jdump(rows); jn=f'{u}.{H8(data)}.json'
    write(f'p/{jn}',data)
    c30=Zs(NOW-datetime.timedelta(days=30))
    hi=rank([p for p in ps if p['ts'][:19]>=c30],4,4)
    first=ps[:12]; pdays=sorted({dkey(p['ts']) for p in ps},reverse=True)
    dl='—' if a['d'] is None else f'{a["d"]:+,}'
    bio=f'<p class="bio">{e(re.sub(r"\s*https?://t\.co/\w+","",pr["description"]).strip())}</p>' if re.sub(r"\s*https?://t\.co/\w+","",pr.get('description') or '').strip() else ''
    tags=''.join(f'<span class="tag" style="--dc:#fff">{DN[d]}</span>' for d in a['doms'])
    b=((WK.get('people') or {}).get(u) or {}).get('bullets') or []
    if b: wkb=''.join(f'<li>{e(str(x)[:140])}</li>' for x in b[:3]); wkn='本周要点'
    elif a['p7']:
        t=a['last']; wkb=f'<li>近 7 天发了 {len(a["p7"])} 条；最热一条：{e(clean1(t["ex"],80))}</li>'; wkn='本周概览（自动）'
    else: wkb='<li>近 7 天没有新帖。</li>'; wkn='本周概览'
    tc={}
    for p in ps:
        if p['ts'][:19]>=c30:
            for t in p['tags']: tc[t]=tc.get(t,0)+1
    tgl=''.join(f'<span class="tc">{e(TAGL[t])} <small>{n}</small></span>' for t,n in sorted(tc.items(),key=lambda z:-z[1])[:4]) or '<span class="mu">暂无标签</span>'
    days14=[(NOW-datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(13,-1,-1)]
    cnt14=[sum(1 for p in ps if dkey(p['ts'])==x) for x in days14]
    avg=int(sum(p['heat'] for p in ps[:30])/max(1,len(ps[:30])))
    glance=(f'<section class="glance" aria-label="一屏读懂"><div class="gl1"><h2>{wkn}</h2><ul>{wkb}</ul></div><div class="gl2"><h2>近 30 天话题</h2><div class="tcs">{tgl}</div><h2 class="g2">近 14 天节奏</h2>{minimap(cnt14)}</div>'
            f'<div class="gl3"><div class="chip"><b>{fmt(a["f"])}</b><span>粉丝</span></div><div class="chip"><b>{dl}</b><span>较上次</span></div><div class="chip"><b>{len(a["p7"])}</b><span>近 7 天发帖</span></div><div class="chip"><b>{fmt(avg)}</b><span>近 30 条平均热度</span></div></div></section>')
    hcards=''.join(post_html(p,'../',False) for p in hi)
    feed=''.join(post_html(p,'../',False) for p in first) if ps else '<div class="empty">这个账号暂时没有可显示的推文：可能是受保护账号，或者近期没有发原创帖。</div>'
    srt='<div class="seg" role="group" aria-label="排序"><button type="button" data-sort="t" class="on" aria-pressed="true">时间</button><button type="button" data-sort="s" aria-pressed="false">重要度</button></div>'
    body=(f'<section class="phc">{av(u,a["name"],"xl","../",True)}<div style="min-width:0"><h1>{e(a["name"])}<small translate="no">@{e(H)}</small>{tags}</h1>{bio}</div><div class="chips"><a class="xb" href="https://x.com/{e(H)}" target="_blank" rel="noopener noreferrer">在 X 查看 ↗</a></div></section>'+glance+
          '<i id="rdy" hidden></i>'+(f'<section class="sec"><h2>高光帖 <small>近 30 天 · 重要度前 {len(hi)}</small></h2><div class="grid hi4">{hcards}</div></section>' if hi else '')+
          '<section class="sec" id="tl">'+tools('全部推文',f'<input id="q" type="search" aria-label="搜索推文" placeholder="搜索 {e(a["name"])} 的推文摘录…" autocomplete="off" spellcheck="false">',dctl(pdays)+srt,f'<span class="cnt" id="cnt" aria-live="polite">共 {len(ps)} 条摘录</span>',h='h2')+
          f'<div id="feed" class="grid pgrid" data-pre="{len(first)}" data-total="{len(ps)}" data-mode="t">{feed}</div><button id="more" class="more" type="button" hidden>再显示</button></section>'
          f'<script type="application/json" id="tw-meta">{jsafe({"name":a["name"],"handle":H,"u":u,"dom":a["dom"],"av":AVS.get(u,""),"h":hue(u),"src":jn,"week":WEEK})}</script>')
    return page(f'{a["name"]} (@{H}) · XHOT',body,'ppl',pref='../',mods=('feed',),desc=f'{a["name"]} 本周要点与高光帖。')

def about_page():
    L=lambda u,t:f'<a href="{u}" target="_blank" rel="noopener noreferrer">{t}</a>'
    body=(f'<h1 class="ph1">关于 XHOT</h1><p class="lead">XHOT 是一个纯静态的个人项目：每天一次，把 X 上 AI / 搞钱 / 成长领域 {len(ACC)} 个公开账号的热点整理成 10 分钟能读完的简报。没有登录、没有广告、没有统计脚本、没有第三方请求。</p>'
      '<section class="abt"><h2>数据来源</h2><ul>'
      f'<li><b>X</b>：通过 X 官方 API（只读，开发者账号授权）获取公开帖子与账号资料。站内展示的是<b>短摘录</b>、互动数字和指向原帖的链接；每条都可点「在 X 打开」查看完整原文。{L("https://developer.x.com/en/developer-terms/agreement-and-policy","X 开发者协议与政策")}适用于这些内容。头像为小尺寸缓存，仅用于标识作者。</li>'
      f'<li><b>AIHOT</b>：资讯页的精选与热点来自 {L("https://aihot.news","aihot.news")} 的公开 API，按其 MIT 许可使用并署名；文章原文版权属于原站，本站只给链接。许可声明见仓库中的 LICENSE-THIRD-PARTY.md。</li>'
      f'<li><b>GitHub Trending</b>：趋势页读取 {L("https://github.com/trending","GitHub Trending")} 公开页面中的项目名与星标数，只做索引并链接到项目主页，不转载项目内容；每日一次，不做高频抓取。</li>'
      '</ul></section>'
      '<section class="abt"><h2>哪些内容是 AI 生成的</h2><ul>'
      '<li>「今天一眼看完」「必读」中的<b>中文要点</b>、英文帖的<b>中文译文</b>（带「译」标记）、人物「本周要点」和话题解读，均由 AI 助手自动整理，<b>不是 X 官方内容，也不代表原作者的表述</b>，可能有误；以原帖为准。</li>'
      '<li>热度、重要度、标签是公开的规则公式 / 关键词规则计算的结果，不是 X 官方排名。</li></ul></section>'
      '<section class="abt"><h2>内容撤下与合规</h2><ul>'
      '<li>每天刷新一次；X 已删除、改为受保护或不再可获取的帖子，会在下一轮刷新后撤下。站点另有一份撤下清单，可按帖子或账号即时屏蔽。</li>'
      f'<li>如果你是原作者或相关方，希望撤下某条内容、头像或整个账号，请在 {L("https://github.com/88daxiong/xhot/issues","GitHub Issues")} 留言（只需给出帖子或账号链接，不要提供个人隐私信息），我们会尽快处理。</li>'
      '<li>站内不收集访客信息：偏好（主题、密度、已读标记）只保存在你自己的浏览器里。</li></ul></section>'
      '<section class="abt"><h2>免责声明</h2><p>XHOT 与 X Corp.、AIHOT、GitHub 没有隶属、授权或背书关系；X、Twitter、GitHub 及相关标识属于各自所有者。内容仅供信息参考，不构成投资、法律或其他专业建议；数据可能延迟或不完整，请以原始来源为准。站点托管在 GitHub Pages，并遵守其服务条款与可接受使用政策。</p></section>'
      f'<p class="mu">代码与说明：{L("https://github.com/88daxiong/xhot","github.com/88daxiong/xhot")} · 当前数据抓取于 {NOW.strftime("%Y-%m-%d %H:%M")} 北京时间</p>')
    return page('关于 · 数据来源 · 免责声明 · XHOT',body,'about',desc='XHOT 的数据来源、AI 生成内容说明、撤下方式与免责声明。')
# ======================= 生成全部页面 =======================
open_ok=True
emit('about.html',about_page()); emit('news.html',news()); emit('trends.html',trends())     # news() 先跑：NEWS 供今日页/领域页引用
FEEDDAYS=feed_shards()
for old in glob.glob(os.path.join(OUT,'p','*.html')): pass
if DAYS:
    emit('index.html',today_page(len(DAYS)-1,''))
    for i,x in enumerate(DAYS): emit(f'day/{x["date"]}.html',today_page(i,'../'))
else:
    emit('index.html',page('XHOT · 今日','<div id="daily" class="empty">还没有日报，先看 <a href="d/all.html">全部归档</a>。</div>','today'))
for d in DOMS: emit(f'd/{d}.html',domain_page(d))
emit('d/all.html',all_page()); emit('people.html',people_page())
for u in ACC: emit(f'p/{u}.html',person(u))
# 旧链接跳转页
def stub(to): return f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url={to}"><link rel="icon" href="data:,"><meta name="robots" content="noindex"><title>已移动</title></head><body><p>页面已移动：<a href="{to}">{to}</a></p></body></html>'
emit('hot.html',stub('d/all.html')); emit('accounts.html',stub('people.html'))
for x in DAYS: emit(f'daily/{x["date"]}.html',stub(f'../day/{x["date"]}.html'))
# 搜索索引（⌘K：人物 / 标签 / 话题 / 日期；帖子按需读 feed 分片）
SJ=jdump({'p':[[u,a['H'],a['name'],AVS.get(u,''),hue(u),a['dom'],','.join(a['doms']),a['f'],a['d'] or 0] for u,a in ACC.items()],
          't':[[k,l,d] for k,l,d,_ in TAGS],'d':FEEDDAYS,'dy':[x['date'] for x in DAYS],'tp':[[x['name'],d] for d in DOMS for x in DATA[d]['trends']]})
SJN=f'search.{H8(SJ)}.json'; put(SJN,SJ)
# ---- JS / CSS ----
JSN={}
for m in ('core','news','feed'):
    src=open(f'app_{m}.js',encoding='utf-8').read(); JSN[m]=f'{m}.{H8(src)}.js'; put(JSN[m],src)
TOK=re.compile(r'[A-Za-z_][\w-]*')
JSTOK={m:set(TOK.findall(open(f'app_{m}.js',encoding='utf-8').read())) for m in ('core','news','feed')}
def _split(s,ch=','):
    out=[];d=0;cur=''
    for c in s:
        if c in '([': d+=1
        elif c in ')]': d-=1
        if c==ch and d==0: out.append(cur);cur=''
        else: cur+=c
    out.append(cur); return out
def purge(css,corpus):
    out=[];i=0;n=len(css)
    while i<n:
        j=css.find('{',i)
        if j<0: out.append(css[i:]);break
        pre=css[i:j]; d=1;k=j+1
        while k<n and d: d+= (css[k]=='{')-(css[k]=='}'); k+=1
        body=css[j+1:k-1]; ps=pre.strip()
        if ps.startswith('@media') or ps.startswith('@supports'):
            b=purge(body,corpus)
            if b.strip(): out.append(f'{ps}{{{b}}}')
        elif ps.startswith('@'): out.append(f'{ps}{{{body}}}')
        else:
            keep=[s for s in _split(ps) if all(t in corpus for t in re.findall(r'[.#]([A-Za-z_][\w-]*)',re.sub(r'\[[^\]]*\]|"[^"]*"','',s)))]
            if keep: out.append(','.join(x.strip() for x in keep)+'{'+body.strip()+'}')
        i=k
    return ''.join(out)
CSSR=(open('style_base.css',encoding='utf-8').read()+'\n'+open('style.css',encoding='utf-8').read()).replace('$SANS',SANS)
def readable(css):
    """可读性变换（构建期，不动 v14 源 CSS）：字号整体 +1px（≤11.5→12；12/12.5→13；13→14；…；≥20 不变）、字距归零、字重只留 400/500/600、渐变文字改纯色"""
    def fs(m):
        v=float(m.group(2)); n=12 if v<=11.5 else 13 if v<=12.5 else v+1 if v<=18 else v
        return m.group(1)+(str(int(n)) if n==int(n) else str(n))+'px'
    css=re.sub(r'(font-size:)(\d+(?:\.\d+)?)px',fs,css)
    css=re.sub(r'(font:(?:\d{3} )?)(\d+(?:\.\d+)?)px',fs,css)
    css=re.sub(r'letter-spacing:[^;}]*','letter-spacing:0',css)
    def fw(m):
        v=int(m.group(1)); return 'font-weight:'+('400' if v<=400 else '500' if v<=550 else '600')
    css=re.sub(r'font-weight:(\d{3})',fw,css)
    css=css.replace('font-weight:bold','font-weight:600').replace('font-weight:normal','font-weight:400')
    return css
CSSR=readable(CSSR)+'\n'+open('style_final.css',encoding='utf-8').read()
CSSR=re.sub(r'/\*.*?\*/','',CSSR,flags=re.S); CSSR=re.sub(r'\s*\n\s*','',CSSR)
CSSBYKEY={}
def page_css(html):
    mods=set(re.findall(r'@@JS:(\w+)@@',html))|{'core'}
    cp=set(TOK.findall(re.sub(r'<script.*?</script>','',html,flags=re.S)))
    for m in mods: cp|=JSTOK[m]
    k=hash(frozenset(cp))
    if k not in CSSBYKEY: CSSBYKEY[k]=purge(CSSR,cp)
    return CSSBYKEY[k]
_sizes=[]
for rel,html in PAGES.items():
    _c=page_css(html); _sizes.append(len(_c.encode())); html=html.replace('@@CSS@@','<style>'+_c+'</style>',1).replace('@@SJ@@',SJN)
    for m,nm in JSN.items(): html=html.replace(f'@@JS:{m}@@',nm)
    write(rel,html)
print('inline css/page: min',min(_sizes),'max',max(_sizes),'raw',len(CSSR))
write('_headers',"""/*
  Content-Security-Policy: """+CSP+"""; frame-ancestors 'none'
  Referrer-Policy: strict-origin-when-cross-origin
  X-Content-Type-Options: nosniff
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  Permissions-Policy: camera=(), microphone=(), geolocation=()
/assets/*
  Cache-Control: public, max-age=31536000, immutable
/feed/*
  Cache-Control: public, max-age=31536000, immutable
/p/*.json
  Cache-Control: public, max-age=31536000, immutable
""")
# 清理：只保留本次产出的文件
for root,ds,fs in os.walk(OUT,topdown=False):
    for f in fs:
        p=os.path.abspath(os.path.join(root,f))
        if p not in EMIT: os.remove(p)
    if root!=OUT and not os.listdir(root): os.rmdir(root)
print('v15: pages',len(PAGES),'| days',len(DAYS),'| people',len(ACC),'| feed shards',len(FEEDDAYS),'| posts',len(POSTS),'| avatars',len(AVF))

