/* 主题预绘：在首帧前根据 localStorage / 系统偏好设置明暗，避免刷新闪白。
   独立文件而非内联脚本，以满足站点 CSP（script-src 'self'，不允许新增内联脚本）。 */
;(function () {
  try {
    var raw = localStorage.getItem('xhot-ui')
    var theme = raw ? JSON.parse(raw).state.theme || 'system' : 'system'
    var dark =
      theme === 'dark' ||
      (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)
    document.documentElement.classList.toggle('dark', dark)
    document.documentElement.classList.toggle('light', !dark)
  } catch (e) {
    /* 忽略：主题预绘失败不影响渲染 */
  }
})()
