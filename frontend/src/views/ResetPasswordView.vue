<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '../api'
import { useUIStore } from '../stores/ui'

const router = useRouter()
const route = useRoute()
const uiStore = useUIStore()

const token = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const success = ref(false)
const tokenError = ref(false)

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) {
    tokenError.value = true
  }
})

const passwordMatch = computed(() => {
  if (!confirmPassword.value) return true
  return newPassword.value === confirmPassword.value
})

const canSubmit = computed(() => {
  return newPassword.value && 
         confirmPassword.value && 
         passwordMatch.value &&
         newPassword.value.length >= 8
})

const resetPassword = async () => {
  if (!passwordMatch.value) {
    uiStore.showToast({ message: 'Passwords do not match', type: 'error' })
    return
  }
  
  loading.value = true
  try {
    await api.post('/auth/reset-password', { 
      token: token.value, 
      new_password: newPassword.value 
    })
    success.value = true
    uiStore.showToast({ message: 'Password reset successful!', type: 'success' })
    
    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to reset password'
    uiStore.showToast({ message, type: 'error' })
    
    if (error.response?.status === 400) {
      tokenError.value = true
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-100 px-4">
    <div class="max-w-md w-full bg-white rounded-lg shadow-md p-8">
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-800">Reset Password</h1>
        <p class="text-gray-600 mt-2">Enter your new password</p>
      </div>
      
      <!-- Token Error State -->
      <div v-if="tokenError" class="text-center">
        <div class="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">
          <svg class="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 class="font-semibold text-red-800 mb-2">Invalid or Expired Link</h3>
          <p class="text-red-700 text-sm">
            This password reset link is invalid or has expired. Please request a new one.
          </p>
        </div>
        <router-link 
          to="/forgot-password" 
          class="inline-block px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
        >
          Request New Link
        </router-link>
      </div>
      
      <!-- Success State -->
      <div v-else-if="success" class="text-center">
        <div class="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
          <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
          <h3 class="font-semibold text-green-800 mb-2">Password Reset!</h3>
          <p class="text-green-700 text-sm">
            Your password has been reset. Redirecting to login...
          </p>
        </div>
      </div>
      
      <!-- Reset Form -->
      <div v-else>
        <form @submit.prevent="resetPassword" class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              New Password
            </label>
            <input
              v-model="newPassword"
              type="password"
              required
              class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              placeholder="Enter new password"
            />
            <p class="text-xs text-gray-500 mt-1">
              Min 8 chars, uppercase, lowercase, number, and special character
            </p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">
              Confirm Password
            </label>
            <input
              v-model="confirmPassword"
              type="password"
              required
              :class="[
                'w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2',
                !passwordMatch ? 'border-red-500 focus:ring-red-500' : 'border-gray-300 focus:ring-indigo-500'
              ]"
              placeholder="Confirm new password"
            />
            <p v-if="!passwordMatch" class="text-xs text-red-500 mt-1">
              Passwords do not match
            </p>
          </div>
          
          <button
            type="submit"
            :disabled="loading || !canSubmit"
            class="w-full py-2 px-4 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {{ loading ? 'Resetting...' : 'Reset Password' }}
          </button>
        </form>
      </div>
      
      <div v-if="!tokenError && !success" class="mt-6 text-center">
        <router-link to="/login" class="text-indigo-600 hover:text-indigo-800 font-medium">
          ← Back to Login
        </router-link>
      </div>
    </div>
  </div>
</template>
