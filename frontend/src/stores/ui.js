import { defineStore } from 'pinia'
import { ref } from 'vue'

let toastTimer = null

export const useUIStore = defineStore('ui', () => {
  const toast = ref({ message: '', type: 'success', visible: false })
  const loading = ref(false)

  function showToast({ message, type = 'success', duration = 5000 }) {
    toast.value = { message, type, visible: true }

    if (toastTimer) {
      clearTimeout(toastTimer)
    }

    if (duration > 0) {
      toastTimer = setTimeout(() => {
        hideToast()
      }, duration)
    }
  }

  function hideToast() {
    toast.value = { ...toast.value, visible: false }
    if (toastTimer) {
      clearTimeout(toastTimer)
      toastTimer = null
    }
  }

  function startLoading() {
    loading.value = true
  }

  function stopLoading() {
    loading.value = false
  }

  return {
    toast,
    loading,
    showToast,
    hideToast,
    startLoading,
    stopLoading
  }
})
