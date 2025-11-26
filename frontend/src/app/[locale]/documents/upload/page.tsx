'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import FileUpload from '@/components/FileUpload'
import { apiClient } from '@/lib/api-client'
import { ArrowLeftIcon, SparklesIcon } from '@heroicons/react/24/outline'

export default function DocumentUploadPage() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [extractionConfidence, setExtractionConfidence] = useState<number | null>(null)

  const [metadata, setMetadata] = useState({
    insurer: '',
    product_name: '',
    product_code: '',
    launch_date: '',
    description: '',
    document_type: 'terms',
    tags: '',
  })

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    setError(null)
    setSuccess(false)
    setExtractionConfidence(null)

    // 파일명에서 간단한 정보 추출 시도
    extractFromFilename(selectedFile.name)
  }

  const extractFromFilename = (filename: string) => {
    // 파일명에서 기본 정보 추출 (예: 삼성화재_암보험_2024.pdf, 삼성화재_암보험_20240115.pdf)
    const parts = filename.replace('.pdf', '').split(/[_-]/)

    let insurer = ''
    let product_name = ''
    let launch_date = ''

    if (parts.length >= 2) {
      insurer = parts[0] || ''
      product_name = parts[1] || ''

      // 날짜 패턴 찾기 (YYYYMMDD, YYMMDD, YYYY-MM-DD, YYYY)
      for (let i = 2; i < parts.length; i++) {
        const part = parts[i]

        // YYYYMMDD 형식 (8자리)
        if (/^\d{8}$/.test(part)) {
          const year = part.substring(0, 4)
          const month = part.substring(4, 6)
          const day = part.substring(6, 8)
          launch_date = `${year}-${month}-${day}`
          break
        }
        // YYMMDD 형식 (6자리) - 예: 250901 → 2025-09-01
        else if (/^\d{6}$/.test(part)) {
          const yy = part.substring(0, 2)
          const mm = part.substring(2, 4)
          const dd = part.substring(4, 6)
          const year = `20${yy}` // 20xx년으로 가정
          launch_date = `${year}-${mm}-${dd}`
          break
        }
        // YYYY-MM-DD 형식 (이미 split되어서 YYYY만 남음)
        else if (/^\d{4}$/.test(part)) {
          // 다음 부분이 MM이고 그 다음이 DD인지 확인
          if (i + 2 < parts.length && /^\d{2}$/.test(parts[i + 1]) && /^\d{2}$/.test(parts[i + 2])) {
            launch_date = `${part}-${parts[i + 1]}-${parts[i + 2]}`
          } else {
            // 연도만 있는 경우 1월 1일로 설정
            launch_date = `${part}-01-01`
          }
          break
        }
      }

      setMetadata(prev => ({
        ...prev,
        insurer: insurer || prev.insurer,
        product_name: product_name || prev.product_name,
        launch_date: launch_date || prev.launch_date,
      }))
    }
  }

  const handleAIAnalysis = async () => {
    if (!file) {
      setError('먼저 파일을 선택해주세요.')
      return
    }

    setIsAnalyzing(true)
    setError(null)

    try {
      // 1. 먼저 백엔드 API 시도
      const result = await apiClient.extractDocumentMetadata(file)

      // AI가 추출한 정보로 폼 자동 입력
      setMetadata({
        ...metadata,
        insurer: result.insurer || metadata.insurer,
        product_name: result.product_name || metadata.product_name,
        product_code: result.product_code || metadata.product_code,
        launch_date: result.launch_date || metadata.launch_date,
        description: result.description || metadata.description,
      })

      setExtractionConfidence(result.confidence)
      setError(null)
      setIsAnalyzing(false)
    } catch (err: any) {
      // 백엔드 API 호출 실패
      const isNetworkError = !err.response && err.code === 'ERR_NETWORK'

      if (isNetworkError) {
        setError('백엔드 서버에 연결할 수 없습니다. 서버를 시작하거나 수동으로 입력해주세요.')
        console.log('💡 파일명에서 추출된 정보를 확인하세요.')
      } else {
        const errorMessage =
          err.response?.data?.detail ||
          err.message ||
          'AI 분석에 실패했습니다. 수동으로 입력해주세요.'
        setError(errorMessage)
      }
      setIsAnalyzing(false)
    }
  }

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setMetadata({
      ...metadata,
      [e.target.name]: e.target.value,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!file) {
      setError('파일을 선택해주세요.')
      return
    }

    if (!metadata.insurer || !metadata.product_name) {
      setError('필수 항목을 입력해주세요.')
      return
    }

    try {
      setIsUploading(true)
      setError(null)

      const response = await apiClient.uploadDocument(file, metadata)

      setSuccess(true)
      setError(null)

      // Redirect to documents list after 2 seconds
      setTimeout(() => {
        router.push('/documents')
      }, 2000)
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail?.error_message ||
        err.message ||
        '문서 업로드에 실패했습니다.'
      setError(errorMessage)
    } finally {
      setIsUploading(false)
    }
  }

  if (success) {
    return (
      <DashboardLayout>
        <div className="max-w-2xl mx-auto">
          <div className="rounded-md bg-green-50 p-6 text-center">
            <div className="mb-4">
              <svg
                className="w-16 h-16 text-green-500 mx-auto"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-green-800 mb-2">
              업로드 성공!
            </h3>
            <p className="text-sm text-green-700">
              문서가 성공적으로 업로드되었습니다. 문서 처리가 시작됩니다.
            </p>
            <p className="text-xs text-green-600 mt-2">
              2초 후 문서 목록으로 이동합니다...
            </p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            뒤로 가기
          </button>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">문서 업로드</h2>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            새로운 보험 약관 문서를 업로드하고 분석하세요
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-8">
          {/* File Upload */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">파일 선택</h3>
            <FileUpload onFileSelect={handleFileSelect} accept=".pdf" maxSize={50} />

            {/* AI Analysis Button */}
            {file && (
              <div className="mt-6 border-t border-gray-200 dark:border-dark-border pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      AI가 문서를 분석하여 정보를 자동으로 추출합니다
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      OCR + LLM 기반 메타데이터 추출 (약 5-10초 소요)
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleAIAnalysis}
                    disabled={isAnalyzing}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isAnalyzing ? (
                      <>
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        AI 분석 중...
                      </>
                    ) : (
                      <>
                        <SparklesIcon className="w-5 h-5 mr-2" />
                        AI로 자동 입력
                      </>
                    )}
                  </button>
                </div>

                {/* Confidence Score */}
                {extractionConfidence !== null && (
                  <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-md">
                    <div className="flex items-center">
                      <div className="flex-1">
                        <p className="text-sm font-medium text-green-800 dark:text-green-200">
                          AI 분석 완료!
                        </p>
                        <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                          추출된 정보를 확인하고 수정하세요
                        </p>
                      </div>
                      <div className="ml-4">
                        <div className="flex items-center">
                          <span className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {Math.round(extractionConfidence * 100)}%
                          </span>
                          <span className="ml-2 text-xs text-green-600 dark:text-green-400">
                            신뢰도
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Metadata Form */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold">문서 정보</h3>
              {extractionConfidence !== null && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300">
                  AI 자동 입력됨
                </span>
              )}
            </div>
            <div className="space-y-6">
              {/* Insurer */}
              <div>
                <label htmlFor="insurer" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  보험사 *
                </label>
                <input
                  type="text"
                  id="insurer"
                  name="insurer"
                  required
                  className="input-field"
                  placeholder="예: 삼성화재, 현대해상"
                  value={metadata.insurer}
                  onChange={handleInputChange}
                />
              </div>

              {/* Product Name */}
              <div>
                <label
                  htmlFor="product_name"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  상품명 *
                </label>
                <input
                  type="text"
                  id="product_name"
                  name="product_name"
                  required
                  className="input-field"
                  placeholder="예: 암보험, 실손보험"
                  value={metadata.product_name}
                  onChange={handleInputChange}
                />
              </div>

              {/* Product Code */}
              <div>
                <label
                  htmlFor="product_code"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  상품 코드
                </label>
                <input
                  type="text"
                  id="product_code"
                  name="product_code"
                  className="input-field"
                  placeholder="예: SS-CA-2024-001"
                  value={metadata.product_code}
                  onChange={handleInputChange}
                />
              </div>

              {/* Launch Date */}
              <div>
                <label
                  htmlFor="launch_date"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  출시일
                </label>
                <input
                  type="date"
                  id="launch_date"
                  name="launch_date"
                  className="input-field"
                  value={metadata.launch_date}
                  onChange={handleInputChange}
                />
              </div>

              {/* Document Type */}
              <div>
                <label
                  htmlFor="document_type"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  문서 유형
                </label>
                <select
                  id="document_type"
                  name="document_type"
                  className="input-field"
                  value={metadata.document_type}
                  onChange={handleInputChange}
                >
                  <option value="terms">약관</option>
                  <option value="brochure">상품 안내장</option>
                  <option value="guide">가입 설계서</option>
                  <option value="other">기타</option>
                </select>
              </div>

              {/* Tags */}
              <div>
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  태그
                </label>
                <input
                  type="text"
                  id="tags"
                  name="tags"
                  className="input-field"
                  placeholder="쉼표로 구분 (예: 암보험, 비갱신형, 무배당)"
                  value={metadata.tags}
                  onChange={handleInputChange}
                />
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                  태그는 쉼표(,)로 구분하여 입력하세요
                </p>
              </div>

              {/* Description */}
              <div>
                <label
                  htmlFor="description"
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                  설명
                </label>
                <textarea
                  id="description"
                  name="description"
                  rows={4}
                  className="input-field"
                  placeholder="문서에 대한 추가 설명을 입력하세요"
                  value={metadata.description}
                  onChange={handleInputChange}
                />
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">오류 발생</h3>
                  <div className="mt-2 text-sm text-red-700">
                    <p>{error}</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Submit Button */}
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="btn-secondary"
              disabled={isUploading}
            >
              취소
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={isUploading || !file}
            >
              {isUploading ? '업로드 중...' : '업로드'}
            </button>
          </div>
        </form>
      </div>
    </DashboardLayout>
  )
}
