<script setup>
import { ref, computed, reactive, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import {
  Camera,
  Upload,
  Trash2,
  Plus,
  Check,
  AlertCircle,
  ArrowLeft,
  AlertTriangle,
  RefreshCw,
  Copy,
  CheckCircle2,
  FileText,
  X
} from 'lucide-vue-next'
import { useUIStore } from '@/stores/ui'
import WalletSelector from '@/components/inputs/WalletSelector.vue'
import CategorySelector from '@/components/inputs/CategorySelector.vue'
import CurrencyInput from '@/components/CurrencyInput.vue'
import api from '@/api'
import logger, { getRequestId } from '@/services/logger'
import { compressReceiptImage } from '@/utils/imageCompressor'

// Store & Router
const uiStore = useUIStore()
const router = useRouter()

// State
const step = ref('upload') // 'upload' | 'review'
const isLoading = ref(false)
const loadingProgressText = ref('Sedang Menganalisis Struk...')
let loadingInterval = null
const abortController = ref(null)

const cancelScan = () => {
  if (abortController.value) {
    abortController.value.abort()
  }
  isLoading.value = false
  if (loadingInterval) {
    clearInterval(loadingInterval)
    loadingInterval = null
  }
}
const receiptDate = ref(new Date().toISOString().split('T')[0])
const selectedWalletId = ref(null)
const scannedItems = ref([])
const wallets = ref([])
const categories = ref([])

// Error State & Diagnostics
const scanError = ref(null)
const lastUploadedFile = ref(null)
const copiedRequestId = ref(false)

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
 const res = await api.get('/wallets')
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
 const res = await api.get('/categories')
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

const getErrorTitle = (code) => {
  switch (code) {
    case 'AI_QUOTA_EXCEEDED':
      return 'Kuota Scan AI Habis'
    case 'AI_IMAGE_UNREADABLE':
      return 'Foto Struk Tidak Terbaca'
    case 'FILE_TOO_LARGE':
      return 'Ukuran File Terlalu Besar'
    case 'INVALID_FILE_TYPE':
    case 'INVALID_MAGIC_BYTES':
      return 'Format File Tidak Didukung'
    case 'AI_TIMEOUT':
      return 'Waktu Pemrosesan Habis'
    case 'AI_SERVICE_UNAVAILABLE':
      return 'Layanan AI Sedang Sibuk'
    case 'EMPTY_FILE':
      return 'File Struk Kosong'
    default:
      return 'Gagal Memindai Struk'
  }
}

const copyRequestId = async () => {
  if (!scanError.value?.requestId) return
  try {
    await navigator.clipboard.writeText(scanError.value.requestId)
    copiedRequestId.value = true
    uiStore.showToast({
      message: 'ID Masalah berhasil disalin ke clipboard',
      type: 'success',
      duration: 3000
    })
    setTimeout(() => {
      copiedRequestId.value = false
    }, 3000)
  } catch (err) {
    logger.captureError(err, { context: 'copy_request_id' })
  }
}

const handleFileUpload = async (event) => {
  const file = event?.target?.files?.[0] || lastUploadedFile.value
  if (!file) return

  lastUploadedFile.value = file
  scanError.value = null

  // Pre-flight file size check (5MB)
  if (file.size > 5 * 1024 * 1024) {
    const errorData = {
      code: 'FILE_TOO_LARGE',
      title: 'Ukuran File Terlalu Besar',
      detail: 'Ukuran file struk maksimal 5MB. Silakan kompres atau ambil foto dengan resolusi standar.',
      requestId: getRequestId() || '-',
      retryable: false,
      actionHint: 'retake_photo'
    }
    scanError.value = errorData
    logger.warn('Client-side rejected file: too large', { fileSize: file.size })
    if (event?.target) event.target.value = ''
    return
  }

  isLoading.value = true
  loadingProgressText.value = 'Mengompresi gambar untuk menghemat token...'

  const startTime = Date.now()
  if (loadingInterval) clearInterval(loadingInterval)
  loadingInterval = setInterval(() => {
    const elapsed = Math.round((Date.now() - startTime) / 1000)
    if (elapsed < 8) {
      loadingProgressText.value = 'Mengunggah & membaca teks struk...'
    } else if (elapsed < 20) {
      loadingProgressText.value = 'Sedang menganalisis item dan kategori belanja...'
    } else if (elapsed < 35) {
      loadingProgressText.value = 'Memproses struk dengan AI, mohon tunggu sebentar...'
    } else {
      loadingProgressText.value = 'Hampir selesai, memvalidasi hasil ekstraksi...'
    }
  }, 2000)

  try {
    // Client-side in-memory compression (pure RAM)
    const compressedFile = await compressReceiptImage(file, 1200, 0.85)

    abortController.value = new AbortController()
    const formData = new FormData()
    formData.append('file', compressedFile)

    const { data } = await api.post('/receipts/scan', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      skipToast: true,
      signal: abortController.value.signal
    })

    // Success handling
    if (data.date) receiptDate.value = data.date

    // Map items to our structure
    scannedItems.value = (data.items || []).map((item, index) => ({
      id: Date.now() + index, // Temp ID for v-for key
      name: item.name,
      amount: item.price,
      category_id: guessCategoryId(item.category_guess)
    }))

    scanError.value = null
    step.value = 'review'
  } catch (error) {
    // Ignore explicit user cancellation
    if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
      logger.info('Receipt scan aborted by user')
      return
    }

    console.error('Scan failed', error)
    const errData = error.response?.data || {}
    const statusCode = error.response?.status
    const reqId =
      errData.request_id ||
      error.response?.headers?.['x-request-id'] ||
      getRequestId() ||
      '-'

    const code =
      errData.code ||
      (statusCode === 429
        ? 'AI_QUOTA_EXCEEDED'
        : statusCode === 413
        ? 'FILE_TOO_LARGE'
        : statusCode === 415
        ? 'INVALID_MAGIC_BYTES'
        : statusCode === 422
        ? 'AI_IMAGE_UNREADABLE'
        : statusCode === 504
        ? 'AI_TIMEOUT'
        : statusCode === 503
        ? 'AI_SERVICE_UNAVAILABLE'
        : 'SCAN_FAILED')

    const detail =
      errData.detail ||
      error.message ||
      'Gagal memproses struk. Silakan coba lagi atau gunakan input manual.'
    const retryable = errData.retryable ?? (statusCode === 504 || statusCode === 503)
    const actionHint =
      errData.action_hint || (code === 'AI_QUOTA_EXCEEDED' ? 'manual_input' : 'retake_photo')

    scanError.value = {
      code,
      title: getErrorTitle(code),
      detail,
      requestId: reqId,
      retryable,
      actionHint
    }

    // Synchronize to frontend logger for backend trace visibility
    logger.error(`Receipt scan failed: ${code} - ${detail}`, {
      code,
      status: statusCode,
      requestId: reqId,
      fileName: file.name,
      fileSize: file.size,
      fileType: file.type,
      durationMs: Date.now() - startTime,
      detail
    })
  } finally {
    if (loadingInterval) {
      clearInterval(loadingInterval)
      loadingInterval = null
    }
    isLoading.value = false
    if (event?.target) event.target.value = ''
  }
}

