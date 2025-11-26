'use client'

import { formatDateTime } from '@/lib/utils'
import { useQueryStore } from '@/store/query-store'
import { ChatBubbleLeftRightIcon, ClockIcon } from '@heroicons/react/24/outline'

interface QueryHistoryProps {
  onSelectQuery: (queryId: string) => void
}

export default function QueryHistory({ onSelectQuery }: QueryHistoryProps) {
  const { queryHistory } = useQueryStore()

  if (queryHistory.length === 0) {
    return (
      <div className="card text-center py-8">
        <ChatBubbleLeftRightIcon className="w-12 h-12 text-gray-400 dark:text-gray-500 mx-auto mb-2" />
        <p className="text-sm text-gray-600 dark:text-gray-400">아직 질의 내역이 없습니다</p>
      </div>
    )
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">최근 질의 내역</h3>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {queryHistory.map((query) => (
          <button
            key={query.query_id}
            onClick={() => onSelectQuery(query.query_id)}
            className="w-full text-left p-3 rounded-lg border border-gray-200 dark:border-dark-border hover:border-primary-300 hover:bg-primary-50 transition-colors"
          >
            <div className="flex items-start justify-between mb-2">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100 line-clamp-2 flex-1">
                {query.question}
              </p>
              <span
                className={`
                  ml-2 px-2 py-0.5 text-xs font-medium rounded-full flex-shrink-0
                  ${
                    query.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : query.status === 'processing'
                      ? 'bg-blue-100 text-blue-800'
                      : query.status === 'failed'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }
                `}
              >
                {query.status === 'completed'
                  ? '완료'
                  : query.status === 'processing'
                  ? '처리중'
                  : query.status === 'failed'
                  ? '실패'
                  : '대기'}
              </span>
            </div>

            <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <div className="flex items-center gap-1">
                <ClockIcon className="w-3 h-3" />
                <span>{formatDateTime(query.timestamp)}</span>
              </div>
              {query.citations && (
                <span>{query.citations.length}개 인용</span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
