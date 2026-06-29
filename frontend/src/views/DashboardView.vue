<script setup>
import { ref, onMounted, computed } from 'vue'
import { useFinanceStore } from '../stores/finance'
import EditTransactionModal from '../components/EditTransactionModal.vue'
import WalletCard from '../components/WalletCard.vue'

const financeStore = useFinanceStore()

const showEditModal = ref(false)
const editingTransaction = ref(null)

const getLocalToday = () => {
 const now = new Date()
 const year = now.getFullYear()
 const month = String(now.getMonth() + 1).padStart(2, '0')
 const day = String(now.getDate()).padStart(2, '0')
 return `${year}-${month}-${day}`
}

const filterDate = ref(getLocalToday())

const getPastDate = (daysAgo) => {
 const date = new Date()
 date.setDate(date.getDate() - daysAgo)
 const year = date.getFullYear()
 const month = String(date.getMonth() + 1).padStart(2, '0')
 const day = String(date.getDate()).padStart(2, '0')
 return `${year}-${month}-${day}`
}

const isDefaultView = ref(true)

const isToday = computed(() => filterDate.value === getLocalToday())

onMounted(async () => {
 const today = getLocalToday()
 const fiveDaysAgo = getPastDate(4) // Today + 4 days back = 5 days total

 await Promise.all([
 financeStore.fetchWallets(),
 financeStore.fetchTransactions({
 start_date: fiveDaysAgo,
 end_date: today,
 limit: 100
 }),
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
 
 // Refresh transactions based on current view
 if (isDefaultView.value) {
 await resetView()
 } else {
 await handleDateFilter()
 }
 
 // Refresh summary and wallets as they might have changed
 await Promise.all([
 financeStore.fetchSummary(),
 financeStore.fetchWallets()
 ])
}

const formatCurrency = (value) => {
 return new Intl.NumberFormat('id-ID', {
 style: 'currency',
 currency: 'IDR',
 minimumFractionDigits: 0
 }).format(value)
}

const formatDateHeader = (dateStr) => {
 return new Intl.DateTimeFormat('en-US', {
 weekday: 'long',
 day: 'numeric',
 month: 'short',
 year: 'numeric'
 }).format(new Date(dateStr + 'T00:00:00'))
}

const handleDelete = async (id) => {
 if (confirm('Are you sure you want to delete this transaction?')) {
 await financeStore.deleteTransaction(id)
 }
}

const handleDateFilter = async () => {
 if (filterDate.value) {
 isDefaultView.value = false
 await financeStore.fetchTransactions({
 start_date: filterDate.value,
 end_date: filterDate.value,
 limit: 100
 })
 } else {
 await resetView()
 }
}

const resetView = async () => {
 const today = getLocalToday()
 const fiveDaysAgo = getPastDate(4)
 filterDate.value = today
 isDefaultView.value = true
 await financeStore.fetchTransactions({
 start_date: fiveDaysAgo,
 end_date: today,
 limit: 100
 })
}

const isTransferCategory = (name) => (name || '').toLowerCase() === 'transfer'

const getCategoryBadgeClass = (trans) => {
  const base = 'bg-transparent border rounded-sm px-2 py-1 font-mono text-xs uppercase'
  if (isTransferCategory(trans.category_name)) return `${base} border-slate text-slate`
  return trans.type === 'INCOME' 
    ? `${base} border-deep-green text-deep-green`
    : `${base} border-coral text-coral`
}

const groupedTransactions = computed(() => {
 const groups = {}
 for (const trans of financeStore.transactions) {
 const dateKey = trans.transaction_date
 if (!groups[dateKey]) {
 groups[dateKey] = { transactions: [], dailyTotal: 0 }
 }
 groups[dateKey].transactions.push(trans)
 groups[dateKey].dailyTotal += trans.type === 'INCOME'
 ? parseFloat(trans.amount)
 : -parseFloat(trans.amount)
 }
 return Object.entries(groups)
 .sort(([a], [b]) => b.localeCompare(a))
 .map(([date, data]) => ({ date, ...data }))
})
</script>

<template>
 <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
 <h1 class="text-2xl font-bold text-gray-800 mb-8">Dashboard</h1>
 
    <!-- Summary Cards -->
    <div class="bg-deep-green rounded-lg p-8 mb-8 flex flex-col lg:flex-row justify-between items-start gap-8">
      <div>
        <p class="text-pale-green opacity-80 font-mono text-xs uppercase tracking-widest mb-2">Total Balance</p>
        <p class="font-display text-5xl lg:text-7xl tracking-tighter text-on-dark whitespace-nowrap">{{ formatCurrency(financeStore.summary.total_balance || 0) }}</p>
      </div>
      <div class="flex flex-col md:flex-row gap-8 lg:gap-12 text-left lg:text-right w-full lg:w-auto">
        <div>
          <p class="text-pale-green opacity-80 font-mono text-xs uppercase tracking-widest mb-2">Total Income</p>
          <p class="font-display text-3xl tracking-tight text-on-dark">{{ formatCurrency(financeStore.summary.total_income || 0) }}</p>
        </div>
        <div>
          <p class="text-pale-green opacity-80 font-mono text-xs uppercase tracking-widest mb-2">Total Expense</p>
          <p class="font-display text-3xl tracking-tight text-on-dark">{{ formatCurrency(financeStore.summary.total_expense || 0) }}</p>
        </div>
        <div>
          <p class="text-pale-green opacity-80 font-mono text-xs uppercase tracking-widest mb-2">Net</p>
          <p class="font-display text-3xl tracking-tight text-on-dark">{{ formatCurrency(financeStore.summary.net || 0) }}</p>
        </div>
      </div>
    </div>

 <!-- Wallets -->
 <div class="mb-8">
 <h2 class="text-lg font-semibold text-gray-800 mb-4 px-1">Wallets</h2>
 <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
 <WalletCard
 v-for="wallet in financeStore.wallets"
 :key="wallet.id"
 :wallet="wallet"
 :isLoading="financeStore.isLoadingWallets"
 />
 </div>
 <p v-if="financeStore.wallets.length === 0" class="text-gray-500 text-center py-4">
 No wallets found
 </p>
 </div>

 <!-- Transactions -->
 <div class="bg-canvas border border-card-border rounded-lg">
 <div class="px-6 py-4 border-b flex flex-wrap justify-between items-center gap-4">
 <h2 class="text-lg font-semibold text-gray-800">
 {{ isDefaultView ? 'Recent Transactions (Last 5 Days)' : `Transactions for ${formatDateHeader(filterDate)}` }}
 </h2>
 <div class="flex items-center gap-3">
 <input 
 type="date" 
 v-model="filterDate"
 @change="handleDateFilter"
 class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
 />
 <button 
 v-if="!isDefaultView"
 @click="resetView"
 class="text-sm text-gray-500 hover:text-gray-700"
 >
 Show Recent
 </button>
 <router-link 
 to="/transactions/add" 
 class="px-4 py-2 bg-primary text-on-primary rounded-pill px-6 py-3 font-medium text-sm"
 >
 Add Transaction
 </router-link>
 </div>
 </div>

 <div class="p-4">
 <phantom-ui :loading="financeStore.isLoadingTransactions" animation="shimmer">
 <!-- Grouped Transactions -->
 <div v-if="groupedTransactions.length > 0" class="space-y-4">
 <div v-for="group in groupedTransactions" :key="group.date">
 <!-- Date Header -->
 <div class="bg-gray-100 px-4 py-3 rounded-t-lg flex justify-between items-center">
 <span class="font-semibold text-gray-800">{{ formatDateHeader(group.date) }}</span>
 <span 
 class="font-semibold"
 :class="group.dailyTotal >= 0 ? 'text-ink' : 'text-slate'"
 >
 {{ group.dailyTotal >= 0 ? '+' : '' }}{{ formatCurrency(group.dailyTotal) }}
 </span>
 </div>

 <!-- Transaction Items -->
 <div class="border border-t-0 border-gray-200 rounded-b-lg">
 <div 
 v-for="trans in group.transactions" 
 :key="trans.id"
 class="flex flex-col sm:grid sm:grid-cols-12 gap-2 sm:gap-4 p-4 border-b border-gray-100 last:border-b-0 hover:bg-gray-50 transition-colors"
 >
 <!-- Top Row (Mobile) / Left Side (Desktop): Category & Description -->
 <div class="flex items-center gap-3 w-full sm:col-span-7">
 <!-- Category Badge -->
 <div class="flex-shrink-0">
 <span 
 class="inline-flex items-center gap-1"
 :class="getCategoryBadgeClass(trans)"
 >
 <template v-if="isTransferCategory(trans.category_name)">
 <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
 <path d="M3 7h9.586l-2.293-2.293a1 1 0 0 1 1.414-1.414l4 4a1 1 0 0 1 0 1.414l-4 4a1 1 0 0 1-1.414-1.414L12.586 9H3a1 1 0 1 1 0-2zm14 6h-9.586l2.293 2.293a1 1 0 1 1-1.414 1.414l-4-4a1 1 0 0 1 0-1.414l4-4a1 1 0 0 1 1.414 1.414L5.414 11H17a1 1 0 1 1 0 2z" />
 </svg>
 Transfer
 </template>
 <template v-else>
 {{ trans.category_name }}
 </template>
 </span>
 </div>

 <!-- Description -->
 <div class="min-w-0 flex-1">
 <span class="text-sm text-gray-800 font-medium truncate block" :title="trans.description">
 {{ trans.description || '-' }}
 </span>
 </div>
 </div>

 <!-- Bottom Row (Mobile) / Right Side (Desktop): Wallet, Amount, Actions -->
 <div class="flex items-center justify-between w-full sm:col-span-5 sm:justify-end sm:gap-4 mt-1 sm:mt-0">
 <!-- Wallet Name -->
 <div class="text-sm text-gray-500 truncate max-w-[120px] sm:max-w-none">
 {{ trans.wallet_name }}
 </div>

 <div class="flex items-center gap-3">
 <!-- Amount -->
  <span 
  class="font-medium text-sm whitespace-nowrap"
  :class="isTransferCategory(trans.category_name) ? 'text-slate' : (trans.type === 'INCOME' ? 'text-deep-green' : 'text-coral')"
  >
 {{ trans.type === 'INCOME' ? '+' : '-' }}{{ formatCurrency(trans.amount) }}
 </span>

 <!-- Actions -->
 <div class="flex items-center gap-1 flex-shrink-0">
 <button 
 @click="handleEdit(trans)"
 class="p-1.5 text-slate hover:text-ink rounded"
 title="Edit"
 >
 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
 </svg>
 </button>
 <button 
 @click="handleDelete(trans.id)"
 class="p-1.5 text-slate hover:text-ink rounded"
 title="Delete"
 >
 <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
 </svg>
 </button>
 </div>
 </div>
 </div>
 </div>
 </div>
 </div>
 </div>

 <!-- Empty State -->
 <p v-else class="text-gray-500 text-center py-8">
 {{ isDefaultView ? 'No recent transactions. Start by adding one!' : 'No transactions for this date.' }}
 </p>
 </phantom-ui>
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
