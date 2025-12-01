<script setup>
import { useAuthStore } from './stores/auth'
import { useRouter } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()

const logout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <nav v-if="authStore.isAuthenticated" class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <div class="flex items-center">
            <router-link to="/" class="text-xl font-bold text-indigo-600">
              Finance Tracker
            </router-link>
            <div class="ml-10 flex space-x-4">
              <router-link 
                to="/" 
                class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-indigo-600"
              >
                Dashboard
              </router-link>
              <router-link 
                to="/transactions/add" 
                class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-indigo-600"
              >
                Add Transaction
              </router-link>
              <router-link 
                to="/wallets" 
                class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-indigo-600"
              >
                Wallets
              </router-link>
              <router-link 
                to="/categories" 
                class="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-indigo-600"
              >
                Categories
              </router-link>
            </div>
          </div>
          <div class="flex items-center">
            <span class="text-gray-600 mr-4">{{ authStore.user?.username }}</span>
            <button 
              @click="logout"
              class="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>
