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
  labels: {
    type: Array,
    required: true
  },
  data: {
    type: Array,
    required: true
  },
  title: {
    type: String,
    default: ''
  }
})

const generateColors = (count) => {
  const baseColors = [
    'rgba(239, 68, 68, 0.8)',   // red-500
    'rgba(249, 115, 22, 0.8)',  // orange-500
    'rgba(245, 158, 11, 0.8)',  // amber-500
    'rgba(234, 179, 8, 0.8)',   // yellow-500
    'rgba(132, 204, 22, 0.8)',  // lime-500
    'rgba(34, 197, 94, 0.8)',   // green-500
    'rgba(20, 184, 166, 0.8)',  // teal-500
    'rgba(6, 182, 212, 0.8)',   // cyan-500
    'rgba(59, 130, 246, 0.8)',  // blue-500
    'rgba(99, 102, 241, 0.8)',  // indigo-500
    'rgba(139, 92, 246, 0.8)',  // violet-500
    'rgba(168, 85, 247, 0.8)',  // purple-500
    'rgba(217, 70, 239, 0.8)',  // fuchsia-500
    'rgba(236, 72, 153, 0.8)',  // pink-500
    'rgba(244, 63, 94, 0.8)',   // rose-500
  ]
  
  const colors = []
  for (let i = 0; i < count; i++) {
    colors.push(baseColors[i % baseColors.length])
  }
  return colors
}

const chartData = computed(() => ({
  labels: props.labels,
  datasets: [
    {
      data: props.data,
      backgroundColor: generateColors(props.data.length),
      borderColor: generateColors(props.data.length).map(c => c.replace('0.8', '1')),
      borderWidth: 1,
      borderRadius: 4,
      barThickness: 24
    }
  ]
}))

const chartOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    title: {
      display: false
    },
    tooltip: {
      callbacks: {
        label: (context) => {
          return context.raw + '%'
        }
      }
    }
  },
  scales: {
    x: {
      beginAtZero: true,
      max: 100,
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.05)'
      },
      ticks: {
        callback: (value) => value + '%'
      }
    },
    y: {
      grid: {
        display: false
      },
      ticks: {
        font: {
          size: 12
        }
      }
    }
  }
}
</script>

<template>
  <div class="w-full" :style="{ height: Math.max(200, labels.length * 40) + 'px' }">
    <Bar :data="chartData" :options="chartOptions" />
  </div>
</template>
