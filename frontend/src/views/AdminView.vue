<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { auth, logout, hasPerm, isSuperAdmin } from '../store/auth'
import { roleLabel } from '../utils'
import ContentTab from '../components/admin/ContentTab.vue'
import NginxTab from '../components/admin/NginxTab.vue'
import UsersTab from '../components/admin/UsersTab.vue'
import BannedTab from '../components/admin/BannedTab.vue'
import SettingsTab from '../components/admin/SettingsTab.vue'

const router = useRouter()
const tab = ref('content')

const TABS = [
  { key: 'content', label: '内容管理', show: () => hasPerm('content.manage') },
  { key: 'users', label: '账号管理', show: () => hasPerm('users.manage') },
  { key: 'banned', label: 'IP黑名单', show: () => hasPerm('ban.manage') },
  { key: 'settings', label: '服务器设置', show: () => hasPerm('settings.view') },
  { key: 'nginx', label: '域名解析', show: () => isSuperAdmin() },
]

const visibleTabs = TABS.filter((t) => t.show())

function doLogout() {
  logout()
  router.push('/account')
}

function switchTab(key) {
  if (TABS.find((t) => t.key === key)?.show()) tab.value = key
}

onMounted(() => {
  if (!visibleTabs.length) {
    router.replace('/account')
    return
  }
  if (!visibleTabs.some((t) => t.key === tab.value)) tab.value = visibleTabs[0].key
})
</script>

<template>
  <div class="admin-page">
    <template v-if="auth.user">
      <div class="admin-head">
        <div>
          <h2 class="admin-title">🛠️ 管理后台</h2>
          <p class="form-sub">
            {{ auth.user.nickname }} · <span class="role-badge" :class="auth.user.role">{{ roleLabel(auth.user.role) }}</span>
          </p>
        </div>
        <button class="btn-ghost btn-sm" @click="doLogout">退出登录</button>
      </div>

      <div class="sort-tabs admin-tabs">
        <button
          v-for="t in visibleTabs"
          :key="t.key"
          class="sort-tab"
          :class="{ active: tab === t.key }"
          @click="switchTab(t.key)"
        >
          {{ t.label }}
        </button>
      </div>

      <ContentTab v-if="tab === 'content'" />
      <UsersTab v-else-if="tab === 'users'" />
      <BannedTab v-else-if="tab === 'banned'" />
      <SettingsTab v-else-if="tab === 'settings'" />
      <NginxTab v-else-if="tab === 'nginx'" />
    </template>
    <div v-else class="empty">
      <div class="empty-emoji">⏳</div>
      <p class="empty-text">正在跳转…</p>
    </div>
  </div>
</template>
