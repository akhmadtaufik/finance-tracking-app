<script setup>
import { ref, watch, nextTick } from 'vue'

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

const inputRef = ref(null)
const displayValue = ref('')

const formatNumber = (num) => {
  if (num === 0) return '0'
  if (!num) return ''
  return new Intl.NumberFormat('id-ID').format(num)
}

const parseNumber = (str) => {
  if (!str) return 0
  const cleaned = str.replace(/\./g, '').replace(/,/g, '')
  return parseInt(cleaned) || 0
}

// Count digits in a string
const countDigits = (str) => (str.match(/\d/g) || []).length

const handleInput = (event) => {
  const input = event.target
  const oldCursorPos = input.selectionStart
  const rawValue = input.value

  // 1. Clean: Remove all non-numeric chars
  let cleanStr = rawValue.replace(/\D/g, '')

  // 2. Parse to Integer (automatically strips leading zeros: '05' -> 5)
  const numericValue = parseInt(cleanStr || '0', 10)

  // 3. Count digits before cursor in raw input
  const leftSide = rawValue.substring(0, oldCursorPos)
  let digitsBeforeCursor = countDigits(leftSide)

  // 4. Handle leading zero replacement scenario
  // If cleanStr was "05", "01", etc. the leading zero gets stripped by parseInt
  const hadLeadingZeroReplacement = cleanStr.length > 1 && cleanStr.startsWith('0')
  if (hadLeadingZeroReplacement) {
    digitsBeforeCursor = Math.max(0, digitsBeforeCursor - 1)
  }

  // 5. Format
  const formattedValue = formatNumber(numericValue)

  // 6. Update DOM & Emit
  displayValue.value = formattedValue
  emit('update:modelValue', numericValue)

  // 7. Restore Cursor
  nextTick(() => {
    if (!inputRef.value) return

    let newCursorPos = 0
    let digitsFound = 0

    // Scan the new formatted string to find where cursor should be
    for (let i = 0; i < formattedValue.length; i++) {
      if (/\d/.test(formattedValue[i])) {
        digitsFound++
      }
      // Position cursor after the Nth digit
      if (digitsFound === digitsBeforeCursor && digitsBeforeCursor > 0) {
        newCursorPos = i + 1
        break
      }
    }

    // Edge case: cursor past all digits, put at end
    if (digitsBeforeCursor > 0 && digitsFound < digitsBeforeCursor) {
      newCursorPos = formattedValue.length
    }

    // Edge case: If digitsBeforeCursor is 0, put at start
    if (digitsBeforeCursor === 0) {
      newCursorPos = 0
    }

    // Special case: If leading zero was replaced, put cursor at end
    if (hadLeadingZeroReplacement) {
      newCursorPos = formattedValue.length
    }

    // CRITICAL FIX: Force cursor to END when value is 0
    // This ensures typing on "0" works correctly (cursor is "0|" not "|0")
    if (numericValue === 0) {
      newCursorPos = formattedValue.length
    }

    inputRef.value.setSelectionRange(newCursorPos, newCursorPos)
  })
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
      ref="inputRef"
      type="text"
      inputmode="numeric"
      :value="displayValue"
      @input="handleInput"
      :placeholder="placeholder"
      class="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
    />
  </div>
</template>
