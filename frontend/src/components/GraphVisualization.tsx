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

// Node type to color mapping - 다양한 엔티티 타입 지원
const getNodeColor = (type: string): string => {
  const colorMap: Record<string, string> = {
    // 주요 엔티티 타입
    coverage_item: '#3b82f6',      // Blue - 보장항목
    benefit_amount: '#10b981',     // Green - 보험금액
    article: '#8b5cf6',            // Purple - 조항
    period: '#f59e0b',             // Amber - 기간
    exclusion: '#ef4444',          // Red - 제외사항
    rider: '#ec4899',              // Pink - 특약
    term: '#6366f1',               // Indigo - 조건
    payment_condition: '#14b8a6',  // Teal - 지급조건

    // GraphRAG 타입
    insurer: '#2563eb',            // Dark Blue - 보험사
    product_type: '#7c3aed',       // Dark Purple - 상품타입
    document: '#059669',           // Dark Green - 문서

    // 기타
    unknown: '#6b7280',            // Gray - 미분류
  }
  return colorMap[type] || '#6b7280'
}

// Circular layout - 원형으로 노드 배치하여 가독성 향상
const getCircularLayout = (nodes: Node[], edges: Edge[]) => {
  const centerX = 800
  const centerY = 600
  const radius = Math.min(600, Math.max(300, nodes.length * 8))

  const layoutedNodes = nodes.map((node, index) => {
    const angle = (2 * Math.PI * index) / nodes.length
    return {
      ...node,
      position: {
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      },
    }
  })

  return { nodes: layoutedNodes, edges }
}

