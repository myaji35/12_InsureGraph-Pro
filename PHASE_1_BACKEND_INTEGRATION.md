# Phase 1: 백엔드 API 통합

**목표**: 프론트엔드를 실제 백엔드 API와 완전히 연동
**Story Points**: 16 pts
**예상 기간**: 2주 (Sprint 1-2)

---

## 📋 현재 상태

### ✅ 이미 구현된 기능
- API Client (axios 기반) - `frontend/src/lib/api-client.ts`
- Clerk 인증 통합
- Request/Response 인터셉터
- 토큰 갱신 로직
- 환경 변수 설정
- Zustand 상태 관리 스토어 (auth, document, query, graph, customer)

### 🚧 개선 필요 사항
- [ ] 에러 처리 표준화
- [ ] Toast 알림 시스템 통합
- [ ] 타입 안전성 강화
- [ ] WebSocket 연결 (실시간 처리 상태)
- [ ] API 응답 캐싱 (React Query 또는 SWR)
- [ ] 로딩 상태 관리 개선
- [ ] 에러 바운더리 추가
- [ ] Retry 로직 with exponential backoff

---

## Story 1.1: 에러 처리 & Toast 시스템 (4 pts)

### 목표
사용자 친화적인 에러 메시지 및 피드백 시스템 구축

### 작업 내용

#### 1. React Hot Toast 설치 및 설정
```bash
cd frontend
npm install react-hot-toast
```

#### 2. Toast 설정 파일
**`src/lib/toast-config.ts`** (새 파일)
```typescript
import toast, { Toaster } from 'react-hot-toast'

export const showSuccess = (message: string, duration = 4000) => {
  toast.success(message, {
    duration,
    position: 'top-right',
    style: {
      background: '#10b981',
      color: '#fff',
    },
    iconTheme: {
      primary: '#fff',
      secondary: '#10b981',
    },
  })
}

export const showError = (message: string, duration = 5000) => {
  toast.error(message, {
    duration,
    position: 'top-right',
    style: {
      background: '#ef4444',
      color: '#fff',
    },
  })
}

export const showInfo = (message: string, duration = 3000) => {
  toast(message, {
    duration,
    position: 'top-right',
    icon: 'ℹ️',
  })
}

export const showLoading = (message: string) => {
  return toast.loading(message, {
    position: 'top-right',
  })
}

export const dismissToast = (id: string) => {
  toast.dismiss(id)
}

export { Toaster }
```

#### 3. 에러 메시지 매핑
**`src/lib/error-messages.ts`** (새 파일)
```typescript
export const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  NETWORK_ERROR: '네트워크 연결을 확인해주세요',
  TIMEOUT: '요청 시간이 초과되었습니다',

  // Auth errors
  UNAUTHORIZED: '로그인이 필요합니다',
  FORBIDDEN: '권한이 없습니다',
  INVALID_CREDENTIALS: '이메일 또는 비밀번호가 올바르지 않습니다',
  TOKEN_EXPIRED: '세션이 만료되었습니다. 다시 로그인해주세요',

  // Document errors
  FILE_TOO_LARGE: '파일 크기는 10MB 이하여야 합니다',
  INVALID_FILE_TYPE: 'PDF 파일만 업로드 가능합니다',
  DOCUMENT_NOT_FOUND: '문서를 찾을 수 없습니다',
  UPLOAD_FAILED: '파일 업로드에 실패했습니다',

  // Query errors
  QUERY_FAILED: '질의 처리에 실패했습니다',
  NO_DOCUMENTS_SELECTED: '문서를 선택해주세요',

  // Customer errors
  CUSTOMER_NOT_FOUND: '고객을 찾을 수 없습니다',

  // Generic
  INTERNAL_SERVER_ERROR: '서버 오류가 발생했습니다',
  BAD_REQUEST: '잘못된 요청입니다',
  UNKNOWN_ERROR: '알 수 없는 오류가 발생했습니다',
}

export const getErrorMessage = (errorCode?: string): string => {
  if (!errorCode) return ERROR_MESSAGES.UNKNOWN_ERROR
  return ERROR_MESSAGES[errorCode] || ERROR_MESSAGES.UNKNOWN_ERROR
}
```

#### 4. API Client 에러 처리 개선
**`src/lib/api-client.ts`** (업데이트)
```typescript
import { showError } from './toast-config'
import { getErrorMessage } from './error-messages'

// Response interceptor 수정
this.client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<{ error_code?: string; message?: string }>) => {
    const originalRequest = error.config as any

    // Network error
    if (!error.response) {
      const isDev = process.env.NODE_ENV === 'development'

      if (isDev) {
        console.warn('⚠️  백엔드 서버에 연결할 수 없습니다.')
      } else {
        showError(getErrorMessage('NETWORK_ERROR'))
      }

      return Promise.reject(error)
    }

    // HTTP error handling
    const status = error.response.status
    const errorCode = error.response.data?.error_code
    const errorMessage = error.response.data?.message

    // 401 처리 (기존 코드)
    if (status === 401 && !originalRequest._retry) {
      // ... (기존 refresh 로직)
    }

    // 다른 에러 처리
    if (status !== 401) {
      const message = errorMessage || getErrorMessage(errorCode)
      showError(message)
    }

    return Promise.reject(error)
  }
)
```

