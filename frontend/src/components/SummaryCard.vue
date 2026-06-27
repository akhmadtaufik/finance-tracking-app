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
 },
 isLoading: {
 type: Boolean,
 default: false
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
      return 'text-pale-green'
    case 'expense':
      return 'text-coral-soft'
    case 'net':
      return 'text-on-dark'
    default:
      return 'text-on-dark'
  }
})
</script>

<template>
  <div class="bg-white/5 border border-white/10 rounded-sm p-6" data-testid="summary-card">
    <p class="text-sm font-medium text-pale-green">{{ title }}</p>
    <phantom-ui :loading="isLoading" animation="shimmer">
      <p class="text-2xl font-bold mt-2" :class="variantClasses">
        {{ formattedAmount }}
      </p>
    </phantom-ui>
  </div>
</template>
