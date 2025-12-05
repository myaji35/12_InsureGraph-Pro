'use client'

import { useEffect, useRef, useCallback } from 'react'
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
import dagre from 'dagre'
import 'reactflow/dist/style.css'
import type { GraphNode, GraphEdge } from '@/types'

interface GraphVisualizationProps {
  data: {
    nodes: GraphNode[]
    edges: GraphEdge[]
  }
  onNodeClick?: (node: GraphNode) => void
  selectedNodeId?: string | null
}

// Node type to color mapping
const getNodeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    // GraphRAG entity types (from worker)
    insurer: '#3b82f6',        // Blue - 보험사
    product_type: '#8b5cf6',   // Purple - 상품타입
    document: '#10b981',       // Green - 문서

    // Legacy types (for backward compatibility)
    INSURANCE_PRODUCT: '#2563eb',
    COVERAGE: '#10b981',
    DISEASE: '#dc2626',
    CONDITION: '#f59e0b',
    CLAUSE: '#8b5cf6',
    ENTITY: '#6b7280',
  }
  return colorMap[type] || '#6b7280'
}

// Dagre layout algorithm for better graph visualization
const getLayoutedElements = (nodes: Node[], edges: Edge[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  const nodeWidth = 220
  const nodeHeight = 100

  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 150,      // Horizontal spacing between nodes (increased from 100)
    ranksep: 200,      // Vertical spacing between ranks (increased from 150)
    marginx: 80,       // Horizontal margin (increased from 50)
    marginy: 80,       // Vertical margin (increased from 50)
    align: 'UL',       // Align nodes to upper-left for cleaner layout
    ranker: 'tight-tree', // Use tight-tree algorithm for hierarchical layout
  })

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight })
  })

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target)
  })

  dagre.layout(dagreGraph)

  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id)
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - nodeWidth / 2,
        y: nodeWithPosition.y - nodeHeight / 2,
      },
    }
  })

  return { nodes: layoutedNodes, edges }
}

export default function GraphVisualization({
  data,
  onNodeClick,
  selectedNodeId,
}: GraphVisualizationProps) {
  const reactFlowWrapper = useRef<HTMLDivElement>(null)
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  useEffect(() => {
    if (!data.nodes || !data.edges) return

    const flowNodes: Node[] = data.nodes.map((node) => {
      // Size nodes based on their type
      const nodeSize = node.size || (node.type === 'insurer' ? 40 : node.type === 'product_type' ? 30 : 20)
      const scaleFactor = nodeSize / 25 // Base scale

      return {
        id: node.id,
        type: 'default',
        data: {
          label: (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="text-xs font-semibold text-center leading-tight">
                {node.label}
              </div>
              {node.type === 'document' && node.metadata?.title && (
                <div className="text-[10px] text-center opacity-80 mt-1 line-clamp-2">
                  {node.metadata.title}
                </div>
              )}
            </div>
          ),
        },
        position: { x: 0, y: 0 }, // Will be set by dagre layout
        style: {
          background: getNodeColor(node.type),
          color: 'white',
          border: selectedNodeId === node.id ? '3px solid #fbbf24' : '2px solid rgba(255, 255, 255, 0.3)',
          borderRadius: '12px',
          padding: `${8 * scaleFactor}px ${12 * scaleFactor}px`,
          fontSize: `${11 + scaleFactor * 2}px`,
          fontWeight: 600,
          minWidth: `${160 * scaleFactor}px`,
          maxWidth: `${240 * scaleFactor}px`,
          minHeight: '60px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: selectedNodeId === node.id
            ? '0 8px 16px -2px rgba(0, 0, 0, 0.3), 0 0 0 3px rgba(251, 191, 36, 0.5)'
            : '0 4px 8px 0 rgba(0, 0, 0, 0.2)',
          transition: 'all 0.2s ease-in-out',
          cursor: 'pointer',
        },
      }
    })

    const flowEdges: Edge[] = data.edges.map((edge) => ({
      id: edge.id || `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: false,
      label: edge.label || '',
      style: {
        stroke: '#64748b',
        strokeWidth: 2.5,
        strokeOpacity: 0.7,
      },
      labelStyle: {
        fontSize: '10px',
        fill: '#475569',
        fontWeight: 600,
        backgroundColor: 'rgba(255, 255, 255, 0.9)',
        padding: '2px 6px',
        borderRadius: '4px',
      },
      labelBgStyle: {
        fill: 'rgba(255, 255, 255, 0.9)',
        fillOpacity: 0.9,
      },
      labelBgPadding: [4, 6] as [number, number],
      labelBgBorderRadius: 4,
    }))

    // Apply dagre layout
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      flowNodes,
      flowEdges,
      'TB' // Top to Bottom direction
    )

    setNodes(layoutedNodes)
    setEdges(layoutedEdges)
  }, [data, selectedNodeId, setNodes, setEdges])

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const graphNode = data.nodes.find((n) => n.id === node.id)
      if (graphNode && onNodeClick) {
        onNodeClick(graphNode)
      }
    },
    [data.nodes, onNodeClick]
  )

  if (!data.nodes || data.nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50 dark:bg-dark-bg rounded-lg border border-gray-200 dark:border-dark-border">
        <div className="text-center p-8">
          <svg
            className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
            />
          </svg>
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            그래프가 비어있습니다
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 max-w-sm">
            왼쪽 필터에서 문서를 선택하고 그래프 생성 버튼을 클릭하여 지식 그래프를 생성하세요.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div ref={reactFlowWrapper} className="h-full w-full bg-gray-50 dark:bg-dark-bg rounded-lg border border-gray-200 dark:border-dark-border overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        connectionMode={ConnectionMode.Loose}
        fitView
        fitViewOptions={{
          padding: 0.2,
          includeHiddenNodes: false,
        }}
        minZoom={0.1}
        maxZoom={2}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
        }}
      >
        <Background color="#94a3b8" gap={16} />
        <Controls
          className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg shadow-lg"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={(node) => {
            const graphNode = data.nodes.find((n) => n.id === node.id)
            return graphNode ? getNodeColor(graphNode.type) : '#6b7280'
          }}
          className="bg-white dark:bg-dark-surface border border-gray-200 dark:border-dark-border rounded-lg shadow-lg"
          maskColor="rgba(0, 0, 0, 0.1)"
        />
        <Panel position="top-right" className="bg-white dark:bg-dark-surface rounded-lg shadow-lg p-3 m-2">
          <div className="text-xs space-y-1">
            <div className="font-semibold text-gray-700 dark:text-gray-300 mb-2">범례</div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#3b82f6' }}></div>
              <span className="text-gray-600 dark:text-gray-400">보험사</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#8b5cf6' }}></div>
              <span className="text-gray-600 dark:text-gray-400">상품타입</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded" style={{ backgroundColor: '#10b981' }}></div>
              <span className="text-gray-600 dark:text-gray-400">문서</span>
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}
