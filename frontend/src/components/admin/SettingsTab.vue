<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '../../api'
import { isSuperAdmin, hasPerm } from '../../store/auth'
import { toastSuccess, toastError } from '../../store/toast'

const settings = ref([])
const loading = ref(false)
const saving = ref({})

const BOOL_KEYS = ['moderation_mode', 'allow_register', 'register_approval']
const LABELS = {
  site_name: '站点名称',
  site_announcement: '站点公告',
  moderation_mode: '发布需审核',
  allow_register: '开放注册',
  register_approval: '注册需管理员激活',
  anonymous_post_limit: '匿名限发条数',
  rate_register: '注册限速',
  rate_login: '登录限速',
  rate_post: '发布限速',
  rate_comment: '评论限速',
  rate_like: '点赞限速',
  max_body_kb: '请求体上限',
  image_max_mb: '单张图片上限',
  video_max_mb: '视频上限',
  jwt_secret: 'JWT 密钥',
}
// 单位说明：显示在每项输入框上方（次/分钟 等）
const UNITS = {
  rate_register: '单位：次/分钟',
  rate_login: '单位：次/分钟',
  rate_post: '单位：次/分钟',
  rate_comment: '单位：次/分钟',
  rate_like: '单位：次/分钟',
  max_body_kb: '单位：KB',
  image_max_mb: '单位：MB（压缩后上传上限）',
  video_max_mb: '单位：MB',
}

// 该设置当前用户能否编辑
function canEdit(s) {
  if (s.sensitive) return isSuperAdmin()
  return hasPerm(`settings.${s.key}`)
}

// 可见设置：需要超管权限的选项（站点名/限速/请求体上限/JWT密钥）不对非超管显示
const visibleSettings = computed(() => {
  if (isSuperAdmin()) return settings.value
  return settings.value.filter((s) => !s.sensitive)
})

// 能否看到真实值（仅需要隐藏值的设置项如 JWT 密钥，非超管打码）
function canSeeValue(s) {
  return !s.masked || isSuperAdmin()
}

async function load() {
  loading.value = true
  try {
    settings.value = await api.adminListSettings()
  } catch (e) {
    toastError(e.message)
  } finally {
    loading.value = false
  }
}

function isBool(key) {
  return BOOL_KEYS.includes(key)
}

async function save(s) {
  saving.value[s.key] = true
  try {
    await api.adminUpdateSetting(s.key, String(s.value))
    toastSuccess(`已保存：${LABELS[s.key] || s.key}`)
  } catch (e) {
    toastError(e.message)
  } finally {
    saving.value[s.key] = false
  }
}

function toggle(s, e) {
  s.value = e.target.checked ? '1' : '0'
  save(s)
}

onMounted(load)
</script>

<template>
  <div class="settings-tab">
    <h3 class="section-title">⚙️ 服务器设置</h3>
    <p class="form-sub">
      {{ isSuperAdmin() ? '显示全部设置（含仅超管可改的敏感项）' : '仅显示你有权限管理的设置项' }}
    </p>

    <div v-if="loading" class="loading-box">加载中…</div>
    <div v-else-if="!visibleSettings.length" class="empty">
      <div class="empty-emoji">🔒</div>
      <p class="empty-text">没有可管理的设置项</p>
    </div>
    <div v-else class="settings-list">
      <div v-for="s in visibleSettings" :key="s.key" class="setting-item">
        <div class="setting-info">
          <div class="setting-name-row">
            <span class="setting-name">{{ LABELS[s.key] || s.key }}</span>
            <code class="setting-key">{{ s.key }}</code>
            <span v-if="s.sensitive" class="sensitive-badge">🔒 仅超管可改</span>
            <span v-if="s.masked" class="masked-badge">🕶 值隐藏</span>
            <span v-if="!canEdit(s)" class="lock-badge">🔑 无权修改</span>
          </div>
          <p class="setting-desc">{{ s.description }}</p>
          <!-- 单位显示在每项上方 -->
          <p v-if="UNITS[s.key]" class="setting-unit">{{ UNITS[s.key] }}</p>
        </div>

        <div class="setting-control">
          <label v-if="isBool(s.key)" class="switch">
            <input
              type="checkbox"
              :checked="String(s.value) === '1'"
              :disabled="!canEdit(s)"
              @change="(e) => toggle(s, e)"
            />
            <span class="switch-slider"></span>
          </label>
          <template v-else>
            <input
              v-model="s.value"
              class="input setting-input"
              :type="s.masked ? 'password' : 'text'"
              :disabled="!canEdit(s)"
              @keyup.enter="save(s)"
            />
            <button class="btn-primary btn-sm" :disabled="saving[s.key] || !canEdit(s)" @click="save(s)">
              {{ saving[s.key] ? '保存中…' : '保存' }}
            </button>
          </template>
        </div>
      </div>
    </div>

    <p class="form-tip" style="margin-top: 10px">
      💡 修改 JWT 密钥后，所有人需重新登录。限速格式如 <code>20/minute</code>。
    </p>
  </div>
</template>
