/**
 * Query History API Client
 *
 * Enhancement #2: Query History Frontend
 */

import type {
  QueryHistory,
  QueryHistoryCreate,
  QueryHistoryListResponse,
  QueryHistoryStats,
  QueryHistoryFilters,
} from '@/types/query-history'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/**
 * Get auth headers with JWT token
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }
}

/**
 * Create a new query history entry
 */
export async function createQueryHistory(
  data: QueryHistoryCreate
): Promise<QueryHistory> {
  const response = await fetch(`${API_BASE}/api/v1/query-history/`, {
    method: 'POST',
    headers: await getAuthHeaders(),
    body: JSON.stringify(data),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to create query history')
  }

  return response.json()
}

/**
 * List query history with filters and pagination
 */
export async function listQueryHistory(
  filters: QueryHistoryFilters = {}
): Promise<QueryHistoryListResponse> {
  const params = new URLSearchParams()

  if (filters.customer_id) params.append('customer_id', filters.customer_id)
  if (filters.intent) params.append('intent', filters.intent)
  if (filters.date_from) params.append('date_from', filters.date_from)
  if (filters.date_to) params.append('date_to', filters.date_to)
  if (filters.search) params.append('search', filters.search)
  if (filters.page) params.append('page', filters.page.toString())
  if (filters.page_size) params.append('page_size', filters.page_size.toString())

  const response = await fetch(
    `${API_BASE}/api/v1/query-history/?${params.toString()}`,
    {
      headers: await getAuthHeaders(),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch query history')
  }

  return response.json()
}

/**
 * Get query statistics
 */
export async function getQueryStats(): Promise<QueryHistoryStats> {
  const response = await fetch(`${API_BASE}/api/v1/query-history/stats`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch query stats')
  }

  return response.json()
}

/**
 * Get specific query history detail
 */
export async function getQueryHistory(queryId: string): Promise<QueryHistory> {
  const response = await fetch(`${API_BASE}/api/v1/query-history/${queryId}`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch query history')
  }

  return response.json()
}

/**
 * Delete query history entry
 */
export async function deleteQueryHistory(queryId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/query-history/${queryId}`, {
    method: 'DELETE',
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to delete query history')
  }
}

/**
 * Get query history for a specific customer
 */
export async function getCustomerQueryHistory(
  customerId: string,
  page: number = 1,
  pageSize: number = 10
): Promise<QueryHistoryListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  })

  const response = await fetch(
    `${API_BASE}/api/v1/query-history/customer/${customerId}/history?${params.toString()}`,
    {
      headers: await getAuthHeaders(),
    }
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch customer query history')
  }

  return response.json()
}
