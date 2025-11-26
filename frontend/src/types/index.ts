/**
 * User Types
 */
export type UserRole = 'admin' | 'fp_manager' | 'fp' | 'user'

export type UserStatus = 'pending' | 'active' | 'suspended'

export interface User {
  user_id: string
  email: string
  username: string
  full_name: string
  role: UserRole
  status: UserStatus
  organization_name?: string
  created_at: string
  last_login_at?: string
}

/**
 * Auth Types
 */
export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  password: string
  username: string
  full_name: string
  phone?: string
  organization_name?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

/**
 * Document Types
 */
export type DocumentStatus = 'pending' | 'processing' | 'ready' | 'failed'

export interface Document {
  document_id: string
  insurer: string
  product_name: string
  product_code?: string
  launch_date?: string
  status: DocumentStatus
  filename: string
  document_type?: string
  description?: string
  tags?: string[]
  chunk_count?: number
  entity_count?: number
  relationship_count?: number
  gcs_uri?: string
  error_message?: string
  created_at: string
  processed_at?: string
  uploaded_by_user_id?: string
}

export interface DocumentListResponse {
  documents: Document[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * Query Types
 */
export type QueryStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface QueryRequest {
  question: string
  document_ids: string[]
}

export interface Citation {
  document_id?: string
  document_name?: string
  content: string
  relevance_score?: number
  metadata?: {
    page_number?: number
    section?: string
    [key: string]: any
  }
}

export interface QueryResponse {
  query_id: string
  question: string
  answer?: string
  status: QueryStatus
  confidence_score?: number
  citations?: Citation[]
  processing_time?: number
  error_message?: string
  created_at?: string
  completed_at?: string
}

/**
 * API Error Types
 */
export interface APIError {
  error_code: string
  error_message: string
  details?: Record<string, any>
  timestamp?: string
}

/**
 * Pagination Types
 */
export interface PaginatedResponse<T> {
  items: T[]
  page: number
  page_size: number
  total_pages: number
  total_items: number
  has_next: boolean
  has_prev: boolean
}

/**
 * Customer Types
 */
export interface Customer {
  customer_id: string
  name: string
  email?: string
  phone?: string
  birth_date?: string
  gender?: 'male' | 'female' | 'other'
  occupation?: string
  annual_income?: number
  risk_profile?: 'conservative' | 'moderate' | 'aggressive'
  notes?: string
  created_at: string
  updated_at: string
  created_by_user_id: string
}

export interface Insurance {
  insurance_id: string
  customer_id: string
  insurer: string
  product_name: string
  product_type: string
  premium: number
  coverage_amount: number
  start_date: string
  end_date?: string
  status: 'active' | 'expired' | 'cancelled'
  notes?: string
  created_at: string
}

export interface PortfolioAnalysis {
  customer_id: string
  total_premium: number
  total_coverage: number
  coverage_by_type: Record<string, number>
  premium_by_type: Record<string, number>
  risk_assessment: {
    score: number
    level: 'low' | 'medium' | 'high'
    recommendations: string[]
  }
  coverage_gaps: string[]
  recommendations: {
    product_name: string
    reason: string
    priority: 'high' | 'medium' | 'low'
  }[]
}

/**
 * Graph Types
 */
export type NodeType = 'document' | 'entity' | 'concept' | 'clause'

export interface GraphNode {
  id: string
  type: NodeType
  label: string
  properties?: Record<string, any>
  metadata?: {
    document_id?: string
    document_name?: string
    entity_type?: string
    importance?: number
    [key: string]: any
  }
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  label?: string
  type?: string
  weight?: number
  properties?: Record<string, any>
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  metadata?: {
    total_nodes: number
    total_edges: number
    document_ids?: string[]
    [key: string]: any
  }
}
