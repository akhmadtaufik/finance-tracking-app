import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SummaryCard from '../SummaryCard.vue'

describe('SummaryCard', () => {
  it('renders title and formatted amount', () => {
    const wrapper = mount(SummaryCard, {
      props: {
        title: 'Total Income',
        amount: 1500000,
        variant: 'income'
      }
    })

    expect(wrapper.get('[data-testid="summary-card"]').text()).toContain('Total Income')
    expect(wrapper.text()).toContain('Rp')
  })

  it('applies variant classes for expense', () => {
    const wrapper = mount(SummaryCard, {
      props: {
        title: 'Total Expense',
        amount: 750000,
        variant: 'expense'
      }
    })

    const amount = wrapper.get('p.text-2xl')
    expect(amount.classes()).toContain('text-red-600')
  })
})
