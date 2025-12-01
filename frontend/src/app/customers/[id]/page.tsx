'use client'

/**
 * Customer Detail Page
 *
 * Enhancement: Customer Portfolio Management Detail View
 */

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { getCustomer, getCoverageSummary, updateCustomer, deleteCustomer } from '@/lib/customer-api'
import { CustomerWithPolicies, CoverageSummary, CustomerUpdateInput, Gender } from '@/types/customer'
import { getCustomerQueryHistory } from '@/lib/query-history-api'
import { QueryHistoryListResponse } from '@/types/query-history'
import { useToast } from '@/components/Toast'

export default function CustomerDetailPage() {
  const router = useRouter()
  const params = useParams()
  const toast = useToast()
  const customerId = params.id as string

  const [customer, setCustomer] = useState<CustomerWithPolicies | null>(null)
  const [coverage, setCoverage] = useState<CoverageSummary | null>(null)
  const [queryHistory, setQueryHistory] = useState<QueryHistoryListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editData, setEditData] = useState<CustomerUpdateInput>({})

  useEffect(() => {
    loadCustomerData()
  }, [customerId])

  const loadCustomerData = async () => {
    try {
      setLoading(true)
      setError(null)

      const [customerData, coverageData, historyData] = await Promise.all([
        getCustomer(customerId),
        getCoverageSummary(customerId).catch(() => null), // Coverage might not exist
        getCustomerQueryHistory(customerId, 1, 5).catch(() => null), // Query history might not exist
      ])

      setCustomer(customerData)
      setCoverage(coverageData)
      setQueryHistory(historyData)
      setEditData({
        name: customerData.name,
        birth_year: customerData.birth_year,
        gender: customerData.gender,
        phone: customerData.phone,
        email: customerData.email,
        occupation: customerData.occupation,
        notes: customerData.notes,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : '고객 정보를 불러오는데 실패했습니다')
      toast.error('고객 정보를 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = () => {
    setShowEditModal(true)
  }

  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await updateCustomer(customerId, editData)
      toast.success('고객 정보가 수정되었습니다')
      setShowEditModal(false)
      loadCustomerData()
    } catch (err) {
      toast.error(err instanceof Error ? err.message : '고객 정보 수정에 실패했습니다')
    }
  }

  const handleDelete = async () => {
    if (!confirm(`${customer?.name} 고객을 삭제하시겠습니까?\n\n모든 정책 정보도 함께 삭제됩니다.`)) {
      return
    }

    try {
      await deleteCustomer(customerId)
      toast.success('고객이 삭제되었습니다')
      router.push('/customers')
    } catch (err) {
      toast.error('고객 삭제에 실패했습니다')
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('ko-KR')
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
    }).format(amount)
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      active: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      expired: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
    }
    const labels = {
      active: '유효',
      expired: '만료',
      cancelled: '해지',
    }
    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[status as keyof typeof styles] || styles.cancelled}`}>
        {labels[status as keyof typeof labels] || status}
      </span>
    )
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  if (error || !customer) {
    return (
      <DashboardLayout>
        <div className="max-w-7xl mx-auto">
          <div className="text-center py-12">
            <p className="text-red-600">{error || '고객을 찾을 수 없습니다'}</p>
            <button onClick={() => router.push('/customers')} className="mt-4 btn-primary">
              고객 목록으로
            </button>
          </div>
        </div>
      </DashboardLayout>
    )
  }

  return (
    <DashboardLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/customers')}
              className="text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                {customer.name}
              </h2>
              <p className="mt-1 text-gray-600 dark:text-gray-400">
                {customer.age}세 · {customer.gender === 'M' ? '남성' : customer.gender === 'F' ? '여성' : '기타'}
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <button onClick={handleEdit} className="btn-secondary">
              수정
            </button>
            <button onClick={handleDelete} className="px-4 py-2 border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20">
              삭제
            </button>
          </div>
        </div>

        {/* Customer Info Card */}
        <div className="card mb-6">
          <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
            고객 정보
          </h3>
          <dl className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">이름</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{customer.name}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">생년</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{customer.birth_year}년 ({customer.age}세)</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">성별</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                {customer.gender === 'M' ? '남성' : customer.gender === 'F' ? '여성' : '기타'}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">연락처</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{customer.phone || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">이메일</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{customer.email || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">직업</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{customer.occupation || '-'}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">마지막 상담일</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{formatDate(customer.last_contact_date)}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">등록일</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{formatDate(customer.created_at)}</dd>
            </div>
            {customer.notes && (
              <div className="md:col-span-2">
                <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">메모</dt>
                <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{customer.notes}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Coverage Summary */}
        {coverage && (
          <div className="card mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
              보장 분석
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400">총 보장 금액</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(coverage.total_coverage)}
                </p>
              </div>
              <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400">월 보험료</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {formatCurrency(coverage.monthly_premium)}
                </p>
              </div>
              <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm text-gray-600 dark:text-gray-400">보장 유형</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  {coverage.coverage_types.length}개
                </p>
              </div>
            </div>

            {coverage.gaps && coverage.gaps.length > 0 && (
              <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border-l-4 border-yellow-400">
                <h4 className="font-semibold text-yellow-800 dark:text-yellow-200 mb-2">
                  보장 공백 발견
                </h4>
                <ul className="list-disc list-inside space-y-1">
                  {coverage.gaps.map((gap, idx) => (
                    <li key={idx} className="text-sm text-yellow-700 dark:text-yellow-300">
                      {gap}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {coverage.recommendations && coverage.recommendations.length > 0 && (
              <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <h4 className="font-semibold text-green-800 dark:text-green-200 mb-2">
                  추천 사항
                </h4>
                <ul className="list-disc list-inside space-y-1">
                  {coverage.recommendations.map((rec, idx) => (
                    <li key={idx} className="text-sm text-green-700 dark:text-green-300">
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Query History - Enhancement #2 */}
        {queryHistory && queryHistory.items.length > 0 && (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                질의 이력 ({queryHistory.total}건)
              </h3>
              {queryHistory.total > 5 && (
                <button
                  onClick={() => router.push(`/query-history?customer_id=${customerId}`)}
                  className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
                >
                  전체 보기 →
                </button>
              )}
            </div>

            <div className="space-y-3">
              {queryHistory.items.map((item) => (
                <div
                  key={item.id}
                  className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                        {item.query_text}
                      </p>
                      {item.answer_preview && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">
                          {item.answer_preview}
                        </p>
                      )}
                      <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                        {item.intent && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-primary-100 text-primary-800 dark:bg-primary-900 dark:text-primary-200">
                            {item.intent}
                          </span>
                        )}
                        {item.confidence !== null && item.confidence !== undefined && (
                          <span>
                            신뢰도: {(item.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                        {item.execution_time_ms && (
                          <span>
                            응답시간: {(item.execution_time_ms / 1000).toFixed(2)}초
                          </span>
                        )}
                        <span>
                          {new Date(item.created_at).toLocaleString('ko-KR')}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {queryHistory.items.length === 0 && (
              <div className="text-center py-8">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
                <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">질의 이력 없음</h3>
                <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  이 고객과 관련된 질의 이력이 아직 없습니다.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Policies */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              보험 계약 ({customer.policy_count}건)
            </h3>
          </div>

          {customer.policies && customer.policies.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      보험사
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      유형
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      보장 금액
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      보험료
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      기간
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                      상태
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {customer.policies.map((policy) => (
                    <tr key={policy.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {policy.insurer}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {policy.policy_type}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {policy.coverage_amount ? formatCurrency(Number(policy.coverage_amount)) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                        {policy.premium ? formatCurrency(Number(policy.premium)) : '-'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatDate(policy.start_date)} ~ {formatDate(policy.end_date)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {getStatusBadge(policy.status)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">보험 없음</h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                아직 등록된 보험 계약이 없습니다.
              </p>
            </div>
          )}
        </div>

        {/* Edit Modal */}
        {showEditModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
              <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
                고객 정보 수정
              </h3>
              <form onSubmit={handleSaveEdit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    이름
                  </label>
                  <input
                    type="text"
                    value={editData.name || ''}
                    onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    출생 연도
                  </label>
                  <input
                    type="number"
                    min={1900}
                    max={new Date().getFullYear()}
                    value={editData.birth_year || ''}
                    onChange={(e) => setEditData({ ...editData, birth_year: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    성별
                  </label>
                  <select
                    value={editData.gender || 'M'}
                    onChange={(e) => setEditData({ ...editData, gender: e.target.value as Gender })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  >
                    <option value="M">남성</option>
                    <option value="F">여성</option>
                    <option value="O">기타</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    연락처
                  </label>
                  <input
                    type="text"
                    value={editData.phone || ''}
                    onChange={(e) => setEditData({ ...editData, phone: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    이메일
                  </label>
                  <input
                    type="email"
                    value={editData.email || ''}
                    onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    직업
                  </label>
                  <input
                    type="text"
                    value={editData.occupation || ''}
                    onChange={(e) => setEditData({ ...editData, occupation: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                    메모
                  </label>
                  <textarea
                    value={editData.notes || ''}
                    onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white"
                  />
                </div>

                <div className="flex gap-2 pt-4">
                  <button
                    type="button"
                    onClick={() => setShowEditModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700"
                  >
                    취소
                  </button>
                  <button
                    type="submit"
                    className="flex-1 btn-primary"
                  >
                    저장
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  )
}
