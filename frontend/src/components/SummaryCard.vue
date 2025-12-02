<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  amount: {
    type: Number,
    required: true
  },
  variant: {
    type: String,
    default: 'default'
  }
})

const formattedAmount = computed(() => new Intl.NumberFormat('id-ID', {
  style: 'currency',
  currency: 'IDR',
  minimumFractionDigits: 0
}).format(props.amount))

const variantClasses = computed(() => {
  switch (props.variant) {
    case 'income':
      return 'text-green-600'
    case 'expense':
      return 'text-red-600'
    case 'net':
      return ''
    default:
      return 'text-gray-800'
  }
})
</script>

<template>
  <div class="bg-white rounded-lg shadow p-6" data-testid="summary-card">
    <p class="text-sm font-medium text-gray-500">{{ title }}</p>
    <p class="text-2xl font-bold" :class="variantClasses">
      {{ formattedAmount }}
    </p>
  </div>
</template>