#### 5. 레이아웃에 Toaster 추가
**`src/app/layout.tsx`** (업데이트)
```typescript
import { Toaster } from '@/lib/toast-config'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <ThemeProvider>
          {children}
          <Toaster />
        </ThemeProvider>
      </body>
    </html>
  )
}
```

### Acceptance Criteria
- ✅ 모든 API 에러에 사용자 친화적 메시지 표시
- ✅ 성공/에러/로딩 Toast 표시
- ✅ 다크 모드 지원
- ✅ 에러 코드 기반 메시지 매핑

---

## Story 1.2: React Query 통합 (캐싱 & 상태 관리) (5 pts)

### 목표
API 응답 캐싱 및 서버 상태 관리 개선

### 작업 내용

#### 1. React Query 설치
```bash
npm install @tanstack/react-query @tanstack/react-query-devtools
```

#### 2. Query Client 설정
**`src/lib/react-query.ts`** (새 파일)
```typescript
import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5분
      cacheTime: 10 * 60 * 1000, // 10분
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
})
```

#### 3. Query Provider 설정
**`src/providers/query-provider.tsx`** (새 파일)
```typescript
'use client'

import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from '@/lib/react-query'

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  )
}
```

#### 4. Custom Hooks 생성
**`src/hooks/use-documents.ts`** (새 파일)
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'
import { showSuccess, showError } from '@/lib/toast-config'

export function useDocuments(params?: {
  insurer?: string
  status?: string
  page?: number
  page_size?: number
}) {
  return useQuery({
    queryKey: ['documents', params],
    queryFn: () => apiClient.getDocuments(params),
  })
}

export function useDocument(documentId: string) {
  return useQuery({
    queryKey: ['document', documentId],
    queryFn: () => apiClient.getDocument(documentId),
    enabled: !!documentId,
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ file, metadata }: { file: File; metadata: any }) =>
      apiClient.uploadDocument(file, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      showSuccess('문서가 업로드되었습니다')
    },
    onError: () => {
      showError('문서 업로드에 실패했습니다')
    },
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (documentId: string) => apiClient.deleteDocument(documentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      showSuccess('문서가 삭제되었습니다')
    },
    onError: () => {
      showError('문서 삭제에 실패했습니다')
    },
  })
}
```

**`src/hooks/use-query.ts`** (새 파일)
```typescript
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

export function useExecuteQuery() {
  return useMutation({
    mutationFn: (data: import('@/types').QueryRequest) =>
      apiClient.executeQuery(data),
  })
}

export function useQueryStatus(queryId: string) {
  return useQuery({
    queryKey: ['query-status', queryId],
    queryFn: () => apiClient.getQueryStatus(queryId),
    enabled: !!queryId,
    refetchInterval: 2000, // Poll every 2 seconds
  })
}
```

#### 5. 페이지에서 React Query 사용
**`src/app/[locale]/documents/page.tsx`** (업데이트 예시)
```typescript
import { useDocuments, useDeleteDocument } from '@/hooks/use-documents'

export default function DocumentsPage() {
  const { data, isLoading, error } = useDocuments()
  const deleteDocument = useDeleteDocument()

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading documents</div>

  return (
    <div>
      {data?.data.map((doc) => (
        <div key={doc.document_id}>
          <h3>{doc.product_name}</h3>
          <button onClick={() => deleteDocument.mutate(doc.document_id)}>
            Delete
          </button>
        </div>
      ))}
    </div>
  )
}
```

### Acceptance Criteria
- ✅ API 응답 캐싱
- ✅ 자동 재시도 (exponential backoff)
- ✅ 낙관적 업데이트
- ✅ Query invalidation on mutations
- ✅ Dev Tools 통합

---

## Story 1.3: WebSocket 연결 (실시간 상태) (4 pts)

### 목표
문서 처리 및 질의응답 실시간 상태 업데이트

### 작업 내용

#### 1. WebSocket Client
**`src/lib/websocket-client.ts`** (새 파일)
```typescript
import { showInfo } from './toast-config'

class WebSocketClient {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  connect(token?: string) {
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws'
    const url = token ? `${wsUrl}?token=${token}` : wsUrl

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('✅ WebSocket connected')
      this.reconnectAttempts = 0
      showInfo('실시간 연결 성공')
    }

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.handleMessage(data)
    }

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('🔌 WebSocket disconnected')
      this.reconnect(token)
    }
  }

  private handleMessage(data: any) {
    const { type, payload } = data

    switch (type) {
      case 'document_processing_update':
        this.onDocumentUpdate(payload)
        break
      case 'query_update':
        this.onQueryUpdate(payload)
        break
      default:
        console.log('Unknown message type:', type)
    }
  }

  private onDocumentUpdate(payload: any) {
    // Dispatch custom event for document updates
    window.dispatchEvent(
      new CustomEvent('document-update', { detail: payload })
    )
  }

  private onQueryUpdate(payload: any) {
    window.dispatchEvent(
      new CustomEvent('query-update', { detail: payload })
    )
  }

  private reconnect(token?: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      return
    }

    this.reconnectAttempts++
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1)

    setTimeout(() => {
      console.log(`Reconnecting... (attempt ${this.reconnectAttempts})`)
      this.connect(token)
    }, delay)
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export const wsClient = new WebSocketClient()
```

#### 2. WebSocket Hook
**`src/hooks/use-websocket.ts`** (새 파일)
```typescript
import { useEffect, useState } from 'react'
import { useAuth } from '@clerk/nextjs'
import { wsClient } from '@/lib/websocket-client'