// Force-directed layout simulation - 타입별 클러스터 배치
const getForceLayout = (nodes: Node[], edges: Edge[]) => {
  // 노드를 엔티티 타입별로 그룹화
  const nodesByType: Record<string, Node[]> = {}

  nodes.forEach(node => {
    // node.data.entityType에서 실제 엔티티 타입 추출
    const entityType = (node.data as any).entityType || 'unknown'
    if (!nodesByType[entityType]) nodesByType[entityType] = []
    nodesByType[entityType].push(node)
  })

  const types = Object.keys(nodesByType)
  const layoutedNodes: Node[] = []

  console.log('📊 Graph Layout - Types:', types)
  console.log('📊 Graph Layout - Node counts:', types.map(t => `${t}: ${nodesByType[t].length}`))

  // 타입별로 클러스터 배치 (2x2 그리드)
  types.forEach((type, typeIndex) => {
    const nodesInType = nodesByType[type]
    const clusterCenterX = 400 + (typeIndex % 2) * 600
    const clusterCenterY = 400 + Math.floor(typeIndex / 2) * 600

    // 노드 수에 따라 반지름 조정 (더 넉넉하게)
    const clusterRadius = Math.min(350, Math.max(180, nodesInType.length * 12))

    nodesInType.forEach((node, nodeIndex) => {
      const angle = (2 * Math.PI * nodeIndex) / nodesInType.length
      const radiusVariation = clusterRadius * (0.8 + Math.random() * 0.4) // 반지름에 변화 추가
      const jitter = (Math.random() - 0.5) * 60

      layoutedNodes.push({
        ...node,
        position: {
          x: clusterCenterX + (radiusVariation * Math.cos(angle)) + jitter,
          y: clusterCenterY + (radiusVariation * Math.sin(angle)) + jitter,
        },
      })
    })
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
      const nodeColor = getNodeColor(node.type)
      const isSelected = selectedNodeId === node.id

      // 의미 있는 텍스트 추출
      const getDisplayText = () => {
        // metadata에서 description이나 source_text 가져오기
        const description = node.metadata?.description || node.data?.description || ''
        const sourceText = node.metadata?.source_text || node.data?.source_text || ''

        // description이 있으면 앞부분만 사용
        if (description && description.length > 3) {
          return description.slice(0, 15).trim()
        }

        // source_text가 있으면 앞부분만 사용
        if (sourceText && sourceText.length > 3) {
          return sourceText.slice(0, 15).trim()
        }

        // 아니면 label 그대로 사용
        return node.label
      }

      const displayText = getDisplayText()

      return {
        id: node.id,
        type: 'default',
        data: {
          label: (
            <div
              style={{
                width: '85px',
                height: '85px',
                borderRadius: '50%',
                background: `radial-gradient(circle at 35% 35%, ${nodeColor}ff, ${nodeColor}dd)`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '8px',
                boxSizing: 'border-box',
                boxShadow: isSelected
                  ? '0 12px 32px rgba(0,0,0,0.3), 0 4px 12px rgba(0,0,0,0.2), inset 0 2px 4px rgba(255,255,255,0.3), 0 0 0 4px #fbbf24'
                  : '0 8px 20px rgba(0,0,0,0.25), 0 3px 8px rgba(0,0,0,0.15), inset 0 2px 4px rgba(255,255,255,0.25)',
                border: isSelected ? '3px solid #ffffff' : '2px solid rgba(255,255,255,0.4)',
                transform: isSelected ? 'scale(1.1)' : 'scale(1)',
                transition: 'all 0.3s ease',
              }}
            >
              <span style={{
                fontSize: '10px',
                fontWeight: '700',
                textAlign: 'center',
                lineHeight: '1.3',
                color: '#ffffff',
                wordBreak: 'break-word',
                display: 'block',
                textShadow: '0 1px 2px rgba(0,0,0,0.4)',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}>
                {displayText}
              </span>
            </div>
          ),
          entityType: node.type,
        },
        position: { x: 0, y: 0 },
        style: {
          background: 'transparent',
          border: 'none',
          padding: 0,
        },
      }
    })

    const flowEdges: Edge[] = data.edges.map((edge) => ({
      id: edge.id || `${edge.source}-${edge.target}`,
      source: edge.source,
      target: edge.target,
      type: 'smoothstep',
      animated: false, // 애니메이션 비활성화 (성능 향상)
      // label 제거 - 깔끔한 시각화
      style: {
        stroke: '#94a3b8',
        strokeWidth: 2,
        strokeOpacity: 0.4,
        strokeLinecap: 'round',
        strokeLinejoin: 'round',
      },
      markerEnd: {
        type: 'arrowclosed',
        width: 15,
        height: 15,
        color: '#94a3b8',
      },
    }))

    // Apply layout based on node count
    if (flowNodes.length > 100) {
      // Simple grid layout for very large graphs (>100 nodes)
      const gridSize = Math.ceil(Math.sqrt(flowNodes.length))
      const spacing = 300

      const gridNodes = flowNodes.map((node, index) => {
        const row = Math.floor(index / gridSize)
        const col = index % gridSize
        return {
          ...node,
          position: {
            x: col * spacing,
            y: row * spacing,
          },
        }
      })

      setNodes(gridNodes)
      setEdges(flowEdges)
    } else {
      // Use force-directed layout for better visualization
      const { nodes: layoutedNodes, edges: layoutedEdges } = getForceLayout(
        flowNodes,
        flowEdges
      )
      setNodes(layoutedNodes)
      setEdges(layoutedEdges)
    }
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
      <style>{`
        .react-flow__node {
          transition: all 0.2s ease-in-out;
        }
        .react-flow__node:hover {
          filter: brightness(1.15);
          z-index: 100 !important;
        }
        .react-flow__node.selected {
          z-index: 1000 !important;
        }
        .react-flow__edge-path {
          transition: all 0.2s ease;
        }
        .react-flow__edge:hover .react-flow__edge-path {
          stroke-width: 3px !important;
          stroke-opacity: 0.8 !important;
        }
        /* 엣지 레이블 숨기기 */
        .react-flow__edge-text {
          display: none;
        }
      `}</style>
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
        <Background
          color="#cbd5e1"
          gap={20}
          size={1.5}
          style={{
            backgroundColor: '#f8fafc',
          }}
        />
        <Controls
          className="bg-white/90 dark:bg-dark-surface/90 backdrop-blur-sm border border-gray-200 dark:border-dark-border rounded-lg shadow-xl"
          showInteractive={false}
        />
        <MiniMap
          nodeColor={(node) => {
            const graphNode = data.nodes.find((n) => n.id === node.id)
            return graphNode ? getNodeColor(graphNode.type) : '#6b7280'
          }}
          className="bg-white/90 dark:bg-dark-surface/90 backdrop-blur-sm border border-gray-200 dark:border-dark-border rounded-lg shadow-xl"
          maskColor="rgba(0, 0, 0, 0.08)"
          nodeStrokeWidth={3}
        />
        <Panel position="top-right" className="bg-white/95 dark:bg-dark-surface/95 backdrop-blur-md rounded-xl shadow-2xl p-4 m-3 border border-gray-100 dark:border-dark-border max-h-[400px] overflow-y-auto">
          <div className="text-xs space-y-2">
            <div className="font-bold text-gray-800 dark:text-gray-200 mb-3 text-sm">엔티티 타입</div>
            <div className="grid grid-cols-1 gap-2">
              {/* 주요 엔티티 */}
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#3b82f6' }}></div>
                <span className="text-gray-700 dark:text-gray-300 text-xs">보장항목</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#10b981' }}></div>
                <span className="text-gray-700 dark:text-gray-300 text-xs">보험금액</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#8b5cf6' }}></div>
                <span className="text-gray-700 dark:text-gray-300 text-xs">조항</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#f59e0b' }}></div>
                <span className="text-gray-700 dark:text-gray-300 text-xs">기간</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#ef4444' }}></div>
                <span className="text-gray-700 dark:text-gray-300 text-xs">제외사항</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ background: '#ec4899' }}></div>
                <span className="text-gray-700 dark:text-gray-300 text-xs">특약</span>
              </div>
            </div>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  )
}
