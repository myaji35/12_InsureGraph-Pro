'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

interface CrawlerDocument {
  id: string
  insurer: string
  product_name: string
  product_type: string
  status: string
  processing_progress: number
  processing_step: string
  processing_detail?: string | { message?: string; sub_step?: string; [key: string]: any }
  pdf_url: string
  created_at: string
  updated_at: string
}

interface CrawlingStats {
  total: number
  pending: number
  processing: number
  completed: number
  failed: number
}

export default function CrawlingProgressMonitor() {
  const [stats, setStats] = useState<CrawlingStats>({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
  })
  const [processingDocs, setProcessingDocs] = useState<CrawlerDocument[]>([])
  const [recentCompleted, setRecentCompleted] = useState<CrawlerDocument[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 3000) // 3초마다 업데이트
    return () => clearInterval(interval)
  }, [])

  const fetchData = async () => {
    try {
      // 1. 초고속 통계 조회 (새 API 사용)
      const statsRes = await fetch('http://localhost:8000/api/v1/crawler/stats')
      if (statsRes.ok) {
        const newStats = await statsRes.json()
        setStats({
          total: newStats.total,
          pending: newStats.pending,
          processing: newStats.processing,
          completed: newStats.completed,
          failed: newStats.failed,
        })
      }

      // 2. 처리 중인 문서들 (최대 5개)
      const processingRes = await fetch('http://localhost:8000/api/v1/crawler/documents?status=processing&limit=5')
      if (processingRes.ok) {
        const result = await processingRes.json()
        setProcessingDocs(result.items || [])
      }

      // 3. 최근 완료된 문서들 (최대 5개)
      const completedRes = await fetch('http://localhost:8000/api/v1/crawler/documents?status=completed&limit=5')
      if (completedRes.ok) {
        const result = await completedRes.json()
        const completed = (result.items || []).sort((a: CrawlerDocument, b: CrawlerDocument) =>
          new Date(b.updated_at || b.created_at).getTime() - new Date(a.updated_at || a.created_at).getTime()
        )
        setRecentCompleted(completed)
      }
    } catch (error) {
      console.error('Failed to fetch crawling progress:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600'
      case 'processing':
        return 'text-blue-600'
      case 'failed':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return '완료'
      case 'processing':
        return '처리 중'
      case 'failed':
        return '실패'
      case 'pending':
        return '대기 중'
      default:
        return status
    }
  }

  const getStepText = (step: string) => {
    const stepMap: Record<string, string> = {
      'downloading_pdf': 'PDF 다운로드',
      'extracting_text': '텍스트 추출',
      'extracting_entities': '엔티티 추출',
      'extracting_relationships': '관계 추출',
      'building_graph': '그래프 생성',
      'completed': '완료',
    }
    return stepMap[step] || step
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>실시간 크롤링 진행 상황</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
          </span>
          실시간 크롤링 진행 상황
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* 전체 통계 */}
        <div className="grid grid-cols-5 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold">{stats.total}</div>
            <div className="text-xs text-gray-600">전체</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-600">{stats.pending}</div>
            <div className="text-xs text-gray-600">대기</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{stats.processing}</div>
            <div className="text-xs text-blue-600">처리 중</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{stats.completed}</div>
            <div className="text-xs text-green-600">완료</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
            <div className="text-xs text-red-600">실패</div>
          </div>
        </div>

        {/* 전체 진행률 */}
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm font-medium">전체 진행률</span>
            <span className="text-sm text-gray-600">
              {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}%
            </span>
          </div>
          <Progress
            value={stats.total > 0 ? (stats.completed / stats.total) * 100 : 0}
            className="h-2"
          />
        </div>

        {/* 처리 중인 문서들 */}
        {processingDocs.length > 0 && (
          <div>
            <h3 className="font-semibold mb-3 text-sm flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-blue-600 rounded-full animate-pulse"></span>
              현재 처리 중 ({processingDocs.length}개)
            </h3>
            <div className="space-y-3">
              {processingDocs.map((doc) => (
                <div key={doc.id} className="border rounded-lg p-3 bg-blue-50 dark:bg-blue-950">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="font-medium text-sm">{doc.insurer}</div>
                      <div className="text-xs text-gray-600 truncate">{doc.product_name}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-medium text-blue-600">
                        {doc.processing_progress || 0}%
                      </div>
                      <div className="text-xs text-gray-500">
                        {getStepText(doc.processing_step)}
                      </div>
                    </div>
                  </div>
                  <Progress value={doc.processing_progress || 0} className="h-1.5" />
                  {doc.processing_detail && (
                    <div className="text-xs text-gray-500 mt-1 truncate">
                      {typeof doc.processing_detail === 'string'
                        ? doc.processing_detail
                        : doc.processing_detail?.message || JSON.stringify(doc.processing_detail)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 최근 완료된 문서들 */}
        {recentCompleted.length > 0 && (
          <div>
            <h3 className="font-semibold mb-3 text-sm flex items-center gap-2">
              <span className="inline-block w-2 h-2 bg-green-600 rounded-full"></span>
              최근 완료 ({recentCompleted.length}개)
            </h3>
            <div className="space-y-2">
              {recentCompleted.map((doc) => (
                <div key={doc.id} className="flex justify-between items-center border-b pb-2 last:border-b-0">
                  <div>
                    <div className="font-medium text-sm">{doc.insurer}</div>
                    <div className="text-xs text-gray-600 truncate max-w-xs">{doc.product_name}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-green-600">✓ 완료</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 처리 중인 문서가 없을 때 */}
        {processingDocs.length === 0 && stats.processing === 0 && (
          <div className="text-center py-8 text-gray-500">
            <div className="text-4xl mb-2">💤</div>
            <div className="text-sm">현재 처리 중인 문서가 없습니다</div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
