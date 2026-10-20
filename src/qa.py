"""v15 内容 QA：python3 qa.py [site_dir]  —— 重复项、空区块、未翻译英文（关键区域）、领域错配、坏标签。输出问题清单，无问题则 OK。"""
import sys,os,re,glob,json,collections
from bs4 import BeautifulSoup
S=sys.argv[1] if len(sys.argv)>1 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'site')
CJK=re.compile('[\u4e00-\u9fff]'); issues=[]
def P(f): return BeautifulSoup(open(f,encoding='utf-8').read(),'html.parser')
def bad(f,m): issues.append(os.path.relpath(f,S)+' '+m)
TAGS={'model','agent','code','oss','product','research','chips','policy','startup','creator','funding','indie','habit','write','career'}
for f in sorted(glob.glob(S+'/*.html')+glob.glob(S+'/day/*.html')+glob.glob(S+'/d/*.html')+glob.glob(S+'/p/*.html')):
    s=P(f)
    if s.find('meta',attrs={'http-equiv':'refresh'}): continue
    ks=[(id(x.find_parent(attrs={'role':'tabpanel'}) or x.find_parent('section')),x['data-k']) for x in s.select('[data-k]')]   # 同一区块内不得重复（人物页的高光帖会在时间线再出现，属设计）
    dup=[k for k,c in collections.Counter(ks).items() if c>1]
    if dup: bad(f,f'重复帖子 {dup[:3]}')
    for ul in s.select('main ul,main ol'):
        if not ul.find('li') and not ul.get('id') and not ul.get('hidden') and 'tl' not in (ul.get('class') or []): bad(f,f'空列表 .{" ".join(ul.get("class") or [])}')
    for sec in s.select('main section'):
        if sec.find('h2') and len(sec.get_text(strip=True))<=len(sec.find('h2').get_text(strip=True))+2 and not sec.select('[id]'): bad(f,f'空区块 {sec.find("h2").get_text()[:20]}')
    b=os.path.basename(f)
    if f.startswith(S+'/index') or '/day/' in f:
        for sel,nm in (('.b3 li','三句话'),('.dsm','必读要点'),('.trg','Top30 一句话')):
            for x in s.select(sel):
                t=x.get_text(' ',strip=True)
                if t and not CJK.search(t): bad(f,f'{nm} 无中文：{t[:50]}')
        txs=[re.sub(r'\W','',x.get_text()) [:40] for x in s.select('.dsm,.trg')]
        d=[t for t,c in collections.Counter(txs).items() if c>1 and t]
        if d: bad(f,f'重复要点 {d[:2]}')
    if '/d/' in f and b!='all.html':
        dom=b[:-5]
        for x in s.select('[data-dom]'):
            if x.parent and 'seg' in (x.parent.get('class') or []): continue
            if x.name in('button','a'): continue
            if dom not in x['data-dom'].split(): bad(f,f'领域错配 {x["data-dom"]} 出现在 {dom}'); break
    DEVTAGS={'agent','coding','mcp','infra','ops','fun'}   # 趋势页 AI 开发工具子标签
    for x in s.select('[data-tags]'):
        for t in x['data-tags'].split():
            if t not in (DEVTAGS if ({'dtw','dcard'}&set(x.get('class') or [])) else TAGS): bad(f,f'未知标签 {t}'); break
s=P(S+'/news.html')
ti=[x.get_text(strip=True) for x in s.select('#nall .nt2')]
print('news 条目',len(ti),'无中文标题',sum(1 for t in ti if not CJK.search(t)))
tc=collections.Counter(ti);du=[t for t,c in tc.items() if c>1]
if du: issues.append('news.html 重复标题 '+str(du[:3]))
# Agent 页：三个区块、每行有 GitHub 链接与子标签、导航含 Agent、趋势页不再含开发工具
try:
    _a=open(S+'/agents.html',encoding='utf-8').read()
    for _id in ('new','day','week'):
        if f'id="{_id}"' not in _a: issues.append('agents.html 缺区块 '+str(_id))
    _rows=_a.count('class="dcard fi"')
    if _rows<10 or _a.count('href="https://github.com/')<_rows: issues.append('agents.html 行数/链接异常 '+str(_rows))
    if _a.count('rel="noopener noreferrer"')<_rows or 'id="dsh"' not in _a: issues.append('agents.html 卡片 GitHub 按钮/详情抽屉缺失')
    try:
        _dj=json.load(open(S+'/assets/agents.json',encoding='utf-8'))
        if any(('<' in str(v[0]) or '>' in str(v[0])) for v in _dj.values()): issues.append('agents.json README 摘要含尖括号')
    except Exception as _x: issues.append('agents.json 读取失败 '+type(_x).__name__)
    if 'href="agents.html"' not in open(S+'/index.html',encoding='utf-8').read(): issues.append('导航缺 Agent')
    if 'dcard' in open(S+'/trends.html',encoding='utf-8').read(): issues.append('trends.html 仍含 AI 开发工具')
    
except FileNotFoundError: issues.append('缺 agents.html')
print('\n'.join(issues[:60]) or 'OK',f'\n问题 {len(issues)} 条')
