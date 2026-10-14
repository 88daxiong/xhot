"""安全回归测试：恶意推文/资讯文本不能跳出 href 属性，非 http(s) 链接必须变成 '#'。
运行：python3 test_escape.py（只抽取 generate.py 里的 lnk / safe_url，不会触发构建）"""
import ast,html,os,re,sys
from html.parser import HTMLParser
D=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(D,'generate.py'),encoding='utf-8').read()
ns={'re':re,'e':html.escape}
for n in ast.parse(src).body:
    if isinstance(n,ast.FunctionDef) and n.name in ('lnk','safe_url'):
        exec(compile(ast.Module([n],[]),'generate.py','exec'),ns)
lnk,safe_url=ns['lnk'],ns['safe_url']
class A(HTMLParser):
    def __init__(s): super().__init__(); s.tags=[]
    def handle_starttag(s,t,a): s.tags.append((t,dict(a)))
def tags(h): p=A(); p.feed(h); return p.tags
fails=0
def check(name,cond):
    global fails; print(('PASS ' if cond else 'FAIL ')+name); fails+=0 if cond else 1
SAMPLES=['see https://a.com/"onmouseover="alert(1) x',
         "see https://a.com/'onmouseover='alert(1) x",
         'https://a.com/"><script>alert(1)</script>',
         'x <img src=x onerror=alert(1)> https://ok.com/path?a=1&b=2']
for s in SAMPLES:
    h=lnk(s); T=tags(h)
    check('no script/img/on* attr: '+s[:40], all(t=='a' for t,_ in T) and all(set(a)<={'href','target','rel'} for _,a in T))
    check('href has no quote/angle: '+s[:40], all(not re.search(r'["\'<>]',a.get('href','')) for _,a in T))
    check('rel noreferrer: '+s[:40], all(a.get('rel')=='noopener noreferrer' for _,a in T))
for u,want in [('javascript:alert(1)','#'),(' JavaScript:alert(1)','#'),('data:text/html,x','#'),('//evil.com','#'),('','#'),(None,'#'),
               ('https://ok.com/a?b=1&c="x"','https://ok.com/a?b=1&amp;c=&quot;x&quot;'),('HTTP://ok.com','HTTP://ok.com')]:
    check(f'safe_url({u!r})',safe_url(u)==want)
print('ALL PASS' if not fails else f'{fails} FAILED'); sys.exit(1 if fails else 0)
