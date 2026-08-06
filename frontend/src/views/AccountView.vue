<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api'
import { auth, setSession, logout, canAccessAdmin } from '../store/auth'
import { toastSuccess, toastError, toastInfo } from '../store/toast'
import { avatarColor, formatTime, roleLabel } from '../utils'
import Modal from '../components/Modal.vue'

const router = useRouter()
const mode = ref('login')
const site = ref(null)

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '', nickname: '', class_name: '', school: '', email: '', phone: '' })
const error = ref('')
const info = ref('')
const busy = ref(false)

const pwdModal = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '' })
const pwdMsg = ref('')
const pwdBusy = ref(false)

onMounted(async () => {
  try {
    site.value = await api.siteInfo()
  } catch {
    /* 忽略 */
  }
})

async function doLogin() {
  error.value = ''
  busy.value = true
  try {
    const r = await api.login(loginForm)
    setSession(r.token, r.user)
    toastSuccess(`欢迎回来，${r.user.nickname || r.user.username}`)
    router.push('/')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

async function doRegister() {
  error.value = ''
  info.value = ''
  const u = regForm.username.trim()
  if (u.length < 3) return (error.value = '用户名至少 3 位（字母/数字/下划线）')
  if (regForm.password.length < 6) return (error.value = '密码至少 6 位')
  if (!regForm.nickname.trim()) return (error.value = '请填写昵称')
  const email = regForm.email.trim()
  const phone = regForm.phone.trim()
  if (!email && !phone) return (error.value = '邮箱和电话至少填写一项')
  if (email && !/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(email)) return (error.value = '邮箱格式不正确（应为 xxx@xx.xxx）')
  if (phone && !/^\d{11}$/.test(phone)) return (error.value = '电话号码应为 11 位数字')
  busy.value = true
  try {
    const r = await api.register({
      username: u,
      password: regForm.password,
      nickname: regForm.nickname.trim(),
      class_name: regForm.class_name.trim() || null,
      school: regForm.school.trim() || null,
      email: email || null,
      phone: phone || null,
    })
    if (r.user.status === 'pending') {
      info.value = '注册成功！账号待管理员激活，激活后即可登录使用。'
      regForm.password = ''
      toastInfo('注册成功，等待激活')
    } else {
      setSession(r.token, r.user)
      toastSuccess('注册成功，欢迎加入！')
      router.push('/')
    }
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}

function doLogout() {
  logout()
  toastInfo('已退出登录')
  router.push('/')
}

async function confirmPasswordChange() {
  pwdMsg.value = ''
  if (pwdForm.new_password.length < 6) return (pwdMsg.value = '新密码至少 6 位')
  pwdBusy.value = true
  try {
    await api.changeOwnPassword(pwdForm)
    pwdModal.value = false
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    toastSuccess('密码修改成功')
  } catch (e) {
    pwdMsg.value = e.message
  } finally {
    pwdBusy.value = false
  }
}
</script>

<template>
  <div class="account-page">
    <!-- 未登录：登录/注册 -->
    <div v-if="!auth.user" class="form-card">
      <div class="auth-tabs">
        <button class="auth-tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">登录</button>
        <button class="auth-tab" :class="{ active: mode === 'register' }" @click="mode = 'register'; error = ''">注册</button>
      </div>

      <template v-if="mode === 'login'">
        <div class="form-field">
          <input v-model="loginForm.username" class="input" placeholder="用户名" @keyup.enter="doLogin" />
        </div>
        <div class="form-field">
          <input v-model="loginForm.password" class="input" type="password" placeholder="密码" @keyup.enter="doLogin" />
        </div>
        <p v-if="error" class="form-error">{{ error }}</p>
        <button class="btn-primary btn-block" :disabled="busy" @click="doLogin">
          {{ busy ? '登录中…' : '登录' }}
        </button>
      </template>

      <template v-else>
        <div v-if="site && !site.allow_register" class="auth-closed">
          🔒 当前未开放注册，请联系管理员。
        </div>
        <template v-else>
          <div class="form-field">
            <input v-model="regForm.username" class="input" placeholder="用户名（字母/数字/下划线，≥3位）" />
          </div>
          <div class="form-field">
            <input v-model="regForm.password" class="input" type="password" placeholder="密码（≥6位）" />
          </div>
          <div class="form-field">
            <input v-model="regForm.nickname" class="input" placeholder="昵称 *" />
          </div>
          <div class="form-field">
            <input v-model="regForm.class_name" class="input" placeholder="班级（选填）" />
          </div>
          <div class="form-field">
            <input v-model="regForm.school" class="input" placeholder="学校（选填）" />
          </div>
          <div class="form-field">
            <input v-model="regForm.email" class="input" type="email" placeholder="邮箱（xxx@xx.xxx，与电话至少填一项）" />
          </div>
          <div class="form-field">
            <input v-model="regForm.phone" class="input" type="tel" maxlength="11" placeholder="电话号码（11位，与邮箱至少填一项）" />
          </div>
          <p class="form-tip" style="margin-top: -6px">📮 邮箱与电话至少填写一项</p>
          <p v-if="error" class="form-error">{{ error }}</p>
          <p v-if="info" class="form-info">{{ info }}</p>
          <p v-if="site?.register_approval" class="form-tip">📋 注册后需管理员审核激活才能登录</p>
          <button class="btn-primary btn-block" :disabled="busy" @click="doRegister">
            {{ busy ? '注册中…' : '注册' }}
          </button>
        </template>
      </template>
    </div>

    <!-- 已登录：个人主页 -->
    <div v-else class="form-card profile-card">
      <div class="profile-top">
        <span class="profile-avatar" :style="{ background: avatarColor(auth.user.nickname) }">
          {{ (auth.user.nickname || auth.user.username)[0] }}
        </span>
        <div>
          <div class="profile-name-row">
            <span class="profile-name">{{ auth.user.nickname || auth.user.username }}</span>
            <span class="role-badge" :class="auth.user.role">{{ roleLabel(auth.user.role) }}</span>
          </div>
          <span class="profile-username">@{{ auth.user.username }}</span>
        </div>
      </div>

      <div v-if="auth.user.title" class="profile-title">🏅 {{ auth.user.title }}</div>

      <div class="profile-info">
        <p v-if="auth.user.class_name">📖 班级：{{ auth.user.class_name }}</p>
        <p v-if="auth.user.school">🏫 学校：{{ auth.user.school }}</p>
        <p v-if="auth.user.email">📧 邮箱：{{ auth.user.email }}</p>
        <p v-if="auth.user.phone">📞 电话：{{ auth.user.phone }}</p>
        <p>🗓️ 加入于 {{ formatTime(auth.user.created_at) }}</p>
      </div>

      <div class="profile-actions">
        <button v-if="canAccessAdmin()" class="btn-primary" @click="router.push('/admin')">🛠️ 进入管理后台</button>
        <button class="btn-ghost" @click="pwdModal = true">🔑 修改密码</button>
        <button class="btn-ghost" @click="doLogout">退出登录</button>
      </div>
    </div>

    <!-- 修改密码弹窗 -->
    <Modal :show="pwdModal" title="修改密码" confirm-text="确认修改" @confirm="confirmPasswordChange" @cancel="pwdModal = false">
      <div class="form-field">
        <input v-model="pwdForm.old_password" class="input" type="password" placeholder="原密码" @keyup.enter="confirmPasswordChange" />
      </div>
      <div class="form-field">
        <input v-model="pwdForm.new_password" class="input" type="password" placeholder="新密码（≥6位）" @keyup.enter="confirmPasswordChange" />
      </div>
      <p v-if="pwdMsg" class="form-error">{{ pwdMsg }}</p>
      <p v-if="pwdBusy" class="form-sub">保存中…</p>
    </Modal>
  </div>
</template>