export function useWebSocket() {
  const { getToken } = useAuth()
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const connect = async () => {
      const token = await getToken()
      wsClient.connect(token || undefined)
      setIsConnected(true)
    }

    connect()

    return () => {
      wsClient.disconnect()
      setIsConnected(false)
    }
  }, [getToken])

  return { isConnected }
}

export function useDocumentUpdates() {
  const [updates, setUpdates] = useState<any[]>([])

  useEffect(() => {
    const handleUpdate = (event: CustomEvent) => {
      setUpdates((prev) => [...prev, event.detail])
    }

    window.addEventListener('document-update', handleUpdate as any)

    return () => {
      window.removeEventListener('document-update', handleUpdate as any)
    }
  }, [])

  return updates
}

export function useQueryUpdates() {
  const [updates, setUpdates] = useState<any[]>([])

  useEffect(() => {
    const handleUpdate = (event: CustomEvent) => {
      setUpdates((prev) => [...prev, event.detail])
    }

    window.addEventListener('query-update', handleUpdate as any)

    return () => {
      window.removeEventListener('query-update', handleUpdate as any)
    }
  }, [])

  return updates
}
```

### Acceptance Criteria
- ✅ WebSocket 연결 및 재연결
- ✅ 문서 처리 상태 실시간 업데이트
- ✅ 질의응답 상태 실시간 업데이트
- ✅ 자동 재연결 (exponential backoff)

---

## Story 1.4: Error Boundary (3 pts)

### 목표
React 에러 바운더리로 UI 크래시 방지

### 작업 내용

#### 1. Error Boundary 컴포넌트
**`src/components/ErrorBoundary.tsx`** (새 파일)
```typescript
'use client'

import React from 'react'

interface Props {
  children: React.ReactNode
  fallback?: React.ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)

    // TODO: Send to Sentry in production
    if (process.env.NODE_ENV === 'production') {
      // Sentry.captureException(error, { contexts: { react: errorInfo } })
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-dark-bg">
          <div className="max-w-md p-8 bg-white dark:bg-dark-surface rounded-lg shadow-lg">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
              오류가 발생했습니다
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              죄송합니다. 예기치 않은 오류가 발생했습니다.
            </p>
            <button
              onClick={() => window.location.reload()}
              className="btn-primary w-full"
            >
              페이지 새로고침
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
```

#### 2. 레이아웃에 적용
**`src/app/[locale]/layout.tsx`** (업데이트)
```typescript
import { ErrorBoundary } from '@/components/ErrorBoundary'

export default function LocaleLayout({ children }) {
  return (
    <ErrorBoundary>
      {children}
    </ErrorBoundary>
  )
}
```

### Acceptance Criteria
- ✅ React 컴포넌트 에러 캐치
- ✅ 사용자 친화적 에러 화면
- ✅ 페이지 새로고침 버튼
- ✅ 에러 로깅 (Sentry 준비)

---

## 📅 Sprint 계획

### Week 1 (Sprint 1)
- **Day 1-2**: Story 1.1 에러 처리 & Toast (4 pts)
- **Day 3-5**: Story 1.2 React Query 통합 (5 pts)

### Week 2 (Sprint 2)
- **Day 1-3**: Story 1.3 WebSocket 연결 (4 pts)
- **Day 4-5**: Story 1.4 Error Boundary (3 pts)

---

## 🧪 테스트 체크리스트

### 에러 처리
- [ ] 네트워크 에러 Toast 표시
- [ ] 401 에러 시 로그인 페이지로 리다이렉트
- [ ] 에러 코드별 올바른 메시지 표시
- [ ] 다크 모드에서 Toast 가독성

### React Query
- [ ] 데이터 캐싱 동작
- [ ] Mutation 후 Query 무효화
- [ ] 자동 재시도 동작
- [ ] Dev Tools 표시

### WebSocket
- [ ] 연결 성공 Toast
- [ ] 문서 처리 상태 실시간 업데이트
- [ ] 질의응답 상태 업데이트
- [ ] 연결 끊김 후 재연결

### Error Boundary
- [ ] 컴포넌트 에러 캐치
- [ ] Fallback UI 표시
- [ ] 페이지 새로고침 동작

---

## 🚀 다음 단계

Phase 1 완료 후:
1. **Phase 2: 테스팅** (Jest, Playwright)
2. **Phase 5: DevOps** (CI/CD, 모니터링)
3. **Phase 3: UX 고도화** (i18n, 접근성, 고급 UI)

---

**작성일**: 2025-11-26
**Status**: 🚧 In Progress
**Total Story Points**: 16 pts
