'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { use } from 'react'
import DashboardLayout from '@/components/DashboardLayout'
import { useCustomerStore } from '@/store/customer-store'
import {
  ArrowLeftIcon,
  UserIcon,
  EnvelopeIcon,
  PhoneIcon,
  BriefcaseIcon,
  CurrencyDollarIcon,
  ShieldCheckIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'
import { formatDate } from '@/lib/utils'

export default function CustomerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params)
  const router = useRouter()
  const {
    currentCustomer,
    customerInsurances,
    portfolioAnalysis,
    isLoading,
    fetchCustomer,
    fetchCustomerInsurances,
    fetchPortfolioAnalysis,
  } = useCustomerStore()

  useEffect(() => {
    loadCustomerData()
  }, [resolvedParams.id])

  const loadCustomerData = async () => {
    try {
      await fetchCustomer(resolvedParams.id)
      await fetchCustomerInsurances(resolvedParams.id)
      await fetchPortfolioAnalysis(resolvedParams.id)
    } catch (error) {
      console.error('Failed to load customer data:', error)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(amount)
  }

  const getRiskBadge = (riskProfile?: string) => {
    const colors: Record<string, string> = {
      conservative: 'bg-blue-100 text-blue-800',
      moderate: 'bg-yellow-100 text-yellow-800',
      aggressive: 'bg-red-100 text-red-800',
    }

    const labels: Record<string, string> = {
      conservative: '안정형',
      moderate: '중립형',
      aggressive: '공격형',
    }

    if (!riskProfile) return null

    return (
      <span className={`px-3 py-1 text-sm font-medium rounded-full ${colors[riskProfile]}`}>
        {labels[riskProfile]}
      </span>
    )
  }

  if (isLoading || !currentCustomer) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/customers')}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            고객 목록으로
          </button>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center">
                <UserIcon className="w-8 h-8 text-primary-600" />
              </div>
              <div>
                <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{currentCustomer.name}</h2>
                <div className="flex items-center gap-3 mt-2">
                  {getRiskBadge(currentCustomer.risk_profile)}
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    고객 ID: {currentCustomer.customer_id}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Customer Info */}
          <div className="lg:col-span-1 space-y-6">
            {/* Basic Info */}
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">기본 정보</h3>
              <div className="space-y-3">
                {currentCustomer.email && (
                  <div className="flex items-center gap-3">
                    <EnvelopeIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">이메일</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">{currentCustomer.email}</p>
                    </div>
                  </div>
                )}
                {currentCustomer.phone && (
                  <div className="flex items-center gap-3">
                    <PhoneIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">전화번호</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">{currentCustomer.phone}</p>
                    </div>
                  </div>
                )}
                {currentCustomer.birth_date && (
                  <div className="flex items-center gap-3">
                    <UserIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">생년월일</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">
                        {formatDate(currentCustomer.birth_date)}
                      </p>
                    </div>
                  </div>
                )}
                {currentCustomer.occupation && (
                  <div className="flex items-center gap-3">
                    <BriefcaseIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">직업</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">{currentCustomer.occupation}</p>
                    </div>
                  </div>
                )}
                {currentCustomer.annual_income && (
                  <div className="flex items-center gap-3">
                    <CurrencyDollarIcon className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-xs text-gray-600 dark:text-gray-400">연 소득</p>
                      <p className="text-sm text-gray-900 dark:text-gray-100">
                        {formatCurrency(currentCustomer.annual_income)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Notes */}
            {currentCustomer.notes && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">메모</h3>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {currentCustomer.notes}
                </p>
              </div>
            )}
          </div>

          {/* Right Column - Insurances & Analysis */}
          <div className="lg:col-span-2 space-y-6">
            {/* Portfolio Summary */}
            {portfolioAnalysis && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">포트폴리오 요약</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">총 보험료</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {formatCurrency(portfolioAnalysis.total_premium)}
                    </p>
                  </div>
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">총 보장액</p>
                    <p className="text-2xl font-bold text-green-600">
                      {formatCurrency(portfolioAnalysis.total_coverage)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Insurances */}
            <div className="card">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">가입 보험</h3>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {customerInsurances.length}건
                </span>
              </div>

              {customerInsurances.length === 0 ? (
                <div className="text-center py-8">
                  <ShieldCheckIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600 dark:text-gray-400">가입된 보험이 없습니다</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {customerInsurances.map((insurance) => (
                    <div
                      key={insurance.insurance_id}
                      className="p-4 border border-gray-200 dark:border-dark-border rounded-lg hover:border-primary-300 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-medium text-gray-900 dark:text-gray-100">
                            {insurance.product_name}
                          </h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">{insurance.insurer}</p>
                        </div>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            insurance.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : insurance.status === 'expired'
                              ? 'bg-gray-100 text-gray-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {insurance.status === 'active'
                            ? '유효'
                            : insurance.status === 'expired'
                            ? '만료'
                            : '해지'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-gray-600 dark:text-gray-400">보험료</p>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {formatCurrency(insurance.premium)}
                          </p>
                        </div>
                        <div>
                          <p className="text-gray-600 dark:text-gray-400">보장액</p>
                          <p className="font-medium text-gray-900 dark:text-gray-100">
                            {formatCurrency(insurance.coverage_amount)}
                          </p>
                        </div>
                      </div>
                      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        {formatDate(insurance.start_date)} ~{' '}
                        {insurance.end_date ? formatDate(insurance.end_date) : '계속'}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Risk Assessment */}
            {portfolioAnalysis && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">위험 평가</h3>
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm text-gray-600 dark:text-gray-400">위험 점수</span>
                    <span
                      className={`text-sm font-medium ${
                        portfolioAnalysis.risk_assessment.level === 'low'
                          ? 'text-green-600'
                          : portfolioAnalysis.risk_assessment.level === 'medium'
                          ? 'text-yellow-600'
                          : 'text-red-600'
                      }`}
                    >
                      {portfolioAnalysis.risk_assessment.level === 'low'
                        ? '낮음'
                        : portfolioAnalysis.risk_assessment.level === 'medium'
                        ? '보통'
                        : '높음'}
                    </span>
                  </div>
                  <div className="w-full h-2 bg-gray-200 dark:bg-dark-border rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        portfolioAnalysis.risk_assessment.level === 'low'
                          ? 'bg-green-500'
                          : portfolioAnalysis.risk_assessment.level === 'medium'
                          ? 'bg-yellow-500'
                          : 'bg-red-500'
                      }`}
                      style={{
                        width: `${portfolioAnalysis.risk_assessment.score * 100}%`,
                      }}
                    />
                  </div>
                </div>

                {portfolioAnalysis.risk_assessment.recommendations.length > 0 && (
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">권장사항</p>
                    <ul className="space-y-2">
                      {portfolioAnalysis.risk_assessment.recommendations.map(
                        (rec, index) => (
                          <li key={index} className="text-sm text-gray-700 dark:text-gray-300 flex gap-2">
                            <span className="text-primary-600">•</span>
                            <span>{rec}</span>
                          </li>
                        )
                      )}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Recommendations */}
            {portfolioAnalysis && portfolioAnalysis.recommendations.length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold mb-4">추천 상품</h3>
                <div className="space-y-3">
                  {portfolioAnalysis.recommendations.map((rec, index) => (
                    <div
                      key={index}
                      className="p-4 border border-gray-200 dark:border-dark-border rounded-lg"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-medium text-gray-900 dark:text-gray-100">{rec.product_name}</h4>
                        <span
                          className={`px-2 py-1 text-xs font-medium rounded-full ${
                            rec.priority === 'high'
                              ? 'bg-red-100 text-red-800'
                              : rec.priority === 'medium'
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {rec.priority === 'high'
                            ? '높음'
                            : rec.priority === 'medium'
                            ? '보통'
                            : '낮음'}
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300">{rec.reason}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
