<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import { useUIStore } from '../stores/ui'

const authStore = useAuthStore()
const uiStore = useUIStore()

// General Info
const username = ref('')
const profileLoading = ref(false)

// Password
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const passwordLoading = ref(false)

const passwordMatch = computed(() => {
  if (!confirmPassword.value) return true
  return newPassword.value === confirmPassword.value
})

const canSubmitPassword = computed(() => {
  return currentPassword.value && 
         newPassword.value && 
         confirmPassword.value && 
         passwordMatch.value &&
         newPassword.value.length >= 8
})

onMounted(() => {
  if (authStore.user) {
    username.value = authStore.user.username
  }
})

const updateProfile = async () => {
  if (!username.value.trim()) {
    uiStore.showToast({ message: 'Username is required', type: 'error' })
    return
  }
  
  profileLoading.value = true
  try {
    await authStore.updateProfile(username.value)
    uiStore.showToast({ message: 'Profile updated successfully', type: 'success' })
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to update profile'
    uiStore.showToast({ message, type: 'error' })
  } finally {
    profileLoading.value = false
  }
}

const updatePassword = async () => {
  if (!passwordMatch.value) {
    uiStore.showToast({ message: 'Passwords do not match', type: 'error' })
    return
  }
  
  passwordLoading.value = true
  try {
    await authStore.changePassword(currentPassword.value, newPassword.value)
    uiStore.showToast({ message: 'Password updated successfully', type: 'success' })
    // Clear form
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  } catch (error) {
    const message = error.response?.data?.detail || 'Failed to update password'
    uiStore.showToast({ message, type: 'error' })
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <div class="max-w-2xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold text-gray-800 mb-8">Profile Settings</h1>
    
    <!-- General Information Card -->
    <div class="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">General Information</h2>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Email</label>
          <input
            type="email"
            :value="authStore.user?.email"
            disabled
            class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100 text-gray-500 cursor-not-allowed"
          />
          <p class="text-xs text-gray-500 mt-1">Email cannot be changed</p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input
            v-model="username"
            type="text"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Enter username"
          />
        </div>
      </div>
      
      <div class="mt-6">
        <button
          @click="updateProfile"
          :disabled="profileLoading"
          class="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ profileLoading ? 'Saving...' : 'Save Changes' }}
        </button>
      </div>
    </div>
    
    <!-- Security Card -->
    <div class="bg-white rounded-lg shadow-md p-6">
      <h2 class="text-lg font-semibold text-gray-800 mb-4">Security</h2>
      <p class="text-sm text-gray-600 mb-4">Change your password to keep your account secure.</p>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Current Password</label>
          <input
            v-model="currentPassword"
            type="password"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Enter current password"
          />
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">New Password</label>
          <input
            v-model="newPassword"
            type="password"
            class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Enter new password"
          />
          <p class="text-xs text-gray-500 mt-1">
            Min 8 chars, uppercase, lowercase, number, and special character
          </p>
        </div>
        
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Confirm New Password</label>
          <input
            v-model="confirmPassword"
            type="password"
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
      </div>
      
      <div class="mt-6">
        <button
          @click="updatePassword"
          :disabled="passwordLoading || !canSubmitPassword"
          class="px-4 py-2 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ passwordLoading ? 'Updating...' : 'Update Password' }}
        </button>
      </div>
    </div>
  </div>
</template>
