import { create } from 'zustand'
import type { GraphData, GraphNode, NodeType } from '@/types'
import { apiClient } from '@/lib/api-client'

interface GraphFilters {
  documentIds: string[]
  nodeTypes: NodeType[]
  searchQuery: string
}

interface GraphState {
  graphData: GraphData | null
  selectedNode: GraphNode | null
  filters: GraphFilters
  isLoading: boolean
  error: string | null

  // Actions
  fetchGraph: (params?: {
    document_ids?: string[]
    node_types?: string[]
    max_nodes?: number
  }) => Promise<void>
  fetchNodeDetails: (nodeId: string) => Promise<void>
  setSelectedNode: (node: GraphNode | null) => void
  updateFilters: (filters: Partial<GraphFilters>) => void
  clearFilters: () => void
  clearError: () => void
}

const defaultFilters: GraphFilters = {
  documentIds: [],
  nodeTypes: [],
  searchQuery: '',
}

export const useGraphStore = create<GraphState>()((set, get) => ({
  graphData: null,
  selectedNode: null,
  filters: defaultFilters,
  isLoading: false,
  error: null,

  fetchGraph: async (params) => {
    try {
      set({ isLoading: true, error: null })

      const response = await apiClient.getGraph(params)

      set({
        graphData: response,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to fetch graph data'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  fetchNodeDetails: async (nodeId: string) => {
    try {
      set({ isLoading: true, error: null })

      const node = await apiClient.getNodeDetails(nodeId)

      set({
        selectedNode: node,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to fetch node details'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  setSelectedNode: (node: GraphNode | null) => {
    set({ selectedNode: node })
  },

  updateFilters: (newFilters: Partial<GraphFilters>) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    }))
  },

  clearFilters: () => {
    set({ filters: defaultFilters })
  },

  clearError: () => {
    set({ error: null })
  },
}))
