<script setup>
import { ref, onMounted, computed } from 'vue'
import { useFinanceStore } from '../stores/finance'
import SummaryCard from '../components/SummaryCard.vue'
import EditTransactionModal from '../components/EditTransactionModal.vue'

const financeStore = useFinanceStore()

const showEditModal = ref(false)
const editingTransaction = ref(null)

onMounted(async () => {
  await Promise.all([
    financeStore.fetchWallets(),
    financeStore.fetchTransactions(),
    financeStore.fetchSummary(),
    financeStore.fetchCategories()
  ])
})

const handleEdit = (trans) => {
  editingTransaction.value = trans
  showEditModal.value = true
}

const handleEditSuccess = async () => {
  showEditModal.value = false
  editingTransaction.value = null
}

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

const isTransferCategory = (name) => (name || '').toLowerCase() === 'transfer'

const getCategoryBadgeClass = (trans) => {
  if (isTransferCategory(trans.category_name)) {
    return 'bg-blue-100 text-blue-800'
  }
  return trans.type === 'INCOME'
    ? 'bg-green-100 text-green-800'
    : 'bg-red-100 text-red-800'
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-8">Dashboard</h1>
    
    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
      <SummaryCard
        title="Total Balance"
        :amount="financeStore.summary.total_balance || 0"
      />
      <SummaryCard
        title="Total Income"
        :amount="financeStore.summary.total_income || 0"
        variant="income"
      />
      <SummaryCard
        title="Total Expense"
        :amount="financeStore.summary.total_expense || 0"
        variant="expense"
      />
      <SummaryCard
        title="Net"
        :amount="financeStore.summary.net || 0"
        :variant="financeStore.summary.net >= 0 ? 'income' : 'expense'"
      />
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
                  class="px-2 py-1 text-xs font-medium rounded-full inline-flex items-center gap-1"
                  :class="getCategoryBadgeClass(trans)"
                >
                  <template v-if="isTransferCategory(trans.category_name)">
                    <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                      <path d="M3 7h9.586l-2.293-2.293a1 1 0 0 1 1.414-1.414l4 4a1 1 0 0 1 0 1.414l-4 4a1 1 0 0 1-1.414-1.414L12.586 9H3a1 1 0 1 1 0-2zm14 6h-9.586l2.293 2.293a1 1 0 1 1-1.414 1.414l-4-4a1 1 0 0 1 0-1.414l4-4a1 1 0 0 1 1.414 1.414L5.414 11H17a1 1 0 1 1 0 2z" />
                    </svg>
                    Transfer
                  </template>
                  <template v-else>
                    {{ trans.category_name }}
                  </template>
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
                  @click="handleEdit(trans)"
                  class="text-indigo-600 hover:text-indigo-800 text-sm mr-3"
                  title="Edit transaction"
                >
                  <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                  </svg>
                </button>
                <button 
                  @click="handleDelete(trans.id)"
                  class="text-red-600 hover:text-red-800 text-sm"
                  title="Delete transaction"
                >
                  <svg class="w-4 h-4 inline" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
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

    <!-- Edit Transaction Modal -->
    <EditTransactionModal
      :show="showEditModal"
      :transaction="editingTransaction"
      :wallets="financeStore.wallets"
      :categories="financeStore.categories"
      @close="showEditModal = false"
      @success="handleEditSuccess"
    />
  </div>
</template>
