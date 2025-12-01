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
import { id } from 'date-fns/locale'
import api from '../api'
import HorizontalBarChart from '../components/charts/HorizontalBarChart.vue'

const period = ref('month')
const selectedDate = ref(new Date())
const breakdown = ref([])
const summary = ref({ total_income: 0, total_expense: 0, net: 0, transaction_count: 0 })
const loading = ref(false)
const transactionType = ref('EXPENSE')

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
    end: format(end, 'yyyy-MM-dd'),
    startDate: start,
    endDate: end
  }
})

const periodLabel = computed(() => {
  const date = selectedDate.value
  switch (period.value) {
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
const chartData = computed(() => breakdown.value.map(item => item.total))

const totalAmount = computed(() => {
  return breakdown.value.reduce((sum, item) => sum + item.total, 0)
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
    
    const [breakdownRes, summaryRes] = await Promise.all([
      api.get('/analytics/category-breakdown', {
        params: { start_date: start, end_date: end, type: transactionType.value }
      }),
      api.get('/analytics/period-summary', {
        params: { start_date: start, end_date: end }
      })
    ])
    
    breakdown.value = breakdownRes.data
    summary.value = summaryRes.data
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

watch([period, selectedDate, transactionType], () => {
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
          {{ transactionType === 'EXPENSE' ? 'Expense' : 'Income' }} by Category
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
      <div v-if="breakdown.length > 0" class="mt-6 border-t pt-4">
        <div class="space-y-2">
          <div
            v-for="(item, index) in breakdown"
            :key="item.name"
            class="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-gray-50"
          >
            <div class="flex items-center gap-3">
              <span class="w-6 text-center text-sm text-gray-400">{{ index + 1 }}</span>
              <span class="font-medium text-gray-800">{{ item.name }}</span>
            </div>
            <div class="flex items-center gap-4">
              <div class="w-32 bg-gray-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full"
                  :class="transactionType === 'EXPENSE' ? 'bg-red-500' : 'bg-green-500'"
                  :style="{ width: (item.total / breakdown[0].total * 100) + '%' }"
                ></div>
              </div>
              <span class="font-semibold text-gray-800 w-32 text-right">
                {{ formatCurrency(item.total) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
