<script setup>
import { onMounted, ref } from 'vue'
import { api } from '../../api'
import { toastSuccess, toastError } from '../../store/toast'
import { formatTime } from '../../utils'
import Modal from '../Modal.vue'

const bannedIps = ref([])
const loading = ref(false)
const unbanTarget = ref(null)

async function load() {
  loading.value = true
  try {
    bannedIps.value = await api.adminListBannedIps()
  } catch (e) {
    toastError(e.message)
  } finally {
    loading.value = false
  }
}

function confirmUnban(ip) {
  unbanTarget.value = ip
}

async function doUnban() {
  if (!unbanTarget.value) return
  try {
    await api.adminUnbanIp(unbanTarget.value)
    toastSuccess('已解除拉黑')
    await load()
  } catch (e) {
    toastError(e.message)
  } finally {
    unbanTarget.value = null
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h3 class="section-title">🚫 IP 黑名单</h3>
    <p class="form-sub">被拉黑的 IP 无法发布、评论与注册。可在此解除拉黑。</p>

    <div v-if="loading" class="loading-box">加载中…</div>
    <div v-else-if="bannedIps.length" class="admin-list">
      <div v-for="b in bannedIps" :key="b.ip" class="admin-post ban-row">
        <div class="ban-info">
          <code class="ban-ip">{{ b.ip }}</code>
          <span class="admin-post-meta">{{ b.reason || '无备注' }} · {{ formatTime(b.created_at) }}</span>
        </div>
        <button class="btn-ok btn-sm" @click="confirmUnban(b.ip)">解除拉黑</button>
      </div>
    </div>
    <div v-else class="ban-empty">暂无拉黑的 IP</div>

    <Modal
      :show="!!unbanTarget"
      title="解除拉黑"
      @confirm="doUnban"
      @cancel="unbanTarget = null"
    >
      <p class="modal-text">确定解除 IP：{{ unbanTarget }} 的拉黑吗？</p>
    </Modal>
  </div>
</template>
