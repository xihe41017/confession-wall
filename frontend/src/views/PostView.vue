<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, uploadFile } from '../api'
import { auth, isLoggedIn } from '../store/auth'
import { THEMES } from '../utils'

const router = useRouter()
const form = reactive({ to_name: '', nickname: '', content: '', theme: 'pink', anonymous: false })
const submitting = ref(false)
const done = ref(false)
const site = ref(null)
const error = ref('')

// 媒体
const images = ref([])   // { file, url }
const video = ref(null)  // { file, url, duration }
const imageError = ref('')
const videoError = ref('')
const MAX_VIDEO_SEC = 15
const USER_IMAGE_LIMIT_MB = 10 // 用户选图原图上限（压缩前）
// 匿名只能发 1 张图，登录后 9 张
const maxImages = computed(() => (isLoggedIn() ? 9 : 1))
// 服务端压缩后/上传大小上限（超管可改）
const imageMaxMb = computed(() => site.value?.image_max_mb || 2)
const videoMaxMb = computed(() => site.value?.video_max_mb || 15)

// 浏览器端图片压缩：Canvas 重绘为 JPEG，压到 ≤maxBytes
async function compressImage(file, maxBytes) {
  if (/\.gif$/i.test(file.name)) return file // GIF 保动画，原样上传
  let bitmap
  try {
    bitmap = await createImageBitmap(file)
  } catch {
    return file
  }
  const maxDim = 1600
  const scale = Math.min(1, maxDim / Math.max(bitmap.width, bitmap.height))
  const w = Math.max(1, Math.round(bitmap.width * scale))
  const h = Math.max(1, Math.round(bitmap.height * scale))
  const canvas = document.createElement('canvas')
  canvas.width = w
  canvas.height = h
  canvas.getContext('2d').drawImage(bitmap, 0, 0, w, h)
  let quality = 0.85
  let blob = await new Promise((r) => canvas.toBlob(r, 'image/jpeg', quality))
  while (blob.size > maxBytes && quality > 0.35) {
    quality -= 0.15
    blob = await new Promise((r) => canvas.toBlob(r, 'image/jpeg', quality))
  }
  if (blob.size > maxBytes) return null
  return blob
}

// 勾选匿名时清空昵称（v-model 已处理状态，这里只做联动）
function onAnonChange() {
  if (form.anonymous) form.nickname = ''
}

const MAX = 500
const remain = computed(() => MAX - form.content.length)

// ---------- 媒体选择 ----------
function onPickImages(e) {
  imageError.value = ''
  const files = [...(e.target.files || [])]
  if (!files.length) return
  const room = maxImages.value - images.value.length
  const valid = []
  for (const f of files) {
    if (!/\.(jpg|jpeg|png|gif|webp)$/i.test(f.name)) {
      imageError.value = `「${f.name}」不是支持的图片格式`
      continue
    }
    if (f.size > USER_IMAGE_LIMIT_MB * 1024 * 1024) {
      imageError.value = `「${f.name}」原图超过 ${USER_IMAGE_LIMIT_MB}MB`
      continue
    }
    valid.push(f)
  }
  const picked = valid.slice(0, room)
  for (const f of picked) images.value.push({ file: f, url: URL.createObjectURL(f) })
  if (valid.length > room) imageError.value = `${isLoggedIn() ? '最多上传 9 张' : '未登录只能发 1 张图片，登录后可发 9 张'}`
  e.target.value = ''
}

function removeImage(i) {
  URL.revokeObjectURL(images.value[i].url)
  images.value.splice(i, 1)
}

