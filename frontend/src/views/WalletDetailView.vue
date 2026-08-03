<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFinanceStore } from '../stores/finance'
import api from '../api'
import EditTransactionModal from '../components/EditTransactionModal.vue'

const route = useRoute()
const router = useRouter()
const financeStore = useFinanceStore()
const walletId = route.params.id

const wallet = ref(null)
const isLoadingWallet = ref(true)
const isLoadingTransactions = ref(false)
const isExporting = ref(false)

const showEditModal = ref(false)
const editingTransaction = ref(null)

const searchQuery = ref('')
const selectedCategory = ref('')
const skip = ref(0)
const limit = ref(20)
const hasMore = ref(false)
const transactionsList = ref([])

let debounceTimer = null

const getCurrentMonthRange = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const lastDayNum = new Date(year, now.getMonth() + 1, 0).getDate()
  const lastDay = String(lastDayNum).padStart(2, '0')
  return {
    start: `${year}-${month}-01`,
    end: `${year}-${month}-${lastDay}`
  }
}

const initialRange = getCurrentMonthRange()
const startDate = ref(initialRange.start)
const endDate = ref(initialRange.end)

onMounted(async () => {
  await loadData()
})

const loadData = async () => {
  isLoadingWallet.value = true
  try {
    await financeStore.fetchWallets()
    wallet.value = financeStore.wallets.find(w => w.id === parseInt(walletId))

    await resetAndFetchTransactions()
    await financeStore.fetchCategories()
  } finally {
    isLoadingWallet.value = false
  }
}

const resetAndFetchTransactions = async () => {
  skip.value = 0
  await fetchWalletTransactions(false)
}

const fetchWalletTransactions = async (isAppend = false) => {
  isLoadingTransactions.value = true
  try {
    const params = {
      wallet_id: walletId,
      skip: skip.value,
      limit: limit.value
    }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (selectedCategory.value) params.category_id = selectedCategory.value
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()

    const response = await api.get('/transactions', { params })
    const fetched = response.data || []
    hasMore.value = fetched.length === limit.value

    if (isAppend) {
      transactionsList.value = [...transactionsList.value, ...fetched]
    } else {
      transactionsList.value = fetched
    }
  } finally {
    isLoadingTransactions.value = false
  }
}

const onSearchInput = () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    resetAndFetchTransactions()
  }, 300)
}

const onFilterChange = async () => {
  await resetAndFetchTransactions()
}

const loadMore = async () => {
  skip.value += limit.value
  await fetchWalletTransactions(true)
}

