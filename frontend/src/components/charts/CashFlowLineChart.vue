<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { format, eachDayOfInterval, parseISO } from 'date-fns'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps({
  data: { type: Array, default: () => [] },
  startDate: { type: String, required: true },
  endDate: { type: String, required: true }
})

const chartData = computed(() => {
  const start = parseISO(props.startDate)
  const end = parseISO(props.endDate)
  const allDates = eachDayOfInterval({ start, end })
  
  const incomeMap = new Map()
  const expenseMap = new Map()
  
  props.data.forEach(item => {
    if (item.type === 'INCOME') {
      incomeMap.set(item.day, item.total)
    } else {
      expenseMap.set(item.day, item.total)
    }
  })
  
  const labels = allDates.map(d => format(d, 'dd MMM'))
  const incomeData = allDates.map(d => incomeMap.get(format(d, 'yyyy-MM-dd')) || 0)
  const expenseData = allDates.map(d => expenseMap.get(format(d, 'yyyy-MM-dd')) || 0)
  
  return {
    labels,
    datasets: [
      {
        label: 'Income',
        data: incomeData,
        borderColor: '#10B981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 3,
        pointHoverRadius: 5
      },
      {
        label: 'Expense',
        data: expenseData,
        borderColor: '#EF4444',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.4,
        fill: true,
        pointRadius: 3,
        pointHoverRadius: 5
      }
    ]
  }
})

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index'
  },
  plugins: {
    legend: {
      position: 'top',
      labels: {
        usePointStyle: true,
        padding: 20
      }
    },
    tooltip: {
      callbacks: {
        label: (ctx) => {
          const value = new Intl.NumberFormat('id-ID', {
            style: 'currency',
            currency: 'IDR',
            minimumFractionDigits: 0
          }).format(ctx.raw)
          return `${ctx.dataset.label}: ${value}`
        }
      }
    }
  },
  scales: {
    x: {
      grid: {
        display: false
      },
      ticks: {
        maxRotation: 45,
        minRotation: 0
      }
    },
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      },
      ticks: {
        callback: (value) => {
          if (value >= 1000000) {
            return 'Rp ' + (value / 1000000).toFixed(1) + 'M'
          } else if (value >= 1000) {
            return 'Rp ' + (value / 1000).toFixed(0) + 'K'
          }
          return 'Rp ' + value
        }
      }
    }
  }
}
</script>

<template>
  <div class="h-72">
    <Line :data="chartData" :options="chartOptions" />
  </div>
</template>
