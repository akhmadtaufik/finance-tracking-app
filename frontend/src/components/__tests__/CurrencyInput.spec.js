import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CurrencyInput from '../CurrencyInput.vue'

describe('CurrencyInput', () => {
  it('renders with Rp prefix', () => {
    const wrapper = mount(CurrencyInput, {
      props: { modelValue: 0 }
    })
    
    expect(wrapper.text()).toContain('Rp')
  })

  it('formats initial value correctly', () => {
    const wrapper = mount(CurrencyInput, {
      props: { modelValue: 500000 }
    })
    
    const input = wrapper.find('input')
    expect(input.element.value).toBe('500.000')
  })

  it('formats large numbers with thousand separators', () => {
    const wrapper = mount(CurrencyInput, {
      props: { modelValue: 1500000 }
    })
    
    const input = wrapper.find('input')
    expect(input.element.value).toBe('1.500.000')
  })

  it('emits update:modelValue on input', async () => {
    const wrapper = mount(CurrencyInput, {
      props: { modelValue: 0 }
    })
    
    const input = wrapper.find('input')
    await input.setValue('250000')
    
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    const emittedValue = wrapper.emitted('update:modelValue')[0][0]
    expect(emittedValue).toBe(250000)
  })

  it('strips non-numeric characters', async () => {
    const wrapper = mount(CurrencyInput, {
      props: { modelValue: 0 }
    })
    
    const input = wrapper.find('input')
    await input.setValue('abc123def456')
    
    const emittedValue = wrapper.emitted('update:modelValue').pop()[0]
    expect(emittedValue).toBe(123456)
  })

  it('handles zero value', () => {
    const wrapper = mount(CurrencyInput, {
      props: { modelValue: 0 }
    })
    
    const input = wrapper.find('input')
    expect(input.element.value).toBe('0')
  })

  it('applies placeholder when provided', () => {
    const wrapper = mount(CurrencyInput, {
      props: {
        modelValue: 0,
        placeholder: 'Enter amount'
      }
    })
    
    const input = wrapper.find('input')
    expect(input.attributes('placeholder')).toBe('Enter amount')
  })

  it('updates display when prop changes', async () => {
    const wrapper = mount(CurrencyInput, {
      props: { modelValue: 100000 }
    })
    
    expect(wrapper.find('input').element.value).toBe('100.000')
    
    await wrapper.setProps({ modelValue: 999999 })
    
    expect(wrapper.find('input').element.value).toBe('999.999')
  })
})
