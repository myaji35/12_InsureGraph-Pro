/**
 * Analytics API Client
 *
 * Story 3.5: Dashboard & Analytics
 */

import { DashboardOverview } from '@/types/analytics'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getAuthHeaders(): Promise<HeadersInit> {
  const token = localStorage.getItem('access_token')
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  }
}

export async function fetchDashboardOverview(): Promise<DashboardOverview> {
  const response = await fetch(`${API_BASE}/api/v1/analytics/overview`, {
    headers: await getAuthHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Failed to fetch dashboard overview: ${response.statusText}`)
  }

  return response.json()
}
