<script setup>
import { ref, computed } from 'vue'
import { api } from '../api'
import { formatTime, themeCls, avatarColor, authorTitle } from '../utils'

const props = defineProps({
  post: { type: Object, required: true },
  index: { type: Number, default: 0 },
})
const emit = defineEmits(['like'])

// 内联展开评论
const expanded = ref(false)
const comments = ref([])
const commentsLoading = ref(false)
const showForm = ref(false)
const form = ref({ nickname: '', content: '' })
const commenting = ref(false)
const commentError = ref('')
const viewerIndex = ref(null)  // 图片查看器当前索引（null=关闭）

const title = computed(() => authorTitle(props.post.author))

async function toggleComments() {
  if (expanded.value) {
    expanded.value = false
    return
  }
  expanded.value = true
  showForm.value = true
  if (!comments.value.length) {
    commentsLoading.value = true
    try {
      comments.value = await api.listComments(props.post.id)
    } catch {
      comments.value = []
    } finally {
      commentsLoading.value = false
    }
  }
}

async function submitComment() {
  commentError.value = ''
  const content = form.value.content.trim()
  if (!content) {
    commentError.value = '说点什么吧～'
    return
  }
  commenting.value = true
  try {
    await api.addComment(props.post.id, { content, nickname: form.value.nickname.trim() || null })
    form.value.content = ''
    props.post.comment_count += 1
    comments.value = await api.listComments(props.post.id)
  } catch (e) {
    commentError.value = e.message
  } finally {
    commenting.value = false
  }
}

async function likeComment(c) {
  try {
    const r = await api.likeComment(props.post.id, c.id)
    c.likes = r.likes
    c.liked = true
  } catch (e) {
    if (e.status === 400) c.liked = true
  }
}
</script>

<template>
  <article class="qq-card" :class="themeCls(post.theme)" :style="{ animationDelay: Math.min(index * 0.06, 0.6) + 's' }">
    <!-- 头部：头像 + 昵称 + 头衔 -->
    <div class="qq-head">
      <span class="qq-avatar" :style="{ background: avatarColor(post.nickname || '匿名') }">
        {{ (post.nickname || '匿')[0] }}
      </span>
      <div class="qq-head-info">
        <div class="qq-nick">
          <span class="qq-name">{{ post.nickname || '匿名同学' }}</span>
          <span v-if="post.pinned" class="pin-badge">📌 置顶</span>
          <span v-if="title" class="title-badge" :class="post.author?.role === 'super_admin' ? 'super' : 'normal'">
            {{ title }}
          </span>
        </div>
        <span class="qq-time">{{ formatTime(post.created_at) }}</span>
      </div>
    </div>

    <!-- 内容 -->
    <div class="qq-body">
      <p v-if="post.to_name" class="qq-to"><span class="qq-to-label">对象</span>{{ post.to_name }}</p>
      <p class="qq-content">{{ post.content }}</p>

      <!-- 图片九宫格 -->
      <div v-if="post.images?.length" class="post-images" :class="'count-' + Math.min(post.images.length, 3)">
        <img
          v-for="(img, i) in post.images"
          :key="img"
          :src="img"
          :alt="'图片' + (i + 1)"
          loading="lazy"
          @click="viewerIndex = i"
        />
      </div>

      <!-- 视频 -->
      <div v-if="post.video" class="post-video">
        <video :src="post.video" controls playsinline preload="metadata"></video>
      </div>
    </div>

    <!-- 图片查看器 -->
    <teleport to="body">
      <transition name="modal">
        <div v-if="viewerIndex !== null" class="viewer-mask" @click="viewerIndex = null">
          <img :src="post.images?.[viewerIndex]" class="viewer-img" alt="大图" />
          <div class="viewer-nav">
            <button v-if="viewerIndex > 0" class="viewer-btn" @click.stop="viewerIndex--">‹</button>
            <button v-if="viewerIndex < post.images.length - 1" class="viewer-btn" @click.stop="viewerIndex++">›</button>
          </div>
          <button class="viewer-close" @click="viewerIndex = null">✕</button>
        </div>
      </transition>
    </teleport>

    <!-- 操作条 -->
    <div class="qq-actions">
      <button class="like-btn" :class="{ liked: post.liked }" @click="emit('like', post)">
        <span class="heart-icon" :class="{ beat: post.liked }">{{ post.liked ? '❤️' : '🤍' }}</span>
        <span>{{ post.likes }}</span>
      </button>
      <button class="comment-toggle" :class="{ active: expanded }" @click="toggleComments">
        💬 {{ post.comment_count }} <span>{{ expanded ? '收起' : '评论' }}</span>
      </button>
    </div>

    <!-- 内联评论区 -->
    <transition name="expand">
      <div v-if="expanded" class="qq-comments">
        <div v-if="commentsLoading" class="comments-loading">加载中…</div>
        <template v-else>
          <ul v-if="comments.length" class="comment-list">
            <li v-for="c in comments" :key="c.id" class="comment-item">
              <span class="comment-avatar" :style="{ background: avatarColor(c.nickname) }">{{ (c.nickname || '匿')[0] }}</span>
              <div class="comment-main">
                <span class="comment-name">{{ c.nickname }}</span>
                <p class="comment-content">{{ c.content }}</p>
                <div class="comment-foot">
                  <button class="comment-like" :class="{ liked: c.liked }" @click="likeComment(c)">
                    <span>{{ c.liked ? '❤️' : '🤍' }}</span>
                    <span>{{ c.likes }}</span>
                  </button>
                </div>
              </div>
            </li>
          </ul>
          <p v-else class="comments-empty">还没有评论，来抢个沙发～</p>

          <div class="comment-form">
            <input v-model="form.nickname" class="input comment-name" maxlength="50" placeholder="昵称（选填）" />
            <div class="comment-input-row">
              <input
                v-model="form.content"
                class="input"
                maxlength="200"
                placeholder="友善评论…"
                @keyup.enter="submitComment"
              />
              <button class="btn-primary btn-sm" :disabled="commenting" @click="submitComment">
                {{ commenting ? '发送…' : '发送' }}
              </button>
            </div>
            <p v-if="commentError" class="form-error">{{ commentError }}</p>
          </div>
        </template>
      </div>
    </transition>
  </article>
</template>
