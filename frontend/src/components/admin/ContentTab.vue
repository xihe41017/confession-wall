<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../api'
import { hasPerm } from '../../store/auth'
import { toastSuccess, toastError, toastInfo } from '../../store/toast'
import { formatTime, statusLabel } from '../../utils'
import Modal from '../Modal.vue'

const stats = ref(null)
const statusFilter = ref('all')
const posts = ref([])
const page = ref(1)
const pages = ref(1)
const loading = ref(false)
const expanded = ref({})
const busy = ref({})

const deleteTarget = ref(null)
const commentTarget = ref(null) // { postId, commentId }
const banTarget = ref(null)     // { ip }
const editTarget = ref(null)    // { post, form }
const commentEditTarget = ref(null) // { comment, form }

const TABS = [
  { key: 'all', label: '📋 全部' },
  { key: 'pending', label: '⏳ 待审核' },
  { key: 'approved', label: '✅ 已上墙' },
]

async function loadStats() {
  stats.value = await api.adminStats()
}

async function loadPosts(reset = true) {
  if (reset) {
    page.value = 1
    posts.value = []
  }
  loading.value = true
  try {
    const d = await api.adminPosts({
      page: page.value,
      page_size: 10,
      status: statusFilter.value === 'all' ? '' : statusFilter.value,
    })
    if (reset) posts.value = d.items
    else posts.value.push(...d.items)
    pages.value = d.pages
  } catch (e) {
    toastError(e.message)
  } finally {
    loading.value = false
  }
}

// 加载更多：先翻页再拉取，避免重复加载同一页
function loadMore() {
  if (loading.value || page.value >= pages.value) return
  page.value += 1
  loadPosts(false)
}

function switchTab(key) {
  statusFilter.value = key
  loadPosts(true)
}

async function approve(p) {
  busy.value[p.id] = true
  try {
    await api.adminSetStatus(p.id, 'approved')
    toastSuccess('已上墙')
    await loadStats()
    if (statusFilter.value === 'pending') posts.value = posts.value.filter((x) => x.id !== p.id)
  } catch (e) {
    toastError(e.message)
  } finally {
    busy.value[p.id] = false
  }
}

async function togglePin(p) {
  busy.value[p.id] = true
  try {
    const next = !p.pinned
    const r = await api.adminPinPost(p.id, next)
    p.pinned = r.pinned
    toastSuccess(next ? '已置顶' : '已取消置顶')
  } catch (e) {
    toastError(e.message)
  } finally {
    busy.value[p.id] = false
  }
}

async function confirmDeletePost() {
  if (!deleteTarget.value) return
  const p = deleteTarget.value
  try {
    await api.adminDeletePost(p.id)
    posts.value = posts.value.filter((x) => x.id !== p.id)
    await loadStats()
    toastSuccess('已删除')
  } catch (e) {
    toastError(e.message)
  } finally {
    deleteTarget.value = null
  }
}

async function toggleComments(p) {
  if (expanded.value[p.id]) {
    expanded.value[p.id] = null
    return
  }
  try {
    expanded.value[p.id] = await api.adminListComments(p.id)
  } catch (e) {
    toastError(e.message)
  }
}

async function confirmDeleteComment() {
  if (!commentTarget.value) return
  const { postId, commentId } = commentTarget.value
  try {
    await api.adminDeleteComment(commentId)
    expanded.value[postId] = expanded.value[postId].filter((c) => c.id !== commentId)
    await loadPosts(true)
    toastSuccess('评论已删除')
  } catch (e) {
    toastError(e.message)
  } finally {
    commentTarget.value = null
  }
}

// ---------- 编辑内容 ----------
function openEdit(p) {
  editTarget.value = {
    post: p,
    form: { likes: p.likes, to_name: p.to_name || '', nickname: p.nickname || '' },
  }
}
async function confirmEditPost() {
  const t = editTarget.value
  if (!t) return
  try {
    const r = await api.adminEditPost(t.post.id, {
      likes: t.form.likes === '' ? undefined : Number(t.form.likes),
      to_name: t.form.to_name.trim() || null,
      nickname: t.form.nickname.trim() || null,
    })
    t.post.likes = r.likes
    t.post.to_name = r.to_name
    t.post.nickname = r.nickname
    toastSuccess('已保存')
  } catch (e) {
    toastError(e.message)
  } finally {
    editTarget.value = null
  }
}

