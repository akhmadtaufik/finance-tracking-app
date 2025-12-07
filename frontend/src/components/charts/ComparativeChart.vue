<script setup>
import { computed } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Bar } from 'vue-chartjs'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const props = defineProps({
  data: { type: Array, default: () => [] },
  currentLabel: { type: String, default: 'This Month' },
  prevLabel: { type: String, default: 'Last Month' }
})

const chartData = computed(() => ({
  labels: props.data.map(item => item.category),
  datasets: [
    {
      label: props.currentLabel,
      data: props.data.map(item => item.current_total),
      backgroundColor: '#3B82F6',
      borderRadius: 4,
      barPercentage: 0.8,
      categoryPercentage: 0.7
    },
    {
      label: props.prevLabel,
      data: props.data.map(item => item.prev_total),
      backgroundColor: '#9CA3AF',
      borderRadius: 4,
      barPercentage: 0.8,
      categoryPercentage: 0.7
    }
  ]
}))

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
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
  <div class="h-80">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
