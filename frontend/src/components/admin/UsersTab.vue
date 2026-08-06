<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../../api'
import { auth } from '../../store/auth'
import { toastSuccess, toastError } from '../../store/toast'
import { avatarColor, formatTime, roleLabel, userStatusLabel } from '../../utils'
import { PERMS, PERM_GROUPS } from '../../perms'
import Modal from '../Modal.vue'

const users = ref([])
const page = ref(1)
const pages = ref(1)
const loading = ref(false)
const search = ref('')
const statusFilter = ref('')
const busy = ref({})

// 弹窗状态
const titleModal = ref(null)   // { user, value }
const pwdModal = ref(null)     // { user, value }
const confirmModal = ref(null) // { title, message, danger, run }
const ipModal = ref(null)      // { ip }
const permModal = ref(null)    // { user, perms:Set }

const TABS = [
  { key: '', label: '全部' },
  { key: 'active', label: '正常' },
  { key: 'pending', label: '待激活' },
  { key: 'banned', label: '已拉黑' },
]

async function load(reset = true) {
  if (reset) {
    page.value = 1
    users.value = []
  }
  loading.value = true
  try {
    const d = await api.adminListUsers({
      page: page.value,
      page_size: 15,
      search: search.value.trim(),
      status: statusFilter.value,
    })
    if (reset) users.value = d.items
    else users.value.push(...d.items)
    pages.value = d.pages
  } catch (e) {
    toastError(e.message)
  } finally {
    loading.value = false
  }
}

function switchTab(key) {
  statusFilter.value = key
  load(true)
}

// 加载更多：先翻页再拉取，避免重复加载
function loadMore() {
  if (loading.value || page.value >= pages.value) return
  page.value += 1
  load(false)
}

function openTitle(u) {
  titleModal.value = { user: u, value: u.title || '' }
}
async function confirmTitle() {
  const t = titleModal.value
  if (!t) return
  try {
    await api.adminSetUserTitle(t.user.id, t.value.trim() || null)
    toastSuccess('头衔已更新')
    await load(true)
  } catch (e) {
    toastError(e.message)
  } finally {
    titleModal.value = null
  }
}

function openPassword(u) {
  pwdModal.value = { user: u, value: '' }
}
async function confirmPassword() {
  const t = pwdModal.value
  if (!t) return
  if (t.value.length < 6) return toastError('密码至少 6 位')
  try {
    await api.adminResetPassword(t.user.id, t.value)
    toastSuccess('密码已重置')
    pwdModal.value = null
  } catch (e) {
    toastError(e.message)
  }
}

function confirmStatus(u, status) {
  const label = { active: '恢复为正常', banned: '拉黑', pending: '激活' }[status]
  confirmModal.value = {
    title: `${label}账号`,
    message: `确定将「${u.nickname || u.username}」${label}吗？`,
    danger: status === 'banned',
    run: async () => {
      await api.adminSetUserStatus(u.id, status)
      toastSuccess(`已${label}`)
      await load(true)
    },
  }
}

function confirmRole(u, role) {
  if (role === u.role) return
  confirmModal.value = {
    title: '修改角色',
    message:
      role === 'admin'
        ? `将「${u.nickname || u.username}」设为「管理员」并授予默认权限？`
        : `将「${u.nickname || u.username}」设为「${roleLabel(role)}」？`,
    danger: role === 'super_admin',
    run: async () => {
      await api.adminSetUserRole(u.id, role)
      toastSuccess('角色已修改')
      await load(true)
    },
  }
}

function confirmBanIp(ip) {
  if (!ip) return toastError('该用户没有可用的注册 IP')
  ipModal.value = { ip }
}
async function doBanIp() {
  if (!ipModal.value) return
  try {
    await api.adminBanIp(ipModal.value.ip, '账号拉黑连带')
    toastSuccess('IP 已拉黑')
  } catch (e) {
    toastError(e.message)
  } finally {
    ipModal.value = null
  }
}

// ---------- 权限编辑 ----------
function openPerm(u) {
  if (u.id === auth.user?.id) return toastError('不能修改自己的权限')
  permModal.value = { user: u, perms: new Set(u.permissions || []) }
}
function togglePerm(key) {
  const set = permModal.value.perms
  if (set.has(key)) set.delete(key)
  else set.add(key)
}
async function confirmPerm() {
  const t = permModal.value
  if (!t) return
  try {
    await api.adminSetUserPermissions(t.user.id, [...t.perms])
    toastSuccess('权限已更新')
    await load(true)
  } catch (e) {
    toastError(e.message)
  } finally {
    permModal.value = null
  }
}

async function runModal() {
  const m = confirmModal.value
  if (!m) return
  try {
    await m.run()
    confirmModal.value = null
  } catch (e) {
    toastError(e.message)
  }
}

onMounted(() => load(true))
</script>

