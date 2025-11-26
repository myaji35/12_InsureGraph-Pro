import { create } from 'zustand'
import type { Customer, Insurance, PortfolioAnalysis, PaginatedResponse } from '@/types'
import { apiClient } from '@/lib/api-client'

interface CustomerState {
  customers: Customer[]
  currentCustomer: Customer | null
  customerInsurances: Insurance[]
  portfolioAnalysis: PortfolioAnalysis | null
  pagination: {
    page: number
    page_size: number
    total_pages: number
    total_items: number
    has_next: boolean
    has_prev: boolean
  } | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchCustomers: (params?: {
    search?: string
    page?: number
    page_size?: number
  }) => Promise<void>
  fetchCustomer: (customerId: string) => Promise<void>
  createCustomer: (data: Omit<Customer, 'customer_id' | 'created_at' | 'updated_at' | 'created_by_user_id'>) => Promise<Customer>
  updateCustomer: (customerId: string, data: Partial<Customer>) => Promise<void>
  deleteCustomer: (customerId: string) => Promise<void>
  fetchCustomerInsurances: (customerId: string) => Promise<void>
  fetchPortfolioAnalysis: (customerId: string) => Promise<void>
  clearError: () => void
  setCurrentCustomer: (customer: Customer | null) => void
}

export const useCustomerStore = create<CustomerState>()((set, get) => ({
  customers: [],
  currentCustomer: null,
  customerInsurances: [],
  portfolioAnalysis: null,
  pagination: null,
  isLoading: false,
  error: null,

  fetchCustomers: async (params) => {
    try {
      set({ isLoading: true, error: null })

      const response = await apiClient.getCustomers(params)

      set({
        customers: response.items,
        pagination: {
          page: response.page,
          page_size: response.page_size,
          total_pages: response.total_pages,
          total_items: response.total_items,
          has_next: response.has_next,
          has_prev: response.has_prev,
        },
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to fetch customers'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  fetchCustomer: async (customerId: string) => {
    try {
      set({ isLoading: true, error: null })

      const customer = await apiClient.getCustomer(customerId)

      set({
        currentCustomer: customer,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to fetch customer'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  createCustomer: async (data) => {
    try {
      set({ isLoading: true, error: null })

      const customer = await apiClient.createCustomer(data)

      // Add to list
      set((state) => ({
        customers: [customer, ...state.customers],
        isLoading: false,
      }))

      return customer
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to create customer'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  updateCustomer: async (customerId: string, data) => {
    try {
      set({ isLoading: true, error: null })

      const updatedCustomer = await apiClient.updateCustomer(customerId, data)

      // Update in list
      set((state) => ({
        customers: state.customers.map((c) =>
          c.customer_id === customerId ? updatedCustomer : c
        ),
        currentCustomer:
          state.currentCustomer?.customer_id === customerId
            ? updatedCustomer
            : state.currentCustomer,
        isLoading: false,
      }))
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to update customer'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  deleteCustomer: async (customerId: string) => {
    try {
      set({ isLoading: true, error: null })

      await apiClient.deleteCustomer(customerId)

      // Remove from list
      set((state) => ({
        customers: state.customers.filter((c) => c.customer_id !== customerId),
        isLoading: false,
      }))
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to delete customer'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  fetchCustomerInsurances: async (customerId: string) => {
    try {
      set({ isLoading: true, error: null })

      const insurances = await apiClient.getCustomerInsurances(customerId)

      set({
        customerInsurances: insurances,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to fetch insurances'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  fetchPortfolioAnalysis: async (customerId: string) => {
    try {
      set({ isLoading: true, error: null })

      const analysis = await apiClient.getPortfolioAnalysis(customerId)

      set({
        portfolioAnalysis: analysis,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to fetch portfolio analysis'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  clearError: () => {
    set({ error: null })
  },

  setCurrentCustomer: (customer: Customer | null) => {
    set({ currentCustomer: customer })
  },
}))
