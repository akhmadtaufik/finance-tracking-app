<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const stats = ref({
  total_users: 0,
  total_transactions: 0,
  active_users_24h: 0,
  total_income: 0,
  total_expense: 0
})
const loading = ref(true)

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}

const fetchStats = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/stats')
    stats.value = response.data
  } catch (error) {
    console.error('Failed to fetch stats:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchStats()
})
</script>

<template>
  <div class="p-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-8">Admin Dashboard</h1>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
    </div>

    <div v-else>
      <!-- Stats Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        <!-- Total Users -->
        <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 mb-1">Total Users</p>
              <p class="text-3xl font-bold text-gray-800">{{ stats.total_users }}</p>
            </div>
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Total Transactions -->
        <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 mb-1">Total Transactions</p>
              <p class="text-3xl font-bold text-gray-800">{{ stats.total_transactions }}</p>
            </div>
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Active Users 24h -->
        <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm text-gray-500 mb-1">Active Users (24h)</p>
              <p class="text-3xl font-bold text-gray-800">{{ stats.active_users_24h }}</p>
            </div>
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
              <svg class="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.636 18.364a9 9 0 010-12.728m12.728 0a9 9 0 010 12.728m-9.9-2.829a5 5 0 010-7.07m7.072 0a5 5 0 010 7.07M13 12a1 1 0 11-2 0 1 1 0 012 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>

      <!-- Financial Overview -->
      <div class="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h2 class="text-lg font-semibold text-gray-800 mb-6">Financial Overview (All Users)</h2>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="p-4 bg-green-50 rounded-lg">
            <p class="text-sm text-green-600 mb-1">Total Income</p>
            <p class="text-2xl font-bold text-green-700">{{ formatCurrency(stats.total_income) }}</p>
          </div>
          
          <div class="p-4 bg-red-50 rounded-lg">
            <p class="text-sm text-red-600 mb-1">Total Expense</p>
            <p class="text-2xl font-bold text-red-700">{{ formatCurrency(stats.total_expense) }}</p>
          </div>
          
          <div class="p-4 bg-gray-50 rounded-lg">
            <p class="text-sm text-gray-600 mb-1">Net Balance</p>
            <p :class="['text-2xl font-bold', stats.total_income - stats.total_expense >= 0 ? 'text-green-700' : 'text-red-700']">
              {{ formatCurrency(stats.total_income - stats.total_expense) }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
