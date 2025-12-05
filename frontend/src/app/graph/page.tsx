'use client'

import { useState, useEffect, useMemo } from 'react'
import dynamic from 'next/dynamic'
import DashboardLayout from '@/components/DashboardLayout'
import GraphControls from '@/components/GraphControls'
import NodeDetail from '@/components/NodeDetail'
import DocumentNetwork from '@/components/DocumentNetwork'
import { useGraphStore } from '@/store/graph-store'
import { useKnowledgeGraphStore } from '@/store/knowledge-graph-store'
import type { GraphNode, NodeType } from '@/types'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

// Dynamically import ReactFlow to avoid SSR issues
const GraphVisualization = dynamic(
  () => import('@/components/GraphVisualization'),
  { ssr: false }
)

export default function GraphPage() {
  // Old Graph Store (for Document Network)
  const {
    graphData,
    selectedNode,
    isLoading,
    error,
    fetchGraph,
    setSelectedNode,
    clearError,
  } = useGraphStore()

  // New Knowledge Graph Store (for Neo4j-based Knowledge Graph)
  const {
    graphData: kgGraphData,
    selectedNode: kgSelectedNode,
    nodeDetail: kgNodeDetail,
    graphStats: kgGraphStats,
    isLoading: kgIsLoading,
    error: kgError,
    fetchGraphData: kgFetchGraphData,
    fetchGraphStats: kgFetchGraphStats,
    setSelectedNode: kgSetSelectedNode,
    searchNodes: kgSearchNodes,
    clearError: kgClearError,
  } = useKnowledgeGraphStore()

  const [filterDocumentIds, setFilterDocumentIds] = useState<string[]>([])
  const [filterNodeTypes, setFilterNodeTypes] = useState<NodeType[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(true)
  const [activeTab, setActiveTab] = useState('document-network')
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastNodeCount, setLastNodeCount] = useState(0)

  // Document Network - 실시간 자동 새로고침
  useEffect(() => {
    if (activeTab !== 'document-network') return

    // 초기 로드
    fetchGraph({ max_nodes: 200 })

    if (!autoRefresh) return

    // 15초마다 그래프 업데이트
    const interval = setInterval(async () => {
      try {
        await fetchGraph({ max_nodes: 200 })
      } catch (error) {
        console.error('Failed to refresh graph:', error)
      }
    }, 15000) // 15초

    return () => clearInterval(interval)
  }, [autoRefresh, fetchGraph, activeTab])

  // Knowledge Graph - 초기 로드
  useEffect(() => {
    if (activeTab !== 'knowledge-graph') return

    // 초기 로드
    kgFetchGraphStats()
    kgFetchGraphData({ limit: 500 })
  }, [activeTab, kgFetchGraphData, kgFetchGraphStats])

  // 노드 수 변화 감지
  useEffect(() => {
    if (graphData?.nodes) {
      const currentNodeCount = graphData.nodes.length
      if (lastNodeCount > 0 && currentNodeCount > lastNodeCount) {
        console.log(`✨ Graph updated: ${currentNodeCount - lastNodeCount} new nodes added`)
      }
      setLastNodeCount(currentNodeCount)
    }
  }, [graphData?.nodes, lastNodeCount])

  const handleApplyFilters = async () => {
    try {
      clearError()

      await fetchGraph({
        document_ids: filterDocumentIds.length > 0 ? filterDocumentIds : undefined,
        node_types: filterNodeTypes.length > 0 ? filterNodeTypes : undefined,
        max_nodes: 200,
      })

      // 그래프 생성 후 선택 초기화 (다음 선택을 위해)
      setFilterDocumentIds([])
      setFilterNodeTypes([])
    } catch (error) {
      console.error('Failed to load graph:', error)
    }
  }

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node)
  }

  const handleCloseNodeDetail = () => {
    setSelectedNode(null)
  }

  // Filter graph data based on search query
  const filteredGraphData = useMemo(() => {
    if (!graphData || !searchQuery) {
      return graphData
    }

    return {
      ...graphData,
      nodes: graphData.nodes.filter((node) =>
        node.label.toLowerCase().includes(searchQuery.toLowerCase())
      ),
      edges: graphData.edges.filter(
        (edge) =>
          graphData.nodes.some(
            (node) =>
              node.id === edge.source &&
              node.label.toLowerCase().includes(searchQuery.toLowerCase())
          ) ||
          graphData.nodes.some(
            (node) =>
              node.id === edge.target &&
              node.label.toLowerCase().includes(searchQuery.toLowerCase())
          )
      ),
    }
  }, [graphData, searchQuery])

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-120px)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-3 px-1">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
              지식 그래프
              {autoRefresh && (
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
                </span>
              )}
            </h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              {activeTab === 'document-network'
                ? `학습된 문서들의 네트워크를 시각화하여 탐색하세요 (노드: ${graphData?.nodes?.length || 0}개)`
                : `보험 약관의 개념과 관계를 시각화하여 탐색하세요 (노드: ${kgGraphStats?.total_nodes.toLocaleString() || 0}개, 관계: ${kgGraphStats?.total_relationships.toLocaleString() || 0}개)`
              }
              {autoRefresh && activeTab === 'document-network' && graphData?.metadata?.last_update && (
                <span className="ml-2 text-xs text-green-600">
                  • 실시간 업데이트 중 (마지막: {graphData.metadata.last_update})
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {/* 자동 새로고침 토글 */}
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                autoRefresh
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {autoRefresh ? '🔄 실시간 업데이트 ON' : '⏸️ 실시간 업데이트 OFF'}
            </button>
            {activeTab === 'knowledge-graph' && (
              <button
                onClick={() => setIsFilterOpen(!isFilterOpen)}
                className="btn-secondary flex items-center gap-2"
                aria-label={isFilterOpen ? '필터 닫기' : '필터 열기'}
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                  />
                </svg>
                {isFilterOpen ? '필터 닫기' : '필터 열기'}
              </button>
            )}
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col px-1">
          <TabsList className="mb-4">
            <TabsTrigger value="document-network">문서 네트워크</TabsTrigger>
            <TabsTrigger value="knowledge-graph">지식 그래프</TabsTrigger>
          </TabsList>

          {/* Document Network Tab */}
          <TabsContent value="document-network" className="flex-1 mt-0">
            <DocumentNetwork />
          </TabsContent>

          {/* Knowledge Graph Tab */}
          <TabsContent value="knowledge-graph" className="flex-1 mt-0 overflow-hidden">
            <div className="h-full flex flex-col gap-2">
              <div className="flex-1 flex gap-2 overflow-hidden">
                {/* Left Sidebar - Collapsible Filter */}
                <div
                  className={`transition-all duration-300 ease-in-out flex-shrink-0 ${
                    isFilterOpen ? 'w-72' : 'w-0 overflow-hidden'
                  }`}
                >
                  <GraphControls
                    selectedDocumentIds={filterDocumentIds}
                    selectedNodeTypes={filterNodeTypes}
                    searchQuery={searchQuery}
                    onDocumentIdsChange={setFilterDocumentIds}
                    onNodeTypesChange={setFilterNodeTypes}
                    onSearchQueryChange={setSearchQuery}
                    onApplyFilters={handleApplyFilters}
                  />

                  {/* Stats */}
                  {activeTab === 'knowledge-graph' && kgGraphData && (
                    <div className="card mt-4">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">현재 표시</h4>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">노드</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {kgGraphData.nodes.length}개
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">관계</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {kgGraphData.edges.length}개
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                  {activeTab === 'document-network' && graphData && (
                    <div className="card mt-4">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">통계</h4>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">노드</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {graphData.metadata?.total_nodes || graphData.nodes.length}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600 dark:text-gray-400">엣지</span>
                          <span className="font-medium text-gray-900 dark:text-gray-100">
                            {graphData.metadata?.total_edges || graphData.edges.length}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Main Graph Area */}
                <div className="flex-1 overflow-hidden">
                  {/* Knowledge Graph Error */}
                  {activeTab === 'knowledge-graph' && kgError && (
                    <div className="card bg-red-50 border border-red-200 mb-6">
                      <p className="text-sm text-red-700">{kgError}</p>
                    </div>
                  )}

                  {/* Document Network Error */}
                  {activeTab === 'document-network' && error && (
                    <div className="card bg-red-50 border border-red-200 mb-6">
                      <p className="text-sm text-red-700">{error}</p>
                    </div>
                  )}

                  {/* Knowledge Graph Loading */}
                  {activeTab === 'knowledge-graph' && kgIsLoading ? (
                    <div className="card flex items-center justify-center h-full">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
                        <p className="mt-4 text-gray-600 dark:text-gray-400">지식 그래프 로딩 중...</p>
                      </div>
                    </div>
                  ) : activeTab === 'knowledge-graph' && kgGraphData ? (
                    <div className="h-full rounded-lg overflow-hidden">
                      <GraphVisualization
                        data={kgGraphData}
                        onNodeClick={(node: any) => kgSetSelectedNode(node)}
                        selectedNodeId={kgSelectedNode?.id}
                      />
                    </div>
                  ) : null}

                  {/* Document Network Loading */}
                  {activeTab === 'document-network' && isLoading ? (
                    <div className="card flex items-center justify-center h-full">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
                        <p className="mt-4 text-gray-600 dark:text-gray-400">그래프 생성 중...</p>
                      </div>
                    </div>
                  ) : activeTab === 'document-network' && filteredGraphData ? (
                    <div className="h-full rounded-lg overflow-hidden">
                      <GraphVisualization
                        data={filteredGraphData}
                        onNodeClick={handleNodeClick}
                        selectedNodeId={selectedNode?.id}
                      />
                    </div>
                  ) : null}
                </div>
              </div>

              {/* Legend */}
              {graphData && graphData.nodes.length > 0 && (
                <div className="mt-2">
                  <div className="flex items-center justify-center gap-6 text-xs">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-blue-600"></div>
                      <span className="text-gray-700 dark:text-gray-300">보험상품</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-emerald-600"></div>
                      <span className="text-gray-700 dark:text-gray-300">보장</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-red-600"></div>
                      <span className="text-gray-700 dark:text-gray-300">질병</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-amber-600"></div>
                      <span className="text-gray-700 dark:text-gray-300">조건</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded bg-violet-600"></div>
                      <span className="text-gray-700 dark:text-gray-300">조항</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>

      {/* Node Detail Modal - Document Network */}
      {activeTab === 'document-network' && selectedNode && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={handleCloseNodeDetail}
        >
          <div
            className="bg-white dark:bg-dark-surface rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <NodeDetail node={selectedNode} onClose={handleCloseNodeDetail} />
          </div>
        </div>
      )}

      {/* Node Detail Modal - Knowledge Graph */}
      {activeTab === 'knowledge-graph' && kgSelectedNode && kgNodeDetail && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => kgSetSelectedNode(null)}
        >
          <div
            className="bg-white dark:bg-dark-surface rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="sticky top-0 bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-gray-700 p-4 flex items-start justify-between">
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100">{kgNodeDetail.label}</h3>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  {kgNodeDetail.type} • {kgNodeDetail.insurer} • {kgNodeDetail.product_type}
                </p>
              </div>
              <button
                onClick={() => kgSetSelectedNode(null)}
                className="ml-4 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                aria-label="Close"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Content */}
            <div className="p-4 space-y-4">
              {/* Description */}
              {kgNodeDetail.description && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">설명</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{kgNodeDetail.description}</p>
                </div>
              )}

              {/* Source Text */}
              {kgNodeDetail.source_text && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">원문</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-3 rounded">
                    {kgNodeDetail.source_text}
                  </p>
                </div>
              )}

              {/* Neighbors */}
              {kgNodeDetail.neighbors && kgNodeDetail.neighbors.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                    연결된 노드 ({kgNodeDetail.neighbors.length}개)
                  </h4>
                  <div className="space-y-2 max-h-60 overflow-y-auto">
                    {kgNodeDetail.neighbors.map((neighbor, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-gray-50 dark:bg-gray-800 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-colors"
                        onClick={() => {
                          kgSetSelectedNode(null)
                          // Wait for modal to close, then load the neighbor
                          setTimeout(() => {
                            kgSetSelectedNode({
                              id: neighbor.entity_id,
                              type: neighbor.type,
                              label: neighbor.label,
                              data: {
                                description: '',
                                source_text: '',
                                insurer: '',
                                product_type: '',
                                document_id: '',
                                created_at: ''
                              }
                            })
                          }, 100)
                        }}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{neighbor.label}</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                              {neighbor.type} • {neighbor.relationship_type}
                            </p>
                            {neighbor.relationship_description && (
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                                {neighbor.relationship_description}
                              </p>
                            )}
                          </div>
                          <span className={`ml-2 px-2 py-1 text-xs rounded ${
                            neighbor.direction === 'outgoing'
                              ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                              : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                          }`}>
                            {neighbor.direction === 'outgoing' ? '→' : '←'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Document ID</p>
                  <p className="text-sm font-mono text-gray-900 dark:text-gray-100">{kgNodeDetail.document_id}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">Entity ID</p>
                  <p className="text-sm font-mono text-gray-900 dark:text-gray-100">{kgNodeDetail.entity_id}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
