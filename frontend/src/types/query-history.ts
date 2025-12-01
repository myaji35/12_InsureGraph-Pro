/**
 * Query History Types
 *
 * Enhancement #2: Query History Frontend
 */

export interface QueryHistoryBase {
  query_text: string
  intent?: string
  customer_id?: string
}

export interface QueryHistoryCreate extends QueryHistoryBase {
  answer?: string
  confidence?: number
  source_documents?: Record<string, any>[]
  reasoning_path?: Record<string, any>
  execution_time_ms?: number
}

export interface QueryHistory extends QueryHistoryBase {
  id: string
  user_id: string
  answer?: string
  confidence?: number
  source_documents?: Record<string, any>[]
  reasoning_path?: Record<string, any>
  execution_time_ms?: number
  created_at: string
}

export interface QueryHistoryResponse {
  id: string
  query_text: string
  intent?: string
  answer_preview?: string
  confidence?: number
  customer_id?: string
  customer_name?: string
  execution_time_ms?: number
  created_at: string
}

export interface QueryHistoryListResponse {
  items: QueryHistoryResponse[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface QueryHistoryStats {
  total_queries: number
  queries_today: number
  queries_this_week: number
  queries_this_month: number
  avg_confidence?: number
  avg_execution_time_ms?: number
  top_intents: Array<{
    intent: string
    count: number
  }>
  queries_by_customer: Array<{
    customer_id: string
    customer_name: string
    query_count: number
  }>
}

export interface QueryHistoryFilters {
  customer_id?: string
  intent?: string
  date_from?: string
  date_to?: string
  search?: string
  page?: number
  page_size?: number
}
