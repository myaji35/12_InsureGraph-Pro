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

  // Clerk 로딩 중에도 레이아웃을 표시하여 더 빠른 체감 속도 제공
  // 미들웨어가 인증을 처리하므로 안전함

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
            <div className="px-[10px] py-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </>
  )
}
