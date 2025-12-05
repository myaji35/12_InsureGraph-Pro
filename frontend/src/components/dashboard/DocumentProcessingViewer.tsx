'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'

interface ProcessingDetail {
  sub_step?: string
  message?: string
  algorithm?: string
  quality_score?: number
  quality_level?: string
  total_pages?: number
  text_length?: number
  processing_time_seconds?: number
  avg_chars_per_page?: number
  korean_ratio?: number
  english_ratio?: number
  all_attempts?: Array<{
    algorithm: string
    quality_score: number
    text_length: number
    quality_level: string
  }>
}

interface Document {
  id: string
  insurer: string
  product_type: string
  product_name: string
  status: string
  processing_progress: number
  processing_step: string
  processing_detail?: string | ProcessingDetail
  pdf_url: string
  created_at: string
  updated_at: string
}

interface DocumentProcessingViewerProps {
  documentId?: string
  autoSelectLatest?: boolean
}

const PROCESSING_STEPS = [
  { key: 'downloading_pdf', label: 'PDF 다운로드', progress: 20, icon: '📥' },
  { key: 'extracting_text', label: '텍스트 추출', progress: 40, icon: '📝' },
  { key: 'extracting_entities', label: '엔티티 추출', progress: 60, icon: '🏷️' },
  { key: 'extracting_relationships', label: '관계 추출', progress: 80, icon: '🔗' },
  { key: 'building_graph', label: '그래프 구축', progress: 90, icon: '🕸️' },
  { key: 'generating_embeddings', label: '임베딩 생성', progress: 95, icon: '🧠' },
  { key: 'completed', label: '완료', progress: 100, icon: '✅' },
]

