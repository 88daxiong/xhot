#!/usr/bin/env python3
"""抓取 aihot.news 公开数据（无需 Key，不耗 x 调用）→ raw/<ts>_aihot*.json"""
import json,re,time,urllib.request,datetime,os,gzip,html as H
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
UA='aihot-api/2.0.0 xhot-monitor'; TS=datetime.datetime.now().strftime('%Y%m%d_%H%M%S'); B='https://aihot.news'
def get(path,raw=False):
    r=urllib.request.urlopen(urllib.request.Request(B+path,headers={'User-Agent':UA,'Accept-Encoding':'gzip'}),timeout=30); b=r.read()
    if r.headers.get('Content-Encoding')=='gzip': b=gzip.decompress(b)
    time.sleep(0.4); return b.decode('utf-8') if raw else json.loads(b)
def save(label,obj): json.dump(obj,open(f'raw/{TS}_{label}.json','w',encoding='utf-8'),ensure_ascii=False); print('saved',label)
save('aihot',get('/api/v1/items?mode=selected&window=24h&limit=100'))
pool={}
for mode in ('selected','all'):
    for cat in ('','ai-models','ai-products','industry','paper','tip','opinion'):
        try:
            j=get(f'/api/v1/items?mode={mode}&window=7d&limit=100'+(f'&category={cat}' if cat else ''))
            for it in j.get('items',[]): pool.setdefault(it['id'],it)
        except Exception as x: print('fail',mode,cat,x)
save('aihot_pool',{'items':list(pool.values())})
for lab,p in (('aihot_hot','/api/v1/hot-topics'),('aihot_daily','/api/v1/dailies/latest'),('aihot_weekly','/api/v1/weeklies/latest')):
    try: save(lab,get(p))
    except Exception as x: print('fail',lab,x)
try:
    t=get('/topics',raw=True)
    m=re.search(r'"itemListElement":(\[.*?\])\}',t); save('aihot_topics',{'items':json.loads(m.group(1))})
except Exception as x: print('fail topics',x)
try:
    t=get('/leaderboard',raw=True)
    rows=[]
    for tr in re.findall(r'<tr[^>]*>(.*?)</tr>',t,flags=re.S):
        c=[H.unescape(re.sub(r'\s+',' ',re.sub('<[^>]+>',' ',x))).strip() for x in re.findall(r'<td[^>]*>(.*?)</td>',tr,flags=re.S)]
        if len(c)<8 or not c[0].isdigit(): continue
        head=c[1].split(' · ')[0]; w=head.split(' '); name,org=head,''
        for k in range(1,4):
            if len(w)>2*k and w[-k:]==w[-2*k:-k]: org=' '.join(w[-k:]); name=' '.join(w[:-2*k]); break
        rows.append(dict(rank=int(c[0]),name=name,org=org,date=c[2],evals=c[3].split(' 覆盖')[0],price_in=c[5],price_out=c[6],score=float(c[7].split()[0])))
    save('aihot_models',{'items':rows,'url':B+'/leaderboard'})
except Exception as x: print('fail leaderboard',x)
# 热点故事的 AI 综述（AIHOT 自己写的多段 digest，可直接展示；原文全文版权属于原站，只链接）
try:
    hot=json.load(open(sorted(__import__('glob').glob('raw/*_aihot_hot.json'))[-1],encoding='utf-8')).get('items',[])
    st={}
    for it in hot[:15]:
        sl=(it.get('links') or {}).get('story') or ''
        sid=sl.rstrip('/').split('/')[-1]
        if not sid: continue
        try: st[it['id']]=get(f'/api/v1/stories/{sid}').get('story',{})
        except Exception as x: print('fail story',sid,x)
    save('aihot_stories',{'items':st})
except Exception as x: print('fail stories',x)
