#!/usr/bin/env python3
"""AI 开发工具：匿名抓 github.com/trending（daily+weekly × 全部/python/typescript/rust/go/javascript）
+ 可选 GitHub 公开搜索 API（不带 token，近 45 天新建、按星排序，6 个话题）。规则分类后写 raw/<ts>_devtools.json。
用法：python3 devtools_fetch.py [--no-search]   请求数：20 页 trending + 最多 20 次匿名搜索（每次间隔 7s）。"""
import urllib.request,urllib.parse,re,html,json,os,sys,datetime,time
D=os.path.dirname(os.path.abspath(__file__))
UA={'User-Agent':'Mozilla/5.0 xhot-devtools'}
def get(u,acc='text/html'):
    r=urllib.request.Request(u,headers={**UA,'Accept':acc});return urllib.request.urlopen(r,timeout=30).read().decode('utf-8','ignore')
def num(s): return int(re.sub(r'[^\d]','',s) or 0)
# 分类规则：按顺序匹配，取前两个命中作 tags；第一个为主标签。只看 仓库名 + 描述 + topics
# 分类规则（顺序 = 优先级，第一个命中为主标签，最多两个）。只看 仓库名 + 描述 + topics
RULES=[('fun',r'caveman|laziest|notch|tamagotchi|desktop.?pet|麦当劳|mcdonald|酒馆|tavern|\bgames?\b|\btoy\b|meme|pixel.?art|retro|ascii|emoji|pokemon|minecraft|doom|anime|silly|weird|key viewer|keeps? your macbook awake'),
 ('infra',r'sandbox|e2b|firecracker|micro.?vm|isolat|gateway|inference engine|serving|router|\bmemory\b|browser for ai|computer.?use|observab|tracing|ci/cd|rl environments|runtime'),
 ('mcp',r'\bmcp\b|model.?context.?protocol|plugins?\b|\bskills?\b|extensions?\b|slash.?command|subagents?|\bhooks?\b|awesome'),
 ('ops',r'orchestr|fleet|swarm|multi.?agent|parallel|worktree|dashboard|control.?plane|manag|menu bar|one place|monitor|kanban|team'),
 ('coding',r'claude.?code|codex|coding.?agent|code.?agent|copilot|cursor|aider|opencode|gemini.?cli|cline|vibe.?cod|swe.?agent|terminal|code.?review'),
 ('agent',r'\bagents?\b|agentic|harness|autonomous|assistant|\bllm\b|\bai\b|\bgpt|claude|openai|anthropic|deepseek|qwen|gemini')]
CAND=re.compile(r'agent|harness|mcp|claude|codex|copilot|sandbox|llm|\bai\b|gpt|coding|skills?\b|plugin|orchestr|e2b|inference|openai|anthropic|gemini|deepseek|qwen',re.I)
# 不收录：越狱/破解/反代/伪造证件/薅羊毛类
BLOCK=re.compile(r'jailbreak|nsfw|破甲|逆向工具|反代|2api|id cards|licenses, letters|crack|unrestricted|bypass|free-claude|支付接口|for free \(',re.I)
def classify(r):
    nd=(r['repo'].replace('/',' ').replace('-',' ').replace('_',' ')+' '+r['desc']).lower(); s=nd+' '+' '.join(r.get('topics',[])).lower()
    if BLOCK.search(nd): return []
    tags=[k for k,p in RULES if re.search(p,s)]
    if not CAND.search(nd): return ['fun'] if tags[:1]==['fun'] else []
    return tags[:2] or ['agent']
out={'repos':[],'calls':0};idx={}
def add(r):
    k=r['repo'].lower()
    if k in idx:
        o=idx[k]; o['today']=max(o['today'],r.get('today',0)); o['week']=max(o.get('week',0),r.get('week',0)); o['stars']=max(o['stars'],r['stars'])
        o['src']=sorted(set(o['src'])|set(r['src'])); o['topics']=o.get('topics') or r.get('topics',[]); o['created']=o.get('created') or r.get('created','')
        if not o['desc']: o['desc']=r['desc']
        return
    idx[k]=r; out['repos'].append(r)
