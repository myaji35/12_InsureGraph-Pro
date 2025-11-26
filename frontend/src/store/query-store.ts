import { create } from 'zustand'
import type { QueryRequest, QueryResponse } from '@/types'
import { apiClient } from '@/lib/api-client'

interface QueryHistoryItem extends QueryResponse {
  timestamp: string
}

interface QueryState {
  currentQuery: QueryResponse | null
  queryHistory: QueryHistoryItem[]
  isLoading: boolean
  error: string | null

  // Actions
  executeQuery: (data: QueryRequest) => Promise<QueryResponse>
  getQueryStatus: (queryId: string) => Promise<QueryResponse>
  clearError: () => void
  clearCurrentQuery: () => void
  addToHistory: (query: QueryResponse) => void
}

export const useQueryStore = create<QueryState>()((set, get) => ({
  currentQuery: null,
  queryHistory: [],
  isLoading: false,
  error: null,

  executeQuery: async (data: QueryRequest) => {
    try {
      set({ isLoading: true, error: null })

      const response = await apiClient.executeQuery(data)

      set({
        currentQuery: response,
        isLoading: false,
      })

      // Add to history
      get().addToHistory(response)

      return response
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Query execution failed'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  getQueryStatus: async (queryId: string) => {
    try {
      set({ isLoading: true, error: null })

      const response = await apiClient.getQueryStatus(queryId)

      set({
        currentQuery: response,
        isLoading: false,
      })

      return response
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to get query status'

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

  clearCurrentQuery: () => {
    set({ currentQuery: null })
  },

  addToHistory: (query: QueryResponse) => {
    const historyItem: QueryHistoryItem = {
      ...query,
      timestamp: new Date().toISOString(),
    }

    set((state) => ({
      queryHistory: [historyItem, ...state.queryHistory].slice(0, 50), // Keep last 50
    }))
  },
}))
