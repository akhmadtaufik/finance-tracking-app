<script setup>
import { ref, computed, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { Camera, Upload, Trash2, Plus, Check, AlertCircle, ArrowLeft } from 'lucide-vue-next'
import { useUIStore } from '@/stores/ui'
import WalletSelector from '@/components/inputs/WalletSelector.vue'
import CategorySelector from '@/components/inputs/CategorySelector.vue'
import CurrencyInput from '@/components/CurrencyInput.vue'
import axios from 'axios'

// Store & Router
const uiStore = useUIStore()
const router = useRouter()

// Constants
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000' // Adjust as needed or use configured axios instance

// State
const step = ref('upload') // 'upload' | 'review'
const isLoading = ref(false)
const receiptDate = ref(new Date().toISOString().split('T')[0])
const selectedWalletId = ref(null)
const scannedItems = ref([])
const wallets = ref([])
const categories = ref([])

// Editing State for Category Modal
const showCategoryModal = ref(false)
const editingItemIndex = ref(-1)

// Computed
const totalAmount = computed(() => {
  return scannedItems.value.reduce((sum, item) => sum + (Number(item.amount) || 0), 0)
})

const isValidToSave = computed(() => {
  if (!selectedWalletId.value) return false
  if (scannedItems.value.length === 0) return false
  return scannedItems.value.every((item) => item.name && item.amount > 0 && item.category_id)
})

// Lifecycle
onMounted(async () => {
  await fetchWallets()
  await fetchCategories()
})

const fetchWallets = async () => {
  try {
    // Assuming auth token is handled by interceptor or we need to add it manually
    // For now using simple axios call, modify if you have a configured api client
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }

    const res = await axios.get(`${API_URL}/wallets`, { headers })
    wallets.value = res.data

    // Auto-select first wallet if available
    if (wallets.value.length > 0) {
      selectedWalletId.value = wallets.value[0].id
    }
  } catch (error) {
    console.error('Failed to fetch wallets', error)
  }
}

const fetchCategories = async () => {
  try {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }
    const res = await axios.get(`${API_URL}/categories`, { headers })
    // Filter only EXPENSE categories for receipts
    categories.value = res.data.filter((c) => c.type === 'EXPENSE')
  } catch (error) {
    console.error('Failed to fetch categories', error)
  }
}

// Actions
const triggerFileInput = () => {
  document.getElementById('receipt-upload').click()
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return

  isLoading.value = true

  const formData = new FormData()
  formData.append('file', file)

  try {
    const token = localStorage.getItem('token')
    const headers = {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'multipart/form-data'
    }

    const { data } = await axios.post(`${API_URL}/receipts/scan`, formData, { headers })

    // Success handling
    if (data.date) receiptDate.value = data.date

    // Map items to our structure
    scannedItems.value = data.items.map((item, index) => ({
      id: Date.now() + index, // Temp ID for v-for key
      name: item.name,
      amount: item.price,
      category_id: guessCategoryId(item.category_guess)
    }))

    step.value = 'review'
  } catch (error) {
    console.error('Scan failed', error)

    if (error.response && error.response.status === 429) {
      // 429 Quota Exceeded logic
      uiStore.showToast({
        message: 'Kuota Scan AI habis untuk hari ini. Silakan input manual.',
        type: 'warning', // Yellow/Warning color
        duration: 6000
      })
      // Optional: Redirect logic if desired, or let user retry/manual
    } else {
      uiStore.showToast({
        message:
          error.response?.data?.detail || 'Gagal memproses struk. Coba lagi atau input manual.',
        type: 'error'
      })
    }
  } finally {
    isLoading.value = false
    // Reset input
    event.target.value = ''
  }
}

const guessCategoryId = (guess) => {
  if (!guess) return null
  // Simple matching based on backend guess
  // In a real app, this might match by ID if backend returned ID,
  // but backend returns string guess. We try to find a category with similar name or type.
  // Implementation depends on how robust we want this to be.
  // For now, let's try to match by name (case insensitive)
  const match = categories.value.find(
    (c) =>
      c.name.toLowerCase().includes(guess.toLowerCase()) ||
      guess.toLowerCase().includes(c.name.toLowerCase())
  )
  return match ? match.id : null
}

const addItem = () => {
  scannedItems.value.push({
    id: Date.now(),
    name: 'Item Baru',
    amount: 0,
    category_id: null
  })
  // Auto scroll to bottom
  nextTick(() => {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
  })
}

const removeItem = (index) => {
  scannedItems.value.splice(index, 1)
}

const openCategoryModal = (index) => {
  editingItemIndex.value = index
  showCategoryModal.value = true
}

