<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { 
  startOfWeek, endOfWeek, 
  startOfMonth, endOfMonth, 
  startOfYear, endOfYear,
  addDays, subDays,
  addWeeks, subWeeks,
  addMonths, subMonths,
  addYears, subYears,
  format,
  getMonth, getYear
} from 'date-fns'
import { id } from 'date-fns/locale'
import api from '../api'
import HorizontalBarChart from '../components/charts/HorizontalBarChart.vue'
import CashFlowLineChart from '../components/charts/CashFlowLineChart.vue'
import ComparativeChart from '../components/charts/ComparativeChart.vue'

const period = ref('month')
const selectedDate = ref(new Date())
const breakdown = ref([])
const trendData = ref([])
const comparisonData = ref([])
const summary = ref({ total_income: 0, total_expense: 0, net: 0, transaction_count: 0 })
const loading = ref(false)
const transactionType = ref('EXPENSE')
const groupBy = ref('category')

const dateRange = computed(() => {
  const date = selectedDate.value
  let start, end
  
  switch (period.value) {
    case 'daily':
      start = date
      end = date
      break
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
    end: format(end, 'yyyy-MM-dd'),
    startDate: start,
    endDate: end
  }
})

const periodLabel = computed(() => {
  const date = selectedDate.value
  switch (period.value) {
    case 'daily':
      return format(date, 'd MMMM yyyy', { locale: id })
    case 'week':
      const weekStart = startOfWeek(date, { weekStartsOn: 1 })
      const weekEnd = endOfWeek(date, { weekStartsOn: 1 })
      return `${format(weekStart, 'd MMM', { locale: id })} - ${format(weekEnd, 'd MMM yyyy', { locale: id })}`
    case 'month':
      return format(date, 'MMMM yyyy', { locale: id })
    case 'year':
      return format(date, 'yyyy')
    default:
      return ''
  }
})

const chartLabels = computed(() => breakdown.value.map(item => item.name))
const chartData = computed(() => {
  const total = totalAmount.value
  if (total === 0) return breakdown.value.map(() => 0)
  return breakdown.value.map(item => parseFloat(((item.total / total) * 100).toFixed(1)))
})

const totalAmount = computed(() => {
  return breakdown.value.reduce((sum, item) => sum + item.total, 0)
})

