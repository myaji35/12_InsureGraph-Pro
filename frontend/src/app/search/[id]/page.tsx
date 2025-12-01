'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft, FileText, Building2, Calendar, Hash, DollarSign, Clock } from 'lucide-react'

interface Article {
  article_num: string
  title: string
  page: number
  raw_text: string
  paragraphs: any[]
}

interface Amount {
  amount_str: string
  normalized_value: number
  context: string
  position: number
}

interface Period {
  period_str: string
  normalized_days: number
  context: string
  position: number
}

interface KCDCode {
  code: string
  description: string
  position: number
}

interface DocumentDetail {
  id: string
  policy_name: string
  insurer: string
  full_text: string
  parsed_structure: {
    articles: Article[]
    total_pages: number
    parsing_confidence: number
  }
  critical_data: {
    amounts: Amount[]
    periods: Period[]
    kcd_codes: KCDCode[]
  }
  total_pages: number
  total_chars: number
  total_articles: number
  total_paragraphs: number
  total_subclauses: number
  total_amounts: number
  total_periods: number
  total_kcd_codes: number
  created_at: string
  updated_at: string
}

export default function DocumentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const documentId = params.id as string

  const [document, setDocument] = useState<DocumentDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'articles' | 'amounts' | 'periods' | 'codes'>('articles')

  useEffect(() => {
    loadDocument()
  }, [documentId])

  const loadDocument = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/search/documents/${documentId}`
      )

      if (!response.ok) {
        throw new Error('Failed to load document')
      }

      const data: DocumentDetail = await response.json()
      setDocument(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  const formatAmount = (amount: number) => {
    if (amount >= 100000000) {
      return `${(amount / 100000000).toFixed(1)}억원`
    } else if (amount >= 10000) {
      return `${(amount / 10000).toFixed(0)}만원`
    } else {
      return `${amount}원`
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">문서를 불러오는 중...</p>
        </div>
      </div>
    )
  }

  if (error || !document) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm p-8 max-w-md">
          <h2 className="text-xl font-semibold text-gray-900 mb-2">오류 발생</h2>
          <p className="text-gray-600 mb-4">{error || '문서를 찾을 수 없습니다'}</p>
          <button
            onClick={() => router.back()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            돌아가기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
          >
            <ArrowLeft className="h-5 w-5" />
            검색 결과로 돌아가기
          </button>

          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            {document.policy_name}
          </h1>

          <div className="flex items-center gap-6 text-sm text-gray-600">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              {document.insurer}
            </div>
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {document.total_pages} 페이지
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              {new Date(document.created_at).toLocaleDateString('ko-KR')}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8">
        <div className="grid grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="col-span-2">
            {/* Tabs */}
            <div className="bg-white rounded-lg shadow-sm mb-6">
              <div className="border-b border-gray-200">
                <nav className="flex">
                  <button
                    onClick={() => setActiveTab('articles')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 ${
                      activeTab === 'articles'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    조항 ({document.total_articles})
                  </button>
                  <button
                    onClick={() => setActiveTab('amounts')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 ${
                      activeTab === 'amounts'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    보험금 ({document.total_amounts})
                  </button>
                  <button
                    onClick={() => setActiveTab('periods')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 ${
                      activeTab === 'periods'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    기간 ({document.total_periods})
                  </button>
                  <button
                    onClick={() => setActiveTab('codes')}
                    className={`px-6 py-4 text-sm font-medium border-b-2 ${
                      activeTab === 'codes'
                        ? 'border-blue-600 text-blue-600'
                        : 'border-transparent text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    질병코드 ({document.total_kcd_codes})
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {/* Articles Tab */}
                {activeTab === 'articles' && (
                  <div className="space-y-6">
                    {document.parsed_structure.articles.map((article, idx) => (
                      <div key={idx} className="border-b border-gray-200 pb-6 last:border-0">
                        <div className="flex items-start gap-3 mb-3">
                          <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded">
                            {article.article_num}
                          </span>
                          <h3 className="text-lg font-semibold text-gray-900 flex-1">
                            {article.title}
                          </h3>
                          <span className="text-sm text-gray-500">
                            p.{article.page}
                          </span>
                        </div>
                        <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                          {article.raw_text}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Amounts Tab */}
                {activeTab === 'amounts' && (
                  <div className="space-y-4">
                    {document.critical_data.amounts.map((amount, idx) => (
                      <div key={idx} className="border-l-4 border-green-500 pl-4 py-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xl font-bold text-gray-900">
                            {formatAmount(amount.normalized_value)}
                          </span>
                          <span className="text-sm text-gray-500">{amount.amount_str}</span>
                        </div>
                        <p className="text-sm text-gray-600">{amount.context}</p>
                      </div>
                    ))}
                    {document.critical_data.amounts.length === 0 && (
                      <p className="text-gray-500 text-center py-8">
                        추출된 보험금 정보가 없습니다
                      </p>
                    )}
                  </div>
                )}

                {/* Periods Tab */}
                {activeTab === 'periods' && (
                  <div className="space-y-4">
                    {document.critical_data.periods.map((period, idx) => (
                      <div key={idx} className="border-l-4 border-purple-500 pl-4 py-2">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xl font-bold text-gray-900">
                            {period.normalized_days}일
                          </span>
                          <span className="text-sm text-gray-500">{period.period_str}</span>
                        </div>
                        <p className="text-sm text-gray-600">{period.context}</p>
                      </div>
                    ))}
                    {document.critical_data.periods.length === 0 && (
                      <p className="text-gray-500 text-center py-8">
                        추출된 기간 정보가 없습니다
                      </p>
                    )}
                  </div>
                )}

                {/* KCD Codes Tab */}
                {activeTab === 'codes' && (
                  <div className="space-y-4">
                    {document.critical_data.kcd_codes.map((code, idx) => (
                      <div key={idx} className="border-l-4 border-orange-500 pl-4 py-2">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="px-3 py-1 bg-orange-100 text-orange-800 text-sm font-mono rounded">
                            {code.code}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">{code.description}</p>
                      </div>
                    ))}
                    {document.critical_data.kcd_codes.length === 0 && (
                      <p className="text-gray-500 text-center py-8">
                        추출된 질병코드가 없습니다
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="col-span-1">
            {/* Stats Card */}
            <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">문서 통계</h3>

              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">총 페이지</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {document.total_pages}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">총 문자 수</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {document.total_chars.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">조항 수</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {document.total_articles}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">단락 수</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {document.total_paragraphs}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">파싱 정확도</span>
                  <span className="text-sm font-semibold text-gray-900">
                    {(document.parsed_structure.parsing_confidence * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>

            {/* Extracted Data Summary */}
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">추출 데이터</h3>

              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <DollarSign className="h-5 w-5 text-green-600" />
                  <div className="flex-1">
                    <div className="text-sm text-gray-600">보험금</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {document.total_amounts}개
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Clock className="h-5 w-5 text-purple-600" />
                  <div className="flex-1">
                    <div className="text-sm text-gray-600">기간</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {document.total_periods}개
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <Hash className="h-5 w-5 text-orange-600" />
                  <div className="flex-1">
                    <div className="text-sm text-gray-600">질병코드</div>
                    <div className="text-lg font-semibold text-gray-900">
                      {document.total_kcd_codes}개
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