function onPickVideo(e) {
  videoError.value = ''
  const file = e.target.files && e.target.files[0]
  e.target.value = ''
  if (!file) return
  if (!/\.(mp4|webm|mov)$/i.test(file.name)) return (videoError.value = '仅支持 mp4 / webm / mov 视频')
  if (file.size > videoMaxMb.value * 1024 * 1024) return (videoError.value = `视频不能超过 ${videoMaxMb.value}MB`)
  const url = URL.createObjectURL(file)
  const probe = document.createElement('video')
  probe.preload = 'metadata'
  probe.onloadedmetadata = () => {
    URL.revokeObjectURL(url)
    if (probe.duration > MAX_VIDEO_SEC + 0.5) {
      videoError.value = `视频时长 ${probe.duration.toFixed(1)} 秒，不能超过 ${MAX_VIDEO_SEC} 秒`
      return
    }
    video.value = { file, url: URL.createObjectURL(file), duration: probe.duration }
  }
  probe.onerror = () => {
    URL.revokeObjectURL(url)
    videoError.value = '无法读取视频，请检查文件'
  }
  probe.src = url
}

function removeVideo() {
  if (video.value) URL.revokeObjectURL(video.value.url)
  video.value = null
}

onMounted(async () => {
  try {
    site.value = await api.siteInfo()
  } catch {
    /* 忽略 */
  }
  // 登录用户昵称默认填入自己的
  if (auth.user && !form.nickname) form.nickname = auth.user.nickname || ''
})

function pickTheme(key) {
  form.theme = key
}