for since in ['daily','weekly']:
    for lang in ['','python','typescript','rust','go','javascript','c++','swift','shell','jupyter-notebook']:
        try: t=get(f'https://github.com/trending/{lang}?since={since}'); out['calls']+=1
        except Exception as ex: print('WARN trending',lang,since,type(ex).__name__); continue
        for a in t.split('<article class="Box-row')[1:]:
            m=re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"',a)
            if not m: continue
            full=m.group(1).strip()
            d=re.search(r'<p class="col-9[^"]*">(.*?)</p>',a,re.S); desc=html.unescape(re.sub(r'<[^>]+>','',d.group(1))).strip() if d else ''
            l=re.search(r'itemprop="programmingLanguage">([^<]+)<',a)
            st=re.search(r'href="/'+re.escape(full)+r'/stargazers"[^>]*>.*?</svg>\s*([\d,]+)',a,re.S)
            td=re.search(r'([\d,]+) stars (today|this week)',a); n=num(td.group(1)) if td else 0
            add({'repo':full,'desc':desc,'lang':l.group(1).strip() if l else '','stars':num(st.group(1)) if st else 0,
                 'today':n if since=='daily' else 0,'week':n if since=='weekly' else 0,'url':'https://github.com/'+full,'src':[f'trending:{since}:{lang or "all"}'],'topics':[]})
        time.sleep(1)
def search(q,tag,n=20):
    qs=urllib.parse.quote(q)
    try: j=json.loads(get(f'https://api.github.com/search/repositories?q={qs}&sort=stars&order=desc&per_page={n}','application/vnd.github+json')); out['calls']+=1
    except Exception as ex: print('WARN search',tag,type(ex).__name__); return []
    time.sleep(7)   # 匿名搜索 10 次/分
    return j.get('items',[])
def addit(it,tag):
    add({'repo':it['full_name'],'desc':(it.get('description') or '').strip(),'lang':it.get('language') or '','stars':it.get('stargazers_count',0),'today':0,'week':0,
         'url':'https://github.com/'+it['full_name'],'src':[f'search:{tag}'],'topics':(it.get('topics') or [])[:8],'created':(it.get('created_at') or '')[:10]})
if '--no-search' not in sys.argv:
    d45=(datetime.date.today()-datetime.timedelta(days=45)).isoformat(); d14=(datetime.date.today()-datetime.timedelta(days=14)).isoformat()
    for q in ['agent','ai-agents','mcp','mcp-server','claude-code','codex','coding-agent','sandbox','llm-tools','agent-framework','multi-agent','browser-automation']:
        for it in search(f'topic:{q} created:>{d45} stars:>200',q): addit(it,q)
    for kw in ['agent','mcp','claude','codex']:   # 近 14 天新建、名称/描述含关键词（不要求打 topic）
        for it in search(f'{kw} in:name,description created:>{d14} stars:>80',kw+'14'): addit(it,kw+'14')
    # 趋势榜上的仓库补创建日期：一次搜索最多带 6 个 repo: 限定，只补今日/本周星增最多的 24 个
    need=sorted([r for r in out['repos'] if not r.get('created') and CAND.search(r['repo']+' '+r['desc'])],key=lambda r:-(r['today']*7+r['week']))[:24]
    for i in range(0,len(need),6):
        for it in search(' '.join('repo:'+r['repo'] for r in need[i:i+6]),'created',10):
            o=idx.get(it['full_name'].lower())
            if o: o['created']=(it.get('created_at') or '')[:10]; o['topics']=o.get('topics') or (it.get('topics') or [])[:8]
for r in out['repos']:
    r['tags']=classify(r); r['url']='https://github.com/'+r['repo']
out['repos']=[r for r in out['repos'] if r['tags'] and re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',r['repo'])]
out['_fetched_at']=datetime.datetime.now().astimezone().isoformat()
p=os.path.join(D,'raw',datetime.datetime.now().strftime('%Y%m%d_%H%M%S')+'_devtools.json');json.dump(out,open(p,'w'),ensure_ascii=False,indent=1)
from collections import Counter
print(p,'calls',out['calls'],'repos',len(out['repos']),dict(Counter(r['tags'][0] for r in out['repos'])))
