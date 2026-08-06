<script setup>
import { onMounted, ref } from 'vue'

const hearts = ref([])
const EMOJIS = ['❤️', '💗', '💕', '💘', '💖', '💜', '🩷']

onMounted(() => {
  // 手机端爱心更少更小，避免小屏显得杂乱
  const count = window.innerWidth < 640 ? 6 : 14
  const sizeBase = window.innerWidth < 640 ? 10 : 16
  hearts.value = Array.from({ length: count }, (_, i) => ({
    id: i,
    left: Math.random() * 92,
    size: sizeBase + Math.random() * 18,
    delay: Math.random() * 14,
    duration: 16 + Math.random() * 18,
    opacity: window.innerWidth < 640 ? 0.06 + Math.random() * 0.08 : 0.08 + Math.random() * 0.14,
    emoji: EMOJIS[i % EMOJIS.length],
  }))
})
</script>

<template>
  <div class="heart-bg" aria-hidden="true">
    <span
      v-for="h in hearts"
      :key="h.id"
      class="float-heart"
      :style="{
        left: h.left + '%',
        fontSize: h.size + 'px',
        animationDelay: h.delay + 's',
        animationDuration: h.duration + 's',
        opacity: h.opacity,
      }"
    >
      {{ h.emoji }}
    </span>
  </div>
</template>

<style scoped>
.heart-bg {
  position: fixed;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}
.float-heart {
  position: absolute;
  bottom: -70px;
  animation: rise linear infinite;
  user-select: none;
  pointer-events: none; /* 确保不遮挡点击 */
}
@keyframes rise {
  0% {
    transform: translateY(0) rotate(0deg);
  }
  100% {
    transform: translateY(-115vh) rotate(28deg);
  }
}
</style>