const updateItemCategory = (categoryId) => {
  if (editingItemIndex.value !== -1 && scannedItems.value[editingItemIndex.value]) {
    scannedItems.value[editingItemIndex.value].category_id = categoryId
  }
  showCategoryModal.value = false
  editingItemIndex.value = -1
}

const getCategoryName = (id) => {
  const cat = categories.value.find((c) => c.id === id)
  return cat ? cat.name : 'Pilih Kategori'
}

const getCategoryIcon = (id) => {
  const cat = categories.value.find((c) => c.id === id)
  return cat ? cat.icon : 'help-circle'
}

const saveTransactions = async () => {
  if (!isValidToSave.value) return

  isLoading.value = true

  try {
    const token = localStorage.getItem('token')
    const headers = { Authorization: `Bearer ${token}` }

    const payload = scannedItems.value.map((item) => ({
      wallet_id: selectedWalletId.value,
      category_id: item.category_id,
      amount: item.amount,
      type: 'EXPENSE',
      transaction_date: receiptDate.value,
      description: item.name
    }))

    await axios.post(`${API_URL}/transactions/batch`, payload, { headers })

    uiStore.showToast({
      message: 'Berhasil menyimpan transaksi!',
      type: 'success'
    })

    router.push('/')
  } catch (error) {
    console.error('Save failed', error)
    uiStore.showToast({
      message: error.response?.data?.detail || 'Gagal menyimpan transaksi.',
      type: 'error'
    })
  } finally {
    isLoading.value = false
  }
}

// Modal Component Wrapper
// We use a simple teleport or v-if overlay for the modal
</script>