<template>
  <div>
    <div class="users-toolbar">
      <div class="search-row">
        <input v-model="search" class="input" placeholder="搜索用户名 / 昵称 / 学校" @keyup.enter="load(true)" />
        <button class="btn-primary btn-sm" @click="load(true)">搜索</button>
      </div>
      <div class="sort-tabs admin-tabs" style="margin-bottom: 0">
        <button v-for="t in TABS" :key="t.key" class="sort-tab" :class="{ active: statusFilter === t.key }" @click="switchTab(t.key)">
          {{ t.label }}
        </button>
      </div>
    </div>

    <div v-if="users.length" class="admin-list">
      <div v-for="u in users" :key="u.id" class="admin-user">
        <div class="user-head">
          <span class="user-avatar" :style="{ background: avatarColor(u.nickname || u.username) }">{{ (u.nickname || u.username)[0] }}</span>
          <div class="user-main">
            <div class="user-name-row">
              <span class="user-name">{{ u.nickname || u.username }}</span>
              <span class="role-badge" :class="u.role">{{ roleLabel(u.role) }}</span>
              <span class="status-badge" :class="u.status">{{ userStatusLabel(u.status) }}</span>
              <span v-if="u.title" class="title-badge normal">🏅 {{ u.title }}</span>
            </div>
            <div class="user-meta">
              <span>@{{ u.username }}</span>
              <span v-if="u.class_name">{{ u.class_name }}</span>
              <span v-if="u.school">{{ u.school }}</span>
              <span>注册 {{ formatTime(u.created_at) }}</span>
            </div>
            <div class="user-reginfo">
              <span>IP {{ u.register_ip || '—' }}</span>
              <span v-if="u.register_browser" class="user-regua" :title="u.register_browser">{{ u.register_browser.slice(0, 40) }}</span>
              <span v-if="u.register_device" :title="u.register_device">设备 {{ u.register_device.slice(0, 16) }}</span>
            </div>
          </div>
        </div>

        <div class="user-actions">
          <select class="select" :value="u.role" :disabled="u.id === auth.user?.id" @change="(e) => confirmRole(u, e.target.value)">
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
            <option value="super_admin">超级管理员</option>
          </select>

          <button class="btn-ghost btn-sm" @click="openTitle(u)">🏅 头衔</button>
          <button class="btn-ghost btn-sm" @click="openPerm(u)">🔐 权限</button>

          <button v-if="u.status !== 'active' && u.id !== auth.user?.id" class="btn-ok btn-sm" :disabled="busy[u.id]" @click="confirmStatus(u, 'active')">✓ 激活</button>
          <button v-if="u.status === 'active' && u.id !== auth.user?.id" class="btn-danger btn-sm" :disabled="busy[u.id]" @click="confirmStatus(u, 'banned')">⛔ 拉黑</button>

          <button class="btn-warn btn-sm" @click="openPassword(u)">🔑 重置密码</button>
          <button class="btn-danger btn-sm" @click="confirmBanIp(u.register_ip)">🚫 拉黑IP</button>
        </div>
      </div>

      <div v-if="page < pages" class="load-more">
        <button class="btn-ghost" :disabled="loading" @click="loadMore">{{ loading ? '加载中…' : '加载更多' }}</button>
      </div>
    </div>

    <div v-else-if="!loading" class="empty">
      <div class="empty-emoji">🌿</div>
      <p class="empty-text">没有找到相关账号</p>
    </div>

    <!-- 弹窗们 -->
    <Modal :show="!!titleModal" title="下发头衔" @confirm="confirmTitle" @cancel="titleModal = null">
      <p class="modal-text">为「{{ titleModal?.user?.nickname || titleModal?.user?.username }}」设置头衔（显示在个人页与首页），留空取消头衔。</p>
      <input v-if="titleModal" v-model="titleModal.value" class="input" placeholder="输入头衔，如：校园之星" maxlength="50" @keyup.enter="confirmTitle" />
    </Modal>

    <Modal :show="!!pwdModal" title="重置密码" @confirm="confirmPassword" @cancel="pwdModal = null">
      <p class="modal-text">为「{{ pwdModal?.user?.nickname || pwdModal?.user?.username }}」设置新密码：</p>
      <input v-if="pwdModal" v-model="pwdModal.value" class="input" type="password" placeholder="新密码（≥6位）" @keyup.enter="confirmPassword" />
    </Modal>

    <Modal
      :show="!!confirmModal"
      :title="confirmModal?.title"
      :danger="confirmModal?.danger"
      @confirm="runModal"
      @cancel="confirmModal = null"
    >
      <p class="modal-text">{{ confirmModal?.message }}</p>
    </Modal>

    <Modal :show="!!ipModal" title="拉黑 IP" danger @confirm="doBanIp" @cancel="ipModal = null">
      <p class="modal-text">拉黑 IP：{{ ipModal?.ip }} ？被拉黑后无法发布/评论/注册。</p>
    </Modal>

    <Modal :show="!!permModal" title="权限设置" confirm-text="保存权限" @confirm="confirmPerm" @cancel="permModal = null">
      <p class="modal-text">
        为「{{ permModal?.user?.nickname || permModal?.user?.username }}」配置权限。
        <span v-if="permModal?.user?.role === 'super_admin'">超级管理员默认拥有全部权限。</span>
      </p>
      <div v-if="permModal" class="perm-editor">
        <div v-for="g in PERM_GROUPS" :key="g" class="perm-group">
          <div class="perm-group-title">{{ g }}</div>
          <label v-for="p in PERMS.filter((x) => x.group === g)" :key="p.key" class="perm-item">
            <input
              type="checkbox"
              :checked="permModal.perms.has(p.key)"
              :disabled="permModal.user.role === 'super_admin'"
              @change="togglePerm(p.key)"
            />
            <span class="perm-label">{{ p.label }}</span>
          </label>
        </div>
      </div>
    </Modal>
  </div>
</template>
