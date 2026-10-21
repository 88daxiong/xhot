# 贡献指南：重构页面（前端 / 模板 / CSS / JS）

本文写给想要**重构 XHOT 页面**的外部贡献者。数据抓取与内容编辑不在此范围内。你只需要本仓库和演示数据，**不需要维护者的任何令牌或账号**。

English summary: [见文末](#english)。

## 目录
- [1. 工作流程](#1-工作流程)
- [2. 本地环境（演示数据）](#2-本地环境演示数据)
- [3. 重构用的架构地图](#3-重构用的架构地图)
- [4. 硬性约束](#4-硬性约束)
- [5. 提 PR 前必须通过的检查](#5-提-pr-前必须通过的检查)
- [6. 拆分建议与评审合并](#6-拆分建议与评审合并)
- [English](#english)

## 1. 工作流程

1. Fork 本仓库，从最新的 `main` 拉分支：`git switch -c refactor/<主题>`（例如 `refactor/news-page`、`refactor/card-css`）。
2. 只在 `src/` 里改源码。仓库根目录的 `*.html`、`assets/`、`d/`、`day/`、`p/`、`feed/`、`data/` 都是生成产物，由维护者的自动任务重新生成；**PR 里不要提交这些产物**。
3. 向本仓库的 `main` 提 PR，并按模板（`.github/pull_request_template.md`）填写清单。
4. **禁止提交**：真实 `.env`、任何令牌 / 密钥、`xhot.db`、`raw/`、`site/`、`shots/`，以及任何真实个人信息（邮箱、手机号、本机路径、公司信息等）。`src/.gitignore` 已经排除了常见的本地文件，提交前请再用 `git diff --cached` 自查一遍。
5. 推文全文不能进仓库，测试数据也只用 `demo_seed.py` 生成的虚构内容。

## 2. 本地环境（演示数据）

需要 Python 3.10+。浏览器测试需要 Playwright（Chromium + WebKit）。

```bash
git clone https://github.com/<你的账号>/xhot.git && cd xhot/src
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python3 -m playwright install chromium webkit
python3 -m playwright install-deps webkit     # Linux 上 WebKit 需要系统依赖（需要 sudo）

python3 demo_seed.py          # 生成虚构的 xhot.db + raw/ + daily/ weekly/ 示例（离线，不需要任何令牌）
python3 generate.py           # 输出 site/
python3 gzserve.py site 8840  # 打开 http://127.0.0.1:8840/
```

- 预览**必须**用 `gzserve.py`，它带 gzip，和线上一致。不要用 `python3 -m http.server`，否则体积预算会测不准。
- 每次改完 `generate.py` / CSS / JS 都要重新运行 `python3 generate.py`。产物是静态文件，gzserve 不用重启。
- 想用系统 Chrome 跑浏览器测试时，设置 `CHROME_PATH=/path/to/chrome`。

## 3. 重构用的架构地图

### 3.1 生成器：哪个函数渲染哪个页面

所有页面都由 **`src/generate.py`** 一个文件生成。它没有模板引擎，HTML 片段直接写在 Python f-string 里，每个页面对应一个函数，最后用 `emit(路径, html)` 写出：

| 页面 | 函数 | 前端模块 |
|---|---|---|
| `index.html`（今日）与 `day/<日期>.html` | `today_page()`（必读卡片 `dhl()`、Top30 行 `t30row()`、侧栏 `mini_trends()` / `mini_fol()`） | core |
| `d/ai.html` `d/money.html` `d/growth.html` | `domain_page(d)` | core |
| `d/all.html`（全部归档） | `all_page()`，分片 `feed_shards()` | core + feed |
| `people.html` | `people_page()` | core |
| `p/<handle>.html` | `person(u)` | core + feed |
| `news.html` | `news()`（列表 `nrow()`、正文 `nbody()`） | core + news |
| `trends.html` | `trends()` | core |
| `agents.html` | `agents_page()`（卡片 `dt_card()`、行 `dt_row()`） | core + agents |
| `about.html` | `about_page()` | core |
| `hot.html` `accounts.html` `daily/*.html` | `stub()`（跳转页） | — |

共享片段（相当于 partials）：
- `page()`：外壳，包括 `<head>`、CSP、顶栏、页脚、脚本引用。
- `tools()`：页头工具条。
- `post_html()`：帖子卡片。
- `av()`：头像。
- `dctl()`：日期选择器。
- `seg_dom()` / `seg_links()`：领域分段控件。
- `tag_chips()`：标签。
- `CPY()`：复制按钮。
- `fresh()` / `health()`：数据新鲜度与数据健康表。

页面的 CSS 由 `page_css()` 按页裁剪后内联进去。JS 通过 `@@JS:<模块>@@` 占位符引用，生成时替换为带内容哈希的文件名，例如 `assets/core.<hash>.js`。

### 3.2 样式与设计系统

- `src/ds_tokens.json`：设计令牌，包括字号、字重、间距、圆角。构建时 `ds_snap.py` 会把越界值吸附到令牌上，`ds_audit.py` 负责校验。
- `src/style_base.css`：颜色变量与深色模式。
- `src/style_ds.css`：所有共享组件。
- `src/style.css` / `src/style_final.css`：页面级样式。
- 令牌表、颜色表、组件规则见 [README · 设计系统](README.md#设计系统)。

### 3.3 JS 模块

| 文件 | 内容 |
|---|---|
| `app_core.js`（每页都加载） | 主题切换；**`xp()` 展开 / 收起**（高度动画、`aria-expanded`、减少动效时直接切换，长帖 `.pt.clp` 6 行折叠）；**帖子展开 `pexp()`**：每张 `.post` 都有「展开」，解除折叠并按 `data-ts` / `data-m` 生成详情 `.pxd`；`<details>` 行（Top30、Agent 列表）也走 `xp()` 动画；**GitHub 条目** `button.grow` 展开 `.gxd`，首次展开时读 `assets/gh.json`；**一键复制**：`[data-copy]` 按钮在捕获阶段处理，优先 `navigator.clipboard`，不可用时退回 textarea；相对时间补齐；日期选择器；**⌘K 搜索**：首次打开时才读 `assets/search.json`；`esc()` / `lnk()` / `safeUrl()` |
| `app_feed.js`（全部归档 `d/all` / 个人页 `p/*`） | 读 `feed/<日期>.json` 与 `p/<handle>.json` 分片；全部归档的作者表读 **`assets/pm.json`**，个人页直接用页面内联的 `#tw-meta`，不发请求 |
| `app_news.js`（资讯页） | 列表与首条正文由服务端渲染；点开某条时只读它所在的 **`assets/nb/<k>.json`** 分片（每片 10 条），悬停、触摸或聚焦时预取 |
| `app_agents.js`（Agent 页） | 标签页、分页、详情面板；首次打开详情时读 **`assets/agents.json`** |

### 3.4 页面依赖的数据契约（改形状就必须同时改生成器）

下面这些 JSON 由 `generate.py` 写出，再由前端读取。**重构前端时请保持这些形状不变**。如果确实要改，必须在同一个 PR 里同时修改 `generate.py` 中对应的写出代码，以及所有读取它的 JS，并把契约变化写进 PR 说明。

| 文件 | 形状（数组按位置取值，顺序就是契约） |
|---|---|
| `assets/search.json` | `{"p":[[handle,显示handle,名字,头像文件,色相,主领域,"领域,…",粉丝,日期,中文名]], "t":[[标签键,标签名,领域]], "d":[分片日期…], "dy":[日报日期…], "g":[[post_id,handle,要点,日期]], "tp":[[话题,领域]], "gr":[[owner/repo,中文名,分类]]}` |
| `assets/pm.json` | 与 `search.json` 相同的 `p` / `t` / `d` 三个键（精简版） |
| `feed/<YYYY-MM-DD>.json` | `[[id, UTC时间, 摘录, 赞, 转, 回复, 引用, 浏览, 热度, 重要度, handle, "标签,…", 是否英文0/1]]`，每天最多 200 条 |
| `p/<handle>.json` | 个人页「再显示」用的时间线分片（字段同上） |
| `assets/nb/<k>.json` | `["<div class=nb>…</div><div class=act>…</div>", …]`：第 k 片，对应第 k×10 起的 10 条资讯，内容是**生成器已转义**的 HTML 片段 |
| `assets/gh.json` | `{"owner/repo":[README摘要, 中文简介, 描述, 语言, stars, 今日增星, 本周增星或null]}`（趋势页 GitHub 条目，列表元素 `data-gj` 给出带版本号的文件名） |
| 帖子卡片 `data-m` | `"赞,转,评论,引用,浏览,热度"`（服务端 `post_html()` 与 `app_feed.js` 的 `card()` 都要写） |
| `assets/agents.json` | `{"owner/repo":[README摘要, 中文简介, 描述, 话题[], stars, 今日增星, 本周增星, 语言, 创建时间, 中文名]}` |
| `assets/status.html` | 数据健康表的 HTML 片段 |
| 页面上的 `data-*` 属性与 `#tw-meta` | 例如 `data-copy`、`data-days` / `data-cur` / `data-mode`（日期选择器）、`data-src`（资讯来源筛选）。JS 和测试都会选中这些属性，改名要同步修改 |

文件名保持稳定，内容哈希只作为 `?v=` 版本号写在引用处。公开数据目录 `data/` 的格式见 [README · data/ 数据格式](README.md#data-数据格式不含任何推文全文)。

## 4. 硬性约束

- **字号**：沿用 AIHOT 字号阶梯（12 / 13 / 14 / 16 / 20 / 28px，手机正文 15 / 17），以 rem 输出；不要引入新字号、新间距、新圆角，`ds_audit.py` 会拦下越界值。
- **设计系统一致**：共用 `style_ds.css` 里的组件，例如按钮 `.btn`、卡片、分段控件、标签页、分页；不要为单个页面再造一套。选择器要带页面作用域，比如 Agent 网格写作 `.dtpan .dgrid`，通用类名会在多个页面复用。
- **多端适配**：手机（360–430）、平板（768 / 1024）、桌面（1280 / 1440）都要可用，不得出现横向溢出；手机触控目标 ≥44px，阅读文字 ≥15px。
- **深色模式**：所有文字对比度 ≥ WCAG AA（4.5:1），浅色和深色都要检查。
- **体积预算**（gzip，首次加载）：首页首屏 ≤80KB；其余页面 ≤150KB；LCP ≤1.0s（Fast 3G）。由 `shots.py` 断言，`speed.py` 可自测。
- **无布局偏移**：CLS ≤ 0.001。页面源码里不烘焙相对时间，图片要有尺寸，首屏以下懒加载。
- **转义 / XSS**：服务端文本一律走 `e()`，即先脱敏再转义；链接走 `safe_url()`。前端只用 `textContent` 或 `esc()` 插入外部数据，链接走 `safeUrl()`。禁止 `eval`、`document.write`、`outerHTML` 和内联事件属性。CSP 不得放宽：不加第三方源，不加新的内联脚本；`img-src` 只允许本站和 `data:`。
- **GitHub / X 合规**：不展示推文全文，只展示摘录，并保留「原帖 ↗」链接；头像只来自 X 官方图床并重新编码；不加跟踪脚本，不加第三方嵌入。详见 [README · 合规与内容策略](README.md#合规与内容策略)。
- **卡片头部一行**：头像 + 作者名 + handle + 点赞 + 动作按钮。桌面和平板上作者名、handle 都不得换行；空间不够时，让点赞和按钮整体换到下一行。
- **一切皆可展开**：每张帖子卡片、每个 GitHub 条目都必须能展开，并且复用 `pexp()` / `xp()` / `button.grow` + `.gxd` 这几条路径（键盘可用、减少动效时直接切换）；展开详情要懒加载，不能挤占体积预算。
- **复制按钮只放动作区**：新的复制按钮一律放进卡片底部的 `.act`，排在最后；不要往卡片头部塞按钮。按钮要带 `aria-label`，并且必须通过 `CPY()` 生成，它只接受经过 `safe_url()` 校验的链接。

## 5. 提 PR 前必须通过的检查

在 `src/` 目录下，先运行 `python3 demo_seed.py && python3 generate.py`，然后**逐个**运行下面的检查，每个都必须通过：

```bash
python3 qa.py                          # 内容 QA（严格模式）
XHOT_QA_LIGHT=1 python3 qa.py          # 可选：轻量刷新模式（只放行 Top30 里带 EN 标记的英文摘录兜底）；PR 以严格模式通过为准
python3 test_escape.py                 # 转义 / XSS 回归，必须 ALL PASS
python3 fuzz.py 8                      # 随机恶意字符串
python3 check_links.py site            # 站内链接与分片文件

python3 gzserve.py site 8840 &         # 以下需要预览服务器
python3 ds_audit.py                    # 设计令牌
python3 mobile_audit.py                # 手机 / 平板，Chromium + WebKit
python3 expand.py                      # 每张帖子卡片 / GitHub 条目都能展开收起（四个宽度 × 两个引擎）+ 721–1100px CLS
python3 card_layout.py                 # 卡片头部：1440/1280/1024/768/390 × Chromium+WebKit，作者名不换行、按钮不重叠
python3 news_all.py                    # 逐条打开资讯
python3 shots.py --all                 # 截图 1440（浅 / 深）/ 390 + CSP / JS 错误 / 体积预算断言，输出到 shots/
python3 mobile_audit.py --shots        # 同时输出平板截图到 _m/：ipadmini = 768、ipadpro = 1024
```

请把改动页面在 1440 / 1024 / 768 / 390 下的截图附到 PR 里：1440 和 390 取自 `shots/`，1024 和 768 取自 `_m/`。截图文件不要提交进仓库。1024 和 768 的布局另由 `card_layout.py` 断言。

## 6. 拆分建议与评审合并

- **按页面拆成小 PR**，例如先抽共享组件或 CSS，再按 news、agents、今日页、人物页、归档页逐个改。每个 PR 都应该能独立通过全部检查，方便评审和回滚。
- 一个 PR 只做一件事：纯样式重构不要夹带数据契约改动；需要改契约的，单独提一个 PR。
- **由维护者评审并合并。** `main` 会被自动任务定时重新生成并发布到 GitHub Pages，所以 **`main` 必须随时可部署**：不能合入失败的检查、半成品或需要后续 PR 才能运行的改动。
- 合并之后，下一次自动刷新会用新的源码重新生成全站。

---

## English

**Contributor guide for refactoring the pages (front end / templates / CSS / JS).** You never need the maintainer's tokens.

- **Workflow**: fork → branch from `main` as `refactor/<topic>` → PR to `main` using the PR template. Edit `src/` only; root `*.html`, `assets/`, `d/`, `day/`, `p/`, `feed/`, `data/` are build outputs, so don't commit them. Never commit a real `.env`, tokens, `xhot.db`, `raw/`, `site/`, `shots/`, or any personal data.
- **Setup**: `pip install -r requirements.txt`, `playwright install chromium webkit`, then `python3 demo_seed.py && python3 generate.py && python3 gzserve.py site 8840`. Always preview with `gzserve.py`, not `http.server`.
- **Architecture**: one generator, `src/generate.py`, with one function per page (`today_page`, `domain_page`, `all_page`, `people_page`, `person`, `news`, `trends`, `agents_page`, `about_page`). Shared partials are `page`, `post_html`, `av`, `dctl`, `CPY`. Tokens live in `ds_tokens.json`, components in `style_ds.css`. JS: `app_core.js` (xp expander, copy buttons, ⌘K with lazy `search.json`), `app_feed.js` (feed shards, `pm.json`), `app_news.js` (lazy `assets/nb/<k>.json` shards), `app_agents.js` (`agents.json`). The JSON shapes in §3.4 are contracts; if you change one, change the generator and every reader in the same PR.
- **Hard constraints**: AIHOT type scale and tokens only; shared components; works on mobile, tablet and desktop; WCAG AA in light and dark; budgets of ≤80KB first screen on home and ≤150KB on other pages; CLS ≈ 0; escape/XSS rules and a strict CSP; GitHub/X compliance (no full tweet text). The card header stays on one line, and copy buttons go only in the `.act` action row.Every post card and GitHub item must be expandable via the shared `pexp()` / `xp()` paths, with lazy-loaded details.
- **Required checks**: qa (strict; `XHOT_QA_LIGHT=1` is the light-refresh variant), test_escape, fuzz 8, check_links, ds_audit, mobile_audit (Chromium + WebKit), card_layout, expand, news_all, `shots.py --all` (1440/390 shots plus budgets) and `mobile_audit.py --shots` (768/1024 shots in `_m/`). Attach screenshots at 1440/1024/768/390.
- **Process**: keep PRs small, one page each. The maintainer reviews and merges. `main` is regenerated and published by an automated job, so it must always stay deployable.
