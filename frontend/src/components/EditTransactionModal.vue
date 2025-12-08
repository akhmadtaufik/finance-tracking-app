<script setup>
import { ref, computed, watch } from 'vue'
import CurrencyInput from './CurrencyInput.vue'
import WalletSelector from './inputs/WalletSelector.vue'
import CategorySelector from './inputs/CategorySelector.vue'
import api from '../api'
import { useUIStore } from '../stores/ui'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  transaction: {
    type: Object,
    default: null
  },
  wallets: {
    type: Array,
    default: () => []
  },
  categories: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'success'])

const uiStore = useUIStore()

const type = ref('EXPENSE')
const walletId = ref(null)
const categoryId = ref(null)
const amount = ref(0)
const description = ref('')
const transactionDate = ref('')
const loading = ref(false)
const error = ref('')

const filteredCategories = computed(() => {
  return props.categories.filter(c => c.type === type.value)
})

watch(() => props.show, (newVal) => {
  if (newVal && props.transaction) {
    populateForm()
  }
})

watch(() => props.transaction, (newVal) => {
  if (props.show && newVal) {
    populateForm()
  }
})

watch(type, (newType, oldType) => {
  if (newType !== oldType) {
    const currentCategory = props.categories.find(c => c.id === categoryId.value)
    if (currentCategory && currentCategory.type !== newType) {
      categoryId.value = null
    }
  }
})

const populateForm = () => {
  const t = props.transaction
  if (!t) return
  
  type.value = t.type
  walletId.value = t.wallet_id
  categoryId.value = t.category_id
  amount.value = parseFloat(t.amount)
  description.value = t.description || ''
  transactionDate.value = t.transaction_date
  error.value = ''
}

const handleSubmit = async () => {
  error.value = ''
  
  if (!walletId.value || !categoryId.value || !amount.value) {
    error.value = 'Please fill all required fields'
    return
  }
  
  loading.value = true
  
  try {
    await api.put(`/transactions/${props.transaction.id}`, {
      wallet_id: walletId.value,
      category_id: categoryId.value,
      amount: parseFloat(amount.value),
      type: type.value,
      transaction_date: transactionDate.value,
      description: description.value || null
    })
    uiStore.showToast({ message: 'Transaction updated successfully', type: 'success' })
    emit('success')
    emit('close')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to update transaction'
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('close')
}

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}
</script>

<template>
  <div v-if="show" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-3xl mx-4 max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-xl font-bold text-gray-800">Edit Transaction</h2>
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
        <!-- Transaction Type Toggle -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Type</label>
          <div class="flex space-x-4">
            <button
              type="button"
              @click="type = 'INCOME'"
              :class="[
                'flex-1 py-2 px-4 rounded-lg font-medium transition-colors',
                type === 'INCOME' 
                  ? 'bg-green-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              Income
            </button>
            <button
              type="button"
              @click="type = 'EXPENSE'"
              :class="[
                'flex-1 py-2 px-4 rounded-lg font-medium transition-colors',
                type === 'EXPENSE' 
                  ? 'bg-red-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              ]"
            >
              Expense
            </button>
          </div>
        </div>

        <!-- Amount -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Amount</label>
          <CurrencyInput v-model="amount" placeholder="0" />
        </div>

        <!-- Wallet -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Wallet</label>
          <WalletSelector 
            :wallets="wallets" 
            v-model="walletId" 
          />
        </div>

        <!-- Category -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Category</label>
          <CategorySelector 
            :categories="filteredCategories" 
            v-model="categoryId" 
            :current-type="type"
          />
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
          <textarea
            v-model="description"
            rows="2"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Add a note..."
          ></textarea>
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
          {{ loading ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </div>
  </div>
</template>
