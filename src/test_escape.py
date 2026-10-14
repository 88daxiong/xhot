"""安全回归测试：恶意推文/资讯文本不能跳出 href 属性，非 http(s) 链接必须变成 '#'。
另含 jsafe（嵌入 JSON 不能打断 <script>）与 app.js 的 esc/lnk/safeUrl（需要 node，没有则跳过）。
运行：python3 test_escape.py（只抽取函数，不会触发构建）"""
import ast,html,json,os,re,shutil,subprocess,sys
from html.parser import HTMLParser
D=os.path.dirname(os.path.abspath(__file__))
src=open(os.path.join(D,'generate.py'),encoding='utf-8').read()
ns={'re':re,'e':html.escape,'json':json}
for n in ast.parse(src).body:
    if isinstance(n,ast.FunctionDef) and n.name in ('lnk','safe_url','jsafe'):
        exec(compile(ast.Module([n],[]),'generate.py','exec'),ns)
lnk,safe_url,jsafe=ns['lnk'],ns['safe_url'],ns['jsafe']
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
# jsafe：输出里不能出现 < > &（防 </script>、<!--<script> 让解析器吞掉后续页面），且能原样还原
for v in ['a<!--<script>b','</script><script>alert(1)</script>','x & y > z','\u2028\u2029','"\'`${}']:
    o=jsafe({'name':v})
    check('jsafe no <>& : '+repr(v)[:30], not re.search(r'[<>&\u2028\u2029]',o))
    check('jsafe roundtrip: '+repr(v)[:30], json.loads(o)=={'name':v})
# app.js：esc / lnk / safeUrl / xurl（node 存在时）
node=shutil.which('node')
if node:
    js=open(os.path.join(D,'app.js'),encoding='utf-8').read()
    fn=''.join(re.search(r'^function '+n+r'\(.*$',js,re.M).group(0)+'\n' for n in ('esc','safeUrl','xurl','lnk'))
    T=fn+r'''var out={};
out.lnk=lnk('see https://a.com/"onmouseover="alert(1) x '+"https://b.com/'onfocus='alert(1)"+' <img src=x onerror=alert(1)>');
out.su=['javascript:alert(1)',' JavaScript:alert(1)','data:text/html,x','//evil.com','',null,'https://ok.com/a?b=1&c="x"'].map(safeUrl);
out.xu=[xurl(['123','','',0,0,0,0,0,0,''],'sama'),xurl(['1','','',0,0,0,0,0,0,'https://x.com/a/status/1'],'b')];
console.log(JSON.stringify(out));'''
    r=json.loads(subprocess.run([node,'-e',T],capture_output=True,text=True,check=True).stdout)
    Tg=tags(r['lnk'])
    check('JS lnk: only <a> with href/target/rel', bool(Tg) and all(t=='a' and set(a)<={'href','target','rel'} for t,a in Tg))
    check('JS lnk: href has no quote/angle', all(not re.search(r'["\'<>]',a['href']) for _,a in Tg))
    check('JS lnk: rel noopener noreferrer', all(a['rel']=='noopener noreferrer' for _,a in Tg))
    check('JS safeUrl non-http -> #', r['su'][:6]==['#']*6)
    check('JS safeUrl https escaped', r['su'][6]=='https://ok.com/a?b=1&amp;c=&quot;x&quot;')
    check('JS xurl rebuild/keep', r['xu']==['https://x.com/sama/status/123','https://x.com/a/status/1'])
else: print('SKIP JS tests (node not found)')
print('ALL PASS' if not fails else f'{fails} FAILED'); sys.exit(1 if fails else 0)
