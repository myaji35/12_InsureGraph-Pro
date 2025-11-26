'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import DashboardLayout from '@/components/DashboardLayout'
import { useCustomerStore } from '@/store/customer-store'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  UserIcon,
  PhoneIcon,
  EnvelopeIcon,
} from '@heroicons/react/24/outline'
import { formatDate } from '@/lib/utils'

export default function CustomersPage() {
  const router = useRouter()
  const { customers, pagination, isLoading, fetchCustomers } = useCustomerStore()

  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [showAddModal, setShowAddModal] = useState(false)

  useEffect(() => {
    loadCustomers()
  }, [currentPage])

  const loadCustomers = async () => {
    try {
      await fetchCustomers({
        search: searchQuery || undefined,
        page: currentPage,
        page_size: 12,
      })
    } catch (error) {
      console.error('Failed to load customers:', error)
    }
  }

  const handleSearch = () => {
    setCurrentPage(1)
    loadCustomers()
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
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${colors[riskProfile]}`}>
        {labels[riskProfile]}
      </span>
    )
  }

  return (
    <DashboardLayout>
      <div className="mb-8">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">고객 관리</h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400">고객 정보 및 포트폴리오를 관리하세요</p>
          </div>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center gap-2"
          >
            <PlusIcon className="w-5 h-5" />
            고객 추가
          </button>
        </div>
      </div>

      {/* Search */}
      <div className="card mb-6">
        <div className="flex gap-4">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="이름, 이메일, 전화번호로 검색..."
              className="input-field pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <button onClick={handleSearch} className="btn-primary">
            검색
          </button>
        </div>
      </div>

      {/* Customers Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
            <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
          </div>
        </div>
      ) : customers.length === 0 ? (
        <div className="card text-center py-12">
          <UserIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">고객이 없습니다</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">새로운 고객을 추가하여 시작하세요</p>
          <button onClick={() => setShowAddModal(true)} className="btn-primary">
            고객 추가
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {customers.map((customer) => (
              <div
                key={customer.customer_id}
                className="card hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => router.push(`/customers/${customer.customer_id}`)}
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center">
                      <UserIcon className="w-6 h-6 text-primary-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-gray-100">{customer.name}</h3>
                      {getRiskBadge(customer.risk_profile)}
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  {customer.email && (
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <EnvelopeIcon className="w-4 h-4" />
                      <span className="truncate">{customer.email}</span>
                    </div>
                  )}
                  {customer.phone && (
                    <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <PhoneIcon className="w-4 h-4" />
                      <span>{customer.phone}</span>
                    </div>
                  )}
                  {customer.occupation && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium">직업:</span> {customer.occupation}
                    </div>
                  )}
                  {customer.birth_date && (
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      <span className="font-medium">생년월일:</span>{' '}
                      {formatDate(customer.birth_date)}
                    </div>
                  )}
                </div>

                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-dark-border">
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    등록일: {formatDate(customer.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-600 dark:text-gray-400">
                총 {pagination.total_items}명의 고객
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(currentPage - 1)}
                  disabled={!pagination.has_prev}
                  className="px-4 py-2 border border-gray-300 dark:border-dark-border rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-surface hover:bg-gray-50 dark:hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  이전
                </button>
                <span className="px-4 py-2 text-sm text-gray-700 dark:text-gray-300">
                  {currentPage} / {pagination.total_pages}
                </span>
                <button
                  onClick={() => setCurrentPage(currentPage + 1)}
                  disabled={!pagination.has_next}
                  className="px-4 py-2 border border-gray-300 dark:border-dark-border rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-dark-surface hover:bg-gray-50 dark:hover:bg-dark-hover disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  다음
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Add Customer Modal - Placeholder */}
      {showAddModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-dark-surface rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">고객 추가</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              이 기능은 백엔드 API 연동 후 활성화됩니다.
            </p>
            <button onClick={() => setShowAddModal(false)} className="btn-primary w-full">
              닫기
            </button>
          </div>
        </div>
      )}
    </DashboardLayout>
  )
}
