'use client'

import { GraphNode, NodeType } from '@/types'
import { XMarkIcon, DocumentTextIcon, TagIcon, CubeIcon, ScaleIcon } from '@heroicons/react/24/outline'

interface NodeDetailProps {
  node: GraphNode
  onClose: () => void
}

const nodeTypeLabels: Record<NodeType, string> = {
  document: '문서',
  entity: '엔티티',
  concept: '개념',
  clause: '조항',
}

const nodeTypeIcons: Record<NodeType, React.ComponentType<{ className?: string }>> = {
  document: DocumentTextIcon,
  entity: TagIcon,
  concept: CubeIcon,
  clause: ScaleIcon,
}

const nodeTypeColors: Record<NodeType, string> = {
  document: 'text-blue-600 bg-blue-100',
  entity: 'text-green-600 bg-green-100',
  concept: 'text-amber-600 bg-amber-100',
  clause: 'text-violet-600 bg-violet-100',
}

export default function NodeDetail({ node, onClose }: NodeDetailProps) {
  const Icon = nodeTypeIcons[node.type]

  return (
    <div className="card h-full overflow-y-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-start gap-3 flex-1">
          <div className={`p-3 rounded-lg ${nodeTypeColors[node.type]}`}>
            <Icon className="w-6 h-6" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">
                {nodeTypeLabels[node.type]}
              </span>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 break-words">
              {node.label}
            </h3>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-dark-hover transition-colors flex-shrink-0"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Node ID */}
      <div className="mb-6 p-3 bg-gray-50 dark:bg-dark-elevated rounded-lg">
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">노드 ID</p>
        <p className="text-sm text-gray-900 dark:text-gray-100 font-mono break-all">{node.id}</p>
      </div>

      {/* Metadata */}
      {node.metadata && Object.keys(node.metadata).length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">메타데이터</h4>
          <div className="space-y-3">
            {node.metadata.document_name && (
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">문서명</p>
                <p className="text-sm text-gray-900 dark:text-gray-100">{node.metadata.document_name}</p>
              </div>
            )}
            {node.metadata.entity_type && (
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">엔티티 유형</p>
                <p className="text-sm text-gray-900 dark:text-gray-100">{node.metadata.entity_type}</p>
              </div>
            )}
            {node.metadata.importance !== undefined && (
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">중요도</p>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-gray-200 dark:bg-dark-elevated rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary-600 dark:bg-primary-500 rounded-full"
                      style={{ width: `${node.metadata.importance * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-900 dark:text-gray-100 font-medium">
                    {(node.metadata.importance * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Properties */}
      {node.properties && Object.keys(node.properties).length > 0 && (
        <div className="mb-6">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">속성</h4>
          <div className="space-y-3">
            {Object.entries(node.properties).map(([key, value]) => (
              <div key={key}>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">{key}</p>
                <p className="text-sm text-gray-900 dark:text-gray-100 break-words">
                  {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Additional Metadata */}
      {node.metadata && (
        <div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">추가 정보</h4>
          <div className="space-y-3">
            {Object.entries(node.metadata)
              .filter(
                ([key]) =>
                  !['document_name', 'entity_type', 'importance', 'document_id'].includes(key)
              )
              .map(([key, value]) => (
                <div key={key}>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-1">{key}</p>
                  <p className="text-sm text-gray-900 dark:text-gray-100 break-words">
                    {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                  </p>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  )
}
