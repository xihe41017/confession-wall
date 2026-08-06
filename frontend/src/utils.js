// 卡片主题配色
export const THEMES = {
  pink: { label: '初恋粉', cls: 'theme-pink' },
  rose: { label: '玫瑰红', cls: 'theme-rose' },
  purple: { label: '梦幻紫', cls: 'theme-purple' },
  blue: { label: '天空蓝', cls: 'theme-blue' },
  orange: { label: '落日橙', cls: 'theme-orange' },
  mint: { label: '薄荷绿', cls: 'theme-mint' },
}

export function themeCls(name) {
  return THEMES[name]?.cls || THEMES.pink.cls
}

// 相对时间
export function formatTime(iso) {
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const diff = (Date.now() - d.getTime()) / 1000
  if (diff < 60) return '刚刚'
  if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
  if (diff < 86400 * 7) return `${Math.floor(diff / 86400)} 天前`
  const now = new Date()
  const sameYear = d.getFullYear() === now.getFullYear()
  return sameYear
    ? `${d.getMonth() + 1}月${d.getDate()}日`
    : `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

// 状态标签
export function statusLabel(s) {
  return { pending: '待审核', approved: '已上墙', rejected: '已驳回' }[s] || s
}
export function userStatusLabel(s) {
  return { active: '正常', pending: '待激活', banned: '已拉黑' }[s] || s
}
export function roleLabel(r) {
  return { super_admin: '超级管理员', admin: '管理员', user: '普通用户' }[r] || r
}

// 头像配色（根据昵称哈希取色）
const AVATAR_COLORS = ['#e5486f', '#8b5cf6', '#3b82f6', '#f59e0b', '#22c55e', '#06b6d4', '#ec4899', '#6366f1']
export function avatarColor(name = '') {
  let h = 0
  for (const c of name) h = (h * 31 + c.charCodeAt(0)) % 997
  return AVATAR_COLORS[h % AVATAR_COLORS.length]
}

// 作者展示头衔（管理员/超管自动头衔优先于自定义头衔）
export function authorTitle(author) {
  if (!author) return null
  if (author.role === 'super_admin') return '超级管理员'
  if (author.role === 'admin') return '管理员'
  return author.title || null
}
