'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { apiClient } from '@/lib/api-client'
import {
  BuildingOfficeIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

interface CompanyConfig {
  company_name: string
  url: string
  enabled: boolean
  last_crawled_at?: string
  total_documents?: number
}

interface CompanyStats {
  total_documents: number
  status_breakdown: Record<string, number>
}

export default function CompaniesPage() {
  const router = useRouter()
  const [companies, setCompanies] = useState<CompanyConfig[]>([])
  const [companyStats, setCompanyStats] = useState<Record<string, CompanyStats>>({})
  const [isLoading, setIsLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    loadCompanies()
  }, [])

  const loadCompanies = async () => {
    try {
      setIsLoading(true)
      const configs = await apiClient.getCrawlerConfigs(false)
      setCompanies(configs)

      // Load stats for each company
      const statsPromises = configs.map(async (config: CompanyConfig) => {
        try {
          const data = await apiClient.getCompanyCrawledDocuments(config.company_name, 1, 1)
          return {
            company_name: config.company_name,
            stats: {
              total_documents: data.total,
              status_breakdown: {}, // Could be enhanced with actual status data
            },
          }
        } catch (error) {
          return {
            company_name: config.company_name,
            stats: {
              total_documents: 0,
              status_breakdown: {},
            },
          }
        }
      })

      const statsResults = await Promise.all(statsPromises)
      const statsMap = statsResults.reduce((acc, { company_name, stats }) => {
        acc[company_name] = stats
        return acc
      }, {} as Record<string, CompanyStats>)

      setCompanyStats(statsMap)
    } catch (error) {
      console.error('Failed to load companies:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredCompanies = companies.filter((company) => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      return company.company_name.toLowerCase().includes(query)
    }
    return true
  })

  const handleCompanyClick = (companyName: string) => {
    router.push(`/companies/${encodeURIComponent(companyName)}`)
  }

  return (
    <DashboardLayout>
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">보험사 관리</h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              보험사별 크롤링 상태 및 수집된 문서를 관리하세요
            </p>
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="card mb-6">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="보험사 검색..."
            className="input-field pl-10"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      {/* Companies Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        </div>
      ) : filteredCompanies.length === 0 ? (
        <div className="card text-center py-12">
          <BuildingOfficeIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            보험사가 없습니다
          </h3>
          <p className="text-gray-600 dark:text-gray-400">
            등록된 보험사가 없거나 검색 결과가 없습니다
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCompanies.map((company) => {
            const stats = companyStats[company.company_name] || {
              total_documents: 0,
              status_breakdown: {},
            }

            return (
              <div
                key={company.company_name}
                className="card hover:shadow-lg transition-all cursor-pointer group"
                onClick={() => handleCompanyClick(company.company_name)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-primary-100 dark:bg-primary-900/30 rounded-lg">
                      <BuildingOfficeIcon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                        {company.company_name}
                      </h3>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium mt-1 ${
                          company.enabled
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                            : 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400'
                        }`}
                      >
                        {company.enabled ? '활성화' : '비활성화'}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="space-y-3">
                  {/* URL */}
                  <div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">웹사이트</p>
                    <p className="text-sm text-gray-700 dark:text-gray-300 truncate">{company.url}</p>
                  </div>

                  {/* Stats */}
                  <div className="pt-3 border-t border-gray-200 dark:border-dark-border">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <DocumentTextIcon className="w-4 h-4" />
                        <span>수집된 문서</span>
                      </div>
                      <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {stats.total_documents}
                      </span>
                    </div>
                  </div>

                  {/* Last Crawled */}
                  {company.last_crawled_at && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      마지막 크롤링:{' '}
                      {new Date(company.last_crawled_at).toLocaleDateString('ko-KR', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })}
                    </div>
                  )}
                </div>

                {/* Action Button */}
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-dark-border">
                  <button
                    className="w-full text-primary-600 dark:text-primary-400 hover:text-primary-700 dark:hover:text-primary-300 text-sm font-medium flex items-center justify-center gap-1 group-hover:gap-2 transition-all"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleCompanyClick(company.company_name)
                    }}
                  >
                    관리하기
                    <span className="transform group-hover:translate-x-1 transition-transform">→</span>
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Summary Stats */}
      {!isLoading && filteredCompanies.length > 0 && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <BuildingOfficeIcon className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">총 보험사</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {companies.length}
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <ChartBarIcon className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">활성화된 보험사</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {companies.filter((c) => c.enabled).length}
                </p>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                <DocumentTextIcon className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">총 수집 문서</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {Object.values(companyStats).reduce(
                    (sum, stats) => sum + stats.total_documents,
                    0
                  )}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
