<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../../api'

const categories = ref([])
const loading = ref(true)
const showModal = ref(false)
const showDeleteModal = ref(false)
const categoryToDelete = ref(null)
const actionLoading = ref(false)
const deleteLoading = ref(false)
const error = ref('')
const deleteError = ref('')

const form = ref({
  name: '',
  type: 'EXPENSE',
  icon: 'default'
})

const incomeCategories = computed(() => categories.value.filter(c => c.type === 'INCOME'))
const expenseCategories = computed(() => categories.value.filter(c => c.type === 'EXPENSE'))

const fetchCategories = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/categories')
    categories.value = response.data
  } catch (err) {
    console.error('Failed to fetch categories:', err)
  } finally {
    loading.value = false
  }
}

const openModal = () => {
  form.value = { name: '', type: 'EXPENSE', icon: 'default' }
  error.value = ''
  showModal.value = true
}

const createCategory = async () => {
  if (!form.value.name.trim()) {
    error.value = 'Category name is required'
    return
  }

  actionLoading.value = true
  error.value = ''

  try {
    const response = await api.post('/admin/categories', form.value)
    categories.value.push(response.data)
    showModal.value = false
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create category'
  } finally {
    actionLoading.value = false
  }
}

const openDeleteModal = (category) => {
  categoryToDelete.value = category
  deleteError.value = ''
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!categoryToDelete.value) return

  deleteLoading.value = true
  deleteError.value = ''

  try {
    await api.delete(`/admin/categories/${categoryToDelete.value.id}`)
    categories.value = categories.value.filter(c => c.id !== categoryToDelete.value.id)
    showDeleteModal.value = false
    categoryToDelete.value = null
  } catch (err) {
    deleteError.value = err.response?.data?.detail || 'Failed to delete category'
  } finally {
    deleteLoading.value = false
  }
}

onMounted(() => {
  fetchCategories()
})
</script>

<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold text-gray-800">Global Categories</h1>
      <button
        @click="openModal"
        class="px-4 py-2 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 transition-colors"
      >
        + Add Category
      </button>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
    </div>

    <div v-else class="grid grid-cols-1 lg:grid-cols-2 gap-8">
      <!-- Income Categories -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 bg-green-50 border-b border-green-100">
          <h2 class="text-lg font-semibold text-green-800">Income Categories</h2>
          <p class="text-sm text-green-600">{{ incomeCategories.length }} categories</p>
        </div>
        <div class="divide-y divide-gray-100">
          <div
            v-for="cat in incomeCategories"
            :key="cat.id"
            class="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                <span class="text-green-600 font-medium">{{ cat.name.charAt(0) }}</span>
              </div>
              <div>
                <p class="font-medium text-gray-800">{{ cat.name }}</p>
                <p class="text-xs text-gray-500">{{ cat.icon }}</p>
              </div>
            </div>
            <button
              @click="openDeleteModal(cat)"
              class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
          <div v-if="incomeCategories.length === 0" class="px-6 py-8 text-center text-gray-500">
            No income categories
          </div>
        </div>
      </div>

      <!-- Expense Categories -->
      <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="px-6 py-4 bg-red-50 border-b border-red-100">
          <h2 class="text-lg font-semibold text-red-800">Expense Categories</h2>
          <p class="text-sm text-red-600">{{ expenseCategories.length }} categories</p>
        </div>
        <div class="divide-y divide-gray-100">
          <div
            v-for="cat in expenseCategories"
            :key="cat.id"
            class="px-6 py-4 flex items-center justify-between hover:bg-gray-50"
          >
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                <span class="text-red-600 font-medium">{{ cat.name.charAt(0) }}</span>
              </div>
              <div>
                <p class="font-medium text-gray-800">{{ cat.name }}</p>
                <p class="text-xs text-gray-500">{{ cat.icon }}</p>
              </div>
            </div>
            <button
              @click="openDeleteModal(cat)"
              class="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
            >
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
          <div v-if="expenseCategories.length === 0" class="px-6 py-8 text-center text-gray-500">
            No expense categories
          </div>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
        <h2 class="text-xl font-bold text-gray-800 mb-4">Create Global Category</h2>

        <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4">
          {{ error }}
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Category Name</label>
            <input
              v-model="form.name"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              placeholder="e.g., Entertainment"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Type</label>
            <div class="flex gap-4">
              <label class="flex items-center">
                <input type="radio" v-model="form.type" value="INCOME" class="mr-2" />
                <span class="text-green-600 font-medium">Income</span>
              </label>
              <label class="flex items-center">
                <input type="radio" v-model="form.type" value="EXPENSE" class="mr-2" />
                <span class="text-red-600 font-medium">Expense</span>
              </label>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Icon (optional)</label>
            <input
              v-model="form.icon"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500"
              placeholder="e.g., film, car, home"
            />
          </div>
        </div>

        <div class="flex gap-4 mt-6">
          <button
            @click="showModal = false"
            class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="createCategory"
            :disabled="actionLoading"
            class="flex-1 py-2 px-4 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {{ actionLoading ? 'Creating...' : 'Create' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
        <div class="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
          <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>

        <h2 class="text-xl font-bold text-gray-800 text-center mb-2">Delete Category</h2>

        <p v-if="categoryToDelete" class="text-gray-600 text-center mb-4">
          Are you sure you want to delete "<strong>{{ categoryToDelete.name }}</strong>"?
          This is a global category and will affect all users.
        </p>

        <div v-if="deleteError" class="bg-red-50 text-red-600 p-3 rounded-lg text-sm mb-4">
          {{ deleteError }}
        </div>

        <div class="flex gap-4">
          <button
            @click="showDeleteModal = false; categoryToDelete = null; deleteError = ''"
            class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="confirmDelete"
            :disabled="deleteLoading"
            class="flex-1 py-2 px-4 bg-red-600 text-white font-medium rounded-lg hover:bg-red-700 disabled:opacity-50"
          >
            {{ deleteLoading ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
