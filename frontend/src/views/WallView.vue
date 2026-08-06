<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import PostCard from '../components/PostCard.vue'
import { api } from '../api'
import { isLoggedIn } from '../store/auth'
import { toastError } from '../store/toast'

const router = useRouter()
const sort = ref('latest')
const posts = ref([])
const page = ref(1)
const pages = ref(1)
const loading = ref(false)
const site = ref(null)
const sentinel = ref(null)
let observer = null

const SORTS = [
  { key: 'latest', label: '🕐 最新' },
  { key: 'hot', label: '🔥 最热' },
]

async function load(reset = false) {
  if (reset) {
    page.value = 1
    posts.value = []
  }
  loading.value = true
  try {
    const d = await api.listPosts({ page: page.value, page_size: 10, sort: sort.value })
    if (reset) posts.value = d.items
    else posts.value.push(...d.items)
    pages.value = d.pages
  } catch (e) {
    toastError(e.message)
  } finally {
    loading.value = false
  }
}

function switchSort(key) {
  if (sort.value === key) return
  sort.value = key
  load(true)
}

function loadMore() {
  if (page.value < pages.value && !loading.value) {
    page.value += 1
    load()
  }
}

async function onLike(post) {
  try {
    const r = await api.likePost(post.id)
    post.likes = r.likes
    post.liked = true
  } catch (e) {
    if (e.status === 400) {
      post.liked = true
    } else {
      toastError(e.message)
    }
  }
}

onMounted(async () => {
  try {
    site.value = await api.siteInfo()
    document.title = site.value.site_name || '校园墙'
  } catch {
    /* 忽略 */
  }
  await load(true)

  // 无限滚动：划到底端自动加载下一页
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) loadMore()
    },
    { rootMargin: '200px' }
  )
  if (sentinel.value) observer.observe(sentinel.value)
})

onBeforeUnmount(() => observer && observer.disconnect())
</script>

<template>
  <div class="wall">
    <section class="hero">
      <h1 class="hero-title">把想说的话，<br />写在这里</h1>
      <p class="hero-sub">每一份真心，都值得被温柔以待 💗</p>
      <button class="btn-primary btn-lg" @click="router.push('/post')">✏️ 我也要发布</button>
    </section>

    <!-- 公告 + 匿名限发声明 -->
    <section v-if="site" class="site-notice">
      <p v-if="site.site_announcement" class="notice-announcement">📢 {{ site.site_announcement }}</p>
      <p v-if="!isLoggedIn()" class="notice-limit">
        未登录状态每 IP / 设备 24 小时内限发 {{ site.anonymous_post_limit }} 条，登录后不限
        <router-link to="/account" class="notice-link">去登录 →</router-link>
      </p>
    </section>

    <section class="wall-body">
      <div class="sort-tabs">
        <button
          v-for="s in SORTS"
          :key="s.key"
          class="sort-tab"
          :class="{ active: sort === s.key }"
          @click="switchSort(s.key)"
        >
          {{ s.label }}
        </button>
      </div>

      <div v-if="posts.length" class="qq-feed">
        <PostCard v-for="(p, i) in posts" :key="p.id" :post="p" :index="i" @like="onLike" />
      </div>

      <div v-else-if="!loading" class="empty">
        <div class="empty-emoji">🫧</div>
        <p class="empty-text">
          墙上还空空的，<br />
          来做第一个发言的人吧
        </p>
        <button class="btn-primary" @click="router.push('/post')">写下第一句话</button>
      </div>

      <div v-if="loading && !posts.length" class="loading-box">正在收集真心话…</div>

      <!-- 无限滚动哨兵 -->
      <div ref="sentinel" class="feed-sentinel">
        <div v-if="loading && posts.length" class="spinner"></div>
        <p v-else-if="page >= pages && posts.length" class="feed-end">— 已经到底啦 —</p>
      </div>
    </section>
  </div>
</template>
