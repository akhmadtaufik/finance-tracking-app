import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useFinanceStore = defineStore('finance', () => {
  const wallets = ref([])
  const categories = ref([])
  const transactions = ref([])
  const summary = ref({
    total_income: 0,
    total_expense: 0,
    total_balance: 0,
    net: 0
  })
  const loading = ref(false)

  async function fetchWallets() {
    const response = await api.get('/wallets')
    wallets.value = response.data
    return response.data
  }

  async function fetchCategories(type = null) {
    const params = type ? { type } : {}
    const response = await api.get('/categories', { params })
    categories.value = response.data
    return response.data
  }

  async function fetchTransactions(params = {}) {
    loading.value = true
    try {
      const response = await api.get('/transactions', { params })
      transactions.value = response.data
      return response.data
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary() {
    const response = await api.get('/transactions/summary')
    summary.value = response.data
    return response.data
  }

  async function createTransaction(data) {
    const response = await api.post('/transactions', data)
    await fetchTransactions()
    await fetchSummary()
    await fetchWallets()
    return response.data
  }

  async function createCategory(data) {
    const response = await api.post('/categories', data)
    await fetchCategories()
    return response.data
  }

  async function deleteTransaction(id) {
    await api.delete(`/transactions/${id}`)
    await fetchTransactions()
    await fetchSummary()
    await fetchWallets()
  }

  return {
    wallets,
    categories,
    transactions,
    summary,
    loading,
    fetchWallets,
    fetchCategories,
    fetchTransactions,
    fetchSummary,
    createTransaction,
    createCategory,
    deleteTransaction
  }
})
