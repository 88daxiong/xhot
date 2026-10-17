#!/usr/bin/env python3
"""v15 日报素材：python3 daily_draft.py [YYYY-MM-DD] > /tmp/daily_draft.json
= generate.py 的规则评分 Top 40 候选（XHOT_DRAFT）+ daily_topics.py 的话题涨跌 / 粉丝变化 + 候选的本地全文（只在本机 stdout，不进仓库）。
候选字段：id handle name url likes heat score domain tags is_english created_at excerpt(公开摘录) text_full(本地全文，供 agent 读懂/翻译) has_gist。
输出里的全文只给 agent 读，写进 daily/<日期>.json 的只能是 excerpt / excerpt_zh / text_zh / gists 等短字段。"""
import sys,os,json,subprocess,sqlite3,datetime,html
D=os.path.dirname(os.path.abspath(__file__)); os.chdir(D)
TZ=datetime.timezone(datetime.timedelta(hours=8))
day=sys.argv[1] if len(sys.argv)>1 else datetime.datetime.now(TZ).strftime('%Y-%m-%d')
_o=subprocess.run([sys.executable,'generate.py'],env=dict(os.environ,XHOT_DRAFT=day),capture_output=True,text=True,check=True).stdout
cand=json.loads(_o[_o.index('\n[')+1:] if not _o.lstrip().startswith('[') else _o)  # WARN 行也会打到 stdout，跳过
old=json.loads(subprocess.run([sys.executable,'daily_topics.py',day],capture_output=True,text=True,check=True).stdout)
db=sqlite3.connect('xhot.db')
for c in cand:
    r=db.execute('select text from tweets where id=?',(c['id'],)).fetchone(); c['text_full']=html.unescape(r[0]) if r else c['excerpt']
print(json.dumps(dict(date=day,window=old['window'],candidates=cand,topics=old['topics'],followers=old['followers'],
  howto='挑 5-8 条必读（highlights，按 likes 降序）+ 写 summary_zh 三句话 + 给所有英文/非中文入选 Top30 帖写 gists；噪声帖放进 hide，必须置顶的放进 pin'),ensure_ascii=False,indent=1))
