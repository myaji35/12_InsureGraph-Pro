/**
 * Simple Query API Client
 *
 * API client for the Simple Query Engine (Stories 2.1-2.6)
 */

import type { SimpleQueryRequest, SimpleQueryResponse } from '@/types/simple-query'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:3030/api'
const SIMPLE_QUERY_API = `${API_BASE_URL}/v1/query-simple`

class SimpleQueryAPI {
  private async fetchWithAuth(url: string, options: RequestInit = {}) {
    // Get token from localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null

    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async executeQuery(request: SimpleQueryRequest): Promise<SimpleQueryResponse> {
    return this.fetchWithAuth(`${SIMPLE_QUERY_API}/execute`, {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getIntents(): Promise<string[]> {
    return this.fetchWithAuth(`${SIMPLE_QUERY_API}/intents`)
  }

  async getHealth(): Promise<{
    status: string
    neo4j_connected: boolean
    llm_available: boolean
  }> {
    return this.fetchWithAuth(`${SIMPLE_QUERY_API}/health`)
  }
}

export const simpleQueryAPI = new SimpleQueryAPI()
