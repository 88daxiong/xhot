#!/usr/bin/env python3
"""匿名抓取 github.com/trending（daily：全部 / python / typescript），筛选 AI/开发工具，写 raw/<ts>_gh_trending.json。不用任何 token。"""
import urllib.request,re,html,json,os,datetime
D=os.path.dirname(os.path.abspath(__file__))
KW=re.compile(r'\b(ai|llm|gpt|agent|agents|agentic|claude|codex|copilot|model|models|ml|rag|mcp|inference|transformer|diffusion|chat|prompt|embedding|vector|neural|deep.?learning|machine.?learning|cli|sdk|devtool|framework|compiler|ide|editor|coding|code|developer|terminal|lsp|vibe)\b|大模型|智能体',re.I)
def get(u):
    r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0 xhot-trending','Accept':'text/html'})
    return urllib.request.urlopen(r,timeout=30).read().decode('utf-8','ignore')
def num(s): return int(re.sub(r'[^\d]','',s) or 0)
out={};seen=set()
for lang in ['','python','typescript']:
    t=get(f'https://github.com/trending/{lang}?since=daily')
    for a in t.split('<article class="Box-row')[1:]:
        m=re.search(r'<h2[^>]*>\s*<a[^>]*href="/([^"]+)"',a)
        if not m: continue
        full=m.group(1).strip()
        d=re.search(r'<p class="col-9[^"]*">(.*?)</p>',a,re.S); desc=html.unescape(re.sub(r'<[^>]+>','',d.group(1))).strip() if d else ''
        l=re.search(r'itemprop="programmingLanguage">([^<]+)<',a)
        st=re.search(r'href="/'+re.escape(full)+r'/stargazers"[^>]*>.*?</svg>\s*([\d,]+)',a,re.S)
        td=re.search(r'([\d,]+) stars (today|this week)',a)
        r={'repo':full,'desc':desc,'lang':l.group(1).strip() if l else '','stars':num(st.group(1)) if st else 0,'today':num(td.group(1)) if td else 0,'url':'https://github.com/'+full,'list':lang or 'all'}
        r['ai']=bool(KW.search(full.replace('/',' ').replace('-',' ')+' '+desc))
        if full not in seen: seen.add(full); out.setdefault('repos',[]).append(r)
out['_fetched_at']=datetime.datetime.now().astimezone().isoformat()
ts=datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
p=os.path.join(D,'raw',f'{ts}_gh_trending.json');json.dump(out,open(p,'w'),ensure_ascii=False,indent=1)
print(p,len(out.get('repos',[])),'ai',sum(r['ai'] for r in out.get('repos',[])))
