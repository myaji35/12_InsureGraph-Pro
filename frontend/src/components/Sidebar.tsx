'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import {
  HomeIcon,
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  UsersIcon,
  Cog6ToothIcon,
  CircleStackIcon,
  BuildingOfficeIcon,
} from '@heroicons/react/24/outline'

interface NavItem {
  key: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()

  const navigation: NavItem[] = [
    { key: 'dashboard', href: `/dashboard`, icon: HomeIcon },
    { key: 'documents', href: `/documents`, icon: DocumentTextIcon },
    { key: 'companies', href: `/companies`, icon: BuildingOfficeIcon },
    { key: 'query', href: `/query`, icon: ChatBubbleLeftRightIcon },
    { key: 'graph', href: `/graph`, icon: CircleStackIcon },
    { key: 'customers', href: `/customers`, icon: UsersIcon },
    { key: 'settings', href: `/settings`, icon: Cog6ToothIcon },
  ]

  const labels: Record<string, string> = {
    dashboard: '대시보드',
    documents: '문서 관리',
    companies: '보험사 관리',
    query: '질의응답',
    graph: '그래프',
    customers: '고객 관리',
    settings: '설정',
  }

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-gray-600 bg-opacity-75 dark:bg-black dark:bg-opacity-75 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-30 w-64 bg-white dark:bg-dark-surface border-r border-gray-200 dark:border-dark-border
          transform transition-transform duration-300 ease-in-out
          lg:translate-x-0 lg:static lg:z-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200 dark:border-dark-border">
            <Link href={`/dashboard`} className="flex items-center">
              <span className="text-xl font-bold text-primary-600 dark:text-primary-400">
                InsureGraph Pro
              </span>
            </Link>
            <button
              onClick={onClose}
              className="lg:hidden text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/')
              const Icon = item.icon

              return (
                <Link
                  key={item.key}
                  href={item.href}
                  prefetch={true}
                  className={`
                    flex items-center px-4 py-3 text-sm font-medium rounded-lg
                    transition-colors duration-150
                    ${
                      isActive
                        ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-700 dark:text-primary-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-dark-hover hover:text-gray-900 dark:hover:text-gray-100'
                    }
                  `}
                  onMouseEnter={() => {
                    // Prefetch on hover for instant navigation
                    router.prefetch(item.href)
                  }}
                  onClick={() => {
                    // Close sidebar on mobile after navigation
                    if (window.innerWidth < 1024) {
                      onClose()
                    }
                  }}
                >
                  <Icon className="w-5 h-5 mr-3" />
                  <span>{labels[item.key]}</span>
                  {item.badge && (
                    <span className="ml-auto px-2 py-1 text-xs font-medium bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400 rounded-full">
                      {item.badge}
                    </span>
                  )}
                </Link>
              )
            })}
          </nav>

          {/* Footer */}
          <div className="p-4 border-t border-gray-200 dark:border-dark-border">
            <div className="flex items-center px-4 py-3 text-xs text-gray-500 dark:text-gray-400">
              <span>© 2025 InsureGraph Pro</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
