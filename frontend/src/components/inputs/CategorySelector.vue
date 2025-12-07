<script setup>
import { getIconSvg } from '../../constants/icons'

defineProps({
  categories: { type: Array, default: () => [] },
  modelValue: { type: [Number, null], default: null }
})

const emit = defineEmits(['update:modelValue'])

const selectCategory = (id) => {
  emit('update:modelValue', id)
}
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <button
      v-for="cat in categories"
      :key="cat.id"
      type="button"
      @click="selectCategory(cat.id)"
      :class="[
        'inline-flex items-center gap-2 px-3 py-2 rounded-full text-sm transition-all duration-150 cursor-pointer border',
        modelValue === cat.id
          ? 'bg-blue-100 text-blue-700 border-blue-300 font-medium'
          : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50 hover:border-gray-300'
      ]"
    >
      <svg 
        class="w-4 h-4 shrink-0" 
        fill="none" 
        stroke="currentColor" 
        viewBox="0 0 24 24"
        v-html="getIconSvg(cat.icon)"
      ></svg>
      <span class="whitespace-nowrap">{{ cat.name }}</span>
    </button>
  </div>
  <p v-if="categories.length === 0" class="text-sm text-gray-400 text-center py-4">
    No categories available for this type
  </p>
</template>
