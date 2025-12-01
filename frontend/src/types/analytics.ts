/**
 * Analytics Types
 *
 * Story 3.5: Dashboard & Analytics
 */

export interface MetricCard {
  label: string
  value: number
  change?: string
  trend?: 'up' | 'down' | 'neutral'
}

export interface RecentCustomer {
  id: string
  name: string
  age: number
  policy_count: number
  last_contact_date?: string
  created_at: string
}

export interface CoverageBreakdown {
  coverage_type: string
  count: number
  total_amount: number
}

export interface DashboardOverview {
  metrics: MetricCard[]
  recent_customers: RecentCustomer[]
  coverage_breakdown: CoverageBreakdown[]
  period_start: string
  period_end: string
}
