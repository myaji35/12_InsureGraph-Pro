'use client'

/**
 * FP Workspace Dashboard Page
 *
 * Story 3.5: Dashboard & Analytics
 * Main dashboard for FP users showing key metrics and analytics.
 */

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { fetchDashboardOverview } from '@/lib/analytics-api'
import { DashboardOverview } from '@/types/analytics'
import { getQueryStats } from '@/lib/query-history-api'
import { QueryHistoryStats } from '@/types/query-history'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8']

export default function WorkspacePage() {
  const router = useRouter()
  const [overview, setOverview] = useState<DashboardOverview | null>(null)
  const [queryStats, setQueryStats] = useState<QueryHistoryStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Enhancement #3: Auto-refresh every 30 seconds
  useEffect(() => {
    loadDashboard()

    if (autoRefresh) {
      const interval = setInterval(() => {
        loadDashboard(true) // Silent refresh
      }, 30000) // 30 seconds

      return () => clearInterval(interval)
    }
  }, [autoRefresh])

  const loadDashboard = async (silent: boolean = false) => {
    try {
      if (!silent) {
        setLoading(true)
      } else {
        setRefreshing(true)
      }
      setError(null)
      const [overviewData, statsData] = await Promise.all([
        fetchDashboardOverview(),
        getQueryStats().catch(() => null), // Query stats is optional
      ])
      setOverview(overviewData)
      setQueryStats(statsData)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleManualRefresh = () => {
    loadDashboard(false)
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('ko-KR')
  }

  const getTrendIcon = (trend?: string) => {
    if (trend === 'up') {
      return <span className="text-green-500">↑</span>
    } else if (trend === 'down') {
      return <span className="text-red-500">↓</span>
    }
    return <span className="text-gray-400">→</span>
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header - Enhancement #3: Real-time Updates */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                FP 워크스페이스
              </h2>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                고객 관리 및 성과 지표를 한눈에 확인하세요
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
                  자동 갱신 (30초)
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
            <button onClick={loadDashboard} className="mt-4 btn-primary">
              다시 시도
            </button>
          </div>
        ) : overview ? (
          <div className="space-y-6">
            {/* Metric Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {overview.metrics.map((metric, idx) => (
                <div key={idx} className="card">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                        {metric.label}
                      </p>
                      <div className="mt-2 flex items-baseline gap-2">
                        <p className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                          {metric.value.toLocaleString()}
                        </p>
                        {metric.change && (
                          <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
                            {getTrendIcon(metric.trend)} {metric.change}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Coverage Breakdown - Bar Chart */}
              {overview.coverage_breakdown.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                    보험 유형별 분포
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={overview.coverage_breakdown}>
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

              {/* Coverage Breakdown - Pie Chart */}
              {overview.coverage_breakdown.length > 0 && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                    보험 유형별 비율
                  </h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={overview.coverage_breakdown}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ coverage_type, count }) => `${coverage_type}: ${count}`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="count"
                      >
                        {overview.coverage_breakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#1f2937',
                          border: 'none',
                          borderRadius: '8px',
                          color: '#fff',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
              )}
            </div>

            {/* Query History Stats - Enhancement #2 */}
            {queryStats && (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    질의 통계
                  </h3>
                  <button
                    onClick={() => router.push('/query-history')}
                    className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                  >
                    전체 보기 →
                  </button>
                </div>

                {/* Query Count Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div className="text-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                      {queryStats.total_queries}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      총 질의
                    </p>
                  </div>
                  <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {queryStats.queries_today}
                    </p>
                    <p className="text-sm text-blue-600 dark:text-blue-400 mt-1">
                      오늘
                    </p>
                  </div>
                  <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {queryStats.queries_this_week}
                    </p>
                    <p className="text-sm text-green-600 dark:text-green-400 mt-1">
                      이번 주
                    </p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {queryStats.queries_this_month}
                    </p>
                    <p className="text-sm text-purple-600 dark:text-purple-400 mt-1">
                      이번 달
                    </p>
                  </div>
                </div>

                {/* Average Stats */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {queryStats.avg_confidence !== null && queryStats.avg_confidence !== undefined && (
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        평균 신뢰도
                      </span>
                      <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {(queryStats.avg_confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                  {queryStats.avg_execution_time_ms && (
                    <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        평균 응답 시간
                      </span>
                      <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        {(queryStats.avg_execution_time_ms / 1000).toFixed(2)}초
                      </span>
                    </div>
                  )}
                </div>

                {/* Top Intents */}
                {queryStats.top_intents.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                      주요 질의 유형
                    </h4>
                    <div className="space-y-2">
                      {queryStats.top_intents.map((item, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <span className="text-sm text-gray-600 dark:text-gray-400">
                            {item.intent || '기타'}
                          </span>
                          <div className="flex items-center gap-2">
                            <div className="w-24 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary-600"
                                style={{
                                  width: `${(item.count / queryStats.total_queries) * 100}%`,
                                }}
                              />
                            </div>
                            <span className="text-sm font-medium text-gray-900 dark:text-gray-100 w-8 text-right">
                              {item.count}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Recent Customers */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  최근 고객
                </h3>
                <button
                  onClick={() => router.push('/customers')}
                  className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                >
                  전체 보기 →
                </button>
              </div>

              {overview.recent_customers.length === 0 ? (
                <div className="text-center py-8">
                  <svg
                    className="mx-auto h-12 w-12 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                    />
                  </svg>
                  <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
                    고객 없음
                  </h3>
                  <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                    새 고객을 추가하여 시작하세요.
                  </p>
                  <button
                    onClick={() => router.push('/customers')}
                    className="mt-4 btn-primary"
                  >
                    고객 추가
                  </button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                    <thead className="bg-gray-50 dark:bg-gray-800">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          이름
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          나이
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          보험
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          마지막 상담
                        </th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                          등록일
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                      {overview.recent_customers.map((customer) => (
                        <tr
                          key={customer.id}
                          className="hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
                          onClick={() => router.push(`/customers/${customer.id}`)}
                        >
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-gray-100">
                            {customer.name}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {customer.age}세
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                              {customer.policy_count}건
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {formatDate(customer.last_contact_date)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                            {formatDate(customer.created_at)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                빠른 실행
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <button
                  onClick={() => router.push('/customers')}
                  className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-left"
                >
                  <div className="flex items-center gap-3">
                    <svg
                      className="w-8 h-8 text-primary-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
                      />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        고객 관리
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        고객 추가 및 관리
                      </p>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => router.push('/query-simple')}
                  className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-left"
                >
                  <div className="flex items-center gap-3">
                    <svg
                      className="w-8 h-8 text-primary-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                      />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        보험 질의
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        약관 내용 질문하기
                      </p>
                    </div>
                  </div>
                </button>

                <button
                  onClick={() => router.push('/search')}
                  className="p-4 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 text-left"
                >
                  <div className="flex items-center gap-3">
                    <svg
                      className="w-8 h-8 text-primary-600"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        문서 검색
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        보험 약관 검색
                      </p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </DashboardLayout>
  )
}
