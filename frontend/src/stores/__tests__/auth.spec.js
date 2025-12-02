import { describe, it, beforeEach, expect, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../auth'
import api from '../../api'
import axios from 'axios'

vi.mock('../../api', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn(),
    defaults: { headers: { common: {} } }
  }
}))

vi.mock('axios', () => ({
  default: {
    defaults: { headers: { common: {} } }
  }
}))

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    api.post.mockReset()
    api.get.mockReset()
  })

  it('stores token and user data after login', async () => {
    api.post.mockResolvedValueOnce({ data: { access_token: 'token-123' } })
    api.get.mockResolvedValueOnce({ data: { email: 'test@example.com', is_superuser: false } })

    const authStore = useAuthStore()
    await authStore.login('test@example.com', 'secret')

    expect(api.post).toHaveBeenCalledWith(
      '/auth/token',
      expect.any(URLSearchParams),
      expect.objectContaining({ headers: { 'Content-Type': 'application/x-www-form-urlencoded' } })
    )
    expect(localStorage.getItem('token')).toBe('token-123')
    expect(authStore.user.email).toBe('test@example.com')
  })
})
