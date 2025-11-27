'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { apiClient } from '@/lib/api-client'
import { CyberCounter } from '@/components/CyberCounter'
import { useAuth } from '@/hooks/useAuth'
import {
  BuildingOfficeIcon,
  DocumentTextIcon,
  ArrowPathIcon,
  FunnelIcon,
  ChevronLeftIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationCircleIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'
import { showSuccess, showError } from '@/lib/toast-config'

interface CrawledDocument {
  document_id: string
  url: string
  title: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  crawled_at: string
  file_size?: number
  content_length?: number
}

interface CrawlJob {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  started_at: string
  completed_at?: string
  total_documents?: number
  processed_documents?: number
}

export default function CompanyDetailPage() {
  const router = useRouter()
  const params = useParams()
  const companyName = decodeURIComponent(params.companyName as string)
  const { isAdmin, isLoaded } = useAuth()

  const [documents, setDocuments] = useState<CrawledDocument[]>([])
  const [crawlJobs, setCrawlJobs] = useState<CrawlJob[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isStartingCrawl, setIsStartingCrawl] = useState(false)
  const [totalDocuments, setTotalDocuments] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined)
  const [showJobHistory, setShowJobHistory] = useState(false)

  const pageSize = 20

  useEffect(() => {
    loadCompanyData()
  }, [companyName, currentPage, statusFilter])

  useEffect(() => {
    if (showJobHistory) {
      loadCrawlJobs()
    }
  }, [showJobHistory])

  const loadCompanyData = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getCompanyCrawledDocuments(
        companyName,
        currentPage,
        pageSize,
        statusFilter
      )
      setDocuments(data.documents)
      setTotalDocuments(data.total)
      setTotalPages(data.total_pages)
    } catch (error) {
      console.error('Failed to load company documents:', error)
      setDocuments([])
      setTotalDocuments(0)
    } finally {
      setIsLoading(false)
    }
  }

  const loadCrawlJobs = async () => {
    try {
      const data = await apiClient.getCrawlerJobs(companyName, 1, 10)
      setCrawlJobs(data.jobs)
    } catch (error) {
      console.error('Failed to load crawl jobs:', error)
    }
  }

  const handleStartCrawl = async () => {
    try {
      setIsStartingCrawl(true)
      const result = await apiClient.startCrawlJob(companyName)
      showSuccess(`크롤링 작업이 시작되었습니다 (Job ID: ${result.job_id})`)
      loadCompanyData()
      if (showJobHistory) {
        loadCrawlJobs()
      }
    } catch (error) {
      console.error('Failed to start crawl job:', error)
    } finally {
      setIsStartingCrawl(false)
    }
  }

  const handleFilterChange = (filter: string | undefined) => {
    setStatusFilter(filter)
    setCurrentPage(1)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
      case 'processing':
        return <ArrowPathIcon className="w-5 h-5 text-blue-600 dark:text-blue-400 animate-spin" />
      case 'failed':
        return <XCircleIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
      case 'pending':
        return <ClockIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
      default:
        return <ExclamationCircleIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
    }
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      completed: '완료',
      processing: '처리 중',
      failed: '실패',
      pending: '대기 중',
    }
    return labels[status] || status
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
      processing: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
      failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
      pending: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
    }
    return colors[status] || colors.pending
  }

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return '-'
    const kb = bytes / 1024
    if (kb < 1024) return `${kb.toFixed(1)} KB`
    const mb = kb / 1024
    return `${mb.toFixed(1)} MB`
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <DashboardLayout>
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => router.push('/companies')}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors mb-4"
        >
          <ChevronLeftIcon className="w-5 h-5" />
          <span>보험사 목록으로</span>
        </button>

        <div className="flex justify-between items-start">
          <div className="flex items-center gap-4">
            <div className="p-4 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
              <BuildingOfficeIcon className="w-8 h-8 text-primary-600 dark:text-primary-400" />
            </div>
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {companyName}
              </h2>
              <p className="mt-1 text-gray-600 dark:text-gray-400">
                크롤링된 문서 및 작업 관리
              </p>
            </div>
          </div>

          {isAdmin ? (
            <button
              onClick={handleStartCrawl}
              disabled={isStartingCrawl}
              className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ArrowPathIcon className={`w-5 h-5 ${isStartingCrawl ? 'animate-spin' : ''}`} />
              {isStartingCrawl ? '크롤링 시작 중...' : '새 크롤링 시작'}
            </button>
          ) : (
            <div className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-dark-elevated rounded-lg">
              <ShieldCheckIcon className="w-5 h-5 text-gray-500 dark:text-gray-400" />
              <span className="text-sm text-gray-600 dark:text-gray-400">
                관리자 전용 기능
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="stat-card">
          <div className="flex items-center gap-3">
            <DocumentTextIcon className="w-8 h-8 text-cyber-cyan" />
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">총 문서</p>
              <CyberCounter
                value={totalDocuments}
                className="text-2xl"
                glowColor="cyan"
              />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center gap-3">
            <CheckCircleIcon className="w-8 h-8 text-cyber-green" />
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">완료</p>
              <CyberCounter
                value={documents.filter((d) => d.status === 'completed').length}
                className="text-2xl"
                glowColor="green"
              />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center gap-3">
            <ArrowPathIcon className="w-8 h-8 text-cyber-blue" />
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">처리 중</p>
              <CyberCounter
                value={documents.filter((d) => d.status === 'processing').length}
                className="text-2xl"
                glowColor="blue"
              />
            </div>
          </div>
        </div>

        <div className="stat-card">
          <div className="flex items-center gap-3">
            <XCircleIcon className="w-8 h-8 text-cyber-purple" />
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">실패</p>
              <CyberCounter
                value={documents.filter((d) => d.status === 'failed').length}
                className="text-2xl"
                glowColor="purple"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="card mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <FunnelIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">필터:</span>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => handleFilterChange(undefined)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                statusFilter === undefined
                  ? 'bg-primary-600 text-white dark:bg-cyber-cyan dark:text-gray-900'
                  : 'bg-gray-100 text-gray-700 dark:bg-dark-elevated dark:text-gray-300'
              }`}
            >
              전체
            </button>
            <button
              onClick={() => handleFilterChange('completed')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                statusFilter === 'completed'
                  ? 'bg-primary-600 text-white dark:bg-cyber-cyan dark:text-gray-900'
                  : 'bg-gray-100 text-gray-700 dark:bg-dark-elevated dark:text-gray-300'
              }`}
            >
              완료
            </button>
            <button
              onClick={() => handleFilterChange('processing')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                statusFilter === 'processing'
                  ? 'bg-primary-600 text-white dark:bg-cyber-cyan dark:text-gray-900'
                  : 'bg-gray-100 text-gray-700 dark:bg-dark-elevated dark:text-gray-300'
              }`}
            >
              처리 중
            </button>
            <button
              onClick={() => handleFilterChange('failed')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                statusFilter === 'failed'
                  ? 'bg-primary-600 text-white dark:bg-cyber-cyan dark:text-gray-900'
                  : 'bg-gray-100 text-gray-700 dark:bg-dark-elevated dark:text-gray-300'
              }`}
            >
              실패
            </button>
          </div>

          <div className="ml-auto">
            <button
              onClick={() => setShowJobHistory(!showJobHistory)}
              className="btn-secondary text-sm"
            >
              {showJobHistory ? '문서 목록 보기' : '작업 이력 보기'}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {showJobHistory ? (
        /* Crawl Job History */
        <div className="card">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-4">
            크롤링 작업 이력
          </h3>

          {crawlJobs.length === 0 ? (
            <div className="text-center py-12">
              <ClockIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">작업 이력이 없습니다</p>
            </div>
          ) : (
            <div className="space-y-4">
              {crawlJobs.map((job) => (
                <div
                  key={job.job_id}
                  className="border border-gray-200 dark:border-dark-border rounded-lg p-4 hover:border-primary-500 dark:hover:border-cyber-cyan transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(job.status)}
                      <div>
                        <p className="font-medium text-gray-900 dark:text-gray-100">
                          Job ID: {job.job_id}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          시작: {formatDate(job.started_at)}
                        </p>
                        {job.completed_at && (
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            완료: {formatDate(job.completed_at)}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="text-right">
                      <span className={`inline-flex px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                        {getStatusLabel(job.status)}
                      </span>
                      {job.total_documents !== undefined && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                          {job.processed_documents || 0} / {job.total_documents} 문서
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Documents Table */
        <>
          {isLoading ? (
            <div className="card">
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
                  <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
                </div>
              </div>
            </div>
          ) : documents.length === 0 ? (
            <div className="card text-center py-12">
              <DocumentTextIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
                문서가 없습니다
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                아직 크롤링된 문서가 없거나 필터 조건에 맞는 문서가 없습니다
              </p>
              <button
                onClick={handleStartCrawl}
                disabled={isStartingCrawl}
                className="btn-primary inline-flex items-center gap-2"
              >
                <ArrowPathIcon className={`w-5 h-5 ${isStartingCrawl ? 'animate-spin' : ''}`} />
                첫 크롤링 시작하기
              </button>
            </div>
          ) : (
            <div className="card overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-dark-border">
                <thead>
                  <tr className="bg-gray-50 dark:bg-dark-elevated">
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      제목
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      URL
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      크롤링 시간
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      파일 크기
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-cyber-bg-surface divide-y divide-gray-200 dark:divide-dark-border">
                  {documents.map((doc) => (
                    <tr
                      key={doc.document_id}
                      className="hover:bg-gray-50 dark:hover:bg-dark-elevated transition-colors"
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(doc.status)}
                          <span className={`inline-flex px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(doc.status)}`}>
                            {getStatusLabel(doc.status)}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm font-medium text-gray-900 dark:text-gray-100 max-w-md truncate">
                          {doc.title || '제목 없음'}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <a
                          href={doc.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-sm text-primary-600 dark:text-primary-400 hover:underline max-w-xs truncate block"
                        >
                          {doc.url}
                        </a>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {formatDate(doc.crawled_at)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {formatFileSize(doc.file_size)}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="card mt-6">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  페이지 {currentPage} / {totalPages} (총 {totalDocuments}개 문서)
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-dark-elevated text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    이전
                  </button>
                  <button
                    onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 rounded-lg bg-gray-100 dark:bg-dark-elevated text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    다음
                  </button>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  )
}
