<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  modelValue: {
    type: [Number, String],
    default: 0
  },
  placeholder: {
    type: String,
    default: '0'
  }
})

const emit = defineEmits(['update:modelValue'])

const displayValue = ref('')

const formatNumber = (num) => {
  if (!num && num !== 0) return ''
  return new Intl.NumberFormat('id-ID').format(num)
}

const parseNumber = (str) => {
  if (!str) return 0
  const cleaned = str.replace(/\./g, '').replace(/,/g, '')
  return parseInt(cleaned) || 0
}

const handleInput = (event) => {
  const input = event.target
  const cursorPosition = input.selectionStart
  const oldLength = displayValue.value.length
  
  let rawValue = input.value.replace(/[^\d]/g, '')
  const numericValue = parseInt(rawValue) || 0
  
  displayValue.value = formatNumber(numericValue)
  emit('update:modelValue', numericValue)
  
  // Adjust cursor position
  const newLength = displayValue.value.length
  const diff = newLength - oldLength
  
  setTimeout(() => {
    const newPosition = Math.max(0, cursorPosition + diff)
    input.setSelectionRange(newPosition, newPosition)
  }, 0)
}

watch(() => props.modelValue, (newVal) => {
  const numVal = typeof newVal === 'string' ? parseNumber(newVal) : newVal
  displayValue.value = formatNumber(numVal)
}, { immediate: true })
</script>

<template>
  <div class="relative">
    <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 text-sm">Rp</span>
    <input
      type="text"
      inputmode="numeric"
      :value="displayValue"
      @input="handleInput"
      :placeholder="placeholder"
      class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
    />
  </div>
</template>
