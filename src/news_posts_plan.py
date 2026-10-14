#!/usr/bin/env python3
"""每个领域输出一行：<dom> <逗号分隔的 post id>（每条 X 新闻取前 3 个 cluster 帖子，去重，≤100）。
用于 get_posts_by_ids（每领域 1 次调用），结果入库：python3 ingest.py news_posts_<dom> <file>"""
import os,sys,glob,json
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
for d in ('ai','money','growth'):
    fs=sorted(glob.glob(f'raw/*_news_{d}.json'))
    if not fs: continue
    ids=[]
    for n in json.load(open(fs[-1],encoding='utf-8')).get('data',[]):
        for p in list(dict.fromkeys(x['post_id'] for x in n.get('cluster_posts_results',[])))[:3]:
            if p not in ids: ids.append(p)
    print(d,','.join(ids[:100]))
