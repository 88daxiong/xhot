#!/usr/bin/env python3
"""下载头像到 avatars/<handle>.jpg（_400x400 → 再缩成 96px webp/jpg 以减小体积）。数据源：raw/*_users_*.json 与 raw/*_avatars_*.json 里的 profile_image_url。
已存在且 URL 未变则跳过。无 token，只访问 pbs.twimg.com 公开图片。用法：python3 avatars_fetch.py"""
import os,glob,json,urllib.request,concurrent.futures as cf
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
AV='avatars'; os.makedirs(AV,exist_ok=True)
U={}
for f in sorted(glob.glob('raw/*_users_*.json'))+sorted(glob.glob('raw/*_avatars_*.json')):
    try:
        for u in json.load(open(f,encoding='utf-8')).get('data',[]):
            if u.get('profile_image_url'): U[u['username'].lower()]=u['profile_image_url'].replace('_normal.','_400x400.')
    except Exception: pass
idx=os.path.join(AV,'index.json'); old=json.load(open(idx)) if os.path.exists(idx) else {}
def get(item):
    h,url=item; out=os.path.join(AV,h+'.jpg')
    if old.get(h)==url and os.path.exists(out): return h,True
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        data=urllib.request.urlopen(req,timeout=20).read()
        try:
            from PIL import Image; import io
            im=Image.open(io.BytesIO(data)).convert('RGB'); im.thumbnail((128,128)); b=io.BytesIO(); im.save(b,'JPEG',quality=82,optimize=True); data=b.getvalue()
        except Exception: pass
        open(out,'wb').write(data); return h,True
    except Exception as ex: print('fail',h,ex); return h,False
ok={}
with cf.ThreadPoolExecutor(12) as ex:
    for h,s in ex.map(get,U.items()):
        if s: ok[h]=U[h]
json.dump(ok,open(idx,'w'),indent=0,sort_keys=True)
print('avatars',len(ok),'/',len(U))
