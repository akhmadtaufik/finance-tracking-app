<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import api from '../../api'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  categoryId: {
    type: [Number, String],
    default: null
  },
  placeholder: {
    type: String,
    default: 'Enter description...'
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const suggestions = ref([])
const inputRef = ref(null)
const containerRef = ref(null)
const loading = ref(false)

// Fetch suggestions when category changes
watch(() => props.categoryId, async (newVal) => {
  if (newVal) {
    await fetchSuggestions(newVal)
  } else {
    suggestions.value = []
  }
}, { immediate: true })

async function fetchSuggestions(categoryId) {
  loading.value = true
  try {
    const response = await api.get('/transactions/suggestions', {
      params: { category_id: categoryId }
    })
    suggestions.value = response.data
  } catch (error) {
    console.error('Failed to fetch suggestions:', error)
    suggestions.value = []
  } finally {
    loading.value = false
  }
}

const filteredSuggestions = computed(() => {
  if (!props.modelValue && props.modelValue !== '') return []
  
  const query = props.modelValue.toLowerCase()
  return suggestions.value.filter(item => 
    item.toLowerCase().includes(query) && 
    item.toLowerCase() !== query // Don't show if exactly matches
  ).slice(0, 10) // Limit to 10 items
})

const showDropdown = computed(() => {
  return isOpen.value && filteredSuggestions.value.length > 0 && props.modelValue.length > 0
})

function handleInput(event) {
  emit('update:modelValue', event.target.value)
  isOpen.value = true
}

function handleFocus() {
  isOpen.value = true
}

function selectSuggestion(suggestion) {
  emit('update:modelValue', suggestion)
  isOpen.value = false
}

// Click outside to close
function handleClickOutside(event) {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('mousedown', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
})
</script>

<template>
  <div class="relative" ref="containerRef">
    <input
      ref="inputRef"
      :value="modelValue"
      @input="handleInput"
      @focus="handleFocus"
      type="text"
      class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
      :placeholder="placeholder"
    />
    
    <!-- Dropdown -->
    <div 
      v-if="showDropdown"
      class="absolute z-50 w-full mt-1 bg-white shadow-lg rounded-md max-h-60 overflow-auto border border-gray-200"
    >
      <ul class="py-1">
        <li 
          v-for="suggestion in filteredSuggestions" 
          :key="suggestion"
          @mousedown.prevent="selectSuggestion(suggestion)"
          class="px-4 py-2 hover:bg-indigo-50 cursor-pointer text-sm text-gray-700 transition-colors duration-150"
        >
          {{ suggestion }}
        </li>
      </ul>
    </div>
  </div>
</template>
