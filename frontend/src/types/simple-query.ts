/**
 * Simple Query API Types
 *
 * Types for the Simple Query API (Stories 2.1-2.6)
 */

export interface SimpleQueryRequest {
  query: string
  policy_id?: string
  customer_id?: string
  limit?: number
  use_traversal?: boolean
  llm_provider?: 'openai' | 'anthropic' | 'mock'
}

export interface EntityInfo {
  entity_type: string
  value: string
}

export interface SearchResultInfo {
  node_id: string
  node_type: string
  text: string
  relevance_score: number
  article_num?: string
}

export interface GraphNodeInfo {
  node_id: string
  node_type: string
  text: string
  properties: Record<string, any>
}

export interface GraphPathInfo {
  nodes: GraphNodeInfo[]
  relationships: string[]
  path_length: number
  relevance_score: number
}

export interface ValidationInfo {
  passed: boolean
  overall_level: string
  confidence: number
  issues_count: number
  recommendations: string[]
}

export interface SimpleQueryResponse {
  query: string
  intent: string
  entities: EntityInfo[]

  // Search
  search_results_count: number
  search_results: SearchResultInfo[]

  // Traversal
  graph_paths_count: number
  graph_paths: GraphPathInfo[]

  // Answer
  answer: string
  confidence: number
  sources: Array<{
    node_id: string
    node_type: string
    text: string
    relevance_score: number
  }>

  // Validation
  validation: ValidationInfo
}

export interface QueryIntent {
  value: string
  label: string
  description: string
  icon: string
}

export const QUERY_INTENTS: QueryIntent[] = [
  {
    value: 'search',
    label: '일반 검색',
    description: '키워드로 약관 검색',
    icon: '🔍',
  },
  {
    value: 'comparison',
    label: '상품 비교',
    description: '보험 상품 비교',
    icon: '⚖️',
  },
  {
    value: 'amount_filter',
    label: '금액 필터',
    description: '금액별 조회',
    icon: '💰',
  },
  {
    value: 'coverage_check',
    label: '보장 확인',
    description: '특정 보장 확인',
    icon: '✅',
  },
  {
    value: 'exclusion_check',
    label: '면책 확인',
    description: '면책 사항 확인',
    icon: '❌',
  },
  {
    value: 'period_check',
    label: '기간 확인',
    description: '대기 기간 확인',
    icon: '📅',
  },
]

export function getIntentLabel(intent: string): string {
  const found = QUERY_INTENTS.find((i) => i.value === intent)
  return found?.label || intent
}

export function getIntentIcon(intent: string): string {
  const found = QUERY_INTENTS.find((i) => i.value === intent)
  return found?.icon || '❓'
}
