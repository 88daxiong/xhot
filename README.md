# XHOT · X 热点雷达

在线访问：<https://88daxiong.github.io/xhot/>

XHOT 是一个纯静态的 X（Twitter）热点简报，关注 AI、搞钱（创业 / 创作者经济）、个人成长三个领域约 130 个账号，**每天北京时间 08:00 刷新一次**。设计目标：**每天 10 分钟看完重点**，或**几分钟追上某个人 / 某个领域的进度**。

| 页面 | 内容 |
|---|---|
| `index.html` 今日 | 「今天一眼看完」三句话 → 必读（5–8 条，中文要点 + 可展开的原帖摘录，英文帖默认中文译文，可切 EN）→ 更多值得看（与必读合计今日 Top 30，每条一句话中文要点，可按领域筛选、点开看摘录与原帖链接）→ 话题涨跌 · 粉丝变化 · 资讯头条 · 更新日志。顶部「约 N 分钟读完」，已读 / 新增标记只存在你的浏览器里 |
| `d/ai.html` `d/money.html` `d/growth.html` 领域 | 一个领域一屏：本周重要度前列帖子（15 个受控标签可筛）、必关注 10 人、领域话题、相关资讯 |
| `d/all.html` 全部归档 | 原「热帖」：按重要度 / 时间排序，按天分片加载，可搜索摘录；每人默认最多 3 条 |
| `people.html` + `p/<handle>.html` 人物 | 目录：本周 Top 30 人物的「本周要点」+ 全部人物（按领域筛选、按热度 / 粉丝 / 变化排序、搜索）；个人页：一屏读懂（简介、本周概览、话题标签、发帖节奏、粉丝）+ 高光帖 + 时间线 |
| `news.html` 资讯 | 两栏阅读器（左列表约 60% / 右窗格约 40%），AIHOT 中文在前，X 新闻在后 |
| `trends.html` 趋势 | X 话题讨论量涨跌 + GitHub 今日 AI / 开发工具趋势（与资讯完全分开） |
| `day/<日期>.html` 往期 | 每天一个永久链接（旧 `daily/<日期>.html`、`hot.html`、`accounts.html` 自动跳转到新地址） |

全站：顶栏 今日 · 领域 · 人物 · 资讯 · 趋势，⌘K（或「/」）全站搜索（人物、标签、话题、日期，帖子摘录按需读取分片），共用日期控件，浅色 / 深色 / 跟随系统，舒适 / 紧凑两档密度，界面只有中文，**没有任何统计 / 分析脚本**，没有第三方请求。

## 内容与版权策略（v15）

- **仓库与站点只公开帖子 ID、互动指标、≤220 字（必读 ≤320 字）的短摘录、agent 撰写的中文要点 / 译文摘录，以及指向 X 的原帖链接**；不再公开推文全文（v14 的 `data/tweets/*.json` 与日报 `text_orig` 已停止公开）。要读全文请点「在 X 打开」。
- 英文帖的中文是**摘录的中文译文**（带「译」标记，仅供参考，以原文为准）。
- 资讯：AIHOT 的摘要 / 综述来自其公开 API（MIT 许可）；文章原文版权属于原站，本站只给链接。
- 推文内容版权归原作者；本项目只做摘录、索引与展示。

## 重要度、标签、人物榜

- **热度** = 赞 + 2×转推 + 3×引用 + 评论 + 收藏。
- **重要度（0–100，规则可复现）** = `6·ln(1+热度) + 10·clamp(ln((热度+20)/(作者最近 30 条热度中位数+20)), −1, 2.5)`：既看绝对热度，也看相对作者自己的常态，大号小号可比。榜单每人最多 2 条、文本去重、纯链接帖不进榜。**每天由 agent 做最终复核**：必读挑选、置顶 / 隐藏、噪声过滤。
- **15 个受控标签**（关键词规则打标，可能有误差）：AI：模型 · 智能体 · 编程 · 开源 · 产品发布 · 研究 · 芯片算力 · 政策；搞钱：创业 · 创作者经济 · 融资 · 独立开发；成长：习惯 · 写作 · 职业。
- **本周 Top 30 人物** = 近 7 天前 3 条帖子重要度之和最高的 30 人（排除灌水账号），每周一由 agent 写每人 1–2 条「本周要点」。
- **日窗口**：某日的日报覆盖「该日 09:00（北京时间）往前 25 小时」。

