const BASE = import.meta.env.VITE_API_BASE || '/api'

// 客户端设备标识（匿名限发用）
function deviceId() {
  let id = localStorage.getItem('device_id')
  if (!id) {
    id = 'd' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10)
    localStorage.setItem('device_id', id)
  }
  return id
}

async function request(path, { method = 'GET', body, headers = {} } = {}) {
  const opts = {
    method,
    headers: { ...headers, 'X-Device-Id': deviceId() },
  }
  if (body !== undefined) {
    opts.headers['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }
  const res = await fetch(BASE + path, opts)
  if (res.status === 204) return null
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(data.detail || '请求失败，请稍后再试')
    err.status = res.status
    throw err
  }
  return data
}

const qs = (params) =>
  new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== '' && v != null)
  ).toString()

export function authHeader() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 文件上传（FormData，浏览器自动设置 multipart 边界）
export async function uploadFile(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(BASE + '/upload', { method: 'POST', body: fd, headers: authHeader() })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const err = new Error(data.detail || '上传失败，请稍后再试')
    err.status = res.status
    throw err
  }
  return data // { url }
}

export const api = {
  // ---------- 站点 ----------
  health: () => request('/health'),
  siteInfo: () => request('/site/info'),

  // ---------- 公开内容 ----------
  listPosts: (params = {}) => request(`/posts?${qs(params)}`),
  getPost: (id) => request(`/posts/${id}`),
  // 发布/评论带登录令牌：登录用户不受匿名限发限制
  createPost: (data) => request('/posts', { method: 'POST', body: data, headers: authHeader() }),
  likePost: (id) => request(`/posts/${id}/like`, { method: 'POST' }),
  listComments: (postId) => request(`/posts/${postId}/comments`),
  addComment: (postId, data) => request(`/posts/${postId}/comments`, { method: 'POST', body: data, headers: authHeader() }),
  likeComment: (postId, commentId) => request(`/posts/${postId}/comments/${commentId}/like`, { method: 'POST' }),

  // ---------- 账号 ----------
  register: (data) => request('/auth/register', { method: 'POST', body: data }),
  login: (data) => request('/auth/login', { method: 'POST', body: data }),
  me: () => request('/auth/me', { headers: authHeader() }),
  changeOwnPassword: (data) => request('/auth/password', { method: 'POST', body: data, headers: authHeader() }),

  // ---------- 内容管理（管理员） ----------
  adminStats: () => request('/admin/stats', { headers: authHeader() }),
  adminPosts: (params = {}) => request(`/admin/posts?${qs(params)}`, { headers: authHeader() }),
  adminSetStatus: (id, status) => request(`/admin/posts/${id}/status`, { method: 'POST', body: { status }, headers: authHeader() }),
  adminPinPost: (id, pinned) => request(`/admin/posts/${id}/pin`, { method: 'POST', body: { pinned }, headers: authHeader() }),
  adminEditPost: (id, data) => request(`/admin/posts/${id}/edit`, { method: 'POST', body: data, headers: authHeader() }),
  adminDeletePost: (id) => request(`/admin/posts/${id}`, { method: 'DELETE', headers: authHeader() }),
  adminListComments: (postId) => request(`/admin/comments?post_id=${postId}`, { headers: authHeader() }),
  adminEditComment: (id, data) => request(`/admin/comments/${id}/edit`, { method: 'POST', body: data, headers: authHeader() }),
  adminDeleteComment: (id) => request(`/admin/comments/${id}`, { method: 'DELETE', headers: authHeader() }),

  // ---------- 账号管理（超级管理员） ----------
  adminListUsers: (params = {}) => request(`/admin/users?${qs(params)}`, { headers: authHeader() }),
  adminSetUserRole: (id, role) => request(`/admin/users/${id}/role`, { method: 'POST', body: { role }, headers: authHeader() }),
  adminSetUserPermissions: (id, permissions) => request(`/admin/users/${id}/permissions`, { method: 'POST', body: { permissions }, headers: authHeader() }),
  adminSetUserTitle: (id, title) => request(`/admin/users/${id}/title`, { method: 'POST', body: { title }, headers: authHeader() }),
  adminSetUserStatus: (id, status) => request(`/admin/users/${id}/status`, { method: 'POST', body: { status }, headers: authHeader() }),
  adminResetPassword: (id, password) => request(`/admin/users/${id}/password`, { method: 'POST', body: { password }, headers: authHeader() }),
  adminListBannedIps: () => request('/admin/users/banned-ips', { headers: authHeader() }),
  adminBanIp: (ip, reason) => request('/admin/users/banned-ips', { method: 'POST', body: { ip, reason }, headers: authHeader() }),
  adminUnbanIp: (ip) => request(`/admin/users/banned-ips/${ip}`, { method: 'DELETE', headers: authHeader() }),

  // ---------- 服务器设置 ----------
  adminListSettings: () => request('/admin/settings', { headers: authHeader() }),
  adminUpdateSetting: (key, value) => request(`/admin/settings/${key}`, { method: 'PUT', body: { value }, headers: authHeader() }),
}
