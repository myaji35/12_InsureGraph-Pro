'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

interface LearningStats {
  total_documents: number
  completed_documents: number
  processing_documents: number
  pending_documents: number
  neo4j_nodes: number
  neo4j_relationships: number
  last_processed_at: string | null
}

export default function GraphRAGLearningProgress() {
  const [stats, setStats] = useState<LearningStats>({
    total_documents: 0,
    completed_documents: 0,
    processing_documents: 0,
    pending_documents: 0,
    neo4j_nodes: 0,
    neo4j_relationships: 0,
    last_processed_at: null
  })
  const [isLoading, setIsLoading] = useState(true)

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/crawler/stats/learning', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to fetch learning stats:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()

    // 10초마다 자동 새로고침
    const interval = setInterval(fetchStats, 10000)
    return () => clearInterval(interval)
  }, [])

  const completionRate = stats.total_documents > 0
    ? (stats.completed_documents / stats.total_documents) * 100
    : 0

  return (
    <Card className="border-2 border-purple-200 dark:border-purple-800">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">🧠</span>
            <span>GraphRAG 학습 진행 상황</span>
          </CardTitle>
          {stats.processing_documents > 0 && (
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-purple-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-purple-500"></span>
            </span>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* 전체 진행률 */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">전체 학습 진행률</span>
                <span className="text-sm font-bold text-purple-600">
                  {completionRate.toFixed(1)}%
                </span>
              </div>
              <Progress value={completionRate} className="h-3" />
              <p className="text-xs text-muted-foreground mt-2">
                {stats.completed_documents} / {stats.total_documents} 문서 완료
              </p>
            </div>

            {/* 상태별 통계 */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
                <div className="text-2xl font-bold text-green-600">
                  {stats.completed_documents}
                </div>
                <div className="text-xs text-green-700 dark:text-green-400 mt-1">
                  ✅ 학습 완료
                </div>
              </div>

              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <div className="text-2xl font-bold text-blue-600">
                  {stats.processing_documents}
                </div>
                <div className="text-xs text-blue-700 dark:text-blue-400 mt-1">
                  🔄 처리 중
                </div>
              </div>

              <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4">
                <div className="text-2xl font-bold text-orange-600">
                  {stats.pending_documents}
                </div>
                <div className="text-xs text-orange-700 dark:text-orange-400 mt-1">
                  ⏳ 대기 중
                </div>
              </div>
            </div>

            {/* Neo4j 지식 그래프 통계 */}
            <div className="border-t pt-4">
              <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                <span>📊</span>
                <span>Neo4j 지식 그래프</span>
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3">
                  <div className="text-xl font-bold text-purple-600">
                    {stats.neo4j_nodes.toLocaleString()}
                  </div>
                  <div className="text-xs text-purple-700 dark:text-purple-400 mt-1">
                    노드 (엔티티)
                  </div>
                </div>

                <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-3">
                  <div className="text-xl font-bold text-indigo-600">
                    {stats.neo4j_relationships.toLocaleString()}
                  </div>
                  <div className="text-xs text-indigo-700 dark:text-indigo-400 mt-1">
                    관계 (엣지)
                  </div>
                </div>
              </div>
            </div>

            {/* 마지막 처리 시간 */}
            {stats.last_processed_at && (
              <div className="text-xs text-muted-foreground text-center pt-2 border-t">
                마지막 업데이트: {new Date(stats.last_processed_at).toLocaleString('ko-KR')}
              </div>
            )}

            {/* 상태 메시지 */}
            {stats.processing_documents > 0 && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-3">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  🔄 현재 {stats.processing_documents}개 문서를 처리하고 있습니다...
                </p>
              </div>
            )}

            {stats.processing_documents === 0 && stats.pending_documents > 0 && (
              <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg p-3">
                <p className="text-sm text-orange-700 dark:text-orange-300">
                  ⏳ {stats.pending_documents}개 문서가 처리를 기다리고 있습니다.
                </p>
              </div>
            )}

            {stats.completed_documents === stats.total_documents && stats.total_documents > 0 && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-3">
                <p className="text-sm text-green-700 dark:text-green-300">
                  ✅ 모든 문서의 학습이 완료되었습니다!
                </p>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
