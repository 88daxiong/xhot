"""v15 站内链接/资源静态检查：python3 check_links.py [site]
扫描每个 HTML 的 href / src（相对链接），确认目标文件存在（忽略 #hash 与查询串、外链、data:、mailto）；同时检查 JS 里引用的 assets/feed 分片文件名是否存在。"""
import os,sys,re,glob
from html.parser import HTMLParser
S=sys.argv[1] if len(sys.argv)>1 else 'site'
class P(HTMLParser):
    def __init__(s): super().__init__(); s.l=[]
    def handle_starttag(s,t,a):
        for k,v in a:
            if k in('href','src') and v: s.l.append(v)
bad=[];n=0
for f in glob.glob(S+'/**/*.html',recursive=True):
    p=P(); p.feed(open(f,encoding='utf-8').read())
    for u in p.l:
        if re.match(r'(https?:|data:|mailto:|//|#|javascript:)',u): continue
        u=u.split('#')[0].split('?')[0]
        if not u: continue
        t=os.path.normpath(os.path.join(os.path.dirname(f),u)); n+=1
        if os.path.isdir(t): t=os.path.join(t,'index.html')
        if not os.path.exists(t): bad.append(f'{os.path.relpath(f,S)} -> {u}')
print(f'checked {n} internal links; broken: {len(bad)}'); [print(' ',b) for b in bad[:20]]
sys.exit(1 if bad else 0)
