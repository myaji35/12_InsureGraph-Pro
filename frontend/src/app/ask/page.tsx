'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { Search, FileText, X, Sparkles } from 'lucide-react'
import { simpleQueryAPI } from '@/lib/simple-query-api'
import type { SimpleQueryResponse } from '@/types/simple-query'
import { getIntentLabel, getIntentIcon } from '@/types/simple-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface Document {
  id: number
  title: string
  insurer: string
  product_type: string
}

interface Insurer {
  code: string
  name: string
  type: 'life' | 'nonlife'
  logo?: string
}

interface QueryResult {
  id: string
  question: string
  answer: string
  intent: string
  confidence: number
  sources: Array<{
    node_id: string
    node_type: string
    text: string
    relevance_score: number
  }>
  timestamp: Date
  insurers: string[]
  search_results_count: number
  graph_paths_count: number
  validation: {
    passed: boolean
    overall_level: string
    confidence: number
    issues_count: number
    recommendations: string[]
  }
}

export default function AskPage() {
  const router = useRouter()
  const [question, setQuestion] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDocs, setSelectedDocs] = useState<Document[]>([])
  const [showDocSelector, setShowDocSelector] = useState(false)
  const [availableDocs, setAvailableDocs] = useState<Document[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedInsurers, setSelectedInsurers] = useState<string[]>([])
  const [showInsurerSelector, setShowInsurerSelector] = useState<'life' | 'nonlife' | null>(null)
  const [results, setResults] = useState<QueryResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // 보험사 목록 (생명보험 15개 + 손해보험 15개)
  const insurers: Insurer[] = [
    // 생명보험 (15개)
    { code: 'samsung_life', name: '삼성생명', type: 'life' },
    { code: 'hanwha_life', name: '한화생명', type: 'life' },
    { code: 'kyobo_life', name: '교보생명', type: 'life' },
    { code: 'shinhan_life', name: '신한라이프', type: 'life' },
    { code: 'metlife', name: '메트라이프생명', type: 'life' },
    { code: 'korealife', name: '한국투자생명', type: 'life' },
    { code: 'dongbu_life', name: '동부생명', type: 'life' },
    { code: 'allianz_life', name: '알리안츠생명', type: 'life' },
    { code: 'prudential', name: '푸르덴셜생명', type: 'life' },
    { code: 'mirae_asset_life', name: '미래에셋생명', type: 'life' },
    { code: 'kb_life', name: 'KB라이프생명', type: 'life' },
    { code: 'nh_life', name: 'NH농협생명', type: 'life' },
    { code: 'hana_life', name: '하나생명', type: 'life' },
    { code: 'korea_life', name: '코리안리생명', type: 'life' },
    { code: 'aba_life', name: 'ABL생명', type: 'life' },

    // 손해보험 (15개)
    { code: 'samsung_fire', name: '삼성화재', type: 'nonlife' },
    { code: 'hyundai_marine', name: '현대해상', type: 'nonlife' },
    { code: 'db_insurance', name: 'DB손해보험', type: 'nonlife' },
    { code: 'kb_insurance', name: 'KB손해보험', type: 'nonlife' },
    { code: 'meritz', name: '메리츠화재', type: 'nonlife' },
    { code: 'hanwha_nonlife', name: '한화손해보험', type: 'nonlife' },
    { code: 'heungkuk', name: '흥국화재', type: 'nonlife' },
    { code: 'mg', name: 'MG손해보험', type: 'nonlife' },
    { code: 'lotte', name: '롯데손해보험', type: 'nonlife' },
    { code: 'aca', name: 'ACA손해보험', type: 'nonlife' },
    { code: 'carrot', name: '캐롯손해보험', type: 'nonlife' },
    { code: 'nh_nonlife', name: 'NH농협손해보험', type: 'nonlife' },
    { code: 'the_k', name: '더케이손해보험', type: 'nonlife' },
    { code: 'hana_insurance', name: '하나손해보험', type: 'nonlife' },
    { code: 'axa', name: 'AXA손해보험', type: 'nonlife' },
  ]

  // 쿠키에서 선택된 보험사 불러오기
  useEffect(() => {
    const savedInsurers = document.cookie
      .split('; ')
      .find(row => row.startsWith('selectedInsurers='))
      ?.split('=')[1]

    if (savedInsurers) {
      try {
        setSelectedInsurers(JSON.parse(decodeURIComponent(savedInsurers)))
      } catch (e) {
        console.error('Failed to parse saved insurers:', e)
      }
    }
  }, [])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [question])

  const handleSearchDocs = async (query: string) => {
    if (!query.trim()) {
      setAvailableDocs([])
      return
    }

    setIsSearching(true)
    try {
      // TODO: API 호출로 문서 검색
      const mockDocs: Document[] = [
        { id: 1, title: '삼성화재 자동차보험 약관', insurer: '삼성화재', product_type: '자동차보험' },
        { id: 2, title: 'KB손해보험 실손의료보험 약관', insurer: 'KB손해보험', product_type: '실손의료보험' },
        { id: 3, title: '현대해상 종합보험 약관', insurer: '현대해상', product_type: '종합보험' },
      ]

      setAvailableDocs(mockDocs.filter(doc =>
        doc.title.toLowerCase().includes(query.toLowerCase()) ||
        doc.insurer.toLowerCase().includes(query.toLowerCase())
      ))
    } catch (error) {
      console.error('Failed to search documents:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleSelectDoc = (doc: Document) => {
    if (!selectedDocs.find(d => d.id === doc.id)) {
      setSelectedDocs([...selectedDocs, doc])
    }
    setSearchQuery('')
    setAvailableDocs([])
    setShowDocSelector(false)
  }

  const handleRemoveDoc = (docId: number) => {
    setSelectedDocs(selectedDocs.filter(d => d.id !== docId))
  }

  const toggleInsurer = (insurerCode: string) => {
    setSelectedInsurers(prev => {
      const newSelection = prev.includes(insurerCode)
        ? prev.filter(code => code !== insurerCode)
        : [...prev, insurerCode]

      // 쿠키에 저장 (30일 유지)
      const expires = new Date()
      expires.setDate(expires.getDate() + 30)
      document.cookie = `selectedInsurers=${encodeURIComponent(JSON.stringify(newSelection))}; expires=${expires.toUTCString()}; path=/`

      return newSelection
    })
  }

  const handleSubmit = async () => {
    if (!question.trim()) {
      return
    }

    setIsLoading(true)

    try {
      // GraphRAG API 호출
      const response: SimpleQueryResponse = await simpleQueryAPI.executeQuery({
        query: question,
        limit: 20,
        use_traversal: true,
        llm_provider: 'anthropic'
      })

      // 응답을 QueryResult 형식으로 변환
      const result: QueryResult = {
        id: Date.now().toString(),
        question: question,
        answer: response.answer,
        intent: response.intent,
        confidence: response.confidence,
        sources: response.sources,
        timestamp: new Date(),
        insurers: selectedInsurers.map(code => insurers.find(i => i.code === code)?.name || code),
        search_results_count: response.search_results_count,
        graph_paths_count: response.graph_paths_count,
        validation: response.validation
      }

      // 결과를 배열 맨 앞에 추가
      setResults(prev => [result, ...prev])

      // 질문 입력 초기화
      setQuestion('')
    } catch (error) {
      console.error('Failed to submit question:', error)
      const errorMessage = error instanceof Error ? error.message : '질문 처리 중 오류가 발생했습니다.'
      alert(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen flex flex-col items-center justify-center px-2.5 py-8 bg-gradient-to-b from-white to-gray-50 dark:from-dark-bg dark:to-gray-900">
        {/* Header */}
        <div className="w-full mb-12 text-center">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Sparkles className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary-600 to-purple-600 bg-clip-text text-transparent">
              질문하기
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400">
            보험 약관에 대해 궁금한 점을 물어보세요
          </p>
        </div>

        {/* Main Content */}
        <div className="w-full">
          {/* Selected Documents */}
          {selectedDocs.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-2">
              {selectedDocs.map((doc) => (
                <div
                  key={doc.id}
                  className="inline-flex items-center gap-2 px-3 py-1.5 bg-primary-50 dark:bg-primary-900/20
                           text-primary-700 dark:text-primary-300 rounded-full text-lg border border-primary-200 dark:border-primary-800"
                >
                  <FileText className="w-4 h-4" />
                  <span className="font-medium">{doc.title}</span>
                  <button
                    onClick={() => handleRemoveDoc(doc.id)}
                    className="hover:bg-primary-100 dark:hover:bg-primary-800 rounded-full p-0.5"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Question Input Box */}
          <div className="relative bg-white dark:bg-dark-surface rounded-3xl shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden mb-8">
            {/* Textarea */}
            <textarea
              ref={textareaRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="예: 암 진단 시 보장 내용은 무엇인가요?"
              className="w-full px-6 py-5 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500
                       bg-transparent resize-none focus:outline-none text-xl min-h-[80px] max-h-[400px]"
              rows={1}
            />

            {/* Bottom Bar */}
            <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
              <div className="flex items-center gap-2">
                {/* Life Insurance Button */}
                <button
                  onClick={() => {
                    setShowInsurerSelector(showInsurerSelector === 'life' ? null : 'life')
                    setShowDocSelector(false)
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-lg rounded-lg transition-colors ${
                    showInsurerSelector === 'life'
                      ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-800'
                  }`}
                >
                  <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                  <span>생명보험 ({selectedInsurers.filter(code => insurers.find(i => i.code === code)?.type === 'life').length})</span>
                </button>

                {/* Non-Life Insurance Button */}
                <button
                  onClick={() => {
                    setShowInsurerSelector(showInsurerSelector === 'nonlife' ? null : 'nonlife')
                    setShowDocSelector(false)
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-lg rounded-lg transition-colors ${
                    showInsurerSelector === 'nonlife'
                      ? 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-800'
                  }`}
                >
                  <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
                  <span>손해보험 ({selectedInsurers.filter(code => insurers.find(i => i.code === code)?.type === 'nonlife').length})</span>
                </button>

                {/* Document Selector Button */}
                <button
                  onClick={() => {
                    setShowDocSelector(!showDocSelector)
                    setShowInsurerSelector(null)
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-lg text-gray-600 dark:text-gray-400
                           hover:bg-gray-200 dark:hover:bg-gray-800 rounded-lg transition-colors"
                >
                  <FileText className="w-4 h-4" />
                  <span>문서 ({selectedDocs.length})</span>
                </button>
              </div>

              {/* Submit Button */}
              <button
                onClick={handleSubmit}
                disabled={!question.trim() || isLoading}
                className="flex items-center gap-2 px-6 py-2.5 bg-primary-600 hover:bg-primary-700
                         disabled:bg-gray-300 dark:disabled:bg-gray-700 disabled:cursor-not-allowed
                         text-white font-medium rounded-full transition-all shadow-lg hover:shadow-xl
                         disabled:shadow-none"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>생각하는 중...</span>
                  </>
                ) : (
                  <>
                    <span>질문하기</span>
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                    </svg>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Insurer Selector Modal */}
          {showInsurerSelector && (
            <div className="mb-4 bg-white dark:bg-dark-surface rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              {/* Header */}
              <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${showInsurerSelector === 'life' ? 'bg-blue-500' : 'bg-emerald-500'}`}></div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {showInsurerSelector === 'life' ? '생명보험' : '손해보험'} 선택
                </h3>
              </div>

              {/* Insurer List */}
              <div className="max-h-[500px] overflow-y-auto p-4">
                <div className="space-y-2">
                  {insurers.filter(i => i.type === showInsurerSelector).map((insurer) => {
                      const isSelected = selectedInsurers.includes(insurer.code)
                      return (
                        <button
                          key={insurer.code}
                          onClick={() => toggleInsurer(insurer.code)}
                          className="w-full flex items-center justify-between px-4 py-2.5
                                   hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg transition-colors
                                   border border-gray-200 dark:border-gray-700"
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-9 h-9 rounded-full bg-gradient-to-br flex items-center justify-center text-white text-base font-bold ${
                              showInsurerSelector === 'life'
                                ? 'from-blue-500 to-blue-600'
                                : 'from-emerald-500 to-emerald-600'
                            }`}>
                              {insurer.name.slice(0, 2)}
                            </div>
                            <span className="text-lg font-medium text-gray-900 dark:text-gray-100">
                              {insurer.name}
                            </span>
                          </div>

                          {/* Toggle Switch */}
                          <div
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                              isSelected
                                ? (showInsurerSelector === 'life' ? 'bg-blue-600' : 'bg-emerald-600')
                                : 'bg-gray-200 dark:bg-gray-700'
                            }`}
                          >
                            <span
                              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                isSelected ? 'translate-x-6' : 'translate-x-1'
                              }`}
                            />
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>

              {/* Footer */}
              <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  {selectedInsurers.filter(code => insurers.find(i => i.code === code)?.type === showInsurerSelector).length > 0
                    ? `${selectedInsurers.filter(code => insurers.find(i => i.code === code)?.type === showInsurerSelector).length}개 보험사 선택됨`
                    : '보험사를 선택하세요'}
                </p>
              </div>
            </div>
          )}

          {/* Document Search Modal */}
          {showDocSelector && (
            <div className="mb-4 bg-white dark:bg-dark-surface rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
              {/* Search Input */}
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value)
                      handleSearchDocs(e.target.value)
                    }}
                    placeholder="문서 검색..."
                    className="w-full pl-10 pr-4 py-2.5 border border-gray-300 dark:border-gray-600 rounded-lg
                             bg-white dark:bg-dark-surface text-gray-900 dark:text-gray-100
                             placeholder-gray-400 dark:placeholder-gray-500
                             focus:outline-none focus:ring-2 focus:ring-primary-500"
                    autoFocus
                  />
                </div>
              </div>

              {/* Search Results */}
              <div className="max-h-80 overflow-y-auto">
                {availableDocs.length > 0 ? (
                  availableDocs.map((doc) => (
                    <button
                      key={doc.id}
                      onClick={() => handleSelectDoc(doc)}
                      className="w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-800
                               transition-colors border-b border-gray-100 dark:border-gray-800 last:border-b-0"
                    >
                      <div className="flex items-start gap-3">
                        <FileText className="w-5 h-5 text-primary-500 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                            {doc.title}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                            {doc.insurer} · {doc.product_type}
                          </p>
                        </div>
                      </div>
                    </button>
                  ))
                ) : searchQuery ? (
                  <div className="py-12 text-center text-gray-500 dark:text-gray-400">
                    검색 결과가 없습니다
                  </div>
                ) : (
                  <div className="py-12 text-center text-gray-500 dark:text-gray-400">
                    문서를 검색하세요
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Helper Text */}
          <div className="mb-6 text-center text-lg text-gray-500 dark:text-gray-400">
            <p>Shift + Enter로 줄바꿈 | Enter로 질문 전송</p>
          </div>

          {/* Loading Indicator */}
          {isLoading && (
            <div className="mb-4 bg-white dark:bg-dark-surface rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
              <div className="px-6 py-8">
                <div className="flex items-center justify-center gap-3">
                  <div className="relative">
                    <div className="w-10 h-10 border-4 border-primary-200 dark:border-primary-900 border-t-primary-600 dark:border-t-primary-400 rounded-full animate-spin"></div>
                    <Sparkles className="w-5 h-5 text-primary-600 dark:text-primary-400 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                  </div>
                  <div>
                    <p className="text-2xl font-medium text-gray-900 dark:text-gray-100">생각하는 중...</p>
                    <p className="text-lg text-gray-500 dark:text-gray-400 mt-1">약관 검색 및 답변 생성 중입니다</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results - Chat UI Style */}
          {results.length > 0 && (
            <div className="space-y-6">
              {results.map((result) => (
                <div key={result.id} className="space-y-4">
                  {/* Question Box - Left aligned, compact */}
                  <div className="flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                      <svg className="w-6 h-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1 bg-white dark:bg-dark-surface rounded-2xl shadow-md border border-gray-200 dark:border-gray-700 px-5 py-4 max-w-4xl">
                      <p className="text-xl font-medium text-gray-900 dark:text-gray-100">
                        {result.question}
                      </p>
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-base text-gray-500 dark:text-gray-400">
                        <span>{result.timestamp.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <span>{getIntentIcon(result.intent)}</span>
                          <span>{getIntentLabel(result.intent)}</span>
                        </span>
                        {result.insurers.length > 0 && (
                          <>
                            <span>•</span>
                            <div className="flex flex-wrap gap-1">
                              {result.insurers.slice(0, 3).map((insurer, idx) => (
                                <span key={idx} className="px-2 py-0.5 bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-300 rounded">
                                  {insurer}
                                </span>
                              ))}
                              {result.insurers.length > 3 && (
                                <span className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded">
                                  +{result.insurers.length - 3}
                                </span>
                              )}
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Answer Box - Indented right, prominent */}
                  <div className="ml-8 flex items-start gap-3">
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                      <Sparkles className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
                    </div>
                    <div className="flex-1 bg-white dark:bg-dark-surface rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                      {/* Answer Header with LLM Model Info */}
                      <div className="px-5 py-3 bg-emerald-50 dark:bg-emerald-900/20 border-b border-emerald-100 dark:border-emerald-800 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <span className="text-base font-semibold text-emerald-700 dark:text-emerald-300">
                            AI 답변
                          </span>
                          <span className={`px-2 py-0.5 rounded text-sm ${
                            result.validation.passed
                              ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                              : 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                          }`}>
                            신뢰도 {(result.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <span className="text-sm text-emerald-600 dark:text-emerald-400 font-mono">
                          {result.llm_model}
                        </span>
                      </div>

                      {/* Answer Content */}
                      <div className="px-5 py-5">
                        <div className="text-lg text-gray-700 dark:text-gray-300 leading-relaxed markdown-content max-h-[600px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600 scrollbar-track-transparent">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                              h1: ({node, ...props}) => <h1 className="text-3xl font-bold mt-4 mb-2 text-gray-900 dark:text-gray-100" {...props} />,
                              h2: ({node, ...props}) => <h2 className="text-2xl font-bold mt-3 mb-2 text-gray-900 dark:text-gray-100" {...props} />,
                              h3: ({node, ...props}) => <h3 className="text-xl font-bold mt-2 mb-1 text-gray-900 dark:text-gray-100" {...props} />,
                              p: ({node, ...props}) => <p className="mb-3" {...props} />,
                              ul: ({node, ...props}) => <ul className="list-disc list-inside mb-3 space-y-1" {...props} />,
                              ol: ({node, ...props}) => <ol className="list-decimal list-inside mb-3 space-y-1" {...props} />,
                              li: ({node, ...props}) => <li className="ml-2" {...props} />,
                              strong: ({node, ...props}) => <strong className="font-bold text-gray-900 dark:text-gray-100" {...props} />,
                              em: ({node, ...props}) => <em className="italic" {...props} />,
                              code: ({node, inline, ...props}: any) =>
                                inline
                                  ? <code className="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-base font-mono" {...props} />
                                  : <code className="block p-3 bg-gray-100 dark:bg-gray-800 rounded text-base font-mono overflow-x-auto" {...props} />,
                              blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-primary-500 pl-3 italic my-3 text-gray-600 dark:text-gray-400" {...props} />,
                            }}
                          >
                            {result.answer}
                          </ReactMarkdown>
                        </div>

                        {/* Sources and Stats */}
                        {result.sources.length > 0 && (
                          <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                            <div className="flex items-center justify-between mb-3">
                              <p className="text-base font-semibold text-gray-500 dark:text-gray-400">
                                참고 문서 ({result.sources.length}개)
                              </p>
                              <div className="flex items-center gap-3 text-base text-gray-500 dark:text-gray-400">
                                <span>검색 결과: {result.search_results_count}개</span>
                                {result.graph_paths_count > 0 && (
                                  <>
                                    <span>•</span>
                                    <span>그래프 경로: {result.graph_paths_count}개</span>
                                  </>
                                )}
                              </div>
                            </div>
                            <div className="space-y-2">
                              {result.sources.slice(0, 5).map((source, idx) => (
                                <div key={idx} className="flex items-start gap-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50">
                                  <FileText className="w-4 h-4 flex-shrink-0 mt-1 text-primary-500" />
                                  <div className="flex-1 min-w-0">
                                    <p className="text-base text-gray-700 dark:text-gray-300 line-clamp-2">
                                      {source.text}
                                    </p>
                                    <div className="mt-2 flex items-center gap-2 text-sm text-gray-500 dark:text-gray-400">
                                      <span className="px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded">
                                        {source.node_type}
                                      </span>
                                      <span>•</span>
                                      <span>관련도: {(source.relevance_score * 100).toFixed(0)}%</span>
                                    </div>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  )
}
