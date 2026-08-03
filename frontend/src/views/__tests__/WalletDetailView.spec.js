import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import WalletDetailView from '../WalletDetailView.vue'
import api from '../../api'

vi.mock('../../api', () => ({
  default: {
    get: vi.fn()
  }
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({
    params: { id: '10' }
  }),
  useRouter: () => ({
    push: vi.fn()
  })
}))

describe('WalletDetailView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    api.get.mockImplementation((url) => {
      if (url === '/wallets') {
        return Promise.resolve({ data: [{ id: 10, name: 'Main Wallet', balance: 500000 }] })
      }
      if (url === '/categories') {
        return Promise.resolve({ data: [{ id: 1, name: 'Food' }] })
      }
      if (url === '/transactions') {
        return Promise.resolve({
          data: [
            {
              id: 101,
              user_id: 1,
              wallet_id: 10,
              category_id: 1,
              amount: 25000,
              type: 'EXPENSE',
              transaction_date: '2026-08-03',
              description: 'Lunch',
              category_name: 'Food',
              wallet_name: 'Main Wallet'
            }
          ]
        })
      }
      if (url === '/transactions/export/pdf') {
        return Promise.resolve({
          data: new Blob(['%PDF-1.4 mock data'], { type: 'application/pdf' })
        })
      }
      return Promise.resolve({ data: [] })
    })
  })

  it('triggers search API call with debounced query string and skip 0', async () => {
    vi.useFakeTimers()
    const wrapper = mount(WalletDetailView, {
      global: {
        stubs: {
          'phantom-ui': { template: '<div><slot /></div>' },
          'EditTransactionModal': true
        }
      }
    })

    const searchInput = wrapper.find('#search-input')
    await searchInput.setValue('Lunch')

    vi.advanceTimersByTime(350)
    vi.useRealTimers()

    expect(api.get).toHaveBeenCalledWith(
      '/transactions',
      expect.objectContaining({
        params: expect.objectContaining({
          wallet_id: '10',
          search: 'Lunch',
          skip: 0
        })
      })
    )
  })

  it('triggers export PDF with responseType blob when export button clicked', async () => {
    const wrapper = mount(WalletDetailView, {
      global: {
        stubs: {
          'phantom-ui': { template: '<div><slot /></div>' },
          'EditTransactionModal': true
        }
      }
    })

    const buttons = wrapper.findAll('button')
    const exportButton = buttons.find(b => b.text().includes('Export PDF'))
    expect(exportButton).toBeTruthy()

    await exportButton.trigger('click')

    expect(api.get).toHaveBeenCalledWith(
      '/transactions/export/pdf',
      expect.objectContaining({
        params: expect.objectContaining({ wallet_id: '10' }),
        responseType: 'blob'
      })
    )
  })
})
