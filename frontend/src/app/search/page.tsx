'use client'

import { useState, useEffect } from 'react'
import { Search as SearchIcon, Filter, Loader2 } from 'lucide-react'

interface DocumentResult {
  id: string
  policy_name: string
  insurer: string
  total_pages: number
  total_articles: number
  total_paragraphs: number
  total_amounts: number
  total_periods: number
  total_kcd_codes: number
  relevance: number
  created_at: string
}

interface SearchResponse {
  results: DocumentResult[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export default function SearchPage() {
  // State
  const [query, setQuery] = useState('')
  const [insurer, setInsurer] = useState('')
  const [amountMin, setAmountMin] = useState('')
  const [amountMax, setAmountMax] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)

  const [results, setResults] = useState<DocumentResult[]>([])
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [insurers, setInsurers] = useState<string[]>([])
  const [showFilters, setShowFilters] = useState(false)

  // Load insurers on mount
  useEffect(() => {
    loadInsurers()
  }, [])

  // Search when params change
  useEffect(() => {
    if (query || insurer || amountMin || amountMax) {
      performSearch()
    }
  }, [page])

  const loadInsurers = async () => {
    try {
      const response = await fetch('http://localhost:3030/api/v1/search/insurers')
      const data = await response.json()
      setInsurers(data.insurers)
    } catch (err) {
      console.error('Failed to load insurers:', err)
    }
  }

  const performSearch = async () => {
    setLoading(true)
    setError('')

    try {
      // Build query params
      const params = new URLSearchParams()
      if (query) params.append('q', query)
      if (insurer) params.append('insurer', insurer)
      if (amountMin) params.append('amount_min', amountMin)
      if (amountMax) params.append('amount_max', amountMax)
      params.append('page', page.toString())
      params.append('page_size', pageSize.toString())

      const response = await fetch(
        `http://localhost:3030/api/v1/search/documents?${params.toString()}`
      )

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data: SearchResponse = await response.json()

      setResults(data.results)
      setTotal(data.total)
      setTotalPages(data.total_pages)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    performSearch()
  }

  const handleClearFilters = () => {
    setQuery('')
    setInsurer('')
    setAmountMin('')
    setAmountMax('')
    setPage(1)
    setResults([])
    setTotal(0)
  }

  const formatAmount = (amount: string) => {
    const num = parseInt(amount)
    if (num >= 100000000) {
      return `${(num / 100000000).toFixed(1)}억원`
    } else if (num >= 10000) {
      return `${(num / 10000).toFixed(0)}만원`
    } else {
      return `${num}원`
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">보험 약관 검색</h1>
          <p className="mt-2 text-gray-600">
            업로드된 보험 약관에서 내용을 검색하세요
          </p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="bg-white rounded-lg shadow-sm p-6 mb-6">
          {/* Main Search Bar */}
          <div className="flex gap-3 mb-4">
            <div className="flex-1 relative">
              <SearchIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="보험금, 질병명, 조항 내용 검색..."
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  검색 중...
                </>
              ) : (
                <>
                  <SearchIcon className="h-5 w-5" />
                  검색
                </>
              )}
            </button>
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 flex items-center gap-2"
            >
              <Filter className="h-5 w-5" />
              필터
            </button>
          </div>

          {/* Filters (collapsible) */}
          {showFilters && (
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
              {/* Insurer Filter */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  보험사
                </label>
                <select
                  value={insurer}
                  onChange={(e) => setInsurer(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">전체</option>
                  {insurers.map((ins) => (
                    <option key={ins} value={ins}>
                      {ins}
                    </option>
                  ))}
                </select>
              </div>

              {/* Amount Min */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최소 보험금 (원)
                </label>
                <input
                  type="number"
                  value={amountMin}
                  onChange={(e) => setAmountMin(e.target.value)}
                  placeholder="예: 10000000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Amount Max */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  최대 보험금 (원)
                </label>
                <input
                  type="number"
                  value={amountMax}
                  onChange={(e) => setAmountMax(e.target.value)}
                  placeholder="예: 100000000"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Clear Filters Button */}
              <div className="col-span-3 flex justify-end">
                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900"
                >
                  필터 초기화
                </button>
              </div>
            </div>
          )}
        </form>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Results Header */}
        {total > 0 && (
          <div className="flex items-center justify-between mb-4">
            <p className="text-gray-600">
              총 <span className="font-semibold text-gray-900">{total}</span>개 문서 검색됨
            </p>
            <p className="text-sm text-gray-500">
              페이지 {page} / {totalPages}
            </p>
          </div>
        )}

        {/* Results List */}
        <div className="space-y-4">
          {results.length === 0 && !loading && (
            <div className="bg-white rounded-lg shadow-sm p-12 text-center">
              <SearchIcon className="h-12 w-12 mx-auto text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                검색 결과가 없습니다
              </h3>
              <p className="text-gray-600">
                다른 검색어나 필터를 시도해보세요
              </p>
            </div>
          )}

          {results.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-lg shadow-sm p-6 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => window.open(`/search/${doc.id}`, '_blank')}
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {doc.policy_name}
                  </h3>
                  <p className="text-sm text-gray-600">{doc.insurer}</p>
                </div>
                {query && (
                  <div className="ml-4">
                    <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
                      관련도: {(doc.relevance * 100).toFixed(0)}%
                    </span>
                  </div>
                )}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-4 gap-4 text-sm text-gray-600 mb-3">
                <div>
                  <span className="font-medium text-gray-700">{doc.total_pages}</span> 페이지
                </div>
                <div>
                  <span className="font-medium text-gray-700">{doc.total_articles}</span> 조항
                </div>
                <div>
                  <span className="font-medium text-gray-700">{doc.total_amounts}</span> 보험금
                </div>
                <div>
                  <span className="font-medium text-gray-700">{doc.total_kcd_codes}</span> 질병코드
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between text-sm text-gray-500 pt-3 border-t border-gray-100">
                <span>업로드: {new Date(doc.created_at).toLocaleDateString('ko-KR')}</span>
                <span className="text-blue-600 hover:text-blue-800">자세히 보기 →</span>
              </div>
            </div>
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex justify-center gap-2 mt-8">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1 || loading}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              이전
            </button>

            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = Math.max(1, Math.min(page - 2 + i, totalPages - 4 + i))
              if (pageNum > totalPages) return null
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  disabled={loading}
                  className={`px-4 py-2 border rounded-lg ${
                    page === pageNum
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 hover:bg-gray-50'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {pageNum}
                </button>
              )
            })}

            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages || loading}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              다음
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
