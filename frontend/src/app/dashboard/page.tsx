'use client'

import Link from 'next/link'
import { useUser } from '@clerk/nextjs'
import DashboardLayout from '@/components/DashboardLayout'
import {
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  UsersIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

export default function DashboardPage() {
  const { user } = useUser()

  return (
    <DashboardLayout>
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
          대시보드
        </h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          안녕하세요, {user?.firstName || user?.emailAddresses[0]?.emailAddress}님!
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">총 문서</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">24</p>
            </div>
            <DocumentTextIcon className="w-12 h-12 text-primary-500" />
          </div>
          <div className="mt-4">
            <span className="text-xs text-green-600">+12% from last month</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">질의응답</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">156</p>
            </div>
            <ChatBubbleLeftRightIcon className="w-12 h-12 text-blue-500" />
          </div>
          <div className="mt-4">
            <span className="text-xs text-green-600">+23% from last month</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">고객 수</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">48</p>
            </div>
            <UsersIcon className="w-12 h-12 text-purple-500" />
          </div>
          <div className="mt-4">
            <span className="text-xs text-green-600">+8% from last month</span>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">분석 완료</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">89%</p>
            </div>
            <ChartBarIcon className="w-12 h-12 text-green-500" />
          </div>
          <div className="mt-4">
            <span className="text-xs text-green-600">+5% from last month</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Link href="/documents/upload">
          <div className="card hover:shadow-lg transition-shadow cursor-pointer">
            <DocumentTextIcon className="w-10 h-10 text-primary-600 mb-4" />
            <h3 className="text-lg font-semibold mb-2">문서 업로드</h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">새로운 약관 문서를 업로드하고 분석하세요</p>
          </div>
        </Link>

        <Link href="/query">
          <div className="card hover:shadow-lg transition-shadow cursor-pointer">
            <ChatBubbleLeftRightIcon className="w-10 h-10 text-blue-600 mb-4" />
            <h3 className="text-lg font-semibold mb-2">질의응답</h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">약관에 대해 질문하고 답변을 받으세요</p>
          </div>
        </Link>

        <Link href="/customers">
          <div className="card hover:shadow-lg transition-shadow cursor-pointer">
            <UsersIcon className="w-10 h-10 text-purple-600 mb-4" />
            <h3 className="text-lg font-semibold mb-2">고객 관리</h3>
            <p className="text-gray-600 dark:text-gray-400 text-sm">고객 포트폴리오를 분석하세요</p>
          </div>
        </Link>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">최근 활동</h3>
        <div className="space-y-4">
          <div className="flex items-start gap-4 pb-4 border-b border-gray-100 dark:border-dark-border">
            <div className="w-2 h-2 rounded-full bg-primary-500 mt-2" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">삼성화재 암보험 약관 업로드 완료</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">2시간 전</p>
            </div>
          </div>
          <div className="flex items-start gap-4 pb-4 border-b border-gray-100 dark:border-dark-border">
            <div className="w-2 h-2 rounded-full bg-blue-500 mt-2" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">고객 김철수님 포트폴리오 분석 완료</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">5시간 전</p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-2 h-2 rounded-full bg-green-500 mt-2" />
            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">현대해상 실손보험 약관 질의 15건 처리</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">1일 전</p>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
