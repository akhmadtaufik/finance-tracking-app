<script setup>
import { storeToRefs } from 'pinia'
import { useUIStore } from '../stores/ui'

const uiStore = useUIStore()
const { toast } = storeToRefs(uiStore)

const handleClose = () => {
  uiStore.hideToast()
}
</script>

<template>
  <transition name="fade">
    <div
      v-if="toast.visible"
      class="fixed top-4 right-4 z-50 max-w-sm w-full bg-white shadow-lg rounded-lg border border-gray-200 p-4 flex items-start gap-3"
      role="alert"
      aria-live="assertive"
      tabindex="0"
    >
      <div
        class="w-2 h-2 mt-2 rounded-full"
        :class="toast.type === 'error' ? 'bg-red-500' : 'bg-green-500'"
        aria-hidden="true"
      ></div>
      <div class="flex-1">
        <p class="text-sm text-gray-800">
          {{ toast.message }}
        </p>
      </div>
      <button
        class="text-gray-400 hover:text-gray-600"
        @click="handleClose"
        aria-label="Close notification"
      >
        &times;
      </button>
    </div>
  </transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