## 架构与数据流

```
X API（只读）──┐
aihot.news API ─┼─> raw/*.json ──> SQLite（xhot.db，本机，不进仓库）──> Python 静态生成器 ──> site/ ──> 静态托管（GitHub Pages）
GitHub Trending ┘                         │                                                    
                                          └─> export_data_v15.py ──> data/（仅 ID 与指标）
```

生成器与托管无关：输出是一个纯静态目录，任何静态主机都能托管（GitHub Pages、Cloudflare Pages、Netlify、对象存储 + CDN）。

### 前端性能设计（均有测试与预算）
- 每页只有 **一个内联脚本（主题预绘，带 sha256 的 CSP）和一个内联 `<style>`（按页裁剪，约 7KB gzip）**；JS 拆成 `core`（所有页）与 `news` / `feed`（按页），文件名带内容哈希、`defer`。
- 外链 CSS 在 Fast 3G 下会多一次往返（实测 FCP 约 +1s），所以 CSS 内联；若日后换到支持 HTTP/2 push / Early Hints 的主机，可改回外链。
- 数据分片：`feed/<日期>.<hash>.json`（按天）、`p/<handle>.<hash>.json`（个人时间线）、`assets/search.<hash>.json`（⌘K 索引，首次呼出时才读）。首屏服务端渲染，无 JS 也能读正文。
- 相对时间（x 小时前 / 今天 / 昨天）由前端补齐，**页面源码里不烘焙相对时间**，页面稳定、无数据变化就不改写文件；新 / 已读标记只存浏览器 localStorage。
- `<link rel="expect" blocking="render">` 等页头与工具条解析完再首次绘制，布局偏移（CLS）≈ 0；头像为 64px / 96px webp（约 0.7 / 1.5KB），首屏之外懒加载。
- 目标：首页首屏 ≤80KB gzip、LCP ≤1.0s（Fast 3G）、INP ≤100ms（CPU 4×）、CLS = 0；实测见仓库外的 `speed_v15.json`。

### 限制（诚实说明）
- GitHub Pages **不能设置响应头**：CSP 只能写在 `<meta>`，因此没有 `frame-ancestors`（页面可被 iframe 嵌套）、HSTS 不可控；`_headers` 文件只在 Cloudflare Pages / Netlify 等主机上生效。
- GitHub Pages 有软限制（站点 ≤1GB、月流量约 100GB、构建 10 分钟）；`github.io` 在中国大陆访问不稳定。当前规模远低于限制，若流量增长需要换托管（架构已与托管无关）。
- 每天约 150 个文件会变化（人物页的指标 / 摘录），仓库会持续增长；公开 `data/` 已去掉全文以控制体积和合规风险。
- 没有自定义 404 页（GitHub Pages 默认 404）；旧链接的跳转页不会保留 `#` 之后的参数。

## 仓库结构

```
index.html  news.html  trends.html  people.html  _headers
d/{ai,money,growth,all}.html        # 领域页与全部归档
day/<YYYY-MM-DD>.html               # 每日简报（永久链接）
p/<handle>.html + p/<handle>.<hash>.json
feed/<YYYY-MM-DD>.<hash>.json       # 按天分片的摘录
assets/core|news|feed.<hash>.js  assets/search.<hash>.json  assets/news.<hash>.json  assets/av/*.webp
hot.html accounts.html daily/<日期>.html   # 旧链接跳转页
data/                               # 仅 ID 与指标的数据备份
src/                                # 生成器源码，可从零重建
```

### data/ 数据格式（不含任何推文全文）
- `data/accounts.json`：`{"accounts": [{handle, user_id, name, domains[], groups[], zh, followers, followers_ts, tweets_stored}]}`
- `data/followers_history.json`：每个账号的粉丝时间序列
- `data/tweets/<handle>.json`：`{"handle", "user_id", "tweets": [{id, created_at(UTC), lang, metrics{like, retweet, reply, quote, impression, bookmark}, url}]}`，**没有 text 字段**
- `data/daily/YYYY-MM-DD.json`：`{"date", "summary_zh":[3 句], "highlights":[{handle, name, post_id, url, likes, text_zh, excerpt, excerpt_zh?, tags[]}], "gists":{post_id: 一句话要点}, "pin":[], "hide":[], "topics_zh", "followers_zh", "changelog"}`
- `data/weekly/YYYY-Www.json`：`{"week", "exclude":[], "people":{handle:{"bullets":[…]}}}`

