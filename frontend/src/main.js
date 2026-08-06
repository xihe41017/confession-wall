import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { initAuth } from './store/auth'
import { getSite } from './store/site'
import './style.css'

const withTimeout = (p, ms) =>
  Promise.race([p, new Promise((r) => setTimeout(() => r(null), ms))])

// 启动流程：先展示校徽 → 加载资源 → 再显示应用，丝滑过渡
async function boot() {
  const splash = document.getElementById('splash')
  const logo = document.getElementById('splashLogo')
  const fill = document.querySelector('.splash-bar-fill')

  // 校徽加载 + 最短展示时间（网络慢也不超过 3.5 秒）
  const minTime = new Promise((r) => setTimeout(r, 1300))
  const logoLoad = new Promise((r) => {
    if (logo.complete && logo.naturalWidth) return r()
    logo.onload = logo.onerror = r
  })
  await withTimeout(Promise.all([minTime, logoLoad]), 3500)

  // 进度条动画
  let p = 0
  const tick = setInterval(() => {
    p = Math.min(92, p + Math.random() * 20)
    if (fill) fill.style.width = p + '%'
  }, 160)

  // 并行初始化登录态 + 站点信息（带超时，防止卡在启动页）
  const siteInfo = await withTimeout(getSite().catch(() => null), 3000)
  await withTimeout(initAuth(), 3000)

  const nameEl = document.getElementById('splashName')
  if (nameEl && siteInfo?.site_name) nameEl.textContent = siteInfo.site_name
  if (siteInfo?.site_name) document.title = siteInfo.site_name

  // 挂载应用（失败也不阻塞进入页面）
  try {
    createApp(App).use(router).mount('#app')
  } catch (e) {
    console.error('[boot] 应用挂载失败', e)
  }

  // 无论初始化结果如何，都淡出启动页
  p = 100
  if (fill) fill.style.width = '100%'
  clearInterval(tick)
  requestAnimationFrame(() => {
    splash.classList.add('splash-out')
    setTimeout(() => splash.remove(), 650)
  })
}

boot()
