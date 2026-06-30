<script setup>
import { ref, onMounted, computed } from 'vue'
import { useFinanceStore } from '../stores/finance'
import api from '../api'
import { CATEGORY_ICONS, getIconSvg } from '../constants/icons'

const financeStore = useFinanceStore()

const showModal = ref(false)
const showDeleteModal = ref(false)
const categoryToDelete = ref(null)
const categoryName = ref('')
const categoryType = ref('EXPENSE')
const categoryIcon = ref('wallet')
const loading = ref(false)
const deleteLoading = ref(false)
const error = ref('')
const deleteError = ref('')
const activeTab = ref('ALL')

onMounted(async () => {
 await financeStore.fetchCategories()
})

const filteredCategories = computed(() => {
 if (activeTab.value === 'ALL') return financeStore.categories
 return financeStore.categories.filter(c => c.type === activeTab.value)
})

const incomeCategories = computed(() => financeStore.categories.filter(c => c.type === 'INCOME'))
const expenseCategories = computed(() => financeStore.categories.filter(c => c.type === 'EXPENSE'))

const openModal = () => {
 categoryName.value = ''
 categoryType.value = 'EXPENSE'
 categoryIcon.value = 'wallet'
 error.value = ''
 showModal.value = true
}

const createCategory = async () => {
 if (!categoryName.value.trim()) {
 error.value = 'Category name is required'
 return
 }
 
 loading.value = true
 error.value = ''
 
 try {
 await financeStore.createCategory({
 name: categoryName.value,
 type: categoryType.value,
 icon: categoryIcon.value
 })
 showModal.value = false
 } catch (err) {
 error.value = err.response?.data?.detail || 'Failed to create category'
 } finally {
 loading.value = false
 }
}

const openDeleteModal = (category) => {
 if (category.is_global) {
 deleteError.value = 'Cannot delete global categories'
 showDeleteModal.value = true
 categoryToDelete.value = null
 return
 }
 categoryToDelete.value = category
 deleteError.value = ''
 showDeleteModal.value = true
}

const confirmDelete = async () => {
 if (!categoryToDelete.value) {
 showDeleteModal.value = false
 return
 }
 
 deleteLoading.value = true
 deleteError.value = ''
 
 try {
 await api.delete(`/categories/${categoryToDelete.value.id}`)
 await financeStore.fetchCategories()
 showDeleteModal.value = false
 categoryToDelete.value = null
 } catch (err) {
 deleteError.value = err.response?.data?.detail || 'Failed to delete category'
 } finally {
 deleteLoading.value = false
 }
}
</script>

