<script setup>
import { ref, onErrorCaptured } from 'vue'

const props = defineProps({
  fallbackMessage: {
    type: String,
    default: 'Something went wrong. Please try again.'
  }
})

const hasError = ref(false)
const errorInfo = ref(null)

const resetError = () => {
  hasError.value = false
  errorInfo.value = null
}

onErrorCaptured((err) => {
  console.error('Captured error in boundary:', err)
  hasError.value = true
  errorInfo.value = err
  return false
})
</script>

<template>
  <div>
    <template v-if="!hasError">
      <slot />
    </template>
    <div v-else class="p-6 text-center" role="alert" aria-live="assertive">
      <p class="text-lg font-semibold text-gray-800 mb-2">{{ fallbackMessage }}</p>
      <p class="text-sm text-gray-500 mb-4">Please refresh the page or go back.</p>
      <button
        class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md"
        @click="resetError"
      >
        Retry
      </button>
    </div>
  </div>
</template>
