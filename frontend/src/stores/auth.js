import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(null)

  function setToken(newToken) {
    token.value = newToken
  }

  function clearToken() {
    token.value = null
  }
  const user = ref(null)
  const sessions = ref([])

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_superuser || false)

  async function login(email, password) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    
    token.value = response.data.access_token
    api.defaults.headers.common.Authorization = `Bearer ${token.value}`
    axios.defaults.headers.common.Authorization = `Bearer ${token.value}`
    
    await fetchUser()
    return response.data
  }

  async function register(email, username, password) {
    const response = await api.post('/auth/register', {
      email,
      username,
      password
    })
    return response.data
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      // Jika gagal fetch user, biarkan interceptor handle refresh
      // Jangan langsung logout di sini
      console.error('Failed to fetch user:', error)
    }
  }

  async function logout() {
    try {
      // Panggil endpoint logout untuk revoke refresh token
      await api.post('/auth/logout')
    } catch (error) {
      // Tetap lanjut logout meskipun API gagal
      console.error('Logout API error:', error)
    } finally {
      // Bersihkan state lokal
      token.value = null
      user.value = null
      sessions.value = []
      delete api.defaults.headers.common.Authorization
      delete axios.defaults.headers.common.Authorization
    }
  }

  async function logoutAllDevices() {
    try {
      const response = await api.post('/auth/logout-all')
      // Bersihkan state lokal
      token.value = null
      user.value = null
      sessions.value = []
      delete api.defaults.headers.common.Authorization
      delete axios.defaults.headers.common.Authorization
      return response.data
    } catch (error) {
      console.error('Logout all devices error:', error)
      throw error
    }
  }

  async function fetchSessions() {
    try {
      const response = await api.get('/auth/sessions')
      sessions.value = response.data.sessions
      return sessions.value
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
      throw error
    }
  }

  async function updateProfile(username) {
    const response = await api.put('/users/profile', { username })
    user.value = response.data
    return response.data
  }

  async function changePassword(currentPassword, newPassword) {
    const response = await api.put('/users/password', {
      current_password: currentPassword,
      new_password: newPassword
    })
    return response.data
  }

  async function initialize() {
    try {
      const response = await api.post('/auth/refresh')
      token.value = response.data.access_token
      api.defaults.headers.common.Authorization = `Bearer ${token.value}`
      axios.defaults.headers.common.Authorization = `Bearer ${token.value}`
      await fetchUser()
    } catch (error) {
      console.log('No active session on initialize')
    }
  }

  return {
    token,
    user,
    sessions,
    isAuthenticated,
    isAdmin,
    login,
    register,
    fetchUser,
    logout,
    logoutAllDevices,
    fetchSessions,
    updateProfile,
    changePassword,
    setToken,
    clearToken,
    initialize
  }
})
