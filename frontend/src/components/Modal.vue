<script setup>
defineProps({
  title: { type: String, default: '' },
  show: { type: Boolean, default: false },
  confirmText: { type: String, default: '确定' },
  cancelText: { type: String, default: '取消' },
  danger: { type: Boolean, default: false },
})
const emit = defineEmits(['confirm', 'cancel'])
</script>

<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="show" class="modal-mask" @click.self="emit('cancel')">
        <div class="modal-box">
          <div class="modal-title">{{ title }}</div>
          <div class="modal-body"><slot /></div>
          <div class="modal-footer">
            <button class="btn-ghost btn-sm" @click="emit('cancel')">{{ cancelText }}</button>
            <button class="btn-primary btn-sm" :class="{ 'btn-danger-solid': danger }" @click="emit('confirm')">
              {{ confirmText }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>