export default function DocumentProcessingViewer({
  documentId,
  autoSelectLatest = true,
}: DocumentProcessingViewerProps) {
  const [document, setDocument] = useState<Document | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [processingHistory, setProcessingHistory] = useState<Array<{
    timestamp: string
    step: string
    progress: number
    detail: string
  }>>([])

  useEffect(() => {
    if (documentId) {
      fetchDocumentById(documentId)
      const interval = setInterval(() => fetchDocumentById(documentId), 2000) // 2초마다 업데이트
      return () => clearInterval(interval)
    } else if (autoSelectLatest) {
      fetchLatestProcessingDocument()
      const interval = setInterval(fetchLatestProcessingDocument, 2000)
      return () => clearInterval(interval)
    }
  }, [documentId, autoSelectLatest])

  const fetchDocumentById = async (id: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/crawler/documents/${id}`)
      if (response.ok) {
        const data = await response.json()
        updateDocument(data)
      }
    } catch (error) {
      console.error('Failed to fetch document:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchLatestProcessingDocument = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/crawler/documents?status=processing&limit=1')
      if (response.ok) {
        const result = await response.json()
        const items = result.items || []
        if (items.length > 0) {
          updateDocument(items[0])
        } else {
          setDocument(null)
        }
      }
    } catch (error) {
      console.error('Failed to fetch processing documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const updateDocument = (newDoc: Document) => {
    setDocument(prevDoc => {
      // 진행 상황이 변경되었을 때만 히스토리에 추가
      if (!prevDoc || prevDoc.processing_progress !== newDoc.processing_progress ||
          prevDoc.processing_step !== newDoc.processing_step) {
        const detail = parseProcessingDetail(newDoc.processing_detail)
        setProcessingHistory(prev => [
          {
            timestamp: new Date().toISOString(),
            step: newDoc.processing_step,
            progress: newDoc.processing_progress,
            detail: detail?.message || getStepText(newDoc.processing_step),
          },
          ...prev.slice(0, 19), // 최근 20개만 유지
        ])
      }
      return newDoc
    })
  }

  const parseProcessingDetail = (detail: string | ProcessingDetail | undefined): ProcessingDetail | null => {
    if (!detail) return null
    if (typeof detail === 'string') {
      try {
        return JSON.parse(detail)
      } catch {
        return null
      }
    }
    return detail
  }

  const getStepText = (step: string) => {
    const stepInfo = PROCESSING_STEPS.find(s => s.key === step)
    return stepInfo ? stepInfo.label : step
  }

  const getStepIcon = (step: string) => {
    const stepInfo = PROCESSING_STEPS.find(s => s.key === step)
    return stepInfo ? stepInfo.icon : '⚙️'
  }

  const getCurrentStepIndex = (step: string) => {
    return PROCESSING_STEPS.findIndex(s => s.key === step)
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>문서 학습 과정 뷰어</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!document) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>문서 학습 과정 뷰어</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">📄</div>
            <div className="text-sm">현재 처리 중인 문서가 없습니다</div>
            <div className="text-xs mt-1">새 문서 처리가 시작되면 자동으로 표시됩니다</div>
          </div>
        </CardContent>
      </Card>
    )
  }

  const detail = parseProcessingDetail(document.processing_detail)
  const currentStepIndex = getCurrentStepIndex(document.processing_step)

  return (
    <div className="space-y-4">
      {/* 문서 정보 헤더 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                {getStepIcon(document.processing_step)} 문서 학습 실시간 모니터링
              </CardTitle>
              <p className="text-sm text-gray-600 mt-1">{document.insurer} - {document.product_type}</p>
              <p className="text-xs text-gray-500 truncate max-w-2xl">{document.product_name}</p>
            </div>
            <Badge className={
              document.status === 'completed' ? 'bg-green-600' :
              document.status === 'processing' ? 'bg-blue-600' :
              document.status === 'failed' ? 'bg-red-600' : 'bg-gray-600'
            }>
              {document.status.toUpperCase()}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* 전체 진행률 */}
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">전체 진행률</span>
                <span className="text-sm font-bold text-blue-600">{document.processing_progress}%</span>
              </div>
              <Progress value={document.processing_progress} className="h-3" />
            </div>

            {/* 현재 단계 상세 정보 */}
            {detail?.message && (
              <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  {detail.message}
                </div>
                {detail.sub_step && (
                  <div className="text-xs text-blue-700 dark:text-blue-300 mt-1">
                    세부 단계: {detail.sub_step}
                  </div>
                )}
              </div>
            )}

            {/* 품질 정보 (텍스트 추출 단계) */}
            {detail?.algorithm && (
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                  <div className="text-gray-600 dark:text-gray-400">알고리즘</div>
                  <div className="font-semibold">{detail.algorithm}</div>
                </div>
                {detail.quality_score && (
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                    <div className="text-gray-600 dark:text-gray-400">품질 점수</div>
                    <div className="font-semibold">{detail.quality_score}점</div>
                  </div>
                )}
                {detail.total_pages && (
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                    <div className="text-gray-600 dark:text-gray-400">총 페이지</div>
                    <div className="font-semibold">{detail.total_pages}페이지</div>
                  </div>
                )}
                {detail.processing_time_seconds && (
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded">
                    <div className="text-gray-600 dark:text-gray-400">처리 시간</div>
                    <div className="font-semibold">{detail.processing_time_seconds}초</div>
                  </div>
                )}
              </div>
            )}

            {/* 알고리즘 시도 결과 */}
            {detail?.all_attempts && detail.all_attempts.length > 0 && (
              <div className="border rounded-lg p-3">
                <div className="text-sm font-medium mb-2">알고리즘 품질 비교</div>
                <div className="space-y-2">
                  {detail.all_attempts.map((attempt, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs bg-gray-50 dark:bg-gray-800 p-2 rounded">
                      <span className="font-medium">{attempt.algorithm}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">품질: {attempt.quality_score}점</span>
                        <Badge variant="outline" className="text-xs">
                          {attempt.quality_level}
                        </Badge>
                        {attempt.algorithm === detail.algorithm && (
                          <Badge className="bg-green-600 text-xs">선택됨</Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* 처리 단계 타임라인 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">처리 단계</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {PROCESSING_STEPS.map((step, index) => {
              const isCompleted = index < currentStepIndex || document.status === 'completed'
              const isCurrent = index === currentStepIndex && document.status === 'processing'
              const isUpcoming = index > currentStepIndex && document.status !== 'completed'

              return (
                <div key={step.key} className="flex items-center gap-3">
                  <div className={`
                    flex items-center justify-center w-10 h-10 rounded-full text-lg
                    ${isCompleted ? 'bg-green-600 text-white' : ''}
                    ${isCurrent ? 'bg-blue-600 text-white animate-pulse' : ''}
                    ${isUpcoming ? 'bg-gray-200 dark:bg-gray-700 text-gray-500' : ''}
                  `}>
                    {step.icon}
                  </div>
                  <div className="flex-1">
                    <div className={`font-medium ${isCurrent ? 'text-blue-600' : ''}`}>
                      {step.label}
                    </div>
                    <div className="text-xs text-gray-500">{step.progress}%</div>
                  </div>
                  {isCompleted && <span className="text-green-600">✓</span>}
                  {isCurrent && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* 처리 히스토리 */}
      {processingHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">처리 히스토리 (최근 20개)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {processingHistory.map((entry, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs border-b pb-2 last:border-b-0">
                  <div className="text-gray-500 min-w-16">
                    {new Date(entry.timestamp).toLocaleTimeString('ko-KR', {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })}
                  </div>
                  <div className="font-medium min-w-20">
                    {entry.progress}%
                  </div>
                  <div className="flex-1 text-gray-700 dark:text-gray-300">
                    {entry.detail}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
