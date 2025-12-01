<script setup>
import { onMounted, computed } from 'vue'
import { useFinanceStore } from '../stores/finance'

const financeStore = useFinanceStore()

onMounted(async () => {
  await Promise.all([
    financeStore.fetchWallets(),
    financeStore.fetchTransactions(),
    financeStore.fetchSummary()
  ])
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString('id-ID', {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

const handleDelete = async (id) => {
  if (confirm('Are you sure you want to delete this transaction?')) {
    await financeStore.deleteTransaction(id)
  }
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-8">Dashboard</h1>
    
    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-sm font-medium text-gray-500">Total Balance</p>
        <p class="text-2xl font-bold text-gray-800">
          {{ formatCurrency(financeStore.summary.total_balance) }}
        </p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-sm font-medium text-gray-500">Total Income</p>
        <p class="text-2xl font-bold text-green-600">
          {{ formatCurrency(financeStore.summary.total_income) }}
        </p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-sm font-medium text-gray-500">Total Expense</p>
        <p class="text-2xl font-bold text-red-600">
          {{ formatCurrency(financeStore.summary.total_expense) }}
        </p>
      </div>
      <div class="bg-white rounded-lg shadow p-6">
        <p class="text-sm font-medium text-gray-500">Net</p>
        <p class="text-2xl font-bold" :class="financeStore.summary.net >= 0 ? 'text-green-600' : 'text-red-600'">
          {{ formatCurrency(financeStore.summary.net) }}
        </p>
      </div>
    </div>

    <!-- Wallets -->
    <div class="bg-white rounded-lg shadow mb-8">
      <div class="px-6 py-4 border-b">
        <h2 class="text-lg font-semibold text-gray-800">Wallets</h2>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div 
            v-for="wallet in financeStore.wallets" 
            :key="wallet.id"
            class="border rounded-lg p-4"
          >
            <p class="text-sm text-gray-500">{{ wallet.name }}</p>
            <p class="text-xl font-bold text-gray-800">{{ formatCurrency(wallet.balance) }}</p>
          </div>
        </div>
        <p v-if="financeStore.wallets.length === 0" class="text-gray-500 text-center py-4">
          No wallets found
        </p>
      </div>
    </div>

    <!-- Recent Transactions -->
    <div class="bg-white rounded-lg shadow">
      <div class="px-6 py-4 border-b flex justify-between items-center">
        <h2 class="text-lg font-semibold text-gray-800">Recent Transactions</h2>
        <router-link 
          to="/transactions/add" 
          class="px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-md hover:bg-indigo-700"
        >
          Add Transaction
        </router-link>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Category</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Wallet</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Description</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Amount</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Action</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="trans in financeStore.transactions" :key="trans.id">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ formatDate(trans.transaction_date) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap">
                <span 
                  class="px-2 py-1 text-xs font-medium rounded-full"
                  :class="trans.type === 'INCOME' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                >
                  {{ trans.category_name }}
                </span>
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                {{ trans.wallet_name }}
              </td>
              <td class="px-6 py-4 text-sm text-gray-500">
                {{ trans.description || '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-right font-medium"
                  :class="trans.type === 'INCOME' ? 'text-green-600' : 'text-red-600'">
                {{ trans.type === 'INCOME' ? '+' : '-' }}{{ formatCurrency(trans.amount) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-right">
                <button 
                  @click="handleDelete(trans.id)"
                  class="text-red-600 hover:text-red-800 text-sm"
                >
                  Delete
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <p v-if="financeStore.transactions.length === 0" class="text-gray-500 text-center py-8">
          No transactions yet. Start by adding one!
        </p>
      </div>
    </div>
  </div>
</template>
