'use client'

import { useState } from 'react'
import { useUser } from '@clerk/nextjs'
import Sidebar from './Sidebar'
import Header from './Header'
import { SkipToContent } from './SkipToContent'

interface DashboardLayoutProps {
  children: React.ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const { user, isLoaded } = useUser()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Clerk의 미들웨어가 인증을 처리하므로 여기서는 로딩 상태만 체크
  if (!isLoaded) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 dark:border-primary-400 mx-auto"></div>
          <p className="mt-4 text-gray-600 dark:text-gray-400">로딩 중...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Skip to Content Link for Accessibility */}
      <SkipToContent />

      <div className="flex h-screen bg-gray-50 dark:bg-dark-bg">
        {/* Sidebar */}
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Header */}
          <Header onMenuClick={() => setSidebarOpen(true)} />

          {/* Page content */}
          <main id="main-content" className="flex-1 overflow-y-auto" tabIndex={-1}>
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </>
  )
}