const exportPDF = async () => {
  isExporting.value = true
  try {
    const params = { wallet_id: walletId }
    if (startDate.value) params.start_date = startDate.value
    if (endDate.value) params.end_date = endDate.value
    if (selectedCategory.value) params.category_id = selectedCategory.value
    if (searchQuery.value.trim()) params.search = searchQuery.value.trim()

    const response = await api.get('/transactions/export/pdf', {
      params,
      responseType: 'blob'
    })

    const blob = new Blob([response.data], { type: 'application/pdf' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    const cleanName = wallet.value ? wallet.value.name.toLowerCase().replace(/\s+/g, '_') : 'wallet'
    link.setAttribute('download', `statement_${cleanName}.pdf`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Failed to export PDF:', err)
  } finally {
    isExporting.value = false
  }
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

const handleEdit = (trans) => {
  editingTransaction.value = trans
  showEditModal.value = true
}

const handleEditSuccess = async () => {
  showEditModal.value = false
  editingTransaction.value = null
  await loadData()
}

const handleDelete = async (id) => {
  if (confirm('Are you sure you want to delete this transaction?')) {
    await financeStore.deleteTransaction(id)
    await loadData()
  }
}

const isTransferCategory = (name) => (name || '').toLowerCase() === 'transfer'

const getCategoryBadgeClass = (trans) => {
  const base = 'bg-transparent border rounded-sm px-2 py-1 font-mono text-xs uppercase'
  if (isTransferCategory(trans.category_name)) return `${base} border-slate text-slate`
  return trans.type === 'INCOME' 
    ? `${base} border-deep-green text-deep-green`
    : `${base} border-coral text-coral`
}

const periodIncome = computed(() => {
  return transactionsList.value
    .filter(t => t.type === 'INCOME' && !isTransferCategory(t.category_name))
    .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0)
})

const periodExpense = computed(() => {
  return transactionsList.value
    .filter(t => t.type === 'EXPENSE' && !isTransferCategory(t.category_name))
    .reduce((sum, t) => sum + parseFloat(t.amount || 0), 0)
})

const periodNet = computed(() => {
  return periodIncome.value - periodExpense.value
})

const groupedTransactions = computed(() => {
  const groups = {}
  for (const trans of transactionsList.value) {
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
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 bg-canvas min-h-screen">
    <!-- Back Button -->
    <button 
      class="mb-8 flex items-center text-sm font-medium text-slate hover:text-ink transition-colors" 
      @click="router.push({ name: 'Wallets' })"
    >
      <svg
        class="w-4 h-4 mr-2"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M10 19l-7-7m0 0l7-7m-7 7h18"
        />
      </svg>
      Back to Wallets
    </button>
    
    <phantom-ui
      :loading="isLoadingWallet"
      animation="shimmer"
    >
      <div
        v-if="wallet"
        class="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6"
      >
        <!-- Minimalist Large Display Header -->
        <div>
          <h1 class="font-body text-xl font-medium text-slate mb-2">
            {{ wallet.name }}
          </h1>
          <p class="font-display text-5xl lg:text-7xl tracking-tighter text-ink">
            {{ formatCurrency(wallet.balance) }}
          </p>
        </div>

        <!-- Date Filter Section -->
        <div class="flex flex-wrap items-center gap-3">
          <label
            for="start-date-input"
            class="flex items-center gap-2 cursor-pointer"
          >
            <span class="text-xs font-mono text-slate uppercase">From</span>
            <input 
              id="start-date-input"
              v-model="startDate"
              type="date"
              class="bg-transparent border border-card-border rounded-pill px-4 py-2 font-mono text-sm text-ink focus:outline-none focus:border-ink transition-colors"
              @change="onFilterChange"
            >
          </label>
          <label
            for="end-date-input"
            class="flex items-center gap-2 cursor-pointer"
          >
            <span class="text-xs font-mono text-slate uppercase">To</span>
            <input 
              id="end-date-input"
              v-model="endDate"
              type="date"
              class="bg-transparent border border-card-border rounded-pill px-4 py-2 font-mono text-sm text-ink focus:outline-none focus:border-ink transition-colors"
              @change="onFilterChange"
            >
          </label>
        </div>
      </div>
      <div
        v-else
        class="mb-12"
      >
        <p class="text-error text-lg">
          Wallet not found.
        </p>
      </div>
    </phantom-ui>

    <!-- Insights Row -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
      <!-- Card 1: Period Income -->
      <div class="bg-soft-stone p-6 rounded-lg">
        <p class="text-slate font-mono text-xs uppercase tracking-widest mb-2">
          Income (Period)
        </p>
        <p class="text-deep-green font-display text-2xl lg:text-3xl tracking-tight">
          {{ formatCurrency(periodIncome) }}
        </p>
      </div>

      <!-- Card 2: Period Expense -->
      <div class="bg-soft-stone p-6 rounded-lg">
        <p class="text-slate font-mono text-xs uppercase tracking-widest mb-2">
          Expense (Period)
        </p>
        <p class="text-coral font-display text-2xl lg:text-3xl tracking-tight">
          {{ formatCurrency(periodExpense) }}
        </p>
      </div>

      <!-- Card 3: Net Flow -->
      <div class="bg-soft-stone p-6 rounded-lg">
        <p class="text-slate font-mono text-xs uppercase tracking-widest mb-2">
          Net Flow (Period)
        </p>
        <p class="text-ink font-display text-2xl lg:text-3xl tracking-tight">
          {{ formatCurrency(periodNet) }}
        </p>
      </div>
    </div>

    <!-- Controls Row (Search, Category, Export) -->
    <div class="flex flex-col sm:flex-row gap-4 mb-8 justify-between items-center">
      <div class="flex flex-wrap items-center gap-3 w-full sm:w-auto flex-1">
        <!-- Search Bar -->
        <div class="relative w-full sm:w-64">
          <label
            for="search-input"
            class="block w-full"
          >
            <span class="sr-only">Search transactions</span>
            <input
              id="search-input"
              v-model="searchQuery"
              type="text"
              placeholder="Search transactions..."
              class="w-full border border-card-border rounded-pill px-4 py-2 bg-transparent text-sm text-ink focus:outline-none focus:border-ink transition-colors"
              @input="onSearchInput"
            >
          </label>
        </div>

        <!-- Category Filter Dropdown -->
        <label
          for="category-select"
          class="block"
        >
          <span class="sr-only">Filter by Category</span>
          <select
            id="category-select"
            v-model="selectedCategory"
            class="border border-card-border rounded-pill px-4 py-2 bg-transparent text-sm text-ink focus:outline-none focus:border-ink transition-colors cursor-pointer"
            @change="onFilterChange"
          >
            <option value="">
              All Categories
            </option>
            <option
              v-for="cat in financeStore.categories"
              :key="cat.id"
              :value="cat.id"
            >
              {{ cat.name }}
            </option>
          </select>
        </label>
      </div>

      <!-- Export Button -->
      <button
        :disabled="isExporting"
        class="w-full sm:w-auto border border-card-border rounded-pill px-5 py-2 hover:bg-soft-stone transition-colors font-medium text-sm text-ink flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
        @click="exportPDF"
      >
        <svg
          class="w-4 h-4 text-slate"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        {{ isExporting ? 'Exporting...' : 'Export PDF' }}
      </button>
    </div>

    <!-- Content: Ledger -->
    <div class="max-w-4xl">
      <h2 class="font-display text-3xl tracking-tight text-ink mb-8">
        Transactions
      </h2>

      <phantom-ui
        :loading="isLoadingTransactions"
        animation="shimmer"
      >
        <div v-if="groupedTransactions.length > 0">
          <div
            v-for="group in groupedTransactions"
            :key="group.date"
            class="mb-10"
          >
            <!-- Date Header -->
            <div class="py-3 flex justify-between items-center border-b border-hairline">
              <span class="font-body font-semibold text-ink">{{ formatDateHeader(group.date) }}</span>
              <span 
                class="font-body font-semibold"
                :class="group.dailyTotal >= 0 ? 'text-ink' : 'text-slate'"
              >
                {{ group.dailyTotal >= 0 ? '+' : '' }}{{ formatCurrency(group.dailyTotal) }}
              </span>
            </div>

            <!-- Ledger Rows -->
            <div>
              <div 
                v-for="trans in group.transactions" 
                :key="trans.id"
                class="flex flex-col sm:grid sm:grid-cols-12 gap-2 sm:gap-4 py-4 border-b border-hairline last:border-b-0 hover:bg-soft-stone transition-colors"
              >
                <!-- Left Side -->
                <div class="flex items-center gap-3 w-full sm:col-span-8">
                  <div class="flex-shrink-0">
                    <span 
                      class="inline-flex items-center gap-1"
                      :class="getCategoryBadgeClass(trans)"
                    >
                      <template v-if="isTransferCategory(trans.category_name)">
                        <svg
                          class="w-3.5 h-3.5"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path d="M3 7h9.586l-2.293-2.293a1 1 0 0 1 1.414-1.414l4 4a1 1 0 0 1 0 1.414l-4 4a1 1 0 0 1-1.414-1.414L12.586 9H3a1 1 0 1 1 0-2zm14 6h-9.586l2.293 2.293a1 1 0 1 1-1.414 1.414l-4-4a1 1 0 0 1 0-1.414l4-4a1 1 0 0 1 1.414 1.414L5.414 11H17a1 1 0 1 1 0 2z" />
                        </svg>
                        Transfer
                      </template>
                      <template v-else>
                        {{ trans.category_name }}
                      </template>
                    </span>
                  </div>
                  <div class="min-w-0 flex-1">
                    <span
                      class="text-base text-ink font-medium truncate block"
                      :title="trans.description"
                    >
                      {{ trans.description || '-' }}
                    </span>
                  </div>
                </div>

                <!-- Right Side -->
                <div class="flex items-center justify-between w-full sm:col-span-4 sm:justify-end sm:gap-4 mt-1 sm:mt-0">
                  <span 
                    class="font-body text-base whitespace-nowrap"
                    :class="isTransferCategory(trans.category_name) ? 'text-slate font-medium' : (trans.type === 'INCOME' ? 'text-deep-green font-medium' : 'text-coral font-medium')"
                  >
                    {{ trans.type === 'INCOME' ? '+' : '-' }}{{ formatCurrency(trans.amount) }}
                  </span>
                  <div class="flex items-center gap-1 flex-shrink-0">
                    <button
                      class="p-1.5 text-slate hover:text-ink rounded"
                      title="Edit"
                      @click="handleEdit(trans)"
                    >
                      <svg
                        class="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                      /></svg>
                    </button>
                    <button
                      class="p-1.5 text-slate hover:text-ink rounded"
                      title="Delete"
                      @click="handleDelete(trans.id)"
                    >
                      <svg
                        class="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      ><path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      /></svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Load More Button -->
          <div
            v-if="hasMore"
            class="mt-8 flex justify-center"
          >
            <button
              :disabled="isLoadingTransactions"
              class="border border-card-border rounded-pill px-6 py-2 hover:bg-soft-stone transition-colors font-medium text-sm text-ink disabled:opacity-50 cursor-pointer"
              @click="loadMore"
            >
              {{ isLoadingTransactions ? 'Loading...' : 'Load More' }}
            </button>
          </div>
        </div>
        <p
          v-else
          class="text-slate py-8 font-body"
        >
          No transactions found for this period.
        </p>
      </phantom-ui>
    </div>
  </div>

  <EditTransactionModal
    :show="showEditModal"
    :transaction="editingTransaction"
    :wallets="financeStore.wallets"
    :categories="financeStore.categories"
    @close="showEditModal = false"
    @success="handleEditSuccess"
  />
</template>