// ---------- 编辑评论 ----------
function openCommentEdit(c) {
  commentEditTarget.value = { comment: c, form: { likes: c.likes } }
}
async function confirmEditComment() {
  const t = commentEditTarget.value
  if (!t) return
  try {
    const r = await api.adminEditComment(t.comment.id, {
      likes: t.form.likes === '' ? undefined : Number(t.form.likes),
    })
    t.comment.likes = r.likes
    toastSuccess('已保存')
  } catch (e) {
    toastError(e.message)
  } finally {
    commentEditTarget.value = null
  }
}

// ---------- 拉黑 IP ----------
function confirmBanIp(ip) {
  if (!ip) return toastInfo('该内容没有可用的 IP')
  banTarget.value = { ip }
}
async function doBanIp() {
  if (!banTarget.value) return
  try {
    await api.adminBanIp(banTarget.value.ip, '内容管理拉黑')
    toastSuccess('IP 已拉黑')
  } catch (e) {
    toastError(e.message)
  } finally {
    banTarget.value = null
  }
}

onMounted(async () => {
  try {
    await Promise.all([loadStats(), loadPosts(true)])
  } catch (e) {
    toastInfo('加载失败，请刷新')
  }
})
</script>

<template>
  <div>
    <div v-if="stats" class="stats-grid">
      <div class="stat-card"><span class="stat-num">{{ stats.total_posts }}</span><span class="stat-label">全部内容</span></div>
      <div class="stat-card warn"><span class="stat-num">{{ stats.pending_posts }}</span><span class="stat-label">待审核</span></div>
      <div class="stat-card"><span class="stat-num">{{ stats.total_comments }}</span><span class="stat-label">评论</span></div>
      <div class="stat-card"><span class="stat-num">❤️ {{ stats.total_likes }}</span><span class="stat-label">总赞数</span></div>
    </div>

    <div class="sort-tabs admin-tabs">
      <button v-for="t in TABS" :key="t.key" class="sort-tab" :class="{ active: statusFilter === t.key }" @click="switchTab(t.key)">
        {{ t.label }}
      </button>
    </div>

    <div v-if="posts.length" class="admin-list">
      <div v-for="p in posts" :key="p.id" class="admin-post">
        <div class="admin-post-top">
          <span class="admin-post-id">#{{ p.id }}</span>
          <span class="status-badge" :class="p.status">{{ statusLabel(p.status) }}</span>
          <span v-if="p.pinned" class="pin-badge">📌 置顶</span>
          <span v-if="p.is_anonymous" class="anon-badge">🕶 匿名</span>
          <span class="admin-post-meta">{{ formatTime(p.created_at) }}</span>
          <span class="admin-post-meta">IP {{ p.ip }}</span>
        </div>
        <p class="admin-post-content">
          <span v-if="p.to_name" class="admin-to">对象 {{ p.to_name }}：</span>{{ p.content }}
        </p>
        <div v-if="p.images?.length" class="admin-media">
          <img v-for="img in p.images" :key="img" :src="img" alt="图片" />
        </div>
        <video v-if="p.video" :src="p.video" controls playsinline preload="metadata" class="admin-video"></video>
        <div class="admin-post-bottom">
          <span class="admin-post-meta">来自 {{ p.nickname }}</span>
          <span v-if="p.author_username" class="admin-post-meta">👤 @{{ p.author_username }}<template v-if="p.is_anonymous">（匿名，可追溯）</template></span>
          <span class="admin-post-meta">❤️ {{ p.likes }} · 💬 {{ p.comment_count }}</span>
        </div>
        <div class="admin-post-actions">
          <button v-if="p.status !== 'approved' && hasPerm('content.manage')" class="btn-ok btn-sm" :disabled="busy[p.id]" @click="approve(p)">✓ 上墙</button>
          <button v-if="hasPerm('content.pin')" class="btn-warn btn-sm" :disabled="busy[p.id]" @click="togglePin(p)">{{ p.pinned ? '📌 取消置顶' : '📌 置顶' }}</button>
          <button v-if="hasPerm('content.edit')" class="btn-ghost btn-sm" @click="openEdit(p)">✏️ 编辑</button>
          <button v-if="hasPerm('content.ban_ip')" class="btn-danger btn-sm" @click="confirmBanIp(p.ip)">🚫 拉黑IP</button>
          <button v-if="hasPerm('content.manage')" class="btn-ghost btn-sm" @click="toggleComments(p)">💬 评论{{ expanded[p.id] ? ' · 收起' : '' }}</button>
          <button v-if="hasPerm('content.manage')" class="btn-danger btn-sm" @click="deleteTarget = p">🗑 删除</button>
        </div>

        <div v-if="expanded[p.id]" class="admin-comments">
          <div v-for="c in expanded[p.id]" :key="c.id" class="admin-comment">
            <div class="admin-comment-head">
              <span>💭 {{ c.nickname }} <span class="admin-post-meta">IP {{ c.ip }}</span></span>
              <span class="admin-post-meta">{{ formatTime(c.created_at) }}</span>
            </div>
            <div class="admin-comment-body">
              <p class="admin-comment-content">{{ c.content }}</p>
              <div class="admin-comment-ops">
                <span class="admin-post-meta">❤️ {{ c.likes }}</span>
                <button v-if="hasPerm('comment.edit')" class="btn-ghost btn-xs" @click="openCommentEdit(c)">编辑赞数</button>
                <button v-if="hasPerm('content.manage')" class="btn-danger btn-xs" @click="commentTarget = { postId: p.id, commentId: c.id }">删除</button>
              </div>
            </div>
          </div>
          <p v-if="!expanded[p.id].length" class="admin-comments-empty">暂无评论</p>
        </div>
      </div>

      <div v-if="page < pages" class="load-more">
        <button class="btn-ghost" :disabled="loading" @click="loadMore">{{ loading ? '加载中…' : '加载更多' }}</button>
      </div>
    </div>

    <div v-else-if="!loading" class="empty">
      <div class="empty-emoji">🌿</div>
      <p class="empty-text">这里暂时空空如也</p>
    </div>

    <!-- 删除内容 -->
    <Modal :show="!!deleteTarget" title="删除内容" confirm-text="删除" danger @confirm="confirmDeletePost" @cancel="deleteTarget = null">
      <p class="modal-text">确定删除这条内容吗？删除后不可恢复。</p>
      <p v-if="deleteTarget" class="modal-quote">「{{ deleteTarget.content.slice(0, 50) }}…」</p>
    </Modal>

    <!-- 删除评论 -->
    <Modal :show="!!commentTarget" title="删除评论" confirm-text="删除" danger @confirm="confirmDeleteComment" @cancel="commentTarget = null">
      <p class="modal-text">确定删除这条评论吗？</p>
    </Modal>

    <!-- 拉黑 IP -->
    <Modal :show="!!banTarget" title="拉黑 IP" confirm-text="拉黑" danger @confirm="doBanIp" @cancel="banTarget = null">
      <p class="modal-text">拉黑 IP：{{ banTarget?.ip }} ？被拉黑后无法发布/评论/注册。</p>
    </Modal>

    <!-- 编辑内容 -->
    <Modal :show="!!editTarget" title="编辑内容" @confirm="confirmEditPost" @cancel="editTarget = null">
      <div class="form-field">
        <label class="form-label">点赞数</label>
        <input v-if="editTarget" v-model.number="editTarget.form.likes" class="input" type="number" min="0" />
      </div>
      <div class="form-field">
        <label class="form-label">对象 <span class="optional">（选填）</span></label>
        <input v-if="editTarget" v-model="editTarget.form.to_name" class="input" maxlength="50" placeholder="对象" />
      </div>
      <div class="form-field">
        <label class="form-label">昵称 <span class="optional">（选填）</span></label>
        <input v-if="editTarget" v-model="editTarget.form.nickname" class="input" maxlength="50" placeholder="昵称" />
      </div>
    </Modal>

    <!-- 编辑评论 -->
    <Modal :show="!!commentEditTarget" title="编辑评论点赞数" @confirm="confirmEditComment" @cancel="commentEditTarget = null">
      <div class="form-field">
        <label class="form-label">点赞数</label>
        <input v-if="commentEditTarget" v-model.number="commentEditTarget.form.likes" class="input" type="number" min="0" />
      </div>
    </Modal>
  </div>
</template>
