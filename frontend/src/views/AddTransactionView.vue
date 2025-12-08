<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useFinanceStore } from '../stores/finance'
import CurrencyInput from '../components/CurrencyInput.vue'
import WalletSelector from '../components/inputs/WalletSelector.vue'
import CategorySelector from '../components/inputs/CategorySelector.vue'

const router = useRouter()
const financeStore = useFinanceStore()

const type = ref('EXPENSE')
const walletId = ref(null)
const categoryId = ref(null)
const amount = ref(0)
const description = ref('')
const transactionDate = ref(new Date().toISOString().split('T')[0])
const error = ref('')
const loading = ref(false)

onMounted(async () => {
  await Promise.all([
    financeStore.fetchWallets(),
    financeStore.fetchCategories()
  ])
  
  if (financeStore.wallets.length > 0) {
    walletId.value = financeStore.wallets[0].id
  }
})

const filteredCategories = computed(() => {
  return financeStore.categories.filter(c => c.type === type.value)
})

watch(type, () => {
  categoryId.value = null
})

const handleSubmit = async () => {
  error.value = ''
  
  if (!walletId.value || !categoryId.value || !amount.value) {
    error.value = 'Please fill all required fields'
    return
  }
  
  loading.value = true
  
  try {
    await financeStore.createTransaction({
      wallet_id: walletId.value,
      category_id: categoryId.value,
      amount: parseFloat(amount.value),
      type: type.value,
      transaction_date: transactionDate.value,
      description: description.value || null
    })
    router.push('/')
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create transaction'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-8">Add Transaction</h1>
    
    <div class="bg-white rounded-lg shadow p-6">
      <form @submit.prevent="handleSubmit" class="space-y-6">
        <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-md text-sm">
          {{ error }}
        </div>

        <!-- Transaction Type Toggle -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Type</label>
          <div class="flex space-x-4">
            <button
              type="button"
              @click="type = 'INCOME'"
              :class="[
                'flex-1 py-3 px-4 rounded-lg font-medium transition-colors',
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
                'flex-1 py-3 px-4 rounded-lg font-medium transition-colors',
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
            :wallets="financeStore.wallets" 
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
            required
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <!-- Description -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Description (optional)</label>
          <textarea
            v-model="description"
            rows="3"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Add a note..."
          ></textarea>
        </div>

        <!-- Actions -->
        <div class="flex space-x-4">
          <button
            type="button"
            @click="router.push('/')"
            class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="flex-1 py-2 px-4 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {{ loading ? 'Saving...' : 'Save Transaction' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
