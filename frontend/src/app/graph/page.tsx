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

  const handleApplyFilters = async () => {
    try {
      clearError()

      await fetchGraph({
        document_ids: filterDocumentIds.length > 0 ? filterDocumentIds : undefined,
        node_types: filterNodeTypes.length > 0 ? filterNodeTypes : undefined,
        max_nodes: 200,
      })
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
      <div className="max-w-full">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">지식 그래프</h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            보험 약관의 개념과 관계를 시각화하여 탐색하세요
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Column - Controls */}
          <div className="lg:col-span-1">
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
              <div className="card mt-6">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-4">통계</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">노드</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {graphData.metadata?.total_nodes || graphData.nodes.length}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">엣지</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {graphData.metadata?.total_edges || graphData.edges.length}
                    </span>
                  </div>
                  {searchQuery && (
                    <div className="pt-3 border-t border-gray-200 dark:border-dark-border">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600 dark:text-gray-400">필터링된 노드</span>
                        <span className="text-sm font-medium text-primary-600">
                          {filteredGraphData?.nodes.length || 0}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Middle Column - Graph */}
          <div className="lg:col-span-2">
            {error && (
              <div className="card bg-red-50 border border-red-200 mb-6">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {isLoading ? (
              <div className="card flex items-center justify-center" style={{ height: '600px' }}>
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
                  <p className="mt-4 text-gray-600 dark:text-gray-400">그래프 생성 중...</p>
                </div>
              </div>
            ) : (
              <div style={{ height: '600px' }}>
                <GraphVisualization
                  data={filteredGraphData || { nodes: [], edges: [] }}
                  onNodeClick={handleNodeClick}
                  selectedNodeId={selectedNode?.id}
                />
              </div>
            )}

            {/* Legend */}
            {graphData && graphData.nodes.length > 0 && (
              <div className="card mt-6">
                <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">범례</h4>
                <div className="flex flex-wrap gap-4">
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-blue-500"></div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">문서</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-green-500"></div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">엔티티</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-amber-500"></div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">개념</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded bg-violet-500"></div>
                    <span className="text-sm text-gray-700 dark:text-gray-300">조항</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Node Detail */}
          <div className="lg:col-span-1">
            {selectedNode ? (
              <NodeDetail node={selectedNode} onClose={handleCloseNodeDetail} />
            ) : (
              <div className="card text-center py-12">
                <svg
                  className="w-12 h-12 text-gray-400 mx-auto mb-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  노드를 클릭하면
                  <br />
                  상세 정보를 확인할 수 있습니다
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
