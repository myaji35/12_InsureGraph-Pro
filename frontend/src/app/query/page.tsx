'use client'

import { useState } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import DocumentSelector from '@/components/DocumentSelector'
import AnswerDisplay from '@/components/AnswerDisplay'
import QueryHistory from '@/components/QueryHistory'
import { useQueryStore } from '@/store/query-store'
import { PaperAirplaneIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

export default function QueryPage() {
  const { currentQuery, isLoading, error, executeQuery, getQueryStatus, clearError } =
    useQueryStore()

  const [question, setQuestion] = useState('')
  const [selectedDocumentIds, setSelectedDocumentIds] = useState<string[]>([])
  const [showDocumentSelector, setShowDocumentSelector] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!question.trim()) {
      return
    }

    if (selectedDocumentIds.length === 0) {
      alert('최소 1개 이상의 문서를 선택해주세요.')
      return
    }

    try {
      await executeQuery({
        question: question.trim(),
        document_ids: selectedDocumentIds,
      })

      // Don't clear the form, so user can see what they asked
    } catch (error) {
      console.error('Query execution failed:', error)
    }
  }

  const handleSelectFromHistory = async (queryId: string) => {
    try {
      await getQueryStatus(queryId)
    } catch (error) {
      console.error('Failed to load query:', error)
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">질의응답</h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            보험 약관에 대해 질문하고 AI 기반 답변을 받으세요
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Query Input & History */}
          <div className="lg:col-span-1 space-y-6">
            {/* Query Input Form */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">질문하기</h3>

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Question Input */}
                <div>
                  <label htmlFor="question" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    질문
                  </label>
                  <textarea
                    id="question"
                    rows={4}
                    className="input-field resize-none"
                    placeholder="예: 암 진단 시 보장 내용은 무엇인가요?"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    disabled={isLoading}
                  />
                </div>

                {/* Document Selection */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                      문서 선택 ({selectedDocumentIds.length}개)
                    </label>
                    <button
                      type="button"
                      onClick={() => setShowDocumentSelector(!showDocumentSelector)}
                      className="text-sm text-primary-600 hover:text-primary-700 font-medium"
                    >
                      {showDocumentSelector ? '닫기' : '문서 선택'}
                    </button>
                  </div>

                  {showDocumentSelector && (
                    <div className="border border-gray-200 dark:border-dark-border rounded-lg p-4">
                      <DocumentSelector
                        selectedDocumentIds={selectedDocumentIds}
                        onSelectionChange={setSelectedDocumentIds}
                      />
                    </div>
                  )}

                  {!showDocumentSelector && selectedDocumentIds.length > 0 && (
                    <div className="flex items-center gap-2 p-3 bg-primary-50 border border-primary-200 rounded-lg">
                      <DocumentTextIcon className="w-5 h-5 text-primary-600" />
                      <span className="text-sm text-primary-700">
                        {selectedDocumentIds.length}개 문서 선택됨
                      </span>
                    </div>
                  )}
                </div>

                {/* Error Message */}
                {error && (
                  <div className="rounded-md bg-red-50 p-3">
                    <p className="text-sm text-red-700">{error}</p>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading || !question.trim() || selectedDocumentIds.length === 0}
                  className="btn-primary w-full flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      처리 중...
                    </>
                  ) : (
                    <>
                      <PaperAirplaneIcon className="w-5 h-5" />
                      질문하기
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Query History */}
            <QueryHistory onSelectQuery={handleSelectFromHistory} />
          </div>

          {/* Right Column - Answer Display */}
          <div className="lg:col-span-2">
            {currentQuery ? (
              <AnswerDisplay query={currentQuery} />
            ) : (
              <div className="card text-center py-16">
                <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
                  <PaperAirplaneIcon className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  질문을 입력하세요
                </h3>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto">
                  왼쪽에서 문서를 선택하고 질문을 입력하면 AI가 약관을 분석하여 답변해드립니다.
                </p>
                <div className="mt-8 grid grid-cols-1 gap-4 max-w-md mx-auto text-left">
                  <div className="p-4 bg-gray-50 dark:bg-dark-hover rounded-lg">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">예시 질문 1</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      &ldquo;암 진단 시 보장 내용은 무엇인가요?&rdquo;
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-dark-hover rounded-lg">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">예시 질문 2</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      &ldquo;면책 기간은 얼마나 되나요?&rdquo;
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 dark:bg-dark-hover rounded-lg">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">예시 질문 3</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      &ldquo;보험료 납입 중 해지 시 환급금은 어떻게 되나요?&rdquo;
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