const retryScan = () => {
  if (lastUploadedFile.value) {
    handleFileUpload()
  } else {
    triggerFileInput()
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
 const payload = scannedItems.value.map((item) => ({
 wallet_id: selectedWalletId.value,
 category_id: item.category_id,
 amount: item.amount,
 type: 'EXPENSE',
 transaction_date: receiptDate.value,
 description: item.name
 }))

 await api.post('/transactions/batch', payload)

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
      <h1 class="text-2xl font-bold text-gray-800">
        Scan Struk Belanja
      </h1>
      <button
        v-if="step === 'review'"
        class="text-sm text-gray-500 hover:text-gray-700 flex items-center gap-1"
        @click="step = 'upload'"
      >
        <ArrowLeft class="w-4 h-4" /> Ulangi
      </button>
    </div>

    <!-- Loading Overlay -->
    <div
      v-if="isLoading"
      class="fixed inset-0 bg-white/90 backdrop-blur-sm z-50 flex flex-col items-center justify-center p-6 text-center"
    >
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4" />
      <p class="text-gray-800 font-semibold text-lg mb-1 animate-pulse">
        {{ step === 'upload' ? loadingProgressText : 'Menyimpan Transaksi...' }}
      </p>
      <p v-if="step === 'upload'" class="text-xs text-gray-500 mb-6 max-w-sm">
        Foto diproses sementara di memori tanpa disimpan ke disk server.
      </p>
      <button
        v-if="step === 'upload'"
        type="button"
        class="px-5 py-2.5 text-sm text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-xl transition-colors font-medium border border-gray-200"
        @click="cancelScan"
      >
        Batalkan Pemindaian
      </button>
    </div>

    <!-- STEP 1: UPLOAD -->
    <div
      v-if="step === 'upload'"
      class="flex flex-col gap-6"
    >
      <div
        class="border-2 border-dashed border-gray-300 rounded-2xl bg-gray-50 hover:bg-indigo-50 hover:border-indigo-300 transition-colors cursor-pointer h-64 flex flex-col items-center justify-center gap-4 group"
        @click="triggerFileInput"
      >
        <div
          class="p-4 bg-white rounded-full group-hover:scale-110 transition-transform duration-200"
        >
          <Camera class="w-8 h-8 text-indigo-500" />
        </div>
        <div class="text-center">
          <p class="text-lg font-medium text-gray-700">
            Tap to Scan Receipt
          </p>
          <p class="text-sm text-gray-400">
            or upload image from gallery
          </p>
        </div>
        <input
          id="receipt-upload"
          type="file"
          accept="image/*"
          class="hidden"
          @change="handleFileUpload"
        >
      </div>

      <!-- ERROR FEEDBACK CARD -->
      <div
        v-if="scanError"
        class="border border-red-200 bg-red-50/80 rounded-2xl p-5 flex flex-col gap-4 transition-all duration-300 shadow-sm"
      >
        <div class="flex items-start justify-between gap-3">
          <div class="flex items-start gap-3">
            <div class="p-2.5 bg-red-100 text-red-600 rounded-xl shrink-0 mt-0.5">
              <AlertTriangle class="w-6 h-6" />
            </div>
            <div>
              <h3 class="font-bold text-gray-900 text-base">
                {{ scanError.title }}
              </h3>
              <p class="text-sm text-gray-700 mt-1 leading-relaxed">
                {{ scanError.detail }}
              </p>
            </div>
          </div>
          <button
            type="button"
            class="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-red-100/50 transition-colors"
            title="Tutup pesan error"
            @click="scanError = null"
          >
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Tracking info bar -->
        <div class="flex flex-wrap items-center justify-between gap-2 pt-3 border-t border-red-200/60 text-xs text-gray-600">
          <div class="flex items-center gap-2">
            <span class="bg-red-100 text-red-800 font-mono px-2 py-0.5 rounded font-semibold text-[11px]">
              {{ scanError.code }}
            </span>
            <span v-if="scanError.requestId && scanError.requestId !== '-'" class="font-mono text-gray-500 text-[11px]">
              ID: {{ scanError.requestId }}
            </span>
          </div>
          <button
            v-if="scanError.requestId && scanError.requestId !== '-'"
            type="button"
            class="inline-flex items-center gap-1 font-medium text-indigo-600 hover:text-indigo-800 transition-colors"
            @click="copyRequestId"
          >
            <CheckCircle2 v-if="copiedRequestId" class="w-3.5 h-3.5 text-green-600" />
            <Copy v-else class="w-3.5 h-3.5" />
            <span>{{ copiedRequestId ? 'Tersalin!' : 'Salin ID Masalah' }}</span>
          </button>
        </div>

        <!-- Contextual Action Buttons -->
        <div class="flex flex-wrap items-center gap-2.5 pt-1">
          <button
            type="button"
            class="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-medium transition-colors flex items-center gap-2 shadow-sm"
            @click="triggerFileInput"
          >
            <Camera class="w-4 h-4" />
            <span>Ambil Foto Ulang</span>
          </button>

          <button
            type="button"
            class="px-4 py-2.5 bg-white hover:bg-gray-50 border border-gray-300 text-gray-700 rounded-xl text-sm font-medium transition-colors flex items-center gap-2 shadow-sm"
            @click="router.push('/transactions/add')"
          >
            <FileText class="w-4 h-4 text-gray-500" />
            <span>Input Transaksi Manual</span>
          </button>

          <button
            v-if="scanError.retryable && lastUploadedFile"
            type="button"
            class="px-4 py-2.5 bg-amber-100 hover:bg-amber-200 text-amber-900 rounded-xl text-sm font-medium transition-colors flex items-center gap-2"
            @click="retryScan"
          >
            <RefreshCw class="w-4 h-4" />
            <span>Coba Lagi</span>
          </button>
        </div>
      </div>

      <!-- Informative hint when no error -->
      <div
        v-else
        class="bg-blue-50 p-4 rounded-xl flex items-start gap-3 text-sm text-blue-700"
      >
        <AlertCircle class="w-5 h-5 shrink-0 mt-0.5" />
        <p>
          Pastikan foto struk terlihat jelas, terang, dan menampilkan detail item serta harga. AI
          akan otomatis mengekstrak data untuk Anda.
        </p>
      </div>
    </div>

    <!-- STEP 2: REVIEW -->
    <div
      v-else
      class="space-y-6"
    >
      <!-- General Settings -->
      <div class="bg-canvas border border-card-border p-5 rounded-2xl border border-gray-100 space-y-4">
        <h2 class="font-semibold text-gray-800 border-b pb-2 mb-2">
          Detail Transaksi
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">Tanggal</label>
            <input
              v-model="receiptDate"
              type="date"
              class="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            >
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-500 mb-1">Dompet Pembayaran</label>
            <!-- Custom Wallet Selector integration -->
            <div class="relative">
              <select
                v-model="selectedWalletId"
                class="w-full p-2 border border-gray-300 rounded-lg appearance-none bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option
                  v-for="w in wallets"
                  :key="w.id"
                  :value="w.id"
                >
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
          <h2 class="font-semibold text-gray-800">
            Daftar Item
          </h2>
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
              class="bg-canvas border border-card-border p-4 rounded-xl border border-gray-100 flex flex-col md:flex-row md:items-center gap-3 relative group"
            >
              <!-- Delete Button (Top Right on Mobile, Right on Desktop) -->
              <button
                class="absolute top-2 right-2 md:static md:order-last p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-colors"
                title="Hapus Item"
                @click="removeItem(index)"
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
                >
              </div>

              <!-- Amount Input -->
              <div class="w-full md:w-40">
                <label class="text-xs text-gray-400 md:hidden">Harga</label>
                <CurrencyInput
                  v-model="item.amount"
                  class="font-medium"
                />
              </div>

              <!-- Category Trigger -->
              <div class="w-full md:w-auto md:min-w-[150px]">
                <label class="text-xs text-gray-400 md:hidden mb-1 block">Kategori</label>
                <button
                  class="w-full flex items-center justify-between gap-2 px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg text-sm text-gray-700 transition-colors"
                  @click="openCategoryModal(index)"
                >
                  <span class="truncate">{{ getCategoryName(item.category_id) }}</span>
                  <!-- Simple indicator if selected -->
                  <div
                    v-if="item.category_id"
                    class="w-2 h-2 rounded-full bg-indigo-500"
                  />
                </button>
              </div>
            </div>
          </transition-group>
        </div>

        <!-- Add Item Button -->
        <button
          class="w-full py-3 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-indigo-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all flex items-center justify-center gap-2 font-medium"
          @click="addItem"
        >
          <Plus class="w-5 h-5" /> Tambah Item Manual
        </button>
      </div>

      <!-- Footer Summary -->
      <div
        class="fixed bottom-0 left-0 right-0 p-4 bg-white border-t border-gray-200 z-10 md:static md: md:border-0 md:bg-transparent md:p-0"
      >
        <div class="max-w-3xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div class="w-full md:w-auto">
            <p class="text-sm text-gray-500">
              Total Belanja
            </p>
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
              class="flex-1 md:flex-none px-6 py-3 rounded-xl border border-gray-300 text-gray-700 font-medium hover:bg-gray-50 transition-colors"
              @click="step = 'upload'"
            >
              Batal
            </button>
            <button
              :disabled="!isValidToSave || isLoading"
              class="flex-1 md:flex-none px-6 py-3 rounded-xl bg-primary text-on-primary rounded-pill px-6 py-3 font-medium text-sm"
              @click="saveTransactions"
            >
              <Check
                v-if="!isLoading"
                class="w-5 h-5"
              />
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
        class="bg-white w-full max-w-md rounded-2xl md:rounded-xl p-6 animate-in slide-in-from-bottom-10 md:slide-in-from-bottom-5 fade-in duration-200"
      >
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg font-bold text-gray-900">
            Pilih Kategori
          </h3>
          <button
            class="p-2 bg-gray-100 rounded-full hover:bg-gray-200"
            @click="showCategoryModal = false"
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
            current-type="EXPENSE"
            @update:model-value="updateItemCategory"
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
