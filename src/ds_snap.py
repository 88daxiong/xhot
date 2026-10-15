"""v15 设计令牌吸附：把最终 CSS 里的字号 / 间距 / 圆角全部吸附到令牌刻度（见 ds_tokens.json）。
字号 → var(--t-cap|sm|md|lg|xl|xxl)（rem，随系统字号缩放；手机 md/lg 为 15/17）；间距/圆角 → 刻度（取最近，平局取小）。"""
import re,json,os
T=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ds_tokens.json')))
SP=T['space'];RD=T['radius']
def _near(v,sc,up=False):
    return min(sc,key=lambda o:(abs(o-v),-o if up else o))
def _num(tok):
    m=re.fullmatch(r'(-?)(\d*\.?\d+)(px|rem|em)',tok)
    if not m: return None
    n=float(m.group(2));u=m.group(3)
    if u=='rem': n*=16
    elif u=='em': n*=14
    return -n if m.group(1) else n
def _fmt(n): return '0' if n==0 else '%gpx'%n
def _split(v):
    out=[];d=0;cur=''
    for ch in v:
        if ch=='(':d+=1
        if ch==')':d-=1
        if ch==' ' and d==0:
            if cur:out.append(cur);cur=''
        else:cur+=ch
    if cur:out.append(cur)
    return out
def _snap_list(val,sc,keep_big=64,up=False):
    out=[]
    for t in _split(val):
        n=_num(t)
        if n is None or abs(n)>keep_big: out.append(t);continue
        s=_near(abs(n),sc,up)
        out.append(('-' if n<0 and s else '')+_fmt(s))
    return ' '.join(out)
def tsize(px):
    return 'cap' if px<=12.5 else 'sm' if px<=13.5 else 'md' if px<=15.5 else 'lg' if px<=18.5 else 'xl' if px<=23 else 'xxl'
def snap(css):
    def fs(m):
        n=float(m.group(2))*(16 if m.group(3)=='rem' else 1)
        return m.group(1)+'var(--t-%s)'%tsize(n)
    css=re.sub(r'(?<![\w(,-])(font-size:)(\d*\.?\d+)(px|rem)(?![\w])',fs,css)
    def sp(m):
        v=m.group(2)
        return m.group(1)+_snap_list(v.strip(),SP)
    css=re.sub(r'((?<![\w-])(?:padding|margin|gap|row-gap|column-gap)(?:-(?:top|right|bottom|left|block|inline)(?:-(?:start|end))?)?:)([^;}{!]+)',sp,css)
    def rd(m):
        v=m.group(2)
        if '/' in v: return m.group(0)
        return m.group(1)+_snap_list(v.strip(),RD,keep_big=999,up=True)
    css=re.sub(r'((?<![\w-])border-radius:)([^;}{!]+)',rd,css)
    def fw(m):
        n=int(m.group(2));return m.group(1)+str(400 if n<=450 else 500 if n<=550 else 600 if n<=650 else 700)
    css=re.sub(r'((?<![\w-])font-weight:)(\d{3})(?!\d)',fw,css)
    return css
def root_vars():
    t=T['type_px'];tp=T['type_px_phone']
    r=lambda d:';'.join('--t-%s:%grem'%(k,v/16) for k,v in d.items())
    return ':root{%s}@media(max-width:720px){:root{%s}}'%(r(t),r(tp))
