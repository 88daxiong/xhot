# XHOT · X 热点雷达

在线访问：<https://88daxiong.github.io/xhot/>

XHOT 是一个纯静态的 X（Twitter）热点看板，关注 AI、搞钱（创业 / 创作者经济）、个人成长三个领域约 130 个账号，每天自动刷新一次。

| 页面 | 内容 |
|---|---|
| `index.html` 🔥 热帖 | 顶部 10 秒速览（24 小时新帖、最热帖、粉丝涨最多、话题涨最快、AIHOT 头条）；等高卡片网格，可按 **近一周热度 / 全局热度 / 时间** 排序，按领域筛选，全文搜索；每人最多 3 条 |
| `accounts.html` 👤 账号榜 | 每个账号一张卡片（头像、名字、粉丝数、较上次变化），按领域 / 分组筛选，按粉丝数或变化排序 |
| `news.html` 📰 资讯 | AIHOT 中文资讯（热点综述、日报、精选）在前，X 新闻（英文摘要 + 相关帖子原文）在后，卡片内可直接阅读全文 |
| `trends.html` 📈 趋势 | X 话题讨论量涨跌（排名、近 6 日迷你折线、昨日条数、涨跌条）和 GitHub 今日 AI / 开发工具趋势 |
| `p/<handle>.html` 个人页 | 单个账号的全部已存推文，三种排序 + 搜索 + 发帖统计 |

所有页面支持浅色 / 深色 / 跟随系统，界面为中文。顶栏的「数据」标签可展开**数据健康**面板，显示每个数据源的最近抓取时间和规模（超过 26 小时标黄，超过 48 小时标红）。

## 架构与数据流

```
X API（只读）──┐
aihot.news API ─┼─> raw/*.json 快照 ──> SQLite（xhot.db）──> Python 静态生成器 ──> HTML/CSS/JS/JSON ──> GitHub Pages
GitHub Trending ┘                                         └─> data/*.json 备份
```