const navigate = (direction) => {
  const date = selectedDate.value
  switch (period.value) {
    case 'daily':
      selectedDate.value = direction === 'prev' ? subDays(date, 1) : addDays(date, 1)
      break
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
    
    const breakdownEndpoint = groupBy.value === 'category'
      ? '/analytics/category-breakdown'
      : '/analytics/wallet-breakdown'
    
    const [breakdownRes, summaryRes, trendRes] = await Promise.all([
      api.get(breakdownEndpoint, {
        params: { start_date: start, end_date: end, type: transactionType.value }
      }),
      api.get('/analytics/period-summary', {
        params: { start_date: start, end_date: end }
      }),
      api.get('/analytics/trend', {
        params: { start_date: start, end_date: end }
      })
    ])
    
    breakdown.value = breakdownRes.data
    summary.value = summaryRes.data
    trendData.value = trendRes.data
    
    // Fetch comparison data only for monthly view
    if (period.value === 'month') {
      const compRes = await api.get('/analytics/comparison', {
        params: {
          month: getMonth(selectedDate.value) + 1,
          year: getYear(selectedDate.value)
        }
      })
      comparisonData.value = compRes.data
    } else {
      comparisonData.value = []
    }
  } catch (error) {
    console.error('Failed to fetch analytics:', error)
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

watch([period, selectedDate, transactionType, groupBy], () => {
  fetchData()
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="max-w-6xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-6">Analysis</h1>

    <!-- Controls -->
    <div class="bg-white rounded-lg shadow p-4 mb-6">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <!-- Period Toggle -->
        <div class="flex rounded-lg overflow-hidden border border-gray-200">
          <button
            v-for="p in ['daily', 'week', 'month', 'year']"
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

        <!-- Type Toggle -->
        <div class="flex rounded-lg overflow-hidden border border-gray-200">
          <button
            @click="transactionType = 'EXPENSE'"
            :class="[
              'px-4 py-2 text-sm font-medium transition-colors',
              transactionType === 'EXPENSE' 
                ? 'bg-red-600 text-white' 
                : 'bg-white text-gray-600 hover:bg-gray-50'
            ]"
          >
            Expense
          </button>
          <button
            @click="transactionType = 'INCOME'"
            :class="[
              'px-4 py-2 text-sm font-medium transition-colors',
              transactionType === 'INCOME' 
                ? 'bg-green-600 text-white' 
                : 'bg-white text-gray-600 hover:bg-gray-50'
            ]"
          >
            Income
          </button>
        </div>
      </div>
    </div>

    <!-- Group By Toggle -->
    <div class="flex items-center gap-3 mb-6">
      <span class="text-sm font-medium text-gray-600">Group by:</span>
      <div class="flex rounded-lg overflow-hidden border border-gray-200">
        <button
          @click="groupBy = 'category'"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors',
            groupBy === 'category' 
              ? 'bg-indigo-600 text-white' 
              : 'bg-white text-gray-600 hover:bg-gray-50'
          ]"
        >
          Category
        </button>
        <button
          @click="groupBy = 'wallet'"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors',
            groupBy === 'wallet' 
              ? 'bg-indigo-600 text-white' 
              : 'bg-white text-gray-600 hover:bg-gray-50'
          ]"
        >
          Wallet
        </button>
      </div>
    </div>

    <!-- Summary Cards -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
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
        <p :class="['text-xl font-bold', summary.net >= 0 ? 'text-green-600' : 'text-red-600']">
          {{ formatCurrency(summary.net) }}
        </p>
      </div>
      <div class="bg-white rounded-lg shadow p-4">
        <p class="text-sm text-gray-500">Transactions</p>
        <p class="text-xl font-bold text-gray-800">{{ summary.transaction_count }}</p>
      </div>
    </div>

    <!-- Chart -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-gray-800">
          {{ transactionType === 'EXPENSE' ? 'Expense' : 'Income' }} by {{ groupBy === 'category' ? 'Category' : 'Wallet' }}
        </h2>
        <p class="text-sm text-gray-500">
          Total: <span class="font-semibold">{{ formatCurrency(totalAmount) }}</span>
        </p>
      </div>

      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>

      <div v-else-if="breakdown.length === 0" class="flex flex-col items-center justify-center h-64 text-gray-500">
        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p>No {{ transactionType.toLowerCase() }} data for this period</p>
      </div>

      <HorizontalBarChart
        v-else
        :labels="chartLabels"
        :data="chartData"
      />

      <!-- Category List -->
      <div v-if="breakdown.length > 0" class="mt-6 border-t pt-4 w-full overflow-hidden">
        <div class="space-y-2">
          <div
            v-for="(item, index) in breakdown"
            :key="item.name"
            class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50 gap-2"
          >
            <!-- Left Side: Index & Name -->
            <div class="flex items-center gap-2 sm:gap-3 min-w-0 flex-1">
              <span class="w-6 text-center text-sm text-gray-400 flex-shrink-0">{{ index + 1 }}</span>
              <span class="font-medium text-gray-800 truncate" :title="item.name">{{ item.name }}</span>
            </div>

            <!-- Right Side: Stats -->
            <div class="flex items-center gap-2 sm:gap-4 flex-shrink-0">
              <span class="text-sm text-gray-500 w-10 sm:w-12 text-right text-xs sm:text-sm">
                {{ totalAmount > 0 ? ((item.total / totalAmount) * 100).toFixed(1) : 0 }}%
              </span>
              <div class="w-12 sm:w-24 bg-gray-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full"
                  :class="transactionType === 'EXPENSE' ? 'bg-red-500' : 'bg-green-500'"
                  :style="{ width: (totalAmount > 0 ? (item.total / totalAmount) * 100 : 0) + '%' }"
                ></div>
              </div>
              <span class="font-semibold text-gray-800 w-24 sm:w-32 text-right whitespace-nowrap text-sm sm:text-base">
                {{ formatCurrency(item.total) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Cash Flow Trend Chart -->
    <div class="bg-white rounded-lg shadow p-6 mt-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">Cash Flow Trend</h2>
      <p class="text-sm text-gray-500 mb-4">Income vs Expense over time</p>
      
      <div v-if="loading" class="flex items-center justify-center h-72">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
      
      <div v-else-if="trendData.length === 0" class="flex flex-col items-center justify-center h-72 text-gray-500">
        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
        <p>No transaction data for this period</p>
      </div>
      
      <CashFlowLineChart
        v-else
        :data="trendData"
        :start-date="dateRange.start"
        :end-date="dateRange.end"
      />
    </div>

    <!-- Monthly Comparison Chart (only for month view) -->
    <div v-if="period === 'month'" class="bg-white rounded-lg shadow p-6 mt-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-2">Monthly Comparison</h2>
      <p class="text-sm text-gray-500 mb-4">This month vs last month expenses by category</p>
      
      <div v-if="loading" class="flex items-center justify-center h-80">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
      
      <div v-else-if="comparisonData.length === 0" class="flex flex-col items-center justify-center h-80 text-gray-500">
        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p>No comparison data available</p>
      </div>
      
      <ComparativeChart
        v-else
        :data="comparisonData"
        :current-label="format(selectedDate, 'MMM yyyy', { locale: id })"
        :prev-label="format(subMonths(selectedDate, 1), 'MMM yyyy', { locale: id })"
      />
    </div>
  </div>
</template>
