import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  User,
  QueryRequest,
  QueryResponse,
  Document,
  DocumentListResponse,
  PaginatedResponse,
} from '@/types'
import { showError } from './toast-config'
import { getErrorMessage, getErrorMessageFromStatus } from './error-messages'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1'
const BASE_URL = `${API_URL}/api/${API_VERSION}`

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // Add auth token if exists
        if (typeof window !== 'undefined') {
          // Try to get Clerk session token first
          try {
            // @ts-ignore - Clerk global is available after initialization
            const clerk = window.Clerk
            if (clerk && clerk.session) {
              const token = await clerk.session.getToken()
              if (token) {
                config.headers.Authorization = `Bearer ${token}`
                return config
              }
            }
          } catch (error) {
            console.warn('Failed to get Clerk token:', error)
          }

          // Fallback to localStorage token (legacy)
          const token = localStorage.getItem('access_token')
          if (token) {
            config.headers.Authorization = `Bearer ${token}`
          }
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError<{ error_code?: string; message?: string; detail?: string }>) => {
        const originalRequest = error.config as any

        // Network error - 백엔드 서버가 없는 경우
        if (!error.response) {
          const isDev = process.env.NODE_ENV === 'development'

          if (isDev) {
            console.warn('⚠️  백엔드 서버에 연결할 수 없습니다.')
            console.warn(`   요청 URL: ${error.config?.url}`)
            console.warn(`   해결: 1) 백엔드 서버 시작 또는 2) Clerk 인증 사용`)
            console.warn(`   Clerk를 사용하면 백엔드 없이 개발 가능합니다.`)
          } else {
            // Production: Show user-friendly error
            showError(getErrorMessage('NETWORK_ERROR'))
          }

          // 에러 그대로 전달 (호출한 곳에서 처리)
          return Promise.reject(error)
        }

        // Get error information from response
        const status = error.response.status
        const errorCode = error.response.data?.error_code

        // Extract error message, handling both string and object formats
        let errorMessage: string | undefined
        const responseData = error.response.data as any
        if (responseData) {
          // Check if detail is an object with error_message
          if (typeof responseData.detail === 'object' && responseData.detail?.error_message) {
            errorMessage = responseData.detail.error_message
          }
          // Check if detail is a string
          else if (typeof responseData.detail === 'string') {
            errorMessage = responseData.detail
          }
          // Check for direct message field
          else if (responseData.message) {
            errorMessage = responseData.message
          }
        }

        // If 401 and not already retried, try to refresh token
        if (status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            const refreshToken = localStorage.getItem('refresh_token')
            if (refreshToken) {
              const response = await this.client.post('/auth/refresh', {
                refresh_token: refreshToken,
              })

              const { access_token, refresh_token: newRefreshToken } = response.data

              localStorage.setItem('access_token', access_token)
              localStorage.setItem('refresh_token', newRefreshToken)

              // Retry original request
              originalRequest.headers.Authorization = `Bearer ${access_token}`
              return this.client(originalRequest)
            } else {
              // No refresh token, show error and redirect
              showError(getErrorMessage('UNAUTHORIZED'))
              if (typeof window !== 'undefined') {
                window.location.href = '/sign-in'
              }
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            if (typeof window !== 'undefined') {
              localStorage.removeItem('access_token')
              localStorage.removeItem('refresh_token')
              showError(getErrorMessage('TOKEN_EXPIRED'))
              window.location.href = '/sign-in'
            }
            return Promise.reject(refreshError)
          }
        }

        // Handle other error statuses
        if (status !== 401) {
          // Priority: errorMessage from server > errorCode mapping > status code mapping
          const message = errorMessage || getErrorMessage(errorCode) || getErrorMessageFromStatus(status)

          // Don't show toast for some specific errors (let component handle it)
          const silentErrors = [404] // e.g., Not Found might be handled by component
          if (!silentErrors.includes(status)) {
            showError(message)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  // Auth APIs
  async login(data: LoginRequest): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>('/auth/login', data)
    return response.data
  }

  async register(data: RegisterRequest): Promise<{ user: User; message: string }> {
    const response = await this.client.post<{ user: User; message: string }>(
      '/auth/register',
      data
    )
    return response.data
  }

  async logout(refreshToken: string): Promise<void> {
    await this.client.post('/auth/logout', { refresh_token: refreshToken })
  }

  async getMe(): Promise<{ user: User }> {
    const response = await this.client.get<{ user: User }>('/auth/me')
    return response.data
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await this.client.patch<User>('/auth/me', data)
    return response.data
  }

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>(
      '/auth/change-password',
      {
        current_password: currentPassword,
        new_password: newPassword,
      }
    )
    return response.data
  }

  // Query APIs
  async executeQuery(data: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>('/query', data)
    return response.data
  }

  async getQueryStatus(queryId: string): Promise<QueryResponse> {
    const response = await this.client.get<QueryResponse>(`/query/${queryId}/status`)
    return response.data
  }

  // Document APIs
  async extractDocumentMetadata(file: File): Promise<{
    insurer: string
    product_name: string
    product_code?: string
    launch_date?: string
    description?: string
    confidence: number
  }> {
    // AI 기반 메타데이터 추출 (파일명 분석)
    return new Promise((resolve) => {
      setTimeout(() => {
        const filename = file.name.replace(/\.[^/.]+$/, '')

        // 한국 주요 보험사 목록
        const insurers = [
          '삼성생명', '삼성화재', '삼성',
          '한화생명', '한화손해보험', '한화',
          '교보생명', '교보',
          'KB손해보험', 'KB생명', 'KB',
          '메리츠화재', '메리츠생명', '메리츠',
          '메트라이프생명', 'MetLife', '메트라이프',
          '현대해상', '현대생명', '현대',
          'DB손해보험', 'DB생명', 'DB',
          'AIA생명', 'AIA',
          '흥국생명', '흥국화재', '흥국',
          'NH농협생명', 'NH농협손해보험', 'NH농협', '농협',
          '신한생명', '신한',
          'IBK연금보험', 'IBK',
          'KDB생명', 'KDB',
          '하나생명', '하나손해보험', '하나',
          '푸르덴셜생명', '푸르덴셜',
          '라이나생명', '라이나',
          '오렌지라이프', '오렌지',
          'DGB생명', 'DGB',
          'BNP파리바카디프생명', 'BNP',
          'ABL생명', 'ABL',
        ]

        // 파일명에서 보험사명 찾기
        let detectedInsurer = ''
        let confidence = 0

        for (const insurer of insurers) {
          if (filename.includes(insurer)) {
            detectedInsurer = insurer
            confidence = 0.85 // 파일명 기반 추출은 85% 신뢰도
            break
          }
        }

        // 상품명 추출 (보험사명 제거)
        let productName = filename
        if (detectedInsurer) {
          productName = filename.replace(detectedInsurer, '').trim()
          // 특수문자나 불필요한 공백 정리
          productName = productName.replace(/^[-_\s]+|[-_\s]+$/g, '')
        }

        // 상품코드 추출 시도 (숫자-문자 조합 패턴)
        const codeMatch = filename.match(/[A-Z]{2,4}[-]?\d{4,6}/i)
        const productCode = codeMatch ? codeMatch[0] : ''

        // 날짜 추출 시도 (YYYY-MM-DD, YYYYMMDD, YYYY.MM.DD 등)
        const dateMatch = filename.match(/(\d{4})[.-]?(\d{2})[.-]?(\d{2})/)
        const launchDate = dateMatch ? `${dateMatch[1]}-${dateMatch[2]}-${dateMatch[3]}` : ''

        resolve({
          insurer: detectedInsurer,
          product_name: productName || filename,
          product_code: productCode,
          launch_date: launchDate,
          description: '',
          confidence: confidence,
        })
      }, 500) // Simulate AI processing delay
    })
  }

  async uploadDocument(
    file: File,
    metadata: {
      insurer: string
      product_name: string
      product_code?: string
      launch_date?: string
      description?: string
      document_type?: string
      tags?: string
    },
    onUploadProgress?: (progressEvent: { loaded: number; total?: number; progress?: number }) => void
  ): Promise<{ document_id: string; job_id: string; message: string }> {
    const formData = new FormData()
    formData.append('file', file)
    Object.entries(metadata).forEach(([key, value]) => {
      if (value) formData.append(key, value)
    })

    const response = await this.client.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minutes for file upload and DB storage
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const progress = (progressEvent.loaded / progressEvent.total) * 100
          onUploadProgress({
            loaded: progressEvent.loaded,
            total: progressEvent.total,
            progress: progress,
          })
        }
      },
    })
    return response.data
  }

  async getDocuments(params?: {
    insurer?: string
    status?: string
    page?: number
    page_size?: number
  }): Promise<DocumentListResponse> {
    const response = await this.client.get<DocumentListResponse>(
      '/documents',
      { params }
    )
    return response.data
  }

  async getDocument(documentId: string): Promise<Document> {
    const response = await this.client.get<Document>(`/documents/${documentId}`)
    return response.data
  }

  async deleteDocument(documentId: string): Promise<void> {
    await this.client.delete(`/documents/${documentId}`)
  }

  // Graph APIs
  async getGraph(params?: {
    document_ids?: string[]
    node_types?: string[]
    max_nodes?: number
  }): Promise<import('@/types').GraphData> {
    const response = await this.client.get<import('@/types').GraphData>(
      '/graph',
      { params }
    )
    return response.data
  }

  async getNodeDetails(nodeId: string): Promise<import('@/types').GraphNode> {
    const response = await this.client.get<import('@/types').GraphNode>(
      `/graph/nodes/${nodeId}`
    )
    return response.data
  }

  // Customer APIs
  async getCustomers(params?: {
    search?: string
    page?: number
    page_size?: number
  }): Promise<import('@/types').PaginatedResponse<import('@/types').Customer>> {
    const response = await this.client.get('/customers', { params })
    return response.data
  }

  async getCustomer(customerId: string): Promise<import('@/types').Customer> {
    const response = await this.client.get(`/customers/${customerId}`)
    return response.data
  }

  async createCustomer(data: Omit<import('@/types').Customer, 'customer_id' | 'created_at' | 'updated_at' | 'created_by_user_id'>): Promise<import('@/types').Customer> {
    const response = await this.client.post('/customers', data)
    return response.data
  }

  async updateCustomer(customerId: string, data: Partial<import('@/types').Customer>): Promise<import('@/types').Customer> {
    const response = await this.client.patch(`/customers/${customerId}`, data)
    return response.data
  }

  async deleteCustomer(customerId: string): Promise<void> {
    await this.client.delete(`/customers/${customerId}`)
  }

  async getCustomerInsurances(customerId: string): Promise<import('@/types').Insurance[]> {
    const response = await this.client.get(`/customers/${customerId}/insurances`)
    return response.data
  }

  async getPortfolioAnalysis(customerId: string): Promise<import('@/types').PortfolioAnalysis> {
    const response = await this.client.get(`/customers/${customerId}/portfolio-analysis`)
    return response.data
  }

  // Stats APIs
  async getTimeseriesStats(): Promise<Array<{
    date: string
    learnedDocs: number
    inProgressDocs: number
    pendingDocs: number
    totalDocs: number
  }>> {
    const response = await this.client.get('/documents/stats/timeseries')
    return response.data
  }

  // Crawler APIs
  async getCrawlerConfigs(enabledOnly = false): Promise<any[]> {
    const response = await this.client.get('/crawler/configs', {
      params: { enabled_only: enabledOnly }
    })
    return response.data
  }

  async getCompanyCrawledDocuments(
    companyName: string,
    page = 1,
    pageSize = 50,
    statusFilter?: string
  ): Promise<{
    company_name: string
    total: number
    page: number
    page_size: number
    total_pages: number
    documents: any[]
  }> {
    const response = await this.client.get(`/crawler/companies/${encodeURIComponent(companyName)}/documents`, {
      params: {
        page,
        page_size: pageSize,
        status_filter: statusFilter
      }
    })
    return response.data
  }

  async startCrawlJob(companyName: string): Promise<{
    job_id: string
    status: string
  }> {
    const response = await this.client.post(`/crawler/jobs/start/${encodeURIComponent(companyName)}`)
    return response.data
  }

  async getCrawlerJobs(
    companyName?: string,
    page = 1,
    pageSize = 20
  ): Promise<{
    jobs: any[]
    total: number
    page: number
    page_size: number
  }> {
    const response = await this.client.get('/crawler/jobs', {
      params: {
        company_name: companyName,
        page,
        page_size: pageSize
      }
    })
    return response.data
  }

  async downloadCrawledDocuments(jobId: string): Promise<{
    message: string
    total_pending: number
  }> {
    const response = await this.client.post(`/crawler/jobs/${jobId}/download`)
    return response.data
  }

  async testUrlCrawling(
    url: string,
    crawlerType: 'selenium' = 'selenium',
    headless: boolean = true
  ): Promise<{
    success: boolean
    url: string
    page_title: string | null
    content_length: number
    load_time: number
    current_url?: string
    pdf_links_found?: number
    pdf_links?: Array<{ url: string; text: string; title: string }>
    error?: string
  }> {
    const response = await this.client.post('/crawler/test-url', null, {
      params: {
        url,
        crawler_type: crawlerType,
        headless
      }
    })
    return response.data
  }
}

// Export singleton instance
export const apiClient = new APIClient()
