# XHOT 数据备份（v15：仅 ID 与指标）

由 `export_data_v15.py` 导出，每天刷新时更新。JSON 键排序固定、缩进 2。**本目录不含任何推文全文**；推文内容请点链接回 X 查看。

- `accounts.json`：关注列表里的每个账号（handle、user_id、名字、领域/分组、是否中文号、最新粉丝数）。
- `followers_history.json`：每个账号的粉丝时间序列（北京时间 `YYYYMMDD_HHMMSS`）。
- `tweets/<handle>.json`：该账号本地存储的原创推文的 **id、created_at、lang、指标（点赞/转推/回复/引用/曝光/收藏）、url**，不含正文。
- `daily/YYYY-MM-DD.json`：每日要点（三句话、必读重点的中文概括与短摘录、一句话要点、话题/粉丝变化、更新日志）。
- `weekly/YYYY-Www.json`：每周 Top 人物的「本周要点」。

数据来源：X API。只做备份和展示，版权归原作者。
