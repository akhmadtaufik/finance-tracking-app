<script setup>
defineProps({
  wallets: { type: Array, default: () => [] },
  modelValue: { type: [Number, null], default: null }
})

const emit = defineEmits(['update:modelValue'])

const selectWallet = (id) => {
  emit('update:modelValue', id)
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}

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
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
    <button
      v-for="wallet in wallets"
      :key="wallet.id"
      type="button"
      @click="selectWallet(wallet.id)"
      :class="[
        'p-4 rounded-xl text-left transition-all duration-150 cursor-pointer',
        modelValue === wallet.id
          ? 'bg-blue-50 border-2 border-blue-500 ring-2 ring-blue-200 shadow-md'
          : 'bg-white border border-gray-200 shadow-sm hover:shadow-md hover:border-gray-300'
      ]"
    >
      <div class="flex items-center gap-3">
        <div 
          class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-xs shrink-0"
          :style="{ backgroundColor: getWalletColor(wallet.icon) }"
        >
          {{ getWalletInitials(wallet.name) }}
        </div>
        <div class="min-w-0">
          <p class="font-medium text-gray-800 truncate">{{ wallet.name }}</p>
          <p class="text-sm text-gray-500">{{ formatCurrency(wallet.balance) }}</p>
        </div>
      </div>
    </button>
  </div>
  <p v-if="wallets.length === 0" class="text-sm text-gray-400 text-center py-4">
    No wallets available
  </p>
</template>
