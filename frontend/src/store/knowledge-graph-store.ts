/**
 * Knowledge Graph Store
 *
 * Neo4j 기반 지식 그래프 상태 관리
 * 기존 graph-store와 독립적으로 동작하여 Neo4j 데이터를 관리합니다
 */
import { create } from 'zustand'
import * as KnowledgeGraphAPI from '@/lib/knowledge-graph-api'

export interface KnowledgeGraphNode {
  id: string
  type: string
  label: string
  data: {
    description: string
    source_text: string
    insurer: string
    product_type: string
    document_id: string
    created_at: string
  }
}

export interface KnowledgeGraphEdge {
  id: string
  source: string
  target: string
  type: string
  label: string
  data: {
    description: string
  }
}

export interface KnowledgeGraphData {
  nodes: KnowledgeGraphNode[]
  edges: KnowledgeGraphEdge[]
  stats: {
    nodes: number
    edges: number
  }
}

export interface KnowledgeGraphFilters {
  entity_type?: string
  insurer?: string
  product_type?: string
  searchQuery?: string
  limit: number
}

interface KnowledgeGraphState {
  // Data
  graphData: KnowledgeGraphData | null
  selectedNode: KnowledgeGraphNode | null
  nodeDetail: KnowledgeGraphAPI.NodeDetail | null
  graphStats: KnowledgeGraphAPI.GraphStats | null

  // Filters
  filters: KnowledgeGraphFilters

  // UI State
  isLoading: boolean
  error: string | null

  // Actions
  fetchGraphStats: () => Promise<void>
  fetchGraphData: (filters?: Partial<KnowledgeGraphFilters>) => Promise<void>
  fetchNodeDetail: (entityId: string) => Promise<void>
  searchNodes: (query: string, limit?: number) => Promise<void>
  fetchNeighborhood: (entityId: string, depth?: number) => Promise<void>
  setSelectedNode: (node: KnowledgeGraphNode | null) => void
  updateFilters: (filters: Partial<KnowledgeGraphFilters>) => void
  clearFilters: () => void
  clearError: () => void
}

const defaultFilters: KnowledgeGraphFilters = {
  limit: 500,
}

export const useKnowledgeGraphStore = create<KnowledgeGraphState>()((set, get) => ({
  // Initial State
  graphData: null,
  selectedNode: null,
  nodeDetail: null,
  graphStats: null,
  filters: defaultFilters,
  isLoading: false,
  error: null,

  // Fetch Graph Statistics
  fetchGraphStats: async () => {
    try {
      set({ isLoading: true, error: null })

      const stats = await KnowledgeGraphAPI.getGraphStats()

      set({
        graphStats: stats,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch graph stats'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  // Fetch Graph Data with Filters
  fetchGraphData: async (newFilters) => {
    try {
      set({ isLoading: true, error: null })

      const currentFilters = get().filters
      const mergedFilters = { ...currentFilters, ...newFilters }

      const data = await KnowledgeGraphAPI.getGraphData({
        limit: mergedFilters.limit,
        entity_type: mergedFilters.entity_type,
        insurer: mergedFilters.insurer,
        product_type: mergedFilters.product_type,
      })

      set({
        graphData: data,
        filters: mergedFilters,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch graph data'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  // Fetch Node Detail
  fetchNodeDetail: async (entityId: string) => {
    try {
      set({ isLoading: true, error: null })

      const detail = await KnowledgeGraphAPI.getNodeDetail(entityId)

      set({
        nodeDetail: detail,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch node detail'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  // Search Nodes
  searchNodes: async (query: string, limit = 20) => {
    try {
      set({ isLoading: true, error: null })

      const result = await KnowledgeGraphAPI.searchNodes(query, limit)

      // Convert search results to graph data format
      const graphData: KnowledgeGraphData = {
        nodes: result.results.map(item => ({
          id: item.entity_id,
          type: item.type,
          label: item.label,
          data: {
            description: item.description,
            source_text: '',
            insurer: item.insurer,
            product_type: item.product_type,
            document_id: '',
            created_at: '',
          }
        })),
        edges: [],
        stats: {
          nodes: result.count,
          edges: 0,
        }
      }

      set({
        graphData,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to search nodes'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  // Fetch Neighborhood Subgraph
  fetchNeighborhood: async (entityId: string, depth = 1) => {
    try {
      set({ isLoading: true, error: null })

      const data = await KnowledgeGraphAPI.getNeighborhood(entityId, depth)

      set({
        graphData: data,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail ||
        error.message ||
        'Failed to fetch neighborhood'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  // Set Selected Node
  setSelectedNode: (node: KnowledgeGraphNode | null) => {
    set({ selectedNode: node, nodeDetail: null })

    // Automatically fetch node detail when a node is selected
    if (node) {
      get().fetchNodeDetail(node.id)
    }
  },

  // Update Filters
  updateFilters: (newFilters: Partial<KnowledgeGraphFilters>) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
    }))
  },

  // Clear Filters
  clearFilters: () => {
    set({ filters: defaultFilters })
  },

  // Clear Error
  clearError: () => {
    set({ error: null })
  },
}))
