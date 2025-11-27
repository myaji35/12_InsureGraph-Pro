'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import DashboardLayout from '@/components/DashboardLayout'
import GraphControls from '@/components/GraphControls'
import NodeDetail from '@/components/NodeDetail'
import { useGraphStore } from '@/store/graph-store'
import type { GraphNode, NodeType } from '@/types'

// Dynamically import ReactFlow to avoid SSR issues
const GraphVisualization = dynamic(
  () => import('@/components/GraphVisualization'),
  { ssr: false }
)

export default function GraphPage() {
  const {
    graphData,
    selectedNode,
    isLoading,
    error,
    fetchGraph,
    setSelectedNode,
    clearError,
  } = useGraphStore()

  const [filterDocumentIds, setFilterDocumentIds] = useState<string[]>([])
  const [filterNodeTypes, setFilterNodeTypes] = useState<NodeType[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [isFilterOpen, setIsFilterOpen] = useState(true)

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
  const filteredGraphData = graphData && searchQuery
    ? {
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
    : graphData

  return (
    <DashboardLayout>
      <div className="h-[calc(100vh-120px)] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-3 px-1">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">지식 그래프</h2>
            <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
              보험 약관의 개념과 관계를 시각화하여 탐색하세요
            </p>
          </div>
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
        </div>

        <div className="flex-1 flex gap-2 px-1 overflow-hidden">
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
            {graphData && (
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
            {error && (
              <div className="card bg-red-50 border border-red-200 mb-6">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {isLoading ? (
              <div className="card flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
                  <p className="mt-4 text-gray-600 dark:text-gray-400">그래프 생성 중...</p>
                </div>
              </div>
            ) : (
              <div className="h-full rounded-lg overflow-hidden">
                <GraphVisualization
                  data={filteredGraphData || { nodes: [], edges: [] }}
                  onNodeClick={handleNodeClick}
                  selectedNodeId={selectedNode?.id}
                />
              </div>
            )}
          </div>
        </div>

        {/* Legend */}
        {graphData && graphData.nodes.length > 0 && (
          <div className="px-1 mt-2">
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

      {/* Node Detail Modal */}
      {selectedNode && (
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
    </DashboardLayout>
  )
}
