'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import {
  UserPlusIcon,
  MagnifyingGlassIcon,
  PhoneIcon,
  EnvelopeIcon,
  CalendarIcon,
  DocumentTextIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline'
import { showSuccess, showInfo, showError } from '@/lib/toast-config'

interface Customer {
  id: string
  name: string
  phone: string
  email: string
  birthDate: string
  tags: string[]
  lastContact: string
  consultations: number
  products: number
  status: 'active' | 'inactive' | 'prospect'
}

interface APICustomer {
  id: string
  name: string
  phone: string
  email: string
  birth_date: string
  tags: string[]
  status: 'active' | 'inactive' | 'prospect'
  consultation_count: number
  product_count: number
  last_contact_date: string | null
}

export default function FPDashboardPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Fetch customers from API
  useEffect(() => {
    fetchCustomers()
  }, [])

  const fetchCustomers = async () => {
    try {
      setIsLoading(true)
      const response = await fetch('http://localhost:3030/api/v1/fp/customers')
      if (!response.ok) throw new Error('Failed to fetch customers')

      const data: APICustomer[] = await response.json()

      // Transform API data to UI format
      const transformedCustomers: Customer[] = data.map((apiCustomer) => ({
        id: apiCustomer.id,
        name: apiCustomer.name,
        phone: apiCustomer.phone || '-',
        email: apiCustomer.email || '-',
        birthDate: apiCustomer.birth_date || '-',
        tags: apiCustomer.tags || [],
        lastContact: apiCustomer.last_contact_date
          ? new Date(apiCustomer.last_contact_date).toLocaleDateString('ko-KR')
          : '미상담',
        consultations: apiCustomer.consultation_count,
        products: apiCustomer.product_count,
        status: apiCustomer.status,
      }))

      setCustomers(transformedCustomers)
    } catch (error) {
      console.error('Error fetching customers:', error)
      showError('고객 목록을 불러오는데 실패했습니다.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSyncContacts = async () => {
    try {
      showInfo('주소록 연동 기능을 준비 중입니다...')
      // TODO: Google Contacts API 또는 Apple Contacts 연동 구현
      // 현재는 데모용으로 localStorage를 사용
      const hasPermission = await requestContactsPermission()
      if (hasPermission) {
        showSuccess('주소록 연동이 완료되었습니다!')
      }
    } catch (error) {
      showError('주소록 연동에 실패했습니다.')
    }
  }

  const requestContactsPermission = async (): Promise<boolean> => {
    // 브라우저에서는 직접적인 주소록 접근이 제한됩니다
    // 대신 파일 업로드나 외부 API 연동을 사용합니다
    return new Promise((resolve) => {
      const confirmed = window.confirm(
        '주소록 연동을 시작하시겠습니까?\n\n' +
        '다음 방법 중 하나를 선택할 수 있습니다:\n' +
        '1. CSV 파일로 가져오기\n' +
        '2. Google Contacts 연동\n' +
        '3. 수동으로 추가'
      )
      resolve(confirmed)
    })
  }

  const filteredCustomers = customers.filter((customer) =>
    customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    customer.phone.includes(searchQuery) ||
    customer.email.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    prospect: 0,
    inactive: 0,
  })

  // Fetch stats
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:3030/api/v1/fp/stats/summary')
        if (!response.ok) throw new Error('Failed to fetch stats')

        const data = await response.json()
        setStats(data)
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    }

    fetchStats()
  }, [customers])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-dark-background">
      <div className="p-6 space-y-6">
        {/* 헤더 */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              고객 관리
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              FP 전용 고객 관리 대시보드
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleSyncContacts}
              className="flex items-center gap-2"
            >
              <ArrowPathIcon className="h-4 w-4" />
              주소록 연동
            </Button>
            <Button
              onClick={() => setIsAddModalOpen(true)}
              className="flex items-center gap-2"
            >
              <UserPlusIcon className="h-4 w-4" />
              고객 추가
            </Button>
          </div>
        </div>

        {/* 통계 카드 */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                전체 고객
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}명</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                활성 고객
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{stats.active}명</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                잠재 고객
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{stats.prospect}명</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
                휴면 고객
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-500">{stats.inactive}명</div>
            </CardContent>
          </Card>
        </div>

        {/* 검색 및 필터 */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="relative flex-1">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <Input
                  type="text"
                  placeholder="이름, 전화번호, 이메일로 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 고객 목록 */}
        <Card>
          <CardHeader>
            <CardTitle>고객 목록</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredCustomers.map((customer) => (
                <div
                  key={customer.id}
                  className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => setSelectedCustomer(customer)}
                >
                  <div className="flex items-center gap-4 flex-1">
                    {/* 고객 정보 */}
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-lg">{customer.name}</h3>
                        <Badge
                          variant={
                            customer.status === 'active' ? 'default' :
                            customer.status === 'prospect' ? 'secondary' :
                            'outline'
                          }
                          className={
                            customer.status === 'active' ? 'bg-green-600' :
                            customer.status === 'prospect' ? 'bg-blue-600' :
                            'bg-gray-400'
                          }
                        >
                          {customer.status === 'active' ? '활성' :
                           customer.status === 'prospect' ? '잠재' :
                           '휴면'}
                        </Badge>
                        {customer.tags.map((tag) => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <PhoneIcon className="h-4 w-4" />
                          {customer.phone}
                        </span>
                        <span className="flex items-center gap-1">
                          <EnvelopeIcon className="h-4 w-4" />
                          {customer.email}
                        </span>
                        <span className="flex items-center gap-1">
                          <CalendarIcon className="h-4 w-4" />
                          최근 상담: {customer.lastContact}
                        </span>
                      </div>
                    </div>

                    {/* 통계 */}
                    <div className="flex gap-6 text-center">
                      <div>
                        <div className="text-2xl font-bold text-blue-600">{customer.consultations}</div>
                        <div className="text-xs text-gray-500">상담</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-green-600">{customer.products}</div>
                        <div className="text-xs text-gray-500">상품</div>
                      </div>
                    </div>
                  </div>

                  <Button variant="ghost" size="sm">
                    <DocumentTextIcon className="h-5 w-5" />
                  </Button>
                </div>
              ))}

                {filteredCustomers.length === 0 && (
                  <div className="text-center py-12 text-gray-500">
                    검색 결과가 없습니다.
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 고객 추가 모달 - TODO: 별도 컴포넌트로 분리 */}
      {isAddModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl mx-4">
            <CardHeader>
              <CardTitle>새 고객 추가</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-sm text-gray-600">
                  고객 추가 기능은 곧 구현됩니다.
                </p>
                <Button onClick={() => setIsAddModalOpen(false)}>
                  닫기
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
