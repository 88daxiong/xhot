import json,sys
r=json.load(open(sys.argv[1] if len(sys.argv)>1 else 'speed.json'))
def row(net,cpu,label,vw):
    a=r.get(f'{net}|cpu{cpu}|{label}|{vw}|v14');b=r.get(f'{net}|cpu{cpu}|{label}|{vw}|v15')
    if not a or not b: return None
    return a,b
for net,cpu in (('none',1),('fast3g',1),('fast3g',4)):
    print(f'\n## {net} cpu×{cpu}\n| 页面 | 视口 | FCP v14→v15 | LCP v14→v15 | CLS | 传输KB v14→v15 (html/css/js/img v15) | 请求 |\n|---|---|---|---|---|---|---|')
    for label in ('今日/首页','人物','资讯','趋势','人物页','归档(热帖)'):
        for vw in (1440,390):
            x=row(net,cpu,label,vw)
            if x: a,b=x; print(f"| {label} | {vw} | {a['fcp']}→{b['fcp']} | {a['lcp']}→{b['lcp']} | {a['cls']}→{b['cls']} | {a['kb']}→{b['kb']} ({b['html']}/{b['css']}/{b['js']}/{b['img']}) | {a['req']}→{b['req']} |")
print('\n## INP 近似（CPU×4，最大事件 duration ms）')
for k,v in r.items():
    if k.startswith('inp|'): print(k,v['max'],'n=',v['n'],v['ev'][:6])