JSON 键排序固定、缩进 2。导出脚本在末尾做「全文泄漏检查」（出现 `text` / `text_orig*` 键或超过 400 字的字符串就失败）。

## 刷新计划与配额
每天 1 次（北京时间 08:00，X 配额在此时重置）；每次约 155 次 X API 读取：账号资料 2 + 时间线约 131 + 话题计数 16 + 新闻 3 + 新闻相关帖子 3。限额：每分钟 30 次、每天 1000 次；脚本每批 ≤25 次、批间隔 60 秒。aihot.news 与 GitHub Trending 不占 X 配额。每天由 agent 写日报（三句话、必读与译文摘录、Top 30 一句话要点、置顶 / 隐藏复核），每周一写 Top 30 人物的本周要点。

## 从零重建
需要 Python 3.10+：`pip install -r src/requirements.txt`（Pillow 为运行依赖，playwright 仅测试用）。

1. 准备 X API 只读权限（users by usernames、user posts、posts counts recent、news search、posts by ids），把每次响应存成文件。
2. 编辑 `src/watchlist.json`（每个领域的 `accounts` / `accounts_zh` / `groups` / `trend_queries` / `news_query`）。
3. 抓取并入库（`ingest.py`、`ingest_tl.py`、`aihot_fetch.py`、`gh_trending.py`、`avatars_fetch.py`，细节见刷新流程文档）。
4. 写日报与周要点：`python3 daily_draft.py > /tmp/daily_draft.json`，按字段说明写 `daily/<日期>.json`；每周一 `XHOT_WEEKLY=1 python3 generate.py` 得到周草稿后写 `weekly/<周>.json`。
5. 生成与自检：`python3 generate.py`（输出 `site/`）→ `python3 test_escape.py`（转义 / 安全回归，必须 ALL PASS）→ `python3 fuzz.py 8`（随机恶意字符串灌进日报 / 周要点所有字段）→ `python3 gzserve.py site 8840 &` → `python3 shots.py --all`（截图 + CSP / JS 错误 / 溢出 / 字号 / 同源请求 / 功能断言）→ `python3 speed.py`（Fast 3G + CPU 4×）。
6. 发布：把 `site/` 复制到仓库根目录，`python3 export_data.py` 导出 `data/`，提交并推送到 `main`。推送凭据放环境变量，不要写进 git config、remote 或任何文件。

**安全设计**：每页 meta CSP（`script-src` 仅本站 + 主题预绘脚本的 sha256；`connect-src 'self'`；无第三方）与 referrer meta；所有外链经 `safe_url` / `safeUrl`（只放行 http(s)）并带 `rel="noopener noreferrer"`；所有文本先转义再渲染（含译文、摘录、⌘K 结果、分片数据）；嵌入 HTML 的 JSON 转义 `<>&`、U+2028/2029 与 `@@`；头像只接受 `pbs.twimg.com` 并重新编码；前端无 `eval` / `document.write` / `outerHTML`；本地存储只有主题、密度、已读 ID 与上次访问时间。`src/.gitignore` 已排除 `xhot.db`、`raw/`、头像缓存和生成目录，**不要把这些或任何密钥提交到仓库**。

## English

**XHOT** is a static briefing of hot posts on X across AI, making money and personal growth, refreshed daily at 08:00 (Asia/Shanghai). Pages: Today (three-sentence summary, must-reads, a ranked Top 30 with one-line takeaways), Domains, People (weekly takeaways for the top 30), News, Trends, a full archive and a ⌘K search. The UI is Chinese only. The public repo and site contain **only post IDs, metrics, short excerpts (≤220–320 characters) and agent-written Chinese summaries plus links back to X — no full tweet text**. No analytics, no third-party requests; read/new badges live only in your browser. The generator is host-agnostic (plain static output). Limits on GitHub Pages: no response headers (CSP via `<meta>` only, no `frame-ancestors`), soft bandwidth/size limits, unreliable access from mainland China. Tweet content belongs to the original authors.
