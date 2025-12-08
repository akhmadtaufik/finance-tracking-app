<script setup>
defineProps({
  wallet: { type: Object, required: true },
  showDelete: { type: Boolean, default: false }
})

defineEmits(['delete'])

const walletColors = {
  'wallet': '#6366f1', 'cash': '#22c55e',
  'bca': '#0066AE', 'bni': '#F05A22', 'bri': '#00529C', 'mandiri': '#003D79',
  'cimb': '#7B0C0C', 'danamon': '#003D6A', 'permata': '#C8102E', 'btpn': '#F37021',
  'bsi': '#00A651', 'btn': '#F7941D', 'mega': '#003478', 'ocbc': '#E60012',
  'jago': '#00D4AA', 'jenius': '#00C4E8', 'blu': '#0066AE', 'seabank': '#00AED6',
  'gopay': '#00AA13', 'ovo': '#4C3494', 'dana': '#108EE9', 'shopeepay': '#EE4D2D',
  'linkaja': '#E31E25', 'other': '#6B7280'
}

const getWalletColor = (icon) => walletColors[icon] || walletColors['wallet']
const getWalletInitials = (name) => name.substring(0, 3).toUpperCase()

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}
</script>

<template>
  <div class="bg-white rounded-lg shadow p-4">
    <div class="flex items-center justify-between mb-3">
      <div 
        class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-xs"
        :style="{ backgroundColor: getWalletColor(wallet.icon) }"
      >
        {{ getWalletInitials(wallet.name) }}
      </div>
      <button
        v-if="showDelete"
        @click="$emit('delete', wallet)"
        class="text-red-500 hover:text-red-700 p-1"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>
    </div>
    <h3 class="text-sm font-semibold text-gray-800 truncate">{{ wallet.name }}</h3>
    <p class="text-lg font-bold text-indigo-600 mt-1">
      {{ formatCurrency(wallet.balance) }}
    </p>
  </div>
</template>
