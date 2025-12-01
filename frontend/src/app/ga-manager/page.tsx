'use client'

/**
 * GA Manager Dashboard Page
 *
 * Enhancement #4: GA Manager View
 * Team-wide analytics dashboard for GA Managers (FP_MANAGER role).
 */

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { fetchGATeamOverview } from '@/lib/ga-analytics-api'
import { GATeamMetrics } from '@/types/ga-analytics'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function GAManagerPage() {
  const router = useRouter()
  const [metrics, setMetrics] = useState<GATeamMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Auto-refresh every 60 seconds
  useEffect(() => {
    loadMetrics()

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadMetrics(true) // Silent refresh
      }, 60000) // 60 seconds

      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const loadMetrics = async (silent: boolean = false) => {
    try {
      if (!silent) {
        setLoading(true)
      } else {
        setRefreshing(true)
      }
      setError(null)
      const data = await fetchGATeamOverview()
      setMetrics(data)
      setLastUpdated(new Date())
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load GA metrics'
      setError(message)

      // If access denied, likely not a GA Manager
      if (message.includes('403') || message.includes('Access denied')) {
        setError('이 페이지는 GA Manager만 접근할 수 있습니다.')
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleManualRefresh = () => {
    loadMetrics(false)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(amount)
  }

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('ko-KR')
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                GA Manager Dashboard
              </h2>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                팀 전체 성과 지표 및 FP 관리
              </p>
              {lastUpdated && (
                <p className="mt-1 text-xs text-gray-500 dark:text-gray-500">
                  마지막 업데이트: {lastUpdated.toLocaleTimeString('ko-KR')}
                  {refreshing && (
                    <span className="ml-2 inline-flex items-center">
                      <svg className="animate-spin h-3 w-3 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      <span className="ml-1">갱신 중...</span>
                    </span>
                  )}
                </p>
              )}
            </div>
            <div className="flex items-center gap-3">
              {/* Auto-refresh toggle */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="w-4 h-4 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
                <span className="text-sm text-gray-700 dark:text-gray-300">
                  자동 갱신 (60초)
                </span>
              </label>
              {/* Manual refresh button */}
              <button
                onClick={handleManualRefresh}
                disabled={loading || refreshing}
                className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <svg
                  className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span className="text-sm">새로고침</span>
              </button>
            </div>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        ) : error ? (
          <div className="text-center py-12">
            <p className="text-red-600">{error}</p>
            <button onClick={loadMetrics} className="mt-4 btn-primary">
              다시 시도
            </button>
          </div>
        ) : metrics ? (
          <div className="space-y-6">
            {/* Team Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">총 FP 수</p>
                <div className="mt-2 flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {metrics.total_fps}명
                  </p>
                  <span className="text-sm text-gray-500">
                    활성: {metrics.active_fps}명
                  </span>
                </div>
              </div>

              <div className="card">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">총 고객 수</p>
                <div className="mt-2 flex items-baseline gap-2">
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {metrics.total_customers.toLocaleString()}
                  </p>
                  <span className="text-sm text-green-600">
                    +{metrics.new_customers_this_month} 이번 달
                  </span>
                </div>
              </div>

              <div className="card">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">총 보험 계약</p>
                <div className="mt-2">
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {metrics.total_policies.toLocaleString()}건
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    총 보장액: {formatCurrency(metrics.total_coverage_amount)}
                  </p>
                </div>
              </div>

              <div className="card">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">총 질의 수</p>
                <div className="mt-2">
                  <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    {metrics.total_queries.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    오늘: {metrics.queries_today} / 이번 주: {metrics.queries_this_week}
                  </p>
                </div>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Coverage Breakdown */}
              {metrics.coverage_breakdown.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                    보험 유형별 분포
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={metrics.coverage_breakdown}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="coverage_type" />
                      <YAxis />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: 'none',
                          borderRadius: '8px',
                          color: '#fff',
                        }}
                      />
                      <Legend />
                      <Bar dataKey="count" fill="#0ea5e9" name="계약 수" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Quick Stats */}
              <div className="card">
                <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                  팀 통계
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">활성 고객</span>
                    <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {metrics.active_customers.toLocaleString()}명
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">월 보험료 총액</span>
                    <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {formatCurrency(metrics.total_monthly_premium)}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">평균 질의 신뢰도</span>
                    <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {metrics.avg_query_confidence !== null
                        ? `${(metrics.avg_query_confidence * 100).toFixed(1)}%`
                        : '-'}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 dark:text-gray-400">이번 달 질의</span>
                    <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {metrics.queries_this_month.toLocaleString()}건
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Top Performing FPs */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                우수 FP 순위
              </h3>

              {metrics.top_fps.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-gray-500 dark:text-gray-400">등록된 FP가 없습니다.</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          순위
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          이름
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          고객 수
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          보험 계약
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          질의 수
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          평균 신뢰도
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                          마지막 활동
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                      {metrics.top_fps.map((fp, idx) => (
                        <tr key={fp.fp_id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              {idx < 3 ? (
                                <span className="text-2xl">
                                  {idx === 0 ? '🥇' : idx === 1 ? '🥈' : '🥉'}
                                </span>
                              ) : (
                                <span className="text-sm text-gray-500">#{idx + 1}</span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                            {fp.fp_name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {fp.total_customers}명
                            <span className="text-xs text-gray-400 ml-1">
                              (활성: {fp.active_customers})
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {fp.total_policies}건
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {fp.total_queries}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {fp.avg_query_confidence !== null
                              ? `${(fp.avg_query_confidence * 100).toFixed(0)}%`
                              : '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {formatDate(fp.last_activity)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        ) : null}
      </div>
    </DashboardLayout>
  )
}
