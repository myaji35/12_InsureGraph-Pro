'use client'

import { useCallback, useEffect, useMemo } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from 'reactflow'
import 'reactflow/dist/style.css'
import dagre from 'dagre'
import type { GraphData, GraphNode as CustomGraphNode, GraphEdge, NodeType } from '@/types'

interface GraphVisualizationProps {
  data: GraphData
  onNodeClick?: (node: CustomGraphNode) => void
  selectedNodeId?: string | null
}

// Node type colors - 실제 Neo4j 노드 타입에 맞춘 색상
const nodeColors: Record<string, string> = {
  // Neo4j 노드 타입
  product: '#2563EB',    // blue-600 - 보험 상품
  coverage: '#059669',   // emerald-600 - 보장
  disease: '#DC2626',    // red-600 - 질병
  condition: '#D97706',  // amber-600 - 조건
  clause: '#7C3AED',     // violet-600 - 조항

  // 기존 타입 (호환성)
  document: '#2563EB',   // blue-600
  entity: '#059669',     // emerald-600
  concept: '#D97706',    // amber-600

  // 기본값
  unknown: '#6B7280',    // gray-500
}

// Layout algorithm using dagre
const getLayoutedElements = (nodes: Node[], edges: Edge[]) => {
  const dagreGraph = new dagre.graphlib.Graph()
  dagreGraph.setDefaultEdgeLabel(() => ({}))

  const nodeWidth = 180
  const nodeHeight = 60

  dagreGraph.setGraph({ rankdir: 'TB', nodesep: 100, ranksep: 150 })

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
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])

  // Convert graph data to React Flow format
  useEffect(() => {
    if (!data || !data.nodes || !data.edges) return

    const flowNodes: Node[] = data.nodes.map((node) => ({
      id: node.id,
      type: 'default',
      position: { x: 0, y: 0 }, // Will be set by layout algorithm
      data: {
        label: node.label,
        customData: node,
      },
      style: {
        backgroundColor: nodeColors[node.type] || nodeColors['unknown'],
        color: 'white',
        border: selectedNodeId === node.id ? '3px solid #1E40AF' : 'none',
        borderRadius: '8px',
        padding: '10px',
        fontSize: '12px',
        fontWeight: '600',
        width: 180,
        height: 60,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    }))

    const flowEdges: Edge[] = data.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      type: 'smoothstep',
      animated: false,
      style: {
        stroke: '#475569',
        strokeWidth: edge.weight ? Math.max(2, edge.weight * 3) : 2,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#475569',
        width: 20,
        height: 20,
      },
      labelStyle: {
        fontSize: 11,
        fontWeight: 600,
        fill: '#334155',
        background: '#FFFFFF',
        padding: 4,
        borderRadius: 3,
      },
      labelBgPadding: [8, 4] as [number, number],
      labelBgBorderRadius: 4,
      labelBgStyle: {
        fill: '#FFFFFF',
        fillOpacity: 0.9,
      },
    }))

    // Apply layout
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      flowNodes,
      flowEdges
    )

    setNodes(layoutedNodes)
    setEdges(layoutedEdges)
  }, [data, selectedNodeId, setNodes, setEdges])

  const handleNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (onNodeClick && node.data.customData) {
        onNodeClick(node.data.customData)
      }
    },
    [onNodeClick]
  )

  if (!data || !data.nodes || data.nodes.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-gray-50 dark:bg-dark-elevated rounded-lg">
        <div className="text-center">
          <svg
            className="w-16 h-16 text-gray-400 dark:text-gray-500 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
          <p className="text-gray-600 dark:text-gray-300 font-medium">그래프 데이터가 없습니다</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">
            문서를 선택하거나 필터를 조정하세요
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full bg-gray-50 dark:bg-dark-elevated rounded-lg overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={handleNodeClick}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
      >
        <Background color="#E2E8F0" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const customData = node.data.customData as CustomGraphNode
            return customData
              ? nodeColors[customData.type] || nodeColors['unknown']
              : nodeColors['unknown']
          }}
          maskColor="rgba(255, 255, 255, 0.8)"
        />
      </ReactFlow>
    </div>
  )
}
