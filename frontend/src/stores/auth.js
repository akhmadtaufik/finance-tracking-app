import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email, password) {
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)

    const response = await api.post('/auth/token', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
    
    token.value = response.data.access_token
    localStorage.setItem('token', token.value)
    
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
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  if (token.value) {
    fetchUser()
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    register,
    fetchUser,
    logout
  }
})
