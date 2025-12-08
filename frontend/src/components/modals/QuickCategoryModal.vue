<script setup>
import { ref, onMounted, computed } from 'vue'
import { useFinanceStore } from '../../stores/finance'
import { CATEGORY_ICONS } from '../../constants/icons'

const props = defineProps({
  initialType: {
    type: String,
    default: 'EXPENSE'
  }
})

const emit = defineEmits(['close', 'success'])

const financeStore = useFinanceStore()

const name = ref('')
const type = ref(props.initialType)
const icon = ref('tag')
const loading = ref(false)
const error = ref('')
const nameInput = ref(null)

onMounted(() => {
  if (nameInput.value) {
    nameInput.value.focus()
  }
})

const handleSubmit = async () => {
  if (!name.value.trim()) {
    error.value = 'Category name is required'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const newCategory = await financeStore.createCategory({
      name: name.value,
      type: type.value,
      icon: icon.value
    })
    emit('success', newCategory)
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create category'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60]">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-xl font-bold text-gray-800">Create New Category</h2>
        <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-md text-sm mb-4">
        {{ error }}
      </div>

      <div class="space-y-4">
        <!-- Type Toggle -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Type</label>
          <div class="flex space-x-2 bg-gray-100 p-1 rounded-lg">
            <button
              type="button"
              @click="type = 'INCOME'"
              :class="[
                'flex-1 py-2 text-sm font-medium rounded-md transition-all',
                type === 'INCOME' 
                  ? 'bg-white text-green-700 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              Income
            </button>
            <button
              type="button"
              @click="type = 'EXPENSE'"
              :class="[
                'flex-1 py-2 text-sm font-medium rounded-md transition-all',
                type === 'EXPENSE' 
                  ? 'bg-white text-red-700 shadow-sm' 
                  : 'text-gray-500 hover:text-gray-700'
              ]"
            >
              Expense
            </button>
          </div>
        </div>

        <!-- Name Input -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Name</label>
          <input
            ref="nameInput"
            v-model="name"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g., Groceries, Salary"
            @keyup.enter="handleSubmit"
          />
        </div>

        <!-- Icon Picker -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Icon</label>
          <div class="grid grid-cols-6 gap-2 max-h-48 overflow-y-auto p-2 border border-gray-200 rounded-md bg-gray-50">
            <button
              v-for="i in CATEGORY_ICONS"
              :key="i.id"
              type="button"
              @click="icon = i.id"
              :class="[
                'p-2 rounded-md flex flex-col items-center justify-center transition-all aspect-square',
                icon === i.id 
                  ? 'bg-indigo-100 text-indigo-700 ring-2 ring-indigo-500' 
                  : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-100'
              ]"
              :title="i.name"
            >
              <svg 
                class="w-5 h-5 mb-1" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
                v-html="i.svg"
              ></svg>
            </button>
          </div>
        </div>
      </div>

      <div class="flex space-x-3 mt-6">
        <button
          type="button"
          @click="$emit('close')"
          class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="button"
          @click="handleSubmit"
          :disabled="loading"
          class="flex-1 py-2 px-4 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {{ loading ? 'Creating...' : 'Create' }}
        </button>
      </div>
    </div>
  </div>
</template>
