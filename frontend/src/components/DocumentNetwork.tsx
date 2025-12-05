'use client'

import { useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  Panel,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Document {
  id: string
  name: string
  insurer: string
  category: string
  status: string
  processing_detail?: {
    quality_score?: number
    total_pages?: number
  }
}

interface DocumentNetworkProps {
  onDocumentSelect?: (document: Document) => void
}

// 보험사별 색상 매핑
const INSURER_COLORS: Record<string, string> = {
  '메트라이프생명': '#3b82f6', // blue
  '삼성생명': '#10b981', // green
  'KB생명': '#f59e0b', // amber
  '한화생명': '#ef4444', // red
  'default': '#6b7280', // gray
}

export default function DocumentNetwork({ onDocumentSelect }: DocumentNetworkProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    avgQuality: 0,
  })

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // 문서 데이터 가져오기
  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('http://localhost:3030/api/v1/crawler/documents?limit=1000')
      if (!response.ok) throw new Error('Failed to fetch documents')

      const result = await response.json()
      const data: Document[] = result.items || []
      setDocuments(data)

      // 통계 계산
      const completedDocs = data.filter(d => d.status === 'completed')
      const qualityScores = completedDocs
        .map(d => d.processing_detail?.quality_score || 0)
        .filter(score => score > 0)

      setStats({
        total: data.length,
        completed: completedDocs.length,
        avgQuality: qualityScores.length > 0
          ? Math.round(qualityScores.reduce((a, b) => a + b, 0) / qualityScores.length)
          : 0,
      })

      // 그래프 노드/엣지 생성
      createGraphData(data)
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const createGraphData = (docs: Document[]) => {
    // 보험사별로 그룹화
    const insurerGroups: Record<string, Document[]> = {}
    docs.forEach(doc => {
      if (!insurerGroups[doc.insurer]) {
        insurerGroups[doc.insurer] = []
      }
      insurerGroups[doc.insurer].push(doc)
    })

    const graphNodes: Node[] = []
    const graphEdges: Edge[] = []

    // 각 보험사별로 중심 노드 생성
    const insurers = Object.keys(insurerGroups)
    insurers.forEach((insurer, insurerIndex) => {
      const color = INSURER_COLORS[insurer] || INSURER_COLORS.default
      const insurerDocs = insurerGroups[insurer]

      // 보험사 중심 노드
      const centerX = (insurerIndex % 3) * 400 + 200
      const centerY = Math.floor(insurerIndex / 3) * 400 + 200

      graphNodes.push({
        id: `insurer-${insurer}`,
        type: 'default',
        position: { x: centerX, y: centerY },
        data: {
          label: `${insurer} (${insurerDocs.length})`,
        },
        style: {
          background: color,
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          padding: '10px 20px',
          fontSize: '14px',
          fontWeight: 'bold',
        },
      })

      // 각 문서 노드 (중심 노드 주위에 원형 배치)
      insurerDocs.slice(0, 10).forEach((doc, docIndex) => {
        const angle = (docIndex / Math.min(insurerDocs.length, 10)) * 2 * Math.PI
        const radius = 120
        const x = centerX + Math.cos(angle) * radius
        const y = centerY + Math.sin(angle) * radius

        const nodeId = `doc-${doc.id}`
        graphNodes.push({
          id: nodeId,
          type: 'default',
          position: { x, y },
          data: {
            label: doc.name.length > 20 ? doc.name.substring(0, 20) + '...' : doc.name,
            document: doc,
          },
          style: {
            background: doc.status === 'completed' ? '#10b981' : '#94a3b8',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 12px',
            fontSize: '11px',
            cursor: 'pointer',
          },
        })

        // 보험사 노드와 연결
        graphEdges.push({
          id: `edge-${insurer}-${doc.id}`,
          source: `insurer-${insurer}`,
          target: nodeId,
          style: { stroke: color, strokeWidth: 1.5 },
          animated: doc.status === 'processing',
        })
      })

      // 같은 카테고리 문서끼리 연결
      const categories: Record<string, string[]> = {}
      insurerDocs.slice(0, 10).forEach(doc => {
        if (!categories[doc.category]) {
          categories[doc.category] = []
        }
        categories[doc.category].push(`doc-${doc.id}`)
      })

      Object.values(categories).forEach(docIds => {
        if (docIds.length > 1) {
          for (let i = 0; i < docIds.length - 1; i++) {
            graphEdges.push({
              id: `category-${docIds[i]}-${docIds[i + 1]}`,
              source: docIds[i],
              target: docIds[i + 1],
              style: { stroke: '#e5e7eb', strokeWidth: 0.5, strokeDasharray: '5,5' },
            })
          }
        }
      })
    })

    setNodes(graphNodes)
    setEdges(graphEdges)
  }

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    if (node.data.document) {
      setSelectedDoc(node.data.document)
      onDocumentSelect?.(node.data.document)
    }
  }, [onDocumentSelect])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">문서 네트워크 로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col gap-4">
      {/* 통계 카드 */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              전체 문서
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total}</div>
            <p className="text-xs text-gray-500 mt-1">학습 대상 문서</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              학습 완료율
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}%
            </div>
            <p className="text-xs text-gray-500 mt-1">{stats.completed}개 완료</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              평균 품질 점수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{stats.avgQuality}점</div>
            <p className="text-xs text-gray-500 mt-1">학습 품질 평가</p>
          </CardContent>
        </Card>
      </div>

      {/* 네트워크 그래프 */}
      <div className="flex-1 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          connectionMode={ConnectionMode.Loose}
          fitView
          attributionPosition="bottom-left"
        >
          <Background />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              if (node.id.startsWith('insurer-')) {
                return node.style?.background as string || '#6b7280'
              }
              return node.data.document?.status === 'completed' ? '#10b981' : '#94a3b8'
            }}
            style={{ background: '#f3f4f6' }}
          />
          <Panel position="top-right" className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-md">
            <div className="text-xs space-y-2">
              <div className="font-semibold text-gray-900 dark:text-gray-100 mb-2">범례</div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-green-600"></div>
                <span className="text-gray-700 dark:text-gray-300">학습 완료</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded bg-gray-400"></div>
                <span className="text-gray-700 dark:text-gray-300">미학습</span>
              </div>
            </div>
          </Panel>
        </ReactFlow>
      </div>

      {/* 선택된 문서 상세정보 */}
      {selectedDoc && (
        <Card className="border-l-4 border-l-blue-600">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-base">{selectedDoc.name}</CardTitle>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline">{selectedDoc.insurer}</Badge>
                  <Badge variant="outline">{selectedDoc.category}</Badge>
                  <Badge
                    className={selectedDoc.status === 'completed' ? 'bg-green-600' : 'bg-gray-400'}
                  >
                    {selectedDoc.status === 'completed' ? '학습 완료' : '미학습'}
                  </Badge>
                </div>
              </div>
              <button
                onClick={() => setSelectedDoc(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </CardHeader>
          {selectedDoc.processing_detail && (
            <CardContent>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">품질 점수:</span>
                  <span className="ml-2 font-semibold">
                    {selectedDoc.processing_detail.quality_score}점
                  </span>
                </div>
                <div>
                  <span className="text-gray-600 dark:text-gray-400">페이지 수:</span>
                  <span className="ml-2 font-semibold">
                    {selectedDoc.processing_detail.total_pages}페이지
                  </span>
                </div>
              </div>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  )
}
