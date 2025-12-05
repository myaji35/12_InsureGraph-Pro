'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import DashboardLayout from '@/components/DashboardLayout'
import { useDocumentStore } from '@/store/document-store'
import { Progress } from '@/components/ui/progress'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  FunnelIcon,
  Squares2X2Icon,
  ListBulletIcon,
} from '@heroicons/react/24/outline'
import { formatDate } from '@/lib/utils'

export default function DocumentsPage() {
  const router = useRouter()
  const { documents, pagination, isLoading, fetchDocuments } = useDocumentStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [filterInsurer, setFilterInsurer] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [viewMode, setViewMode] = useState<'list' | 'grouped'>('grouped') // 그룹 뷰가 기본
  const [processingProgress, setProcessingProgress] = useState<Record<string, number>>({})
  const [processingSteps, setProcessingSteps] = useState<Record<string, string>>({})

  useEffect(() => {
    loadDocuments()
  }, [currentPage, filterInsurer, filterStatus])

  // 처리 중인 문서의 진행률 polling
  useEffect(() => {
    const processingDocs = documents?.filter(doc => doc.status === 'processing') || []

    if (processingDocs.length === 0) {
      // 처리 중인 문서가 없으면 진행률 초기화
      setProcessingProgress({})
      return
    }

    // 실제 API에서 진행률 가져오기
    const fetchProgress = async () => {
      const newProgress: Record<string, number> = {}
      const newSteps: Record<string, string> = {}

      await Promise.all(
        processingDocs.map(async (doc) => {
          try {
            const response = await fetch(
              `http://localhost:3030/api/v1/documents/${doc.document_id}/processing-status`
            )

            if (response.ok) {
              const data = await response.json()
              newProgress[doc.document_id] = data.progress_percentage || 0
              newSteps[doc.document_id] = data.current_step || '처리 중...'
            } else {
              // API 오류시 기존 진행률 유지 또는 0
              newProgress[doc.document_id] = processingProgress[doc.document_id] || 0
              newSteps[doc.document_id] = processingSteps[doc.document_id] || '처리 중...'
            }
          } catch (error) {
            console.error(`Failed to fetch progress for ${doc.document_id}:`, error)
            newProgress[doc.document_id] = processingProgress[doc.document_id] || 0
            newSteps[doc.document_id] = processingSteps[doc.document_id] || '처리 중...'
          }
        })
      )

      setProcessingProgress(newProgress)
      setProcessingSteps(newSteps)
    }

    // 즉시 한 번 실행
    fetchProgress()

    // 3초마다 업데이트
    const interval = setInterval(fetchProgress, 3000)

    return () => clearInterval(interval)
  }, [documents])

  const loadDocuments = async () => {
    try {
      await fetchDocuments({
        insurer: filterInsurer || undefined,
        status: filterStatus || undefined,
        page: currentPage,
        page_size: 10,
      })
    } catch (error) {
      console.error('Failed to load documents:', error)
    }
  }

  const handleStartProcessing = async (documentId: string) => {
    try {
      const response = await fetch(
        `http://localhost:3030/api/v1/documents/${documentId}/start-processing`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      )

      if (response.ok) {
        // 문서 목록 다시 로드
        await loadDocuments()
        alert('문서 처리가 시작되었습니다!')
      } else {
        const error = await response.json()
        alert(`처리 시작 실패: ${error.detail?.error_message || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('Failed to start processing:', error)
      alert('문서 처리 시작에 실패했습니다.')
    }
  }

  const handleRelearn = async (documentId: string, e: React.MouseEvent) => {
    e.stopPropagation()

    const confirmRelearn = confirm(
      '이 문서를 미학습 상태로 초기화하시겠습니까?\n\n' +
      '경고: 학습된 데이터가 모두 삭제되고 처음부터 다시 학습해야 합니다.'
    )

    if (!confirmRelearn) return

    try {
      // 문서 상태를 'pending'으로 변경하는 API 호출
      const response = await fetch(`http://localhost:8000/api/v1/crawler-documents/${documentId}/reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (response.ok) {
        alert('문서가 미학습 상태로 초기화되었습니다.')
        // 문서 목록 다시 로드
        await loadDocuments()
      } else {
        const error = await response.json()
        alert(`초기화 실패: ${error.detail || '알 수 없는 오류'}`)
      }
    } catch (error) {
      console.error('Failed to reset document:', error)
      alert('문서 초기화에 실패했습니다.')
    }
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: string; text: string }> = {
      pending: { color: 'bg-yellow-100 text-yellow-800', text: '대기 중' },
      processing: { color: 'bg-blue-100 text-blue-800', text: '처리 중' },
      ready: { color: 'bg-green-100 text-green-800', text: '완료' },
      failed: { color: 'bg-red-100 text-red-800', text: '실패' },
    }

    const { color, text } = statusMap[status] || { color: 'bg-gray-100 text-gray-800', text: status }

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${color}`}>
        {text}
      </span>
    )
  }

  const filteredDocuments = (documents || []).filter((doc) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return (
        doc.product_name.toLowerCase().includes(query) ||
        doc.insurer.toLowerCase().includes(query) ||
        doc.product_code?.toLowerCase().includes(query)
      )
    }
    return true
  })

  // 보험사별로 문서 그룹핑
  const groupedByInsurer = filteredDocuments.reduce((acc, doc) => {
    const insurer = doc.insurer || '기타'
    if (!acc[insurer]) {
      acc[insurer] = []
    }
    acc[insurer].push(doc)
    return acc
  }, {} as Record<string, typeof documents>)

  // 문서 유형별로 그룹핑
  const groupByDocumentType = (docs: typeof documents) => {
    return docs.reduce((acc, doc) => {
      const type = doc.document_type || 'other'
      if (!acc[type]) {
        acc[type] = []
      }
      acc[type].push(doc)
      return acc
    }, {} as Record<string, typeof documents>)
  }

  const documentTypeLabels: Record<string, string> = {
    terms: '약관',
    brochure: '상품 안내장',
    guide: '가입 설계서',
    other: '기타',
  }

  return (
    <DashboardLayout>
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">문서 관리</h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400">보험 약관 문서를 관리하고 분석하세요</p>
          </div>
          <Link href="/documents/upload">
            <button className="btn-primary flex items-center gap-2">
              <PlusIcon className="w-5 h-5" />
              문서 업로드
            </button>
          </Link>
        </div>
      </div>

      {/* View Toggle */}
      <div className="card mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">표시 방식</h3>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('grouped')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'grouped'
                  ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover'
              }`}
            >
              <Squares2X2Icon className="w-4 h-4" />
              회사별 그룹
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                viewMode === 'list'
                  ? 'bg-primary-100 text-primary-700 dark:bg-primary-900/30 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-dark-hover'
              }`}
            >
              <ListBulletIcon className="w-4 h-4" />
              목록 보기
            </button>
          </div>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="card mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="상품명, 보험사, 상품 코드 검색..."
                className="input-field pl-10"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
          </div>

          {/* Filter by Insurer */}
          <div>
            <select
              className="input-field"
              value={filterInsurer}
              onChange={(e) => {
                setFilterInsurer(e.target.value)
                setCurrentPage(1)
              }}
            >
              <option value="">모든 보험사</option>
              <option value="삼성화재">삼성화재</option>
              <option value="현대해상">현대해상</option>
              <option value="DB손해보험">DB손해보험</option>
              <option value="KB손해보험">KB손해보험</option>
              <option value="메리츠화재">메리츠화재</option>
            </select>
          </div>

          {/* Filter by Status */}
          <div>
            <select
              className="input-field"
              value={filterStatus}
              onChange={(e) => {
                setFilterStatus(e.target.value)
                setCurrentPage(1)
              }}
            >
              <option value="">모든 상태</option>
              <option value="pending">대기 중</option>
              <option value="processing">처리 중</option>
              <option value="ready">완료</option>
              <option value="failed">실패</option>
            </select>
          </div>
        </div>
      </div>

      {/* Documents List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        </div>
      ) : filteredDocuments.length === 0 ? (
        <div className="card text-center py-12">
          <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">문서가 없습니다</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">새로운 문서를 업로드하여 시작하세요</p>
          <Link href="/documents/upload">
            <button className="btn-primary">문서 업로드</button>
          </Link>
        </div>
      ) : viewMode === 'grouped' ? (
        // 회사별 그룹 뷰
        <div className="space-y-6">
          {Object.entries(groupedByInsurer).map(([insurer, insurerDocs]) => {
            const docsByType = groupByDocumentType(insurerDocs)

            return (
              <div key={insurer} className="card">
                <div className="border-b border-gray-200 dark:border-dark-border pb-4 mb-4">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">{insurer}</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    총 {insurerDocs.length}개 문서
                  </p>
                </div>

                <div className="space-y-4">
                  {Object.entries(docsByType).map(([docType, typeDocs]) => (
                    <div key={docType}>
                      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
                        {documentTypeLabels[docType] || docType} ({typeDocs.length})
                      </h4>
                      <div className="grid grid-cols-1 gap-3 pl-4">
                        {typeDocs.map((doc) => (
                          <div
                            key={doc.document_id}
                            className="p-3 rounded-lg bg-gray-50 dark:bg-dark-hover hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                            onClick={() => router.push(`/documents/${doc.document_id}`)}
                          >
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-3 flex-1 min-w-0">
                                <DocumentTextIcon className="w-6 h-6 text-primary-500 flex-shrink-0" />
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 flex-wrap">
                                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                                      {doc.product_name}
                                    </p>
                                    {getStatusBadge(doc.status)}
                                    {(doc.status === 'pending' || doc.status === 'failed') && (
                                      <button
                                        className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded"
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          handleStartProcessing(doc.document_id)
                                        }}
                                      >
                                        처리 시작
                                      </button>
                                    )}
                                    {doc.status === 'ready' && (
                                      <>
                                        <span className="text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 px-2 py-1 rounded font-medium">
                                          학습됨
                                        </span>
                                        <button
                                          className="text-xs bg-purple-600 hover:bg-purple-700 text-white px-2 py-1 rounded font-medium"
                                          onClick={(e) => handleRelearn(doc.document_id, e)}
                                        >
                                          재학습
                                        </button>
                                      </>
                                    )}
                                  </div>
                                  <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {doc.product_code && <span>{doc.product_code}</span>}
                                    {doc.launch_date && <span>출시: {formatDate(doc.launch_date)}</span>}
                                    <span>업로드: {formatDate(doc.created_at)}</span>
                                  </div>
                                </div>
                              </div>
                              <button
                                className="text-primary-600 hover:text-primary-700 text-sm font-medium flex-shrink-0"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  router.push(`/documents/${doc.document_id}`)
                                }}
                              >
                                보기 →
                              </button>
                            </div>

                            {/* 처리 중인 문서에 프로그래스바 표시 */}
                            {doc.status === 'processing' && (
                              <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-xs font-medium text-blue-600 dark:text-blue-400">
                                    {processingSteps[doc.document_id] || '처리 중...'}
                                  </span>
                                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                                    {processingProgress[doc.document_id] || 0}%
                                  </span>
                                </div>
                                <Progress value={processingProgress[doc.document_id] || 0} className="h-2" />
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        // 목록 뷰
        <>
          <div className="grid grid-cols-1 gap-4">
            {filteredDocuments.map((doc) => (
              <div
                key={doc.document_id}
                className="card hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => router.push(`/documents/${doc.document_id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-start gap-4 flex-1">
                    <DocumentTextIcon className="w-12 h-12 text-primary-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
                          {doc.product_name}
                        </h3>
                        {getStatusBadge(doc.status)}
                        {(doc.status === 'pending' || doc.status === 'failed') && (
                          <button
                            className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleStartProcessing(doc.document_id)
                            }}
                          >
                            처리 시작
                          </button>
                        )}
                        {doc.status === 'ready' && (
                          <>
                            <span className="text-sm bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300 px-3 py-1.5 rounded font-medium">
                              학습됨
                            </span>
                            <button
                              className="text-sm bg-purple-600 hover:bg-purple-700 text-white px-3 py-1.5 rounded font-medium"
                              onClick={(e) => handleRelearn(doc.document_id, e)}
                            >
                              재학습
                            </button>
                          </>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{doc.insurer}</p>
                      <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                        {doc.product_code && (
                          <span>상품 코드: {doc.product_code}</span>
                        )}
                        {doc.launch_date && (
                          <span>출시일: {formatDate(doc.launch_date)}</span>
                        )}
                        <span>업로드: {formatDate(doc.created_at)}</span>
                      </div>
                      {doc.tags && doc.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-3">
                          {doc.tags.map((tag, index) => (
                            <span
                              key={index}
                              className="px-2 py-1 bg-gray-100 dark:bg-dark-hover text-gray-700 dark:text-gray-300 text-xs rounded"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                  <button
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                    onClick={(e) => {
                      e.stopPropagation()
                      router.push(`/documents/${doc.document_id}`)
                    }}
                  >
                    자세히 보기 →
                  </button>
                </div>

                {/* 처리 중인 문서에 프로그래스바 표시 */}
                {doc.status === 'processing' && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-blue-600 dark:text-blue-400">
                        {processingSteps[doc.document_id] || '처리 중...'}
                      </span>
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        {processingProgress[doc.document_id] || 0}%
                      </span>
                    </div>
                    <Progress value={processingProgress[doc.document_id] || 0} className="h-2.5" />
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                      문서를 분석하고 지식 그래프를 생성하고 있습니다...
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                총 {pagination.total_items}개 문서 중 {(currentPage - 1) * pagination.page_size + 1}-
                {Math.min(currentPage * pagination.page_size, pagination.total_items)}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={!pagination.has_prev}
                  className="px-4 py-2 border border-gray-300 dark:border-dark-border rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-surface hover:bg-gray-50 dark:hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  이전
                </button>
                <div className="flex items-center gap-2">
                  {Array.from({ length: pagination.total_pages }, (_, i) => i + 1)
                    .filter(
                      (page) =>
                        page === 1 ||
                        page === pagination.total_pages ||
                        Math.abs(page - currentPage) <= 1
                    )
                    .map((page, index, array) => (
                      <div key={page}>
                        {index > 0 && array[index - 1] !== page - 1 && (
                          <span className="px-2 text-gray-500 dark:text-gray-400">...</span>
                        )}
                        <button
                          onClick={() => setCurrentPage(page)}
                          className={`px-4 py-2 border rounded-md text-sm font-medium ${
                            currentPage === page
                              ? 'bg-primary-600 text-white border-primary-600'
                              : 'border-gray-300 dark:border-dark-border text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-surface hover:bg-gray-50 dark:hover:bg-dark-hover'
                          }`}
                        >
                          {page}
                        </button>
                      </div>
                    ))}
                </div>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={!pagination.has_next}
                  className="px-4 py-2 border border-gray-300 dark:border-dark-border rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-surface hover:bg-gray-50 dark:hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  다음
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  )
}
