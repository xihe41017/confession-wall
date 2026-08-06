import { reactive } from 'vue'

export const toasts = reactive([])
let _id = 0

export function toast(message, type = 'success', duration = 2200) {
  const id = ++_id
  toasts.push({ id, message, type })
  setTimeout(() => {
    const i = toasts.findIndex((t) => t.id === id)
    if (i >= 0) toasts.splice(i, 1)
  }, duration)
}

export const toastSuccess = (m) => toast(m, 'success', 2200)
export const toastError = (m) => toast(m, 'error', 3000)
export const toastInfo = (m) => toast(m, 'info', 2400)
