<script setup>
import { ref, computed, watch } from 'vue'
import CurrencyInput from './CurrencyInput.vue'
import api from '../api'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  wallets: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'success'])

const sourceWalletId = ref(null)
const destWalletId = ref(null)
const amount = ref(0)
const transactionDate = ref(new Date().toISOString().split('T')[0])
const description = ref('')
const loading = ref(false)
const error = ref('')

const availableDestWallets = computed(() => {
  return props.wallets.filter(w => w.id !== sourceWalletId.value)
})

const sourceWallet = computed(() => {
  return props.wallets.find(w => w.id === sourceWalletId.value)
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}

watch(() => props.show, (newVal) => {
  if (newVal) {
    resetForm()
  }
})

watch(sourceWalletId, () => {
  if (destWalletId.value === sourceWalletId.value) {
    destWalletId.value = null
  }
})

const resetForm = () => {
  sourceWalletId.value = props.wallets.length > 0 ? props.wallets[0].id : null
  destWalletId.value = null
  amount.value = 0
  transactionDate.value = new Date().toISOString().split('T')[0]
  description.value = ''
  error.value = ''
}

const handleSubmit = async () => {
  error.value = ''

  if (!sourceWalletId.value) {
    error.value = 'Please select source wallet'
    return
  }

  if (!destWalletId.value) {
    error.value = 'Please select destination wallet'
    return
  }

  if (amount.value <= 0) {
    error.value = 'Amount must be greater than 0'
    return
  }

  if (sourceWallet.value && amount.value > sourceWallet.value.balance) {
    error.value = 'Insufficient balance in source wallet'
    return
  }

  loading.value = true

  try {
    await api.post('/transactions/transfer', {
      source_wallet_id: sourceWalletId.value,
      dest_wallet_id: destWalletId.value,
      amount: amount.value,
      transaction_date: transactionDate.value,
      description: description.value || null
    })
    emit('success')
    emit('close')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Transfer failed'
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('close')
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-800">Transfer Funds</h2>
        <button @click="close" class="text-gray-400 hover:text-gray-600">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-md text-sm mb-4">
        {{ error }}
      </div>

      <div class="space-y-4">
        <!-- Source Wallet -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">From Wallet</label>
          <select
            v-model="sourceWalletId"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option :value="null" disabled>Select source wallet</option>
            <option v-for="wallet in wallets" :key="wallet.id" :value="wallet.id">
              {{ wallet.name }} ({{ formatCurrency(wallet.balance) }})
            </option>
          </select>
        </div>

        <!-- Arrow Icon -->
        <div class="flex justify-center">
          <div class="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
            <svg class="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </div>
        </div>

        <!-- Destination Wallet -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">To Wallet</label>
          <select
            v-model="destWalletId"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option :value="null" disabled>Select destination wallet</option>
            <option v-for="wallet in availableDestWallets" :key="wallet.id" :value="wallet.id">
              {{ wallet.name }} ({{ formatCurrency(wallet.balance) }})
            </option>
          </select>
        </div>

        <!-- Amount -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Amount</label>
          <CurrencyInput v-model="amount" placeholder="0" />
          <p v-if="sourceWallet" class="text-xs text-gray-500 mt-1">
            Available: {{ formatCurrency(sourceWallet.balance) }}
          </p>
        </div>

        <!-- Date -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Date</label>
          <input
            v-model="transactionDate"
            type="date"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <!-- Description -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
          <input
            v-model="description"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="e.g., Top up e-wallet"
          />
        </div>
      </div>

      <div class="flex space-x-4 mt-6">
        <button
          @click="close"
          class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          @click="handleSubmit"
          :disabled="loading"
          class="flex-1 py-2 px-4 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {{ loading ? 'Transferring...' : 'Transfer' }}
        </button>
      </div>
    </div>
  </div>
</template>
