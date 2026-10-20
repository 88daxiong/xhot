#!/usr/bin/env python3
"""Agent 页详情用的 README 摘要：只在完整刷新时跑，只抓页面上列出的仓库（raw/agents_repos.json，≤70 个）。
匿名读 raw.githubusercontent.com/<repo>/HEAD/<README 名>（不占 api.github.com 每小时 60 次额度），带 If-None-Match（ETag）条件请求，
未变化（304）直接用缓存。结果写 raw/readme_cache.json：{repo:{etag,name,text,fetched}}，text 已是净化后的纯文本（≤600 字）。
请求上限 MAXREQ（默认 100，含文件名回退）。用法：python3 devtools_readme.py"""
import urllib.request,urllib.error,json,os,re,html,datetime,time,sys
D=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(D,'raw','readme_cache.json')
NAMES=['README.md','readme.md','README.MD','Readme.md','README.rst','README']
MAXREQ=int(os.environ.get('MAXREQ','100')); MAXLEN=600
CTRL=re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u2028\u2029\u202a-\u202e\u2066-\u2069\ufeff]')
LANGS=set("english 简体中文 繁體中文 中文 日本語 한국어 español español français deutsch português brasil русский italiano türkçe tiếng việt ไทย українська polski العربية فارسی bahasa indonesia bosanski dansk norsk svenska suomi nederlands čeština magyar română ελληνικά עברית हिन्दी বাংলা català 繁体中文 简中 zh en ja ko readme language languages".split())
def _langnav(l):
    w=[x for x in re.split(r'[\s·|/•,()]+',l.lower()) if x]
    return len(w)>=3 and sum(1 for x in w if x in LANGS)>=0.6*len(w)
def sanitize(md,n=MAXLEN):
    """Markdown/HTML → 纯文本摘要：去掉代码块、HTML 标签与注释、图片、徽章、链接地址、表格线、标题符号；只保留文字。返回 ≤n 字。"""
    t=str(md or '')[:200000]
    t=re.sub(r'<!--.*?(-->|$)','',t,flags=re.S)
    t=re.sub(r'(?is)<(script|style|svg|picture|video|audio|iframe|object|template|noscript)\b.*?(</\1\s*>|$)',' ',t)
    t=re.sub(r'```.*?(```|$)|~~~.*?(~~~|$)',' ',t,flags=re.S)
    t=re.sub(r'(?is)<[^>]*>',' ',t); t=t.replace('<',' ').replace('>',' ')
    t=re.sub(r'!\[[^\]]*\]\([^)]*\)|!\[[^\]]*\]\[[^\]]*\]',' ',t)
    t=re.sub(r'\[!\[[^\]]*\][^\]]*\]\([^)]*\)',' ',t)
    t=re.sub(r'\[([^\]]*)\]\([^)]*\)',r'\1',t); t=re.sub(r'\[([^\]]*)\]\[[^\]]*\]',r'\1',t)
    t=re.sub(r'(?m)^\s*\[[^\]]+\]:\s*\S+.*$','',t)
    t=re.sub(r'(?i)\b(?:https?|ftp|javascript|data|vbscript|file):\S*','',t); t=re.sub(r'\bwww\.\S+','',t)
    t=re.sub(r'(?m)^\s*(\.\.\s.*|:[a-z]+:.*)$','',t)          # rst 指令
    t=re.sub(r'(?m)^\s*\|?[\s:|-]{3,}\|?\s*$','',t); t=t.replace('|',' ')
    t=re.sub(r'(?m)^\s{0,3}(#{1,6}|>+|[-*+]\s|\d+[.)]\s)\s*','',t)
    t=re.sub(r'(?m)^[=\-~^*_]{3,}\s*$','',t)
    t=re.sub(r'[*_`~]{1,3}','',t)
    t=html.unescape(html.unescape(t)); t=t.replace('<',' ').replace('>',' ')
    t=CTRL.sub('',t)
    lines=[re.sub(r'\s+',' ',l).strip() for l in t.split('\n')]
    lines=[l for l in lines if len(re.findall(r'[A-Za-z\u4e00-\u9fff\u3040-\u30ff]',l))>=8]
    lines=[l for l in lines if not _langnav(l)]
    t=re.sub(r'\s+',' ',' '.join(lines)).strip()
    if len(t)>n:
        c=t[:n]; k=max(c.rfind('. '),c.rfind('。'),c.rfind('! '),c.rfind('? '),c.rfind('！'),c.rfind('？'))
        t=(c[:k+1] if k>n*0.5 else c.rsplit(' ',1)[0])+' …'
    return t
def fetch(repo,name,etag):
    r=urllib.request.Request(f'https://raw.githubusercontent.com/{repo}/HEAD/{name}',headers={'User-Agent':'Mozilla/5.0 xhot-readme',**({'If-None-Match':etag} if etag else {})})
    try:
        with urllib.request.urlopen(r,timeout=20) as x: return 200,x.read(300000).decode('utf-8','ignore'),x.headers.get('ETag','')
    except urllib.error.HTTPError as ex: return ex.code,'',''
if __name__=='__main__':
    repos=[r for r in json.load(open(os.path.join(D,'raw','agents_repos.json'))) if re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',r)][:70]
    try: C=json.load(open(CACHE))
    except Exception: C={}
    n=0; st={'new':0,'304':0,'miss':0,'err':0}
    for repo in repos:
        if n>=MAXREQ: break
        c=C.get(repo,{}); names=[c['name']]+[x for x in NAMES if x!=c.get('name')] if c.get('name') else NAMES
        got=False
        for nm in names:
            if n>=MAXREQ: break
            code,body,et=fetch(repo,nm,c.get('etag') if nm==c.get('name') else None); n+=1
            if code==304:
                if C[repo].get('md'): C[repo]['text']=sanitize(C[repo]['md'])   # 规则更新后用缓存原文重新净化
                C[repo]['fetched']=datetime.date.today().isoformat(); st['304']+=1; got=True; break
            if code==200:
                C[repo]={'etag':et,'name':nm,'md':body[:40000],'text':sanitize(body),'fetched':datetime.date.today().isoformat()}; st['new']+=1; got=True; break
            if code!=404: st['err']+=1; break
            time.sleep(0.2)
        if not got: st['miss']+=1
        time.sleep(0.3)
    json.dump(C,open(CACHE,'w'),ensure_ascii=False,indent=0)
    print('readme: requests',n,st,'cache',len(C),'covered',sum(1 for r in repos if C.get(r,{}).get('text')),'/',len(repos))
