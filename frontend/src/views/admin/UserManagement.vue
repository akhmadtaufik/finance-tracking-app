<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api'

const users = ref([])
const loading = ref(true)
const actionLoading = ref(null)

const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await api.get('/admin/users')
    users.value = response.data
  } catch (error) {
    console.error('Failed to fetch users:', error)
  } finally {
    loading.value = false
  }
}

const toggleUserStatus = async (user) => {
  actionLoading.value = user.id
  try {
    await api.patch(`/admin/users/${user.id}/toggle-status`)
    user.is_active = !user.is_active
  } catch (error) {
    alert(error.response?.data?.detail || 'Failed to update user status')
  } finally {
    actionLoading.value = null
  }
}

const formatDate = (dateStr) => {
  return new Date(dateStr).toLocaleDateString('id-ID', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="p-8">
    <div class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold text-gray-800">User Management</h1>
      <span class="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm">
        {{ users.length }} users
      </span>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div v-if="loading" class="flex items-center justify-center h-64">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-red-600"></div>
      </div>

      <table v-else class="w-full">
        <thead class="bg-gray-50 border-b border-gray-100">
          <tr>
            <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
            <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
            <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Stats</th>
            <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Joined</th>
            <th class="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            <th class="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr v-for="user in users" :key="user.id" class="hover:bg-gray-50">
            <td class="px-6 py-4">
              <div class="flex items-center">
                <div class="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold"
                     :class="user.is_superuser ? 'bg-red-600' : 'bg-indigo-600'">
                  {{ user.username.charAt(0).toUpperCase() }}
                </div>
                <div class="ml-4">
                  <p class="font-medium text-gray-800">{{ user.username }}</p>
                  <p class="text-sm text-gray-500">{{ user.email }}</p>
                </div>
              </div>
            </td>
            <td class="px-6 py-4">
              <span v-if="user.is_superuser" class="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-full">
                Admin
              </span>
              <span v-else class="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-700 rounded-full">
                User
              </span>
            </td>
            <td class="px-6 py-4">
              <div class="text-sm">
                <p class="text-gray-600">{{ user.wallet_count }} wallets</p>
                <p class="text-gray-500">{{ user.transaction_count }} transactions</p>
              </div>
            </td>
            <td class="px-6 py-4 text-sm text-gray-600">
              {{ formatDate(user.created_at) }}
            </td>
            <td class="px-6 py-4">
              <span v-if="user.is_active" class="px-2 py-1 text-xs font-medium bg-green-100 text-green-700 rounded-full">
                Active
              </span>
              <span v-else class="px-2 py-1 text-xs font-medium bg-red-100 text-red-700 rounded-full">
                Banned
              </span>
            </td>
            <td class="px-6 py-4 text-right">
              <button
                v-if="!user.is_superuser"
                @click="toggleUserStatus(user)"
                :disabled="actionLoading === user.id"
                :class="[
                  'px-3 py-1.5 text-sm font-medium rounded-lg transition-colors',
                  user.is_active
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-green-100 text-green-700 hover:bg-green-200',
                  actionLoading === user.id ? 'opacity-50 cursor-not-allowed' : ''
                ]"
              >
                <span v-if="actionLoading === user.id">...</span>
                <span v-else>{{ user.is_active ? 'Ban' : 'Unban' }}</span>
              </button>
              <span v-else class="text-sm text-gray-400">-</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!loading && users.length === 0" class="p-12 text-center text-gray-500">
        No users found
      </div>
    </div>
  </div>
</template>
