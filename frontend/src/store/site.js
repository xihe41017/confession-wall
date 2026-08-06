import { ref } from 'vue'
import { api } from '../api'

// 站点信息缓存（boot 时已拉取，组件同步读取避免闪现旧值）
export const site = ref(null)
let loading = null

export async function getSite() {
  if (site.value) return site.value
  if (!loading) {
    loading = api
      .siteInfo()
      .then((d) => {
        site.value = d
        return d
      })
      .finally(() => {
        loading = null
      })
  }
  return loading
}

// 站点名称（供导航/标题等同步使用，无需等待异步）
export const siteName = () => site.value?.site_name || '校园墙'