async function submit() {
  error.value = ''
  const content = form.content.trim()
  if (!content) {
    error.value = '想说的话还没写呢～'
    return
  }
  if (content.length > MAX) {
    error.value = `内容太长啦，最多 ${MAX} 字`
    return
  }
  submitting.value = true
  try {
    // 先压缩再上传媒体，拿到 URL 后再发布
    const imageUrls = []
    for (const img of images.value) {
      const blob = await compressImage(img.file, imageMaxMb.value * 1024 * 1024)
      if (!blob) {
        error.value = '图片压缩后仍超过限制，请更换图片'
        return
      }
      const isGif = /\.gif$/i.test(img.file.name)
      const upload = isGif ? img.file : new File([blob], 'image.jpg', { type: 'image/jpeg' })
      const r = await uploadFile(upload)
      imageUrls.push(r.url)
    }
    let videoUrl = null
    if (video.value) {
      const r = await uploadFile(video.value.file)
      videoUrl = r.url
    }
    await api.createPost({
      content,
      to_name: form.to_name.trim() || null,
      nickname: form.anonymous ? null : (form.nickname.trim() || null),
      theme: form.theme,
      anonymous: form.anonymous,
      images: imageUrls,
      video: videoUrl,
    })
    done.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="post-page">
    <div v-if="!done" class="form-card">
      <h2 class="form-title">✍️ 发布一条动态</h2>
      <p class="form-sub">
        {{ isLoggedIn() ? `将以「${auth.user.nickname || auth.user.username}」的账号发布（昵称可改）` : '未登录将以匿名发布' }}
      </p>

      <div class="form-field">
        <label class="form-label">对象 <span class="optional">（选填）</span></label>
        <input v-model="form.to_name" class="input" maxlength="50" placeholder="写给谁呢？比如：隔壁班的林同学" />
      </div>

      <div class="form-field">
        <label class="form-label">昵称 <span class="optional">（选填）</span></label>
        <input
          v-model="form.nickname"
          class="input"
          maxlength="50"
          :disabled="form.anonymous"
          placeholder="比如：图书馆三楼的小熊"
        />
      </div>

      <!-- 已登录用户可匿名发布 -->
      <div v-if="isLoggedIn()" class="form-field">
        <label class="anon-switch">
          <input v-model="form.anonymous" type="checkbox" @change="onAnonChange" />
          <span class="anon-switch-slider"></span>
          <span class="anon-switch-label">
            匿名发布 <span class="optional">（不显示昵称与头衔）</span>
          </span>
        </label>
        <p v-if="form.anonymous" class="anon-tip" style="margin-top: 8px">
          🕶 已开启匿名，将以「匿名同学」身份发布，不显示昵称与头衔。
        </p>
      </div>

      <div class="form-field">
        <label class="form-label">想说的话 *</label>
        <textarea
          v-model="form.content"
          class="textarea"
          :maxlength="MAX"
          rows="5"
          placeholder="把那些藏了很久的话，写在这里吧…"
        ></textarea>
        <div class="char-count" :class="{ warn: remain < 50 }">{{ remain }} / {{ MAX }}</div>
      </div>

      <div class="form-field">
        <label class="form-label">卡片配色</label>
        <div class="theme-picker">
          <button
            v-for="(t, key) in THEMES"
            :key="key"
            class="theme-swatch"
            :class="[t.cls, { selected: form.theme === key }]"
            :title="t.label"
            @click="pickTheme(key)"
          >
            <span v-if="form.theme === key" class="swatch-check">✓</span>
          </button>
        </div>
      </div>

      <!-- 图片 / 视频 -->
      <div class="form-field">
        <label class="form-label">
          图片 / 视频
          <span class="optional">
            （{{ isLoggedIn() ? `最多 ${maxImages} 张图 + 视频` : '未登录限 1 张图' }}，单图≤{{ imageMaxMb }}MB，视频≤{{ videoMaxMb }}MB / {{ MAX_VIDEO_SEC }}秒）
          </span>
        </label>
        <div class="media-picker">
          <button type="button" class="media-btn" @click="$refs.imgInput && $refs.imgInput.click()">📷 添加图片</button>
          <button v-if="isLoggedIn()" type="button" class="media-btn" @click="$refs.videoInput && $refs.videoInput.click()">🎬 添加视频</button>
          <input ref="imgInput" type="file" accept="image/*" multiple hidden @change="onPickImages" />
          <input ref="videoInput" type="file" accept="video/*" hidden @change="onPickVideo" />
        </div>
        <p v-if="!isLoggedIn()" class="form-tip" style="margin-top: 6px">
          🔒 未登录只能发 1 张图片、不能发视频；<router-link to="/account" class="notice-link">登录</router-link>后可发 9 张图片 + 视频。
        </p>

        <!-- 图片预览 -->
        <div v-if="images.length" class="media-preview-grid">
          <div v-for="(img, i) in images" :key="i" class="media-preview">
            <img :src="img.url" alt="图片" />
            <button type="button" class="media-remove" @click="removeImage(i)">✕</button>
          </div>
        </div>

        <!-- 视频预览 -->
        <div v-if="video" class="media-preview-video">
          <video :src="video.url" controls playsinline muted></video>
          <span class="media-duration">{{ video.duration.toFixed(1) }}s</span>
          <button type="button" class="media-remove" @click="removeVideo">✕</button>
        </div>

        <p v-if="imageError" class="form-error">{{ imageError }}</p>
        <p v-if="videoError" class="form-error">{{ videoError }}</p>
      </div>

      <p v-if="!isLoggedIn() && site" class="anon-tip">
        💡 未登录发布为匿名，每 IP / 设备 24 小时内限发 {{ site.anonymous_post_limit }} 条；<router-link to="/account" class="notice-link">登录</router-link>后不限。
      </p>

      <p v-if="error" class="form-error">{{ error }}</p>

      <button class="btn-primary btn-lg btn-block" :disabled="submitting" @click="submit">
        {{ submitting ? '正在发送…' : '发布' }}
      </button>
    </div>

    <div v-else class="form-card done-card">
      <div class="done-emoji">💖</div>
      <h2 class="form-title">发布成功！</h2>
      <p class="form-sub">
        {{ site?.moderation_mode ? '内容已提交，管理员审核通过后就会上墙哦～' : '你的内容已经出现在墙上了' }}
      </p>
      <div class="done-actions">
        <button class="btn-primary" @click="router.push('/')">去看看</button>
        <button class="btn-ghost" @click="done = false; form.content = ''">再发一条</button>
      </div>
    </div>
  </div>
</template>
