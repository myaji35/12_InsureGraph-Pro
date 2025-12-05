/**
 * Knowledge Graph API Client
 *
 * Neo4j 기반 지식 그래프 데이터를 조회하는 API 클라이언트
 */

import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:3030/api'
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1'
const BASE_URL = `${API_BASE_URL}/${API_VERSION}`

// Create a dedicated axios instance for Knowledge Graph API
const kgClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// Types
export interface GraphNode {
  id: string
  type: string
  label: string
  data: {
    description: string
    source_text: string
    insurer: string
    product_type: string
    document_id: string
    created_at: string
  }
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  label: string
  data: {
    description: string
  }
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  stats: {
    nodes: number
    edges: number
  }
}

export interface GraphStats {
  total_nodes: number
  total_relationships: number
  node_types: Record<string, number>
  relationship_types: Record<string, number>
}

export interface NodeDetail {
  entity_id: string
  label: string
  type: string
  description: string
  source_text: string
  document_id: string
  insurer: string
  product_type: string
  created_at: string
  neighbors: Array<{
    entity_id: string
    label: string
    type: string
    relationship_type: string
    relationship_description: string
    direction: 'incoming' | 'outgoing'
  }>
}

export interface SearchResult {
  query: string
  count: number
  results: Array<{
    entity_id: string
    label: string
    type: string
    description: string
    insurer: string
    product_type: string
  }>
}

// API Functions

/**
 * 그래프 통계 조회
 */
export async function getGraphStats(): Promise<GraphStats> {
  const response = await kgClient.get('/knowledge-graph/stats')
  return response.data
}

/**
 * 그래프 데이터 조회
 */
export async function getGraphData(params?: {
  limit?: number
  entity_type?: string
  insurer?: string
  product_type?: string
}): Promise<GraphData> {
  const response = await kgClient.get('/knowledge-graph/data', { params })
  return response.data
}

/**
 * 노드 상세 정보 조회
 */
export async function getNodeDetail(entityId: string): Promise<NodeDetail> {
  const response = await kgClient.get(`/knowledge-graph/node/${entityId}`)
  return response.data
}

/**
 * 노드 검색
 */
export async function searchNodes(query: string, limit: number = 20): Promise<SearchResult> {
  const response = await kgClient.get('/knowledge-graph/search', {
    params: { query, limit }
  })
  return response.data
}

/**
 * 이웃 서브그래프 조회
 */
export async function getNeighborhood(entityId: string, depth: number = 1): Promise<GraphData & {
  center_node_id: string
  depth: number
}> {
  const response = await kgClient.get(`/knowledge-graph/neighborhood/${entityId}`, {
    params: { depth }
  })
  return response.data
}
