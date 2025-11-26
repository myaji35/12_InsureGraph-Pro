'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { QueryResponse } from '@/types'
import { CheckCircleIcon, DocumentTextIcon, LinkIcon } from '@heroicons/react/24/outline'

interface AnswerDisplayProps {
  query: QueryResponse
}

export default function AnswerDisplay({ query }: AnswerDisplayProps) {
  if (query.status === 'pending' || query.status === 'processing') {
    return (
      <div className="card">
        <div className="flex items-center gap-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 dark:border-primary-400"></div>
          <div>
            <p className="font-medium text-gray-900 dark:text-gray-100">질의 처리 중...</p>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {query.status === 'pending' ? '대기 중입니다' : '답변을 생성하고 있습니다'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (query.status === 'failed') {
    return (
      <div className="card bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
        <div className="flex items-start gap-4">
          <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-900/40 flex items-center justify-center flex-shrink-0">
            <svg
              className="w-5 h-5 text-red-600 dark:text-red-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </div>
          <div>
            <p className="font-medium text-red-900 dark:text-red-300">질의 처리 실패</p>
            <p className="text-sm text-red-700 dark:text-red-400 mt-1">
              {query.error_message || '알 수 없는 오류가 발생했습니다.'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  if (!query.answer) {
    return null
  }

  return (
    <div className="space-y-6">
      {/* Answer */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <CheckCircleIcon className="w-6 h-6 text-green-600 dark:text-green-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">답변</h3>
        </div>

        <div className="prose prose-sm max-w-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{query.answer}</ReactMarkdown>
        </div>

        {/* Confidence Score */}
        {query.confidence_score !== undefined && (
          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-dark-border">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">신뢰도</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-gray-200 dark:bg-dark-elevated rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      query.confidence_score >= 0.8
                        ? 'bg-green-500'
                        : query.confidence_score >= 0.6
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }`}
                    style={{ width: `${query.confidence_score * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {(query.confidence_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Citations */}
      {query.citations && query.citations.length > 0 && (
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <DocumentTextIcon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              인용 출처 ({query.citations.length})
            </h3>
          </div>

          <div className="space-y-3">
            {query.citations.map((citation, index) => (
              <div
                key={index}
                className="p-4 bg-gray-50 dark:bg-dark-elevated rounded-lg border border-gray-200 dark:border-dark-border hover:border-primary-300 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 text-xs font-medium rounded">
                      [{index + 1}]
                    </span>
                    <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {citation.document_name || '문서'}
                    </span>
                  </div>
                  {citation.relevance_score !== undefined && (
                    <span className="text-xs text-gray-600 dark:text-gray-400">
                      관련도: {(citation.relevance_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed mb-2">
                  {citation.content}
                </p>

                {citation.metadata && (
                  <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                    {citation.metadata.page_number && (
                      <span>페이지 {citation.metadata.page_number}</span>
                    )}
                    {citation.metadata.section && (
                      <span>섹션: {citation.metadata.section}</span>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Processing Time */}
      {query.processing_time && (
        <div className="text-xs text-gray-500 dark:text-gray-400 text-center">
          처리 시간: {query.processing_time.toFixed(2)}초
        </div>
      )}
    </div>
  )
}
