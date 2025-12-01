'use client'

/**
 * Simple Query Page
 *
 * Frontend for the Simple Query Engine (Stories 2.1-2.6)
 *
 * Features:
 * - Natural language query input
 * - Intent detection display
 * - Search results visualization
 * - LLM-generated answer
 * - Answer validation display
 * - Query history
 */

import { useState, useEffect } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { useSimpleQueryStore } from '@/store/simple-query-store'
import {
  PaperAirplaneIcon,
  SparklesIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'
import { getIntentLabel, getIntentIcon, GraphNodeInfo } from '@/types/simple-query'
import GraphVisualization from '@/components/GraphVisualization'
import NodeDetailPanel from '@/components/NodeDetailPanel'

export default function SimpleQueryPage() {
  const {
    currentResponse,
    queryHistory,
    isLoading,
    error,
    isNeo4jConnected,
    isLLMAvailable,
    executeQuery,
    checkHealth,
    clearError,
    loadFromHistory,
  } = useSimpleQueryStore()

  const [query, setQuery] = useState('')
  const [llmProvider, setLLMProvider] = useState<'openai' | 'anthropic' | 'mock'>('mock')
  const [useTraversal, setUseTraversal] = useState(true)
  const [selectedNode, setSelectedNode] = useState<GraphNodeInfo | null>(null)

  // Check health on mount
  useEffect(() => {
    checkHealth()
  }, [checkHealth])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!query.trim()) {
      return
    }

    try {
      await executeQuery({
        query: query.trim(),
        limit: 10,
        use_traversal: useTraversal,
        llm_provider: llmProvider,
      })
    } catch (error) {
      console.error('Query execution failed:', error)
    }
  }

  const getValidationLevelColor = (level: string) => {
    switch (level) {
      case 'pass':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'fail':
        return 'text-red-600 bg-red-50 border-red-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <SparklesIcon className="w-8 h-8 text-primary-600" />
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              GraphRAG Query Engine
            </h2>
          </div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            자연어로 보험 약관을 질문하고 AI가 그래프를 탐색하여 답변합니다
          </p>

          {/* Health Status */}
          <div className="mt-4 flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isNeo4jConnected ? 'bg-green-500' : 'bg-red-500'
                }`}
              />
              <span className="text-gray-600 dark:text-gray-400">
                Neo4j: {isNeo4jConnected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isLLMAvailable ? 'bg-green-500' : 'bg-yellow-500'
                }`}
              />
              <span className="text-gray-600 dark:text-gray-400">
                LLM: {isLLMAvailable ? 'Available' : 'Mock Mode'}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Query Input & Settings */}
          <div className="lg:col-span-1 space-y-6">
            {/* Query Input Form */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <MagnifyingGlassIcon className="w-5 h-5" />
                질문하기
              </h3>

              <form onSubmit={handleSubmit} className="space-y-4">
                {/* Question Input */}
                <div>
                  <label htmlFor="query" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    질문
                  </label>
                  <textarea
                    id="query"
                    rows={4}
                    className="input-field resize-none"
                    placeholder="예: 암보험 1억원 이상 보장되는 경우는?"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    disabled={isLoading}
                  />
                </div>

                {/* LLM Provider Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    LLM Provider
                  </label>
                  <select
                    value={llmProvider}
                    onChange={(e) => setLLMProvider(e.target.value as any)}
                    className="input-field"
                    disabled={isLoading}
                  >
                    <option value="mock">Mock (테스트용)</option>
                    <option value="openai">OpenAI GPT-4o-mini</option>
                    <option value="anthropic">Anthropic Claude 3.5 Sonnet</option>
                  </select>
                </div>

                {/* Graph Traversal Toggle */}
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="useTraversal"
                    checked={useTraversal}
                    onChange={(e) => setUseTraversal(e.target.checked)}
                    disabled={isLoading}
                    className="rounded border-gray-300"
                  />
                  <label htmlFor="useTraversal" className="text-sm text-gray-700 dark:text-gray-300">
                    그래프 탐색 사용 (Multi-hop Reasoning)
                  </label>
                </div>

                {/* Error Message */}
                {error && (
                  <div className="rounded-md bg-red-50 p-3 border border-red-200">
                    <p className="text-sm text-red-700">{error}</p>
                    <button
                      type="button"
                      onClick={clearError}
                      className="text-xs text-red-600 hover:text-red-800 mt-1"
                    >
                      닫기
                    </button>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  type="submit"
                  disabled={isLoading || !query.trim()}
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
            {queryHistory.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <ClockIcon className="w-5 h-5" />
                  최근 질문
                </h3>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {queryHistory.map((item, index) => (
                    <button
                      key={index}
                      onClick={() => loadFromHistory(item)}
                      className="w-full text-left p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-dark-hover border border-gray-200 dark:border-dark-border transition-colors"
                    >
                      <div className="flex items-start gap-2">
                        <span className="text-lg">{getIntentIcon(item.intent)}</span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                            {item.query}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-xs text-gray-500">
                              {getIntentLabel(item.intent)}
                            </span>
                            <span className="text-xs text-gray-400">•</span>
                            <span className={`text-xs font-medium ${getConfidenceColor(item.confidence)}`}>
                              {Math.round(item.confidence * 100)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Column - Answer Display */}
          <div className="lg:col-span-2">
            {currentResponse ? (
              <div className="space-y-6">
                {/* Query Info */}
                <div className="card">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {currentResponse.query}
                      </h3>
                      <div className="flex items-center gap-3 mt-2">
                        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-primary-100 text-primary-700 text-sm font-medium">
                          {getIntentIcon(currentResponse.intent)}
                          {getIntentLabel(currentResponse.intent)}
                        </span>
                        <span className={`text-sm font-semibold ${getConfidenceColor(currentResponse.confidence)}`}>
                          신뢰도: {Math.round(currentResponse.confidence * 100)}%
                        </span>
                      </div>
                    </div>

                    {/* Validation Badge */}
                    <div className={`px-3 py-1 rounded-lg border ${getValidationLevelColor(currentResponse.validation.overall_level)}`}>
                      <div className="flex items-center gap-1">
                        {currentResponse.validation.passed ? (
                          <CheckCircleIcon className="w-4 h-4" />
                        ) : (
                          <ExclamationTriangleIcon className="w-4 h-4" />
                        )}
                        <span className="text-sm font-medium">
                          {currentResponse.validation.overall_level.toUpperCase()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Entities */}
                  {currentResponse.entities.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        추출된 엔티티:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {currentResponse.entities.map((entity, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center gap-1 px-2 py-1 rounded bg-gray-100 dark:bg-dark-hover text-xs"
                          >
                            <span className="text-gray-600 dark:text-gray-400">{entity.entity_type}:</span>
                            <span className="font-medium text-gray-900 dark:text-gray-100">{entity.value}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Search Stats */}
                  <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 dark:bg-dark-hover rounded-lg">
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">검색 결과</p>
                      <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {currentResponse.search_results_count}개
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">그래프 경로</p>
                      <p className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {currentResponse.graph_paths_count}개
                      </p>
                    </div>
                  </div>
                </div>

                {/* Answer */}
                <div className="card">
                  <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                    <SparklesIcon className="w-5 h-5 text-primary-600" />
                    AI 답변
                  </h4>
                  <div className="prose dark:prose-invert max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700 dark:text-gray-300">
                      {currentResponse.answer}
                    </div>
                  </div>
                </div>

                {/* Graph Visualization */}
                {currentResponse.graph_paths && currentResponse.graph_paths.length > 0 && (
                  <div className="card">
                    <h4 className="text-lg font-semibold mb-4 flex items-center gap-2">
                      <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                      </svg>
                      추론 경로 그래프
                    </h4>
                    <GraphVisualization
                      paths={currentResponse.graph_paths}
                      height="500px"
                      onNodeClick={setSelectedNode}
                    />
                  </div>
                )}

                {/* Search Results */}
                {currentResponse.search_results.length > 0 && (
                  <div className="card">
                    <h4 className="text-lg font-semibold mb-4">검색된 조문</h4>
                    <div className="space-y-3">
                      {currentResponse.search_results.map((result, index) => (
                        <div
                          key={index}
                          className="p-4 bg-gray-50 dark:bg-dark-hover rounded-lg border border-gray-200 dark:border-dark-border"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 text-xs font-medium">
                                {result.node_type}
                              </span>
                              {result.article_num && (
                                <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                                  {result.article_num}
                                </span>
                              )}
                            </div>
                            <span className="text-xs text-gray-500">
                              관련도: {Math.round(result.relevance_score * 100)}%
                            </span>
                          </div>
                          <p className="text-sm text-gray-700 dark:text-gray-300">
                            {result.text}
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Validation Details */}
                {currentResponse.validation.recommendations.length > 0 && (
                  <div className="card">
                    <h4 className="text-lg font-semibold mb-4">검증 결과</h4>
                    <div className="space-y-2">
                      {currentResponse.validation.recommendations.map((rec, index) => (
                        <div key={index} className="flex items-start gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <SparklesIcon className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                          <p className="text-sm text-blue-900 dark:text-blue-100">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="card text-center py-16">
                <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
                  <SparklesIcon className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  질문을 입력하세요
                </h3>
                <p className="text-gray-600 dark:text-gray-400 max-w-md mx-auto mb-8">
                  왼쪽에서 질문을 입력하면 GraphRAG 엔진이 Neo4j 그래프를 탐색하여 정확한 답변을 제공합니다.
                </p>

                <div className="grid grid-cols-1 gap-4 max-w-2xl mx-auto text-left">
                  <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">💡 예시 질문 1</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      &ldquo;암보험 1억원 이상 보장되는 경우는?&rdquo;
                    </p>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20 rounded-lg border border-green-200 dark:border-green-800">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">💡 예시 질문 2</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      &ldquo;면책 기간은 얼마나 되나요?&rdquo;
                    </p>
                  </div>
                  <div className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">💡 예시 질문 3</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      &ldquo;심근경색 보험금은 얼마인가요?&rdquo;
                    </p>
                  </div>
                </div>

                {/* Features */}
                <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto">
                  <div className="text-center">
                    <div className="text-2xl mb-2">🔍</div>
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Query Parsing</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-2">🕸️</div>
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Graph Traversal</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-2">🤖</div>
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400">LLM Reasoning</p>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl mb-2">✅</div>
                    <p className="text-xs font-medium text-gray-600 dark:text-gray-400">Answer Validation</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Node Detail Panel */}
      <NodeDetailPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
    </DashboardLayout>
  )
}
