<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { 
  startOfWeek, endOfWeek, 
  startOfMonth, endOfMonth, 
  startOfYear, endOfYear,
  addWeeks, subWeeks,
  addMonths, subMonths,
  addYears, subYears,
  format
} from 'date-fns'
import { id as idLocale } from 'date-fns/locale'
import api from '../api'

const period = ref('month')
const selectedDate = ref(new Date())
const transactions = ref([])
const summary = ref({ total_transactions: 0, total_income: 0, total_expense: 0 })
const loading = ref(false)
const exporting = ref(false)

const dateRange = computed(() => {
  const date = selectedDate.value
  let start, end
  
  switch (period.value) {
    case 'week':
      start = startOfWeek(date, { weekStartsOn: 1 })
      end = endOfWeek(date, { weekStartsOn: 1 })
      break
    case 'month':
      start = startOfMonth(date)
      end = endOfMonth(date)
      break
    case 'year':
      start = startOfYear(date)
      end = endOfYear(date)
      break
    default:
      start = startOfMonth(date)
      end = endOfMonth(date)
  }
  
  return {
    start: format(start, 'yyyy-MM-dd'),
    end: format(end, 'yyyy-MM-dd')
  }
})

const periodLabel = computed(() => {
  const date = selectedDate.value
  switch (period.value) {
    case 'week':
      const weekStart = startOfWeek(date, { weekStartsOn: 1 })
      const weekEnd = endOfWeek(date, { weekStartsOn: 1 })
      return `${format(weekStart, 'd MMM', { locale: idLocale })} - ${format(weekEnd, 'd MMM yyyy', { locale: idLocale })}`
    case 'month':
      return format(date, 'MMMM yyyy', { locale: idLocale })
    case 'year':
      return format(date, 'yyyy')
    default:
      return ''
  }
})

const navigate = (direction) => {
  const date = selectedDate.value
  switch (period.value) {
    case 'week':
      selectedDate.value = direction === 'prev' ? subWeeks(date, 1) : addWeeks(date, 1)
      break
    case 'month':
      selectedDate.value = direction === 'prev' ? subMonths(date, 1) : addMonths(date, 1)
      break
    case 'year':
      selectedDate.value = direction === 'prev' ? subYears(date, 1) : addYears(date, 1)
      break
  }
}

const goToToday = () => {
  selectedDate.value = new Date()
}

const fetchData = async () => {
  loading.value = true
  try {
    const { start, end } = dateRange.value
    const response = await api.get('/reports/list', {
      params: { start_date: start, end_date: end }
    })
    transactions.value = response.data.transactions
    summary.value = response.data.summary
  } catch (error) {
    console.error('Failed to fetch report:', error)
  } finally {
    loading.value = false
  }
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return format(date, 'dd/MM/yyyy')
}

const exportCSV = async () => {
  exporting.value = true
  try {
    const { start, end } = dateRange.value
    const response = await api.get('/reports/export/csv', {
      params: { start_date: start, end_date: end },
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `transactions_${start}_${end}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export CSV:', error)
  } finally {
    exporting.value = false
  }
}

const exportExcel = async () => {
  exporting.value = true
  try {
    const { start, end } = dateRange.value
    const response = await api.get('/reports/export/excel', {
      params: { start_date: start, end_date: end },
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `transactions_${start}_${end}.xlsx`)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to export Excel:', error)
  } finally {
    exporting.value = false
  }
}

watch([period, selectedDate], () => {
  fetchData()
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Transaction Report</h1>

    <!-- Controls -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <!-- Period Toggle -->
        <div class="flex rounded-lg overflow-hidden border border-gray-200">
          <button
            v-for="p in ['week', 'month', 'year']"
            :key="p"
            @click="period = p"
            :class="[
              'px-4 py-2 text-sm font-medium capitalize transition-colors',
              period === p 
                ? 'bg-indigo-600 text-white' 
                : 'bg-white text-gray-600 hover:bg-gray-50'
            ]"
          >
            {{ p }}
          </button>
        </div>

        <!-- Navigation -->
        <div class="flex items-center gap-2">
          <button
            @click="navigate('prev')"
            class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          
          <button
            @click="goToToday"
            class="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 min-w-[180px]"
          >
            {{ periodLabel }}
          </button>
          
          <button
            @click="navigate('next')"
            class="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <!-- Export Buttons -->
        <div class="flex gap-2">
          <button
            @click="exportCSV"
            :disabled="exporting || transactions.length === 0"
            class="px-4 py-2 text-sm font-medium bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </button>
          <button
            @click="exportExcel"
            :disabled="exporting || transactions.length === 0"
            class="px-4 py-2 text-sm font-medium bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export Excel
          </button>
        </div>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div class="bg-white rounded-lg shadow p-4">
        <p class="text-sm text-gray-500">Total Income</p>
        <p class="text-xl font-bold text-green-600">{{ formatCurrency(summary.total_income) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4">
        <p class="text-sm text-gray-500">Total Expense</p>
        <p class="text-xl font-bold text-red-600">{{ formatCurrency(summary.total_expense) }}</p>
      </div>
      <div class="bg-white rounded-lg shadow p-4">
        <p class="text-sm text-gray-500">Net</p>
        <p :class="['text-xl font-bold', (summary.total_income - summary.total_expense) >= 0 ? 'text-green-600' : 'text-red-600']">
          {{ formatCurrency(summary.total_income - summary.total_expense) }}
        </p>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-lg shadow overflow-hidden">
      <div class="px-6 py-4 border-b border-gray-200">
        <h2 class="text-lg font-semibold text-gray-800">
          Transactions ({{ summary.total_transactions }})
        </h2>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>

      <div v-else-if="transactions.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-500">
        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p>No transactions for this period</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Wallet</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Description</th>
              <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="(tx, index) in transactions" :key="index" class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {{ formatDate(tx.transaction_date) }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-800 font-medium">
                {{ tx.category_name }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                {{ tx.wallet_name }}
              </td>
              <td class="px-6 py-4 text-sm text-gray-600 max-w-xs truncate">
                {{ tx.description || '-' }}
              </td>
              <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-right"
                  :class="tx.type === 'INCOME' ? 'text-green-600' : 'text-red-600'">
                {{ tx.type === 'INCOME' ? '+' : '-' }}{{ formatCurrency(tx.amount) }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