<template>
 <div class="max-w-4xl mx-auto px-4 py-8">
 <div class="flex justify-between items-center mb-8">
 <h1 class="font-display text-4xl tracking-tight text-ink">Categories</h1>
 <button
 @click="openModal"
 class="bg-primary text-on-primary rounded-pill px-6 py-2.5 font-medium text-sm hover:opacity-90 transition-opacity"
 >
 + Add Category
 </button>
 </div>

 <!-- Tabs -->
 <div class="flex space-x-2 mb-6">
 <button
 @click="activeTab = 'ALL'"
 :class="[
 activeTab === 'ALL' ? 'bg-coral text-canvas font-medium rounded-pill px-5 py-2 transition-colors' : 'bg-transparent text-slate hover:text-ink font-medium rounded-pill px-5 py-2 transition-colors'
 ]"
 >
 All <span class="opacity-60 text-sm">({{ financeStore.categories.length }})</span>
 </button>
 <button
 @click="activeTab = 'INCOME'"
 :class="[
 activeTab === 'INCOME' ? 'bg-coral text-canvas font-medium rounded-pill px-5 py-2 transition-colors' : 'bg-transparent text-slate hover:text-ink font-medium rounded-pill px-5 py-2 transition-colors'
 ]"
 >
 Income <span class="opacity-60 text-sm">({{ incomeCategories.length }})</span>
 </button>
 <button
 @click="activeTab = 'EXPENSE'"
 :class="[
 activeTab === 'EXPENSE' ? 'bg-coral text-canvas font-medium rounded-pill px-5 py-2 transition-colors' : 'bg-transparent text-slate hover:text-ink font-medium rounded-pill px-5 py-2 transition-colors'
 ]"
 >
 Expense <span class="opacity-60 text-sm">({{ expenseCategories.length }})</span>
 </button>
 </div>

 <!-- Categories Grid -->
 <phantom-ui :loading="financeStore.isLoadingCategories" animation="shimmer">
 <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
 <div
 v-for="category in filteredCategories"
 :key="category.id"
 class="bg-canvas border border-card-border rounded-lg p-5 flex items-center justify-between hover:border-ink transition-colors"
 >
 <div class="flex items-center space-x-3">
 <div
 :class="[
 'w-12 h-12 flex items-center justify-center border border-hairline rounded-md',
 category.type === 'INCOME' ? 'text-deep-green' : 'text-coral'
 ]"
 >
 <svg 
 class="w-5 h-5" 
 fill="none" 
 stroke="currentColor" 
 viewBox="0 0 24 24"
 v-html="getIconSvg(category.icon)"
 ></svg>
 </div>
 <div>
 <p class="font-body font-medium text-lg text-ink">{{ category.name }}</p>
 <div class="flex items-center space-x-2 mt-1">
 <span
 :class="[
 'bg-transparent border rounded-sm px-2 py-0.5 font-mono text-xs uppercase tracking-wider',
 category.type === 'INCOME' ? 'border-deep-green text-deep-green' : 'border-coral text-coral'
 ]"
 >
 {{ category.type }}
 </span>
 <span v-if="category.is_global" class="bg-transparent border rounded-sm px-2 py-0.5 font-mono text-xs uppercase tracking-wider border-slate text-slate">
 Global
 </span>
 <span v-else class="bg-transparent border rounded-sm px-2 py-0.5 font-mono text-xs uppercase tracking-wider border-slate text-slate">
 Custom
 </span>
 </div>
 </div>
 </div>
 <button
 v-if="!category.is_global"
 @click="openDeleteModal(category)"
 class="text-slate hover:text-error transition-colors p-2"
 >
 <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
 </svg>
 </button>
 </div>
 </div>

 <p v-if="filteredCategories.length === 0" class="text-center text-gray-500 py-12">
 No categories found.
 </p>
 </phantom-ui>

 <!-- Modal -->
 <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
 <div class="bg-canvas border border-card-border rounded-lg p-6 w-full max-w-md mx-4">
 <h2 class="text-xl font-bold text-gray-800 mb-4">Create Custom Category</h2>
 
 <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-md text-sm mb-4">
 {{ error }}
 </div>

 <div class="space-y-4">
 <div>
 <label class="block text-sm font-medium text-gray-700 mb-1">Category Name</label>
 <input
 v-model="categoryName"
 type="text"
 class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
 placeholder="e.g., Freelance, Gym, Netflix"
 />
 </div>
 
 <div>
 <label class="block text-sm font-medium text-gray-700 mb-2">Type</label>
 <div class="flex space-x-4">
 <button
 type="button"
 @click="categoryType = 'INCOME'"
 :class="[
 'flex-1 py-2 px-4 rounded-md font-medium',
 categoryType === 'INCOME' ? 'bg-green-600 text-white' : 'bg-gray-100 text-gray-700'
 ]"
 >
 Income
 </button>
 <button
 type="button"
 @click="categoryType = 'EXPENSE'"
 :class="[
 'flex-1 py-2 px-4 rounded-md font-medium',
 categoryType === 'EXPENSE' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-700'
 ]"
 >
 Expense
 </button>
 </div>
 </div>

 <div>
 <label class="block text-sm font-medium text-gray-700 mb-2">Icon ({{ CATEGORY_ICONS.length }} available)</label>
 <div class="grid grid-cols-8 gap-2 max-h-56 overflow-y-auto p-2 border border-gray-200 rounded-md bg-gray-50">
 <button
 v-for="icon in CATEGORY_ICONS"
 :key="icon.id"
 type="button"
 @click="categoryIcon = icon.id"
 :class="[
 'p-2 rounded-md flex items-center justify-center transition-all',
 categoryIcon === icon.id 
 ? 'bg-indigo-100 ring-2 ring-indigo-500' 
 : 'bg-gray-50 hover:bg-gray-100'
 ]"
 :title="icon.name"
 >
 <svg 
 class="w-5 h-5 text-gray-700" 
 fill="none" 
 stroke="currentColor" 
 viewBox="0 0 24 24"
 v-html="icon.svg"
 ></svg>
 </button>
 </div>
 <p class="text-xs text-gray-500 mt-1">Selected: {{ CATEGORY_ICONS.find(i => i.id === categoryIcon)?.name }}</p>
 </div>
 </div>

 <div class="flex space-x-4 mt-6">
 <button
 @click="showModal = false"
 class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
 >
 Cancel
 </button>
 <button
 @click="createCategory"
 :disabled="loading"
 class="flex-1 py-2 px-4 bg-primary text-on-primary rounded-pill px-6 py-3 font-medium text-sm"
 >
 {{ loading ? 'Creating...' : 'Create Category' }}
 </button>
 </div>
 </div>
 </div>

 <!-- Delete Confirmation Modal -->
 <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
 <div class="bg-canvas border border-card-border rounded-lg p-6 w-full max-w-md mx-4">
 <div class="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
 <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
 </svg>
 </div>
 
 <h2 class="text-xl font-bold text-gray-800 text-center mb-2">Delete Category</h2>
 
 <p v-if="categoryToDelete" class="text-gray-600 text-center mb-4">
 Are you sure you want to delete "<strong>{{ categoryToDelete.name }}</strong>"? This action cannot be undone.
 </p>
 
 <div v-if="deleteError" class="bg-red-50 text-red-600 p-3 rounded-md text-sm mb-4">
 {{ deleteError }}
 </div>

 <div class="flex space-x-4">
 <button
 @click="showDeleteModal = false; categoryToDelete = null; deleteError = ''"
 class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
 >
 Cancel
 </button>
 <button
 v-if="categoryToDelete"
 @click="confirmDelete"
 :disabled="deleteLoading"
 class="flex-1 py-2 px-4 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 disabled:opacity-50"
 >
 {{ deleteLoading ? 'Deleting...' : 'Delete' }}
 </button>
 <button
 v-else
 @click="showDeleteModal = false; deleteError = ''"
 class="flex-1 py-2 px-4 bg-gray-600 text-white font-medium rounded-md hover:bg-gray-700"
 >
 OK
 </button>
 </div>
 </div>
 </div>
 </div>
</template>
