## 改了什么 / What changed
<!-- 页面、组件，以及为什么这样改 / pages, components, and why -->

## 数据契约 / Data contracts
- [ ] 没有改 JSON 形状和 `data-*` 属性 / No JSON shape or `data-*` change
- [ ] 或者：已在同一个 PR 里同时修改生成器和所有读取方，并在上方写明 / Or: generator and all readers updated in this PR, described above

## 检查清单 / Checklist（在 `src/` 下运行 `demo_seed.py && generate.py` 后，用 gzserve 预览）
- [ ] 分支 `refactor/<topic>`，基于最新 `main` / Branch from latest `main`
- [ ] 只改了 `src/`，没有提交生成产物（根目录 html、assets、d、day、p、feed、data）/ Only `src/` changed
- [ ] 没有 `.env`、令牌、`xhot.db`、`raw/`、`shots/`、个人信息或本机路径 / No secrets or personal data
- [ ] `qa.py` 通过 / passes
- [ ] `test_escape.py` ALL PASS
- [ ] `fuzz.py 8` 通过 / passes
- [ ] `check_links.py site` 通过 / passes
- [ ] `ds_audit.py` 通过（只用设计令牌）/ passes
- [ ] `mobile_audit.py` 通过（Chromium + WebKit）/ passes
- [ ] `expand.py` 通过（每张帖子卡片 / GitHub 条目可展开，768 无布局偏移）/ passes
- [ ] `card_layout.py` 通过（卡片头部一行，按钮不重叠）/ passes
- [ ] `news_all.py` 通过 / passes
- [ ] `shots.py --all` 通过（体积预算、CLS、CSP、无 JS 错误）/ passes
- [ ] 已附 1440 / 1024 / 768 / 390 截图（`shots/` + `mobile_audit.py --shots` 的 `_m/`）（浅色和深色）/ Screenshots attached
- [ ] 深色模式对比度 ≥ AA；触控目标 ≥44px（手机）/ Dark-mode contrast and touch targets OK
- [ ] 复制按钮只在 `.act` 动作区；没有放宽 CSP，没有新增第三方源 / Copy buttons in action row only; CSP unchanged
- [ ] PR 足够小（一个页面或一个组件），合并后 `main` 仍可直接部署 / Small PR; `main` stays deployable
