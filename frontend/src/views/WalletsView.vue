<script setup>
import { ref, onMounted } from 'vue'
import { useFinanceStore } from '../stores/finance'
import api from '../api'

const financeStore = useFinanceStore()

const showModal = ref(false)
const showDeleteModal = ref(false)
const walletToDelete = ref(null)
const walletName = ref('')
const initialBalance = ref(0)
const loading = ref(false)
const deleteLoading = ref(false)
const error = ref('')
const deleteError = ref('')

onMounted(async () => {
  await financeStore.fetchWallets()
})

const formatCurrency = (value) => {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    minimumFractionDigits: 0
  }).format(value)
}

const openModal = () => {
  walletName.value = ''
  initialBalance.value = 0
  error.value = ''
  showModal.value = true
}

const createWallet = async () => {
  if (!walletName.value.trim()) {
    error.value = 'Wallet name is required'
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    await api.post('/wallets', {
      name: walletName.value,
      balance: parseFloat(initialBalance.value) || 0
    })
    await financeStore.fetchWallets()
    showModal.value = false
  } catch (err) {
    error.value = err.response?.data?.detail || 'Failed to create wallet'
  } finally {
    loading.value = false
  }
}

const openDeleteModal = (wallet) => {
  walletToDelete.value = wallet
  deleteError.value = ''
  showDeleteModal.value = true
}

const confirmDelete = async () => {
  if (!walletToDelete.value) return
  
  deleteLoading.value = true
  deleteError.value = ''
  
  try {
    await api.delete(`/wallets/${walletToDelete.value.id}`)
    await financeStore.fetchWallets()
    showDeleteModal.value = false
    walletToDelete.value = null
  } catch (err) {
    deleteError.value = err.response?.data?.detail || 'Failed to delete wallet'
  } finally {
    deleteLoading.value = false
  }
}
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <div class="flex justify-between items-center mb-8">
      <h1 class="text-2xl font-bold text-gray-800">Wallets</h1>
      <button
        @click="openModal"
        class="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700"
      >
        + Add Wallet
      </button>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div
        v-for="wallet in financeStore.wallets"
        :key="wallet.id"
        class="bg-white rounded-lg shadow p-6"
      >
        <div class="flex items-center justify-between mb-4">
          <div class="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
            <svg class="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
            </svg>
          </div>
          <button
            @click="openDeleteModal(wallet)"
            class="text-red-500 hover:text-red-700 p-2"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
        <h3 class="text-lg font-semibold text-gray-800">{{ wallet.name }}</h3>
        <p class="text-2xl font-bold text-indigo-600 mt-2">
          {{ formatCurrency(wallet.balance) }}
        </p>
      </div>
    </div>

    <p v-if="financeStore.wallets.length === 0" class="text-center text-gray-500 py-12">
      No wallets yet. Create your first wallet!
    </p>

    <!-- Modal -->
    <div v-if="showModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
        <h2 class="text-xl font-bold text-gray-800 mb-4">Create New Wallet</h2>
        
        <div v-if="error" class="bg-red-50 text-red-600 p-3 rounded-md text-sm mb-4">
          {{ error }}
        </div>

        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Wallet Name</label>
            <input
              v-model="walletName"
              type="text"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="e.g., Savings, Cash, Bank BCA"
            />
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Initial Balance (IDR)</label>
            <input
              v-model="initialBalance"
              type="number"
              min="0"
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="0"
            />
          </div>
        </div>

        <div class="flex space-x-4 mt-6">
          <button
            @click="showModal = false"
            class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="createWallet"
            :disabled="loading"
            class="flex-1 py-2 px-4 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {{ loading ? 'Creating...' : 'Create Wallet' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div class="bg-white rounded-lg shadow-xl p-6 w-full max-w-md mx-4">
        <div class="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
          <svg class="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        
        <h2 class="text-xl font-bold text-gray-800 text-center mb-2">Delete Wallet</h2>
        
        <p v-if="walletToDelete" class="text-gray-600 text-center mb-4">
          Are you sure you want to delete "<strong>{{ walletToDelete.name }}</strong>"? 
          All transactions associated with this wallet will also be deleted. This action cannot be undone.
        </p>
        
        <div v-if="deleteError" class="bg-red-50 text-red-600 p-3 rounded-md text-sm mb-4">
          {{ deleteError }}
        </div>

        <div class="flex space-x-4">
          <button
            @click="showDeleteModal = false; walletToDelete = null; deleteError = ''"
            class="flex-1 py-2 px-4 border border-gray-300 text-gray-700 font-medium rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            @click="confirmDelete"
            :disabled="deleteLoading"
            class="flex-1 py-2 px-4 bg-red-600 text-white font-medium rounded-md hover:bg-red-700 disabled:opacity-50"
          >
            {{ deleteLoading ? 'Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
