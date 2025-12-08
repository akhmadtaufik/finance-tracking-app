<script setup>
import { ref } from 'vue'
import { getIconSvg } from '../../constants/icons'
import QuickCategoryModal from '../modals/QuickCategoryModal.vue'

defineProps({
  categories: { type: Array, default: () => [] },
  modelValue: { type: [Number, null], default: null },
  currentType: { type: String, default: 'EXPENSE' }
})

const emit = defineEmits(['update:modelValue'])

const showQuickAdd = ref(false)

const selectCategory = (id) => {
  emit('update:modelValue', id)
}

const handleQuickAddSuccess = (newCategory) => {
  emit('update:modelValue', newCategory.id)
  showQuickAdd.value = false
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
    
    <!-- Quick Add Button -->
    <button
      type="button"
      @click="showQuickAdd = true"
      class="inline-flex items-center gap-2 px-3 py-2 rounded-full text-sm transition-all duration-150 cursor-pointer border border-dashed border-gray-300 text-gray-500 hover:border-indigo-500 hover:text-indigo-600 bg-white"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
      </svg>
      <span class="whitespace-nowrap">New</span>
    </button>
  </div>
  <p v-if="categories.length === 0" class="text-sm text-gray-400 text-center py-4">
    No categories found. Create one!
  </p>

  <QuickCategoryModal
    v-if="showQuickAdd"
    :initial-type="currentType"
    @close="showQuickAdd = false"
    @success="handleQuickAddSuccess"
  />
</template>
