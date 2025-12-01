'use client'

/**
 * Query History Page
 *
 * Task B: Complete query history viewing with filters and pagination
 */

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { listQueryHistory, getQueryHistory, deleteQueryHistory } from '@/lib/query-history-api'
import { QueryHistoryListResponse, QueryHistory, QueryHistoryFilters } from '@/types/query-history'
import { useToast } from '@/components/Toast'

export default function QueryHistoryPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const toast = useToast()

  const [history, setHistory] = useState<QueryHistoryListResponse | null>(null)
  const [selectedQuery, setSelectedQuery] = useState<QueryHistory | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [filters, setFilters] = useState<QueryHistoryFilters>({
    customer_id: searchParams.get('customer_id') || undefined,
    intent: searchParams.get('intent') || undefined,
    search: searchParams.get('search') || undefined,
    page: 1,
    page_size: 20,
  })

  useEffect(() => {
    loadHistory()
  }, [filters])

  const loadHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await listQueryHistory(filters)
      setHistory(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load query history')
      toast.error('질의 이력을 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetail = async (queryId: string) => {
    try {
      const detail = await getQueryHistory(queryId)
      setSelectedQuery(detail)
    } catch (err) {
      toast.error('질의 상세 정보를 불러오는데 실패했습니다')
    }
  }

  const handleDelete = async (queryId: string) => {
    if (!confirm('이 질의 이력을 삭제하시겠습니까?')) return

    try {
      await deleteQueryHistory(queryId)
      toast.success('질의 이력이 삭제되었습니다')
      loadHistory()
      if (selectedQuery?.id === queryId) {
        setSelectedQuery(null)
      }
    } catch (err) {
      toast.error('질의 이력 삭제에 실패했습니다')
    }
  }

  const handleFilterChange = (key: keyof QueryHistoryFilters, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
      page: key === 'page' ? value : 1, // Reset to page 1 on filter change
    }))
  }

  const handleClearFilters = () => {
    setFilters({
      page: 1,
      page_size: 20,
    })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR')
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            질의 이력
          </h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            과거 질문과 답변을 검색하고 확인하세요
          </p>
        </div>

        {/* Filters */}
        <div className="card mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                검색
              </label>
              <input
                type="text"
                value={filters.search || ''}
                onChange={(e) => handleFilterChange('search', e.target.value || undefined)}
                placeholder="질문 내용 검색..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
              />
            </div>

            {/* Intent */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                질의 유형
              </label>
              <select
                value={filters.intent || ''}
                onChange={(e) => handleFilterChange('intent', e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
              >
                <option value="">전체</option>
                <option value="search">일반 검색</option>
                <option value="comparison">상품 비교</option>
                <option value="amount_filter">금액 필터</option>
                <option value="coverage_check">보장 확인</option>
                <option value="exclusion_check">면책 확인</option>
                <option value="period_check">기간 확인</option>
              </select>
            </div>

            {/* Clear Filters */}
            <div className="flex items-end">
              <button
                onClick={handleClearFilters}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                필터 초기화
              </button>
            </div>
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
            <button onClick={loadHistory} className="mt-4 btn-primary">
              다시 시도
            </button>
          </div>
        ) : history && history.items.length > 0 ? (
          <div className="space-y-4">
            {/* Query List */}
            {history.items.map((item) => (
              <div
                key={item.id}
                className="card hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => handleViewDetail(item.id)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">
                        {item.query_text}
                      </h3>
                      {item.intent && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                          {item.intent}
                        </span>
                      )}
                    </div>

                    {item.answer_preview && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">
                        {item.answer_preview}
                      </p>
                    )}

                    <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      {item.customer_name && (
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          {item.customer_name}
                        </span>
                      )}
                      {item.confidence !== null && item.confidence !== undefined && (
                        <span>신뢰도: {(item.confidence * 100).toFixed(0)}%</span>
                      )}
                      {item.execution_time_ms && (
                        <span>응답시간: {(item.execution_time_ms / 1000).toFixed(2)}초</span>
                      )}
                      <span>{formatDate(item.created_at)}</span>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(item.id)
                    }}
                    className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}

            {/* Pagination */}
            <div className="flex items-center justify-between pt-4">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                총 {history.total}개 중 {(history.page - 1) * history.page_size + 1}-
                {Math.min(history.page * history.page_size, history.total)}개 표시
              </div>

              <div className="flex gap-2">
                <button
                  onClick={() => handleFilterChange('page', filters.page! - 1)}
                  disabled={filters.page === 1}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  이전
                </button>
                <span className="px-4 py-2 text-gray-700 dark:text-gray-300">
                  {filters.page} / {Math.ceil(history.total / history.page_size)}
                </span>
                <button
                  onClick={() => handleFilterChange('page', filters.page! + 1)}
                  disabled={!history.has_more}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  다음
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="card text-center py-12">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">질의 이력 없음</h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              아직 질의 이력이 없습니다. 질문을 시작해보세요!
            </p>
            <button
              onClick={() => router.push('/query-simple')}
              className="mt-4 btn-primary"
            >
              질문하기
            </button>
          </div>
        )}

        {/* Detail Modal */}
        {selectedQuery && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                {/* Modal Header */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
                      {selectedQuery.query_text}
                    </h3>
                    <div className="flex items-center gap-3 mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {selectedQuery.intent && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                          {selectedQuery.intent}
                        </span>
                      )}
                      <span>{formatDate(selectedQuery.created_at)}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedQuery(null)}
                    className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                  >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Answer */}
                <div className="mb-6">
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">답변</h4>
                  <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                    <p className="text-gray-900 dark:text-gray-100 whitespace-pre-wrap">
                      {selectedQuery.answer || '답변 없음'}
                    </p>
                  </div>
                </div>

                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {selectedQuery.confidence !== null && selectedQuery.confidence !== undefined && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">신뢰도</h4>
                      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                        {(selectedQuery.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  )}
                  {selectedQuery.execution_time_ms && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">응답 시간</h4>
                      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                        {(selectedQuery.execution_time_ms / 1000).toFixed(2)}초
                      </p>
                    </div>
                  )}
                </div>

                {/* Source Documents */}
                {selectedQuery.source_documents && selectedQuery.source_documents.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      출처 문서 ({selectedQuery.source_documents.length}개)
                    </h4>
                    <div className="space-y-2">
                      {selectedQuery.source_documents.map((doc, idx) => (
                        <div
                          key={idx}
                          className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg"
                        >
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {doc.text || 'No text available'}
                          </p>
                          {doc.article_num && (
                            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                              조항: {doc.article_num}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Reasoning Path */}
                {selectedQuery.reasoning_path && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      추론 경로
                    </h4>
                    <div className="p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
                      <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">
                        {JSON.stringify(selectedQuery.reasoning_path, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
