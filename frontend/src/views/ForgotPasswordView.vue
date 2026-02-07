<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '../api'
import { useUIStore } from '../stores/ui'

const router = useRouter()
const uiStore = useUIStore()

const email = ref('')
const loading = ref(false)
const submitted = ref(false)

const requestReset = async () => {
  if (!email.value.trim()) {
    uiStore.showToast({ message: 'Please enter your email', type: 'error' })
    return
  }
  
  loading.value = true
  try {
    await api.post('/auth/forgot-password', { email: email.value })
    submitted.value = true
    uiStore.showToast({ 
      message: 'If that email exists, we sent a reset link', 
      type: 'success' 
    })
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to send reset email'
    uiStore.showToast({ message, type: 'error' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">Forgot Password</h1>
        <p class="text-gray-600 mt-2">
          Enter your email and we'll send you a reset link
        </p>
      </div>
      
      <div v-if="!submitted">
        <form @submit.prevent="requestReset" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Email Address
            </label>
            <input
              v-model="email"
              type="email"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter your email"
            />
          </div>
          
          <button
            type="submit"
            :disabled="loading"
            class="w-full py-2 px-4 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {{ loading ? 'Sending...' : 'Send Reset Link' }}
          </button>
        </form>
      </div>
      
      <div v-else class="text-center">
        <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
          <h3 class="font-semibold text-green-800 mb-2">Check Your Email</h3>
          <p class="text-green-700 text-sm">
            If an account exists for {{ email }}, you will receive a password reset link shortly.
          </p>
        </div>
        
        <button
          @click="submitted = false; email = ''"
          class="text-indigo-600 hover:text-indigo-800 font-medium"
        >
          Try a different email
        </button>
      </div>
      
      <div class="mt-6 text-center">
        <router-link to="/login" class="text-indigo-600 hover:text-indigo-800 font-medium">
          ← Back to Login
        </router-link>
      </div>
    </div>
  </div>
</template>
