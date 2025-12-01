/**
 * Node Detail Panel Component (Story 3.3)
 *
 * Shows detailed information when a graph node is clicked
 */
'use client'

import { GraphNodeInfo } from '@/types/simple-query'

interface NodeDetailPanelProps {
  node: GraphNodeInfo | null
  onClose: () => void
}

export default function NodeDetailPanel({ node, onClose }: NodeDetailPanelProps) {
  if (!node) return null

  const getNodeColor = (type: string) => {
    const colors: Record<string, string> = {
      Product: 'bg-purple-500',
      Article: 'bg-sky-500',
      Paragraph: 'bg-emerald-500',
      Subclause: 'bg-amber-500',
      Coverage: 'bg-cyan-500',
      Disease: 'bg-rose-500',
      Condition: 'bg-pink-500',
    }
    return colors[type] || 'bg-gray-500'
  }

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white dark:bg-gray-800 shadow-2xl border-l border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col z-50">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-full ${getNodeColor(node.node_type)}`}></div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            노드 상세 정보
          </h3>
        </div>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
        {/* Node Type */}
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
            노드 유형
          </label>
          <div className="flex items-center gap-2">
            <div className={`w-4 h-4 rounded-full ${getNodeColor(node.node_type)}`}></div>
            <span className="text-sm font-medium text-gray-900 dark:text-white">
              {node.node_type}
            </span>
          </div>
        </div>

        {/* Node ID */}
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
            노드 ID
          </label>
          <code className="block text-xs text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-900 px-3 py-2 rounded font-mono">
            {node.node_id}
          </code>
        </div>

        {/* Full Text */}
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
            원문
          </label>
          <div className="text-sm text-gray-900 dark:text-white bg-gray-50 dark:bg-gray-900 px-4 py-3 rounded-lg border border-gray-200 dark:border-gray-700 leading-relaxed">
            {node.text}
          </div>
        </div>

        {/* Properties */}
        {Object.keys(node.properties).length > 0 && (
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
              속성
            </label>
            <div className="space-y-2">
              {Object.entries(node.properties).map(([key, value]) => (
                <div
                  key={key}
                  className="flex items-start gap-3 text-sm bg-gray-50 dark:bg-gray-900 px-3 py-2 rounded"
                >
                  <span className="font-medium text-gray-600 dark:text-gray-400 min-w-[100px]">
                    {key}:
                  </span>
                  <span className="text-gray-900 dark:text-white flex-1">
                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Article Number (if available) */}
        {node.properties.article_num && (
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
              조항 번호
            </label>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              제{node.properties.article_num}조
            </div>
          </div>
        )}

        {/* Page Number (if available) */}
        {node.properties.page_num && (
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase mb-2">
              페이지
            </label>
            <div className="text-lg font-semibold text-gray-900 dark:text-white">
              {node.properties.page_num} 페이지
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
        <button
          onClick={onClose}
          className="w-full px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors font-medium"
        >
          닫기
        </button>
      </div>
    </div>
  )
}
