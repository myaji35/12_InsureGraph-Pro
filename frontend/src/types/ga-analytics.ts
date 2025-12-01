/**
 * GA Manager Analytics Types
 *
 * Enhancement #4: GA Manager View
 */

export interface FPPerformance {
  fp_id: string
  fp_name: string
  total_customers: number
  active_customers: number
  total_policies: number
  total_queries: number
  avg_query_confidence: number | null
  last_activity: string | null
}

export interface GATeamMetrics {
  // Overview
  total_fps: number
  active_fps: number

  // Customer metrics
  total_customers: number
  active_customers: number
  new_customers_this_month: number

  // Policy metrics
  total_policies: number
  total_coverage_amount: number
  total_monthly_premium: number

  // Query metrics
  total_queries: number
  queries_today: number
  queries_this_week: number
  queries_this_month: number
  avg_query_confidence: number | null

  // Coverage breakdown
  coverage_breakdown: Array<{
    coverage_type: string
    count: number
  }>

  // Top performing FPs
  top_fps: FPPerformance[]
}
