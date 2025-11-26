import { create } from 'zustand'
import type { Document, PaginatedResponse } from '@/types'
import { apiClient } from '@/lib/api-client'

interface DocumentState {
  documents: Document[]
  currentDocument: Document | null
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
  fetchDocuments: (params?: {
    insurer?: string
    status?: string
    page?: number
    page_size?: number
  }) => Promise<void>
  fetchDocument: (documentId: string) => Promise<void>
  deleteDocument: (documentId: string) => Promise<void>
  clearError: () => void
  setCurrentDocument: (document: Document | null) => void
}

export const useDocumentStore = create<DocumentState>()((set, get) => ({
  documents: [],
  currentDocument: null,
  pagination: null,
  isLoading: false,
  error: null,

  fetchDocuments: async (params) => {
    try {
      set({ isLoading: true, error: null })

      const response = await apiClient.getDocuments(params)

      set({
        documents: response.items,
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
        'Failed to fetch documents'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  fetchDocument: async (documentId: string) => {
    try {
      set({ isLoading: true, error: null })

      const document = await apiClient.getDocument(documentId)

      set({
        currentDocument: document,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to fetch document'

      set({
        error: errorMessage,
        isLoading: false,
      })

      throw error
    }
  },

  deleteDocument: async (documentId: string) => {
    try {
      set({ isLoading: true, error: null })

      await apiClient.deleteDocument(documentId)

      // Remove from list
      const updatedDocuments = get().documents.filter(
        (doc) => doc.document_id !== documentId
      )

      set({
        documents: updatedDocuments,
        isLoading: false,
      })
    } catch (error: any) {
      const errorMessage =
        error.response?.data?.detail?.error_message ||
        error.message ||
        'Failed to delete document'

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

  setCurrentDocument: (document: Document | null) => {
    set({ currentDocument: document })
  },
}))
