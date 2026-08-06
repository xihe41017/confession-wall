import { reactive } from 'vue'
import { api } from '../api'

export const auth = reactive({
  token: localStorage.getItem('token') || '',
  user: null,
})

export const isLoggedIn = () => !!auth.token && !!auth.user
export const isAdmin = () => auth.user && ['admin', 'super_admin'].includes(auth.user.role)
export const isSuperAdmin = () => auth.user?.role === 'super_admin'

// 权限判断（超管恒有全部权限）
export function hasPerm(key) {
  const u = auth.user
  if (!u) return false
  if (u.role === 'super_admin') return true
  return Array.isArray(u.permissions) && u.permissions.includes(key)
}

// 是否能进入管理后台（任一管理权限）
export function canAccessAdmin() {
  return hasPerm('content.manage') || hasPerm('ban.manage') || hasPerm('settings.view')
}

export function setSession(token, user) {
  auth.token = token
  auth.user = user
  localStorage.setItem('token', token)
}

export function logout() {
  auth.token = ''
  auth.user = null
  localStorage.removeItem('token')
}

export async function initAuth() {
  if (auth.token && !auth.user) {
    try {
      auth.user = await api.me()
    } catch {
      logout()
    }
  }
}
