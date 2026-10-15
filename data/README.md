# XHOT 数据备份

由 `export_data.py` 从 xhot.db 导出，每次刷新时更新。JSON 键排序固定、缩进 2。

- `accounts.json`：关注列表里的每个账号，包括 handle、user_id、名字、所属领域/分组、是否中文号、最新粉丝数（`followers_ts` 是快照时间）、已存推文数。
- `followers_history.json`：每个账号的粉丝时间序列（`ts`、`followers`、`following`、`tweets`），ts 是北京时间 `YYYYMMDD_HHMMSS`。
- `daily/YYYY-MM-DD.json`：每日日报（date、highlights[handle,name,text_zh,post_id,url,likes]、topics_zh、followers_zh、changelog[]），由刷新流程撰写。
- `tweets/<handle>.json`：该账号本地存储的原创推文（最多 200 条，最新在前），字段有 id、created_at（UTC）、text（长推文是全文 note_tweet）、lang、metrics（like/retweet/reply/quote/impression/bookmark）、url。

数据来源：X API（get_users_posts、get_users_by_usernames）。只做备份和展示，版权归原作者。
