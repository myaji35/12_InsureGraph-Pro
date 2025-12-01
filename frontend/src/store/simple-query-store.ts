/**
 * Simple Query Store
 *
 * Zustand store for Simple Query API (Stories 2.1-2.6)
 */

import { create } from 'zustand'
import type {
  SimpleQueryRequest,
  SimpleQueryResponse,
} from '@/types/simple-query'
import { simpleQueryAPI } from '@/lib/simple-query-api'

interface QueryHistoryItem extends SimpleQueryResponse {
  timestamp: string
  request: SimpleQueryRequest
}

interface SimpleQueryState {
  currentResponse: SimpleQueryResponse | null
  queryHistory: QueryHistoryItem[]
  isLoading: boolean
  error: string | null

  // Engine health
  isNeo4jConnected: boolean
  isLLMAvailable: boolean

  // Actions
  executeQuery: (request: SimpleQueryRequest) => Promise<SimpleQueryResponse>
  checkHealth: () => Promise<void>
  clearError: () => void
  clearCurrentResponse: () => void
  loadFromHistory: (item: QueryHistoryItem) => void
}

export const useSimpleQueryStore = create<SimpleQueryState>()((set, get) => ({
  currentResponse: null,
  queryHistory: [],
  isLoading: false,
  error: null,
  isNeo4jConnected: false,
  isLLMAvailable: false,

  executeQuery: async (request: SimpleQueryRequest) => {
    try {
      set({ isLoading: true, error: null })

      const response = await simpleQueryAPI.executeQuery(request)

      // Add to history
      const historyItem: QueryHistoryItem = {
        ...response,
        timestamp: new Date().toISOString(),
        request,
      }

      set((state) => ({
        currentResponse: response,
        isLoading: false,
        queryHistory: [historyItem, ...state.queryHistory].slice(0, 50), // Keep last 50
      }))

      return response
    } catch (error: any) {
      const errorMessage = error.message || 'Query execution failed'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  checkHealth: async () => {
    try {
      const health = await simpleQueryAPI.getHealth()

      set({
        isNeo4jConnected: health.neo4j_connected,
        isLLMAvailable: health.llm_available,
      })
    } catch (error) {
      console.error('Health check failed:', error)
      set({
        isNeo4jConnected: false,
        isLLMAvailable: false,
      })
    }
  },

  clearError: () => {
    set({ error: null })
  },

  clearCurrentResponse: () => {
    set({ currentResponse: null })
  },

  loadFromHistory: (item: QueryHistoryItem) => {
    set({ currentResponse: item })
  },
}))
