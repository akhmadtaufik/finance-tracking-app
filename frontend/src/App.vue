<script setup>
import { ref } from "vue";
import { useAuthStore } from "./stores/auth";
import { useRouter, useRoute } from "vue-router";

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();

const sidebarExpanded = ref(false);

const menuItems = [
  {
    path: "/",
    name: "Dashboard",
    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />',
  },
  {
    path: "/transactions/add",
    name: "Add Transaction",
    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />',
  },
  {
    path: "/wallets",
    name: "Wallets",
    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />',
  },
  {
    path: "/categories",
    name: "Categories",
    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />',
  },
  {
    path: "/analysis",
    name: "Analysis",
    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />',
  },
  {
    path: "/report",
    name: "Report",
    icon: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />',
  },
];

const logout = () => {
  authStore.logout();
  router.push("/login");
};

const isActive = (path) => {
  if (path === "/") return route.path === "/";
  return route.path.startsWith(path);
};
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <!-- Sidebar -->
    <aside
      v-if="authStore.isAuthenticated"
      @mouseenter="sidebarExpanded = true"
      @mouseleave="sidebarExpanded = false"
      :class="[
        'fixed left-0 top-0 h-full bg-white shadow-lg z-40 transition-all duration-300 ease-in-out flex flex-col',
        sidebarExpanded ? 'w-64' : 'w-16',
      ]"
    >
      <!-- Logo -->
      <div class="h-16 flex items-center px-4 border-b border-gray-200">
        <div class="flex items-center">
          <div
            class="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center flex-shrink-0"
          >
            <svg
              class="w-5 h-5 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <span
            :class="[
              'ml-3 font-bold text-indigo-600 whitespace-nowrap transition-opacity duration-300',
              sidebarExpanded ? 'opacity-100' : 'opacity-0',
            ]"
          >
            Finance Tracker
          </span>
        </div>
      </div>

      <!-- Menu Items -->
      <nav class="flex-1 py-4">
        <ul class="space-y-1 px-2">
          <li v-for="item in menuItems" :key="item.path">
            <router-link
              :to="item.path"
              :class="[
                'flex items-center px-3 py-3 rounded-lg transition-colors duration-200',
                isActive(item.path)
                  ? 'bg-indigo-50 text-indigo-600'
                  : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
              ]"
            >
              <svg
                class="w-6 h-6 flex-shrink-0"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                v-html="item.icon"
              ></svg>
              <span
                :class="[
                  'ml-3 font-medium whitespace-nowrap transition-opacity duration-300',
                  sidebarExpanded ? 'opacity-100' : 'opacity-0',
                ]"
              >
                {{ item.name }}
              </span>
            </router-link>
          </li>
        </ul>
      </nav>

      <!-- User Section -->
      <div class="border-t border-gray-200 p-4">
        <div class="flex items-center">
          <div
            class="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center flex-shrink-0"
          >
            <svg
              class="w-5 h-5 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <div
            :class="[
              'ml-3 overflow-hidden transition-opacity duration-300',
              sidebarExpanded ? 'opacity-100' : 'opacity-0',
            ]"
          >
            <p class="text-sm font-medium text-gray-700 truncate">
              {{ authStore.user?.username }}
            </p>
            <p class="text-xs text-gray-500 truncate">
              {{ authStore.user?.email }}
            </p>
          </div>
        </div>

        <button
          @click="logout"
          :class="[
            'mt-4 w-full flex items-center px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 transition-colors duration-200',
          ]"
        >
          <svg
            class="w-6 h-6 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
            />
          </svg>
          <span
            :class="[
              'ml-3 font-medium whitespace-nowrap transition-opacity duration-300',
              sidebarExpanded ? 'opacity-100' : 'opacity-0',
            ]"
          >
            Logout
          </span>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main
      :class="[
        'transition-all duration-300',
        authStore.isAuthenticated ? 'ml-16' : '',
      ]"
    >
      <router-view />
    </main>
  </div>
</template>