<template>
  <div class="max-w-3xl mx-auto px-4 py-8 pb-24">
    <!-- Header -->
    <div class="mb-6 flex items-center justify-between">
      <h1 class="text-2xl font-bold text-gray-800">Scan Struk Belanja</h1>
      <button
        v-if="step === 'review'"
        @click="step = 'upload'"
        class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
      >
        <ArrowLeft class="w-4 h-4" /> Ulangi
      </button>
    </div>

    <!-- Loading Overlay -->
    <div
      v-if="isLoading"
      class="fixed inset-0 bg-white/80 z-50 flex flex-col items-center justify-center"
    >
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
      <p class="text-gray-600 font-medium animate-pulse">
        {{ step === 'upload' ? 'Sedang Menganalisis Struk...' : 'Menyimpan Transaksi...' }}
      </p>
    </div>

    <!-- STEP 1: UPLOAD -->
    <div v-if="step === 'upload'" class="flex flex-col gap-6">
      <div
        @click="triggerFileInput"
        class="border-2 border-dashed border-gray-300 rounded-2xl bg-gray-50 hover:bg-indigo-50 hover:border-indigo-300 transition-colors cursor-pointer h-64 flex flex-col items-center justify-center gap-4 group"
      >
        <div
          class="p-4 bg-white rounded-full shadow-sm group-hover:scale-110 transition-transform duration-200"
        >
          <Camera class="w-8 h-8 text-indigo-500" />
        </div>
        <div class="text-center">
          <p class="text-lg font-medium text-gray-700">Tap to Scan Receipt</p>
          <p class="text-sm text-gray-400">or upload image from gallery</p>
        </div>
        <input
          type="file"
          id="receipt-upload"
          accept="image/*"
          class="hidden"
          @change="handleFileUpload"
        />
      </div>

      <div class="bg-blue-50 p-4 rounded-xl flex items-start gap-3 text-sm text-blue-700">
        <AlertCircle class="w-5 h-5 shrink-0 mt-0.5" />
        <p>
          Pastikan foto struk terlihat jelas, terang, dan menampilkan detail item serta harga. AI
          akan otomatis mengekstrak data untuk Anda.
        </p>
      </div>
    </div>

    <!-- STEP 2: REVIEW -->
    <div v-else class="space-y-6">
      <!-- General Settings -->
      <div class="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 space-y-4">
        <h2 class="font-semibold text-gray-800 border-b pb-2 mb-2">Detail Transaksi</h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">Tanggal</label>
            <input
              v-model="receiptDate"
              type="date"
              class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">Dompet Pembayaran</label>
            <!-- Custom Wallet Selector integration -->
            <div class="relative">
              <select
                v-model="selectedWalletId"
                class="w-full p-2 border border-gray-300 rounded-lg appearance-none bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option v-for="w in wallets" :key="w.id" :value="w.id">
                  {{ w.name }} ({{
                    new Intl.NumberFormat('id-ID', {
                      style: 'currency',
                      currency: 'IDR',
                      minimumFractionDigits: 0
                    }).format(w.balance)
                  }})
                </option>
              </select>
              <div
                class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-gray-700"
              >
                <svg
                  class="fill-current h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                >
                  <path
                    d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"
                  />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Items List -->
      <div class="space-y-3">
        <div class="flex items-center justify-between px-1">
          <h2 class="font-semibold text-gray-800">Daftar Item</h2>
          <span class="text-sm bg-indigo-50 text-indigo-700 px-2 py-1 rounded-md font-medium">
            {{ scannedItems.length }} Items
          </span>
        </div>

        <!-- Desktop/Mobile Responsive List -->
        <div class="flex flex-col gap-3">
          <transition-group name="list">
            <div
              v-for="(item, index) in scannedItems"
              :key="item.id"
              class="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex flex-col md:flex-row md:items-center gap-3 relative group"
            >
              <!-- Delete Button (Top Right on Mobile, Right on Desktop) -->
              <button
                @click="removeItem(index)"
                class="absolute top-2 right-2 md:static md:order-last p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                title="Hapus Item"
              >
                <Trash2 class="w-4 h-4" />
              </button>

              <!-- Name Input -->
              <div class="flex-grow">
                <label class="text-xs text-gray-400 md:hidden">Nama Item</label>
                <input
                  v-model="item.name"
                  type="text"
                  placeholder="Nama Item"
                  class="w-full font-medium text-gray-800 bg-transparent border-b border-transparent focus:border-indigo-500 focus:outline-none placeholder-gray-300 transition-colors py-1"
                />
              </div>

              <!-- Amount Input -->
              <div class="w-full md:w-40">
                <label class="text-xs text-gray-400 md:hidden">Harga</label>
                <CurrencyInput v-model="item.amount" class="font-medium" />
              </div>

              <!-- Category Trigger -->
              <div class="w-full md:w-auto md:min-w-[150px]">
                <label class="text-xs text-gray-400 md:hidden mb-1 block">Kategori</label>
                <button
                  @click="openCategoryModal(index)"
                  class="w-full flex items-center justify-between gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg text-sm text-gray-700 transition-colors"
                >
                  <span class="truncate">{{ getCategoryName(item.category_id) }}</span>
                  <!-- Simple indicator if selected -->
                  <div v-if="item.category_id" class="w-2 h-2 rounded-full bg-indigo-500"></div>
                </button>
              </div>
            </div>
          </transition-group>
        </div>

        <!-- Add Item Button -->
        <button
          @click="addItem"
          class="w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center justify-center gap-2 font-medium"
        >
          <Plus class="w-5 h-5" /> Tambah Item Manual
        </button>
      </div>

      <!-- Footer Summary -->
      <div
        class="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200 shadow-lg z-10 md:static md:shadow-none md:border-0 md:bg-transparent md:p-0"
      >
        <div class="max-w-3xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div class="w-full md:w-auto">
            <p class="text-sm text-gray-500">Total Belanja</p>
            <p class="text-2xl font-bold text-gray-900">
              {{
                new Intl.NumberFormat('id-ID', {
                  style: 'currency',
                  currency: 'IDR',
                  minimumFractionDigits: 0
                }).format(totalAmount)
              }}
            </p>
          </div>

          <div class="flex w-full md:w-auto gap-3">
            <button
              @click="step = 'upload'"
              class="flex-1 md:flex-none px-6 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              Batal
            </button>
            <button
              @click="saveTransactions"
              :disabled="!isValidToSave || isLoading"
              class="flex-1 md:flex-none px-6 py-3 rounded-xl bg-indigo-600 text-white font-bold hover:bg-indigo-700 shadow-lg hover:shadow-indigo-200 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <Check v-if="!isLoading" class="w-5 h-5" />
              {{ isLoading ? 'Menyimpan...' : 'Simpan Semua' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Category Selection Modal / Overlay -->
    <div
      v-if="showCategoryModal"
      class="fixed inset-0 z-[60] bg-black/50 flex items-end md:items-center justify-center p-4 backdrop-blur-sm"
      @click.self="showCategoryModal = false"
    >
      <div
        class="bg-white w-full max-w-md rounded-2xl md:rounded-xl p-6 shadow-2xl animate-in slide-in-from-bottom-10 md:slide-in-from-bottom-5 fade-in duration-200"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-gray-900">Pilih Kategori</h3>
          <button
            @click="showCategoryModal = false"
            class="p-2 bg-gray-100 rounded-full hover:bg-gray-200"
          >
            <span class="sr-only">Close</span>
            <svg
              class="w-5 h-5 text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div class="max-h-[60vh] overflow-y-auto">
          <!-- Reusing CategorySelector but strictly for EXPENSE -->
          <CategorySelector
            :categories="categories"
            :model-value="scannedItems[editingItemIndex]?.category_id"
            @update:modelValue="updateItemCategory"
            current-type="EXPENSE"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.list-enter-active,
.list-leave-active {
  transition: all 0.3s ease;
}
.list-enter-from,
.list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}
</style>
