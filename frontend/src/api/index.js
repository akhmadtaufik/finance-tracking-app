import axios from 'axios'

axios.defaults.withCredentials = true
const existingToken = typeof window !== 'undefined' ? localStorage.getItem('token') : null
if (existingToken) {
  axios.defaults.headers.common.Authorization = `Bearer ${existingToken}`
}

// Use /api for Docker (Nginx proxies to backend)
// Use http://localhost:8000 for local development
const baseURL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true  // PENTING: Agar cookie refresh_token terkirim otomatis
})

// State untuk mencegah multiple refresh request
let isRefreshing = false
let failedQueue = []

// Proses antrian request yang gagal setelah refresh berhasil
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Request Interceptor - Tambahkan access token ke header
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response Interceptor - Handle 401 dan auto refresh token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // Jika error 401 dan belum pernah retry
    if (error.response?.status === 401 && !originalRequest._retry) {
      
      // Jika ini adalah request ke /auth/refresh yang gagal, langsung redirect
      if (originalRequest.url?.includes('/auth/refresh')) {
        localStorage.removeItem('token')
        window.location.href = '/login'
        return Promise.reject(error)
      }
      
      // Jika sedang proses refresh, masukkan request ke antrian
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch(err => Promise.reject(err))
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      try {
        // Panggil refresh endpoint - cookie terkirim otomatis
        const { data } = await api.post('/auth/refresh')
        
        // Simpan token baru
        const newToken = data.access_token
        localStorage.setItem('token', newToken)
        api.defaults.headers.common.Authorization = `Bearer ${newToken}`
        axios.defaults.headers.common.Authorization = `Bearer ${newToken}`
        
        // Proses antrian request yang menunggu
        processQueue(null, newToken)
        
        // Retry request original dengan token baru
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
        
      } catch (refreshError) {
        // Refresh gagal - hapus token dan redirect ke login
        processQueue(refreshError, null)
        localStorage.removeItem('token')
        delete api.defaults.headers.common.Authorization
        delete axios.defaults.headers.common.Authorization
        window.location.href = '/login'
        return Promise.reject(refreshError)
        
      } finally {
        isRefreshing = false
      }
    }
    
    return Promise.reject(error)
  }
)

export default api
