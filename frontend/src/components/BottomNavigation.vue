<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()

const isActive = (path) => {
  if (path === "/") return route.path === "/";
  return route.path.startsWith(path);
}
</script>

<template>
  <div class="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
    <div class="flex justify-around items-center h-16 px-2">
      <!-- Dashboard -->
      <router-link
        to="/"
        class="flex flex-col items-center justify-center w-16 h-full space-y-1"
        :class="isActive('/') ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
        <span class="text-[10px] font-medium">Home</span>
      </router-link>

      <!-- Wallets -->
      <router-link
        to="/wallets"
        class="flex flex-col items-center justify-center w-16 h-full space-y-1"
        :class="isActive('/wallets') ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
        <span class="text-[10px] font-medium">Wallets</span>
      </router-link>

      <!-- FAB Add Transaction -->
      <router-link
        to="/transactions/add"
        class="flex items-center justify-center -mt-8"
      >
        <div class="bg-indigo-600 text-white rounded-full w-14 h-14 flex items-center justify-center border-4 border-gray-50 shadow-lg hover:bg-indigo-700 transition-colors">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
        </div>
      </router-link>

      <!-- Analysis -->
      <router-link
        to="/analysis"
        class="flex flex-col items-center justify-center w-16 h-full space-y-1"
        :class="isActive('/analysis') ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <span class="text-[10px] font-medium">Analysis</span>
      </router-link>

      <!-- Categories (as Menu) -->
      <router-link
        to="/categories"
        class="flex flex-col items-center justify-center w-16 h-full space-y-1"
        :class="isActive('/categories') ? 'text-indigo-600' : 'text-gray-500 hover:text-gray-900'"
      >
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
        <span class="text-[10px] font-medium">Menu</span>
      </router-link>
    </div>
  </div>
</template>
