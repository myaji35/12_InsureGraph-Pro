/**
 * Shared Types for InsureGraph Pro
 *
 * This package contains TypeScript types shared between frontend and backend.
 */

// ============================================================================
// Crawler URL Types
// ============================================================================

export interface CrawlerUrl {
  id: string;
  url: string;
  description: string;
  enabled: boolean;
  insurer?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CrawlerUrlCreate {
  insurer: string;
  url: string;
  description?: string;
  enabled?: boolean;
}

export interface CrawlerUrlUpdate {
  url?: string;
  description?: string;
  enabled?: boolean;
}

export interface CrawlerUrlListResponse {
  items: CrawlerUrl[];
  total: number;
}

// ============================================================================
// Document Types
// ============================================================================

export interface Document {
  id: string;
  title: string;
  content?: string;
  metadata?: Record<string, any>;
  created_at?: string;
  updated_at?: string;
}

export interface DocumentUploadRequest {
  title: string;
  file?: File | Blob;
  metadata?: Record<string, any>;
}

// ============================================================================
// Query Types
// ============================================================================

export interface QueryRequest {
  question: string;
  insurer?: string;
  policy_type?: string;
  context?: Record<string, any>;
}

export interface QueryResponse {
  query_id: string;
  answer: string;
  confidence?: number;
  sources?: string[];
  reasoning?: string;
  created_at: string;
}

// ============================================================================
// User Types
// ============================================================================

export interface User {
  id: string;
  email: string;
  name?: string;
  role?: string;
  created_at?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token?: string;
  token_type: string;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface ApiError {
  detail: string;
  code?: string;
  field?: string;
}

export interface PaginationParams {
  page?: number;
  limit?: number;
  offset?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page?: number;
  limit?: number;
  has_more?: boolean;
}

// ============================================================================
// Health Check Types
// ============================================================================

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy' | 'degraded';
  version: string;
  components?: Record<string, any>;
}
