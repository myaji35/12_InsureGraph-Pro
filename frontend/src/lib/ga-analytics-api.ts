/**
 * GA Manager Analytics API Client
 *
 * Enhancement #4: GA Manager View
 */

import type { GATeamMetrics, FPPerformance } from '@/types/ga-analytics'

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
 * Get GA team overview metrics
 * Only accessible by GA Managers (FP_MANAGER role)
 */
export async function fetchGATeamOverview(): Promise<GATeamMetrics> {
  const response = await fetch(`${API_BASE}/api/v1/ga-analytics/overview`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch GA team overview')
  }

  return response.json()
}

/**
 * Get detailed performance metrics for a specific FP
 * Only accessible by GA Managers for FPs in their organization
 */
export async function fetchFPDetails(fpId: string): Promise<FPPerformance> {
  const response = await fetch(`${API_BASE}/api/v1/ga-analytics/fp/${fpId}/details`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(error.detail || 'Failed to fetch FP details')
  }

  return response.json()
}