- **X API（只读）**：账号资料与粉丝数（users by usernames）、各账号时间线（user posts，不含回复和转推）、话题计数（posts counts recent）、新闻（news search）及其相关帖子（posts by ids）。
- **aihot.news 公开 API**：AI 资讯精选、日报、多信源热点及其综述，无需 Key。感谢 [KKKKhazix/AIHOT](https://github.com/KKKKhazix/AIHOT)（MIT 许可）。原文全文的版权属于原站，本站只展示 AIHOT 的摘要 / 综述并附原文链接。
- **GitHub Trending**：匿名读取公开的 github.com/trending 页面，筛选 AI / 开发工具相关仓库。
- **存储**：SQLite（`followers` 粉丝时间序列、`tweets` 推文，每账号保留最新 200 条），原始响应按时间戳存在 `raw/`。
- **生成**：`src/generate.py` 读取数据库和最新快照，输出 4 个栏目页 + 每个账号一个个人页。CSS 内联；JS、热帖数据、头像用内容哈希命名（可长期缓存）；热帖完整数据和个人页推文 JSON 按需加载；头像本地化为 96px WebP，首屏内联、其余滚动时懒加载。
- **发布**：生成结果推送到本仓库 `main` 分支，由 GitHub Pages 直接托管。

## 仓库结构

```
index.html  accounts.html  news.html  trends.html   # 4 个栏目页
p/<handle>.html                                     # 个人页
p/<handle>.<hash>.json                              # 个人页推文数据（按需加载）
assets/app.<hash>.js                                # 前端脚本
assets/hot.<hash>.json                              # 热帖完整数据（切换排序 / 筛选 / 搜索时加载）
assets/av/<handle>.<hash>.webp                      # 本地化头像
data/                                               # JSON 数据备份（见下）
src/                                                # 生成器源码，可从零重建（见下）
```

### data/ 数据格式

- `data/accounts.json`：`{"accounts": [{handle, user_id, name, domains[], groups[], zh, followers, followers_ts, tweets_stored}]}`
- `data/followers_history.json`：`{"history": {"<handle>": [{ts, followers, following, tweets}]}}`，`ts` 为北京时间 `YYYYMMDD_HHMMSS`
- `data/tweets/<handle>.json`：`{"handle", "tweets": [{id, created_at(UTC), text, lang, metrics{like, retweet, reply, quote, impression, bookmark}, url}]}`，最新在前，最多 200 条；长推文为全文

JSON 键排序固定、缩进 2，便于看 diff。推文内容版权归原作者。

## 规则

- **热度** = 赞 + 2×转推 + 3×引用 + 评论 + 收藏。
- **近一周热度**：过去 7 天发布的帖子按热度排序；**全局热度**：全部已存帖子按热度排序；**时间**：最新在前。热帖页每人最多 3 条。
- **语言过滤**：只保留中文和英文内容（按 X 返回的 `lang` 和文字字符集判断，日文假名、韩文、西里尔文等占比高的内容会被过滤）；个人页可切换「显示全部语言」。
- **话题涨跌**：昨日帖子数 vs 之前几天的日均值。
- **粉丝变化**：本次抓取 vs 上一次抓取。

## 刷新计划与配额

- 每天刷新 **1 次**（北京时间 07:58）。
- 每次约 155 次 X API 读取：账号资料 2 + 时间线约 131（每账号 1 次，增量 `since_id`）+ 话题计数 16 + 新闻 3 + 新闻相关帖子 3。
- 参考限额：每分钟 30 次、每天 1000 次；脚本按每批 ≤25 次、批间隔 60 秒执行。aihot.news 与 GitHub Trending 不占 X 配额。

## 从零重建（如果站点坏了）

需要 Python 3.10+ 和 `Pillow`（`pip install pillow`）；截图自检需要 `playwright`。

1. **准备 X API 只读权限**：任意能调用以下 X API v2 只读端点的方式均可 —— users by usernames、user posts timeline、posts counts recent、news search、posts by ids。把每次调用的 JSON 响应存成文件（文件里允许 JSON 前后有说明文字，入库脚本会截取 `{ ... }`）。
2. **配置关注列表**：编辑 `src/watchlist.json`。每个领域（`ai` / `money` / `growth`）包含：
   - `accounts`、`accounts_zh`：账号 handle 列表；`groups`：可选的分组 `{"分组名": [handle, ...]}`
   - `trend_queries`：`{"话题名": "X 搜索语句"}`，用于话题计数
   - `news_query`：新闻搜索关键词
3. **抓取并入库**（在 `src/` 目录下）：
   ```bash
   # 账号资料（user.fields=public_metrics,description,verified,profile_image_url）
   python3 ingest.py users_ai_all <结果文件> users_other <结果文件>
   # 时间线：先列出待抓账号，再逐个调用 user posts（max_results=25, exclude=replies,retweets,
   #   post.fields=created_at,public_metrics,note_tweet,lang，有 since_id 时带上）
   python3 tl_plan.py
   python3 ingest_tl.py <所有时间线结果文件...>
   # 话题计数（granularity=day），每个 trend_queries 一次
   python3 ingest.py counts_ai__<话题名> <结果文件> ...
   # 新闻（news.fields 包含 cluster_posts_results,hook,summary 等）与相关帖子
   python3 ingest.py news_ai <文件> news_money <文件> news_growth <文件>
   python3 news_posts_plan.py        # 输出每个领域要查的帖子 id
   python3 ingest.py news_posts_ai <文件> news_posts_money <文件> news_posts_growth <文件>
   # 不占 X 配额的公开数据与头像
   python3 aihot_fetch.py
   python3 gh_trending.py
   python3 avatars_fetch.py
   ```
4. **生成与自检**：
   ```bash
   python3 generate.py                     # 输出到 src/site/
   python3 gzserve.py site 8802 &          # 本地预览（带 gzip，模拟 Pages）
   python3 shots.py http://127.0.0.1:8802/ # 截图 + 溢出 / 对齐 / JS 错误自检（可用 CHROME_PATH 指定浏览器）
   python3 speed.py http://127.0.0.1:8802/ # 冷启动测速（无节流 + Fast 3G）
   ```
5. **发布**：把 `src/site/` 下的 `*.html`、`p/`、`assets/` 复制到仓库根目录，`python3 export_data.py` 导出 `data/`，提交并推送到 `main`。推送凭据请放在环境变量里（例如 `GITHUB_TOKEN`，只需本仓库的 contents 写权限），不要写进 git config、remote 或任何文件。仓库设置里开启 GitHub Pages（Deploy from branch → `main` / root）。

`src/.gitignore` 已排除 `xhot.db`、`raw/`、头像缓存和生成目录，不要把这些或任何密钥提交到仓库。

## English

**XHOT** is a static dashboard of hot posts on X (Twitter) across three themes: AI, making money (startups / creator economy) and personal growth. It has four tabs: Hot posts (heat-ranked card grid with week / all-time / latest sorting, search and a 10-second overview), Accounts (follower cards with change), News (AIHOT Chinese digests first, then X news summaries with source posts) and Trends (topic volume changes with sparklines, GitHub trending AI repos). Each tracked account also has a person page.

Data comes from read-only X API endpoints, the public [aihot.news](https://aihot.news) API (credit: [KKKKhazix/AIHOT](https://github.com/KKKKhazix/AIHOT), MIT) and the public GitHub Trending page. It is stored in SQLite, rendered by a small Python static generator (`src/`) and served by GitHub Pages. Refresh runs once a day at 07:58 Asia/Shanghai (about 155 X API reads). Heat = likes + 2×reposts + 3×quotes + replies + bookmarks. Only Chinese and English content is shown. JSON backups live in `data/`. See the Chinese section "从零重建" above for rebuild steps.
