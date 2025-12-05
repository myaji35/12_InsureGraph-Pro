/**
 * Graph Visualization Component (Story 3.3)
 *
 * Interactive graph visualization using Cytoscape.js
 * Displays reasoning paths from GraphRAG query results
 */
'use client'

import { useEffect, useRef, useState } from 'react'
import cytoscape, { Core, ElementDefinition } from 'cytoscape'
import dagre from 'cytoscape-dagre'
import { GraphPathInfo, GraphNodeInfo } from '@/types/simple-query'

// Register dagre layout algorithm
if (typeof window !== 'undefined') {
  cytoscape.use(dagre)
}

interface GraphVisualizationProps {
  paths: GraphPathInfo[]
  height?: string
  onNodeClick?: (node: GraphNodeInfo) => void
}

interface CytoscapeNode extends ElementDefinition {
  data: {
    id: string
    label: string
    type: string
    text: string
    properties: Record<string, any>
  }
}

interface CytoscapeEdge extends ElementDefinition {
  data: {
    id: string
    source: string
    target: string
    label: string
  }
}

export default function GraphVisualization({
  paths,
  height = '600px',
  onNodeClick,
}: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<Core | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [nodeCount, setNodeCount] = useState(0)
  const [edgeCount, setEdgeCount] = useState(0)

  useEffect(() => {
    if (!containerRef.current || paths.length === 0) return

    // Convert paths to Cytoscape format
    const elements = convertPathsToElements(paths)
    setNodeCount(elements.filter((e) => e.group === 'nodes').length)
    setEdgeCount(elements.filter((e) => e.group === 'edges').length)

    // Initialize Cytoscape
    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: elements,
      style: getCytoscapeStyles(),
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        nodeSep: 50,
        rankSep: 100,
        padding: 30,
      } as any,
      minZoom: 0.3,
      maxZoom: 3,
      wheelSensitivity: 0.2,
    })

    // Add node click handler
    cyRef.current.on('tap', 'node', (event) => {
      const node = event.target
      const nodeData = node.data() as CytoscapeNode['data']

      if (onNodeClick) {
        onNodeClick({
          node_id: nodeData.id,
          node_type: nodeData.type,
          text: nodeData.text,
          properties: nodeData.properties,
        })
      }

      // Highlight clicked node
      cyRef.current?.elements().removeClass('highlighted')
      node.addClass('highlighted')
    })

    // Cleanup
    return () => {
      cyRef.current?.destroy()
    }
  }, [paths, onNodeClick])

  const toggleFullscreen = () => {
    if (!containerRef.current) return

    if (!isFullscreen) {
      containerRef.current.requestFullscreen()
      setIsFullscreen(true)
    } else {
      document.exitFullscreen()
      setIsFullscreen(false)
    }
  }

  const resetView = () => {
    cyRef.current?.fit(undefined, 50)
  }

  const centerGraph = () => {
    cyRef.current?.center()
  }

  if (paths.length === 0) {
    return (
      <div className="bg-gray-50 dark:bg-gray-900 rounded-lg border-2 border-dashed border-gray-300 dark:border-gray-700 p-12 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-400"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
          />
        </svg>
        <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
          그래프 경로 없음
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          그래프 탐색을 활성화하면 추론 경로가 표시됩니다.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-purple-500"></div>
            <span>노드: {nodeCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-gray-300"></div>
            <span>간선: {edgeCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500"></div>
            <span>경로: {paths.length}</span>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={centerGraph}
            className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title="중앙 정렬"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
          <button
            onClick={resetView}
            className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title="화면 맞춤"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
            </svg>
          </button>
          <button
            onClick={toggleFullscreen}
            className="px-3 py-1.5 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            title="전체화면"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        style={{ height }}
        className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden"
      />

      <div className="flex items-center gap-6 text-xs text-gray-600 dark:text-gray-400 px-4 py-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-purple-500"></div>
          <span>Product</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-sky-500"></div>
          <span>Article</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-emerald-500"></div>
          <span>Paragraph</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-amber-500"></div>
          <span>Subclause</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-rose-500"></div>
          <span>Other</span>
        </div>
        <div className="ml-auto text-xs">
          💡 노드를 클릭하면 상세 정보를 볼 수 있습니다
        </div>
      </div>
    </div>
  )
}

function convertPathsToElements(paths: GraphPathInfo[]): ElementDefinition[] {
  const elements: ElementDefinition[] = []
  const nodeIds = new Set<string>()
  const edgeIds = new Set<string>()

  paths.forEach((path) => {
    path.nodes.forEach((node) => {
      if (!nodeIds.has(node.node_id)) {
        nodeIds.add(node.node_id)
        elements.push({
          group: 'nodes',
          data: {
            id: node.node_id,
            label: getNodeLabel(node),
            type: node.node_type,
            text: node.text,
            properties: node.properties,
          },
        } as CytoscapeNode)
      }
    })

    for (let i = 0; i < path.nodes.length - 1; i++) {
      const source = path.nodes[i].node_id
      const target = path.nodes[i + 1].node_id
      const edgeId = \`\${source}-\${target}\`

      if (!edgeIds.has(edgeId)) {
        edgeIds.add(edgeId)
        elements.push({
          group: 'edges',
          data: {
            id: edgeId,
            source,
            target,
            label: path.relationships[i] || '',
          },
        } as CytoscapeEdge)
      }
    }
  })

  return elements
}

function getNodeLabel(node: GraphNodeInfo): string {
  if (node.properties.article_num) {
    return \`제\${node.properties.article_num}조\`
  }

  const maxLength = 20
  if (node.text.length <= maxLength) {
    return node.text
  }
  return node.text.substring(0, maxLength) + '...'
}

function getCytoscapeStyles(): cytoscape.Stylesheet[] {
  return [
    {
      selector: 'node',
      style: {
        'background-color': '#6b7280',
        label: 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        'text-max-width': '100px',
        color: '#ffffff',
        'font-size': '11px',
        'font-weight': '500',
        width: 80,
        height: 80,
        'border-width': 2,
        'border-color': '#ffffff',
      } as any,
    },
    {
      selector: 'node[type="Product"]',
      style: { 'background-color': '#8b5cf6' } as any,
    },
    {
      selector: 'node[type="Article"]',
      style: { 'background-color': '#0ea5e9' } as any,
    },
    {
      selector: 'node[type="Paragraph"]',
      style: { 'background-color': '#10b981' } as any,
    },
    {
      selector: 'node[type="Subclause"]',
      style: { 'background-color': '#f59e0b' } as any,
    },
    {
      selector: 'node[type="Coverage"]',
      style: { 'background-color': '#06b6d4' } as any,
    },
    {
      selector: 'node[type="Disease"]',
      style: { 'background-color': '#f43f5e' } as any,
    },
    {
      selector: 'node[type="Condition"]',
      style: { 'background-color': '#ec4899' } as any,
    },
    {
      selector: 'edge',
      style: {
        width: 2,
        'line-color': '#cbd5e1',
        'target-arrow-color': '#cbd5e1',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        label: 'data(label)',
        'font-size': '9px',
        color: '#64748b',
        'text-rotation': 'autorotate',
        'text-margin-y': -10,
      } as any,
    },
    {
      selector: 'node.highlighted',
      style: {
        'border-width': 4,
        'border-color': '#3b82f6',
        'z-index': 999,
      } as any,
    },
    {
      selector: 'edge.highlighted',
      style: {
        'line-color': '#3b82f6',
        'target-arrow-color': '#3b82f6',
        width: 4,
        'z-index': 999,
      } as any,
    },
  ]
}
