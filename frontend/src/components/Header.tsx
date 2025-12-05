'use client'

import { Fragment } from 'react'
import { useRouter } from 'next/navigation'
import { Menu, Transition } from '@headlessui/react'
import {
  Bars3Icon,
  UserCircleIcon,
  Cog6ToothIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline'
import { useUser, useClerk } from '@clerk/nextjs'
import { ThemeToggle } from './ThemeToggle'
// import NotificationBell from './NotificationBell' // Temporarily disabled

interface HeaderProps {
  onMenuClick: () => void
}

export default function Header({ onMenuClick }: HeaderProps) {
  const router = useRouter()
  const { user } = useUser()
  const { signOut } = useClerk()

  const handleLogout = async () => {
    await signOut()
    router.push('/')
  }

  return (
    <header className="sticky top-0 z-10 bg-white dark:bg-dark-surface border-b border-gray-200 dark:border-dark-border">
      <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
        {/* Left side - Mobile menu button */}
        <div className="flex items-center">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-hover"
          >
            <Bars3Icon className="w-6 h-6" />
          </button>

          {/* Page title - hidden on mobile */}
          <h1 className="hidden sm:block ml-4 text-xl font-semibold text-gray-900 dark:text-gray-100">
            {/* Will be dynamic based on page */}
          </h1>
        </div>

        {/* Right side - Theme, Language, Notifications & User menu */}
        <div className="flex items-center gap-4">
          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Notifications - Task D */}
          {/* <NotificationBell /> */}

          {/* User menu */}
          <Menu as="div" className="relative">
            <Menu.Button className="flex items-center gap-2 p-2 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-dark-hover">
              <UserCircleIcon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
              <div className="hidden md:block text-left">
                <div className="text-sm font-medium">{user?.firstName || user?.emailAddresses[0]?.emailAddress}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400">사용자</div>
              </div>
            </Menu.Button>

            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right bg-white dark:bg-dark-surface rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 dark:ring-white dark:ring-opacity-10 focus:outline-none">
                <div className="p-4 border-b border-gray-100 dark:border-dark-border">
                  <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {user?.firstName || '사용자'}
                  </div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {user?.emailAddresses[0]?.emailAddress}
                  </div>
                </div>

                <div className="py-1">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={() => router.push('/profile')}
                        className={`
                          ${active ? 'bg-gray-50 dark:bg-dark-hover' : ''}
                          flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300
                        `}
                      >
                        <UserCircleIcon className="w-5 h-5 mr-3 text-gray-400 dark:text-gray-500" />
                        프로필
                      </button>
                    )}
                  </Menu.Item>

                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={() => router.push('/settings')}
                        className={`
                          ${active ? 'bg-gray-50 dark:bg-dark-hover' : ''}
                          flex items-center w-full px-4 py-2 text-sm text-gray-700 dark:text-gray-300
                        `}
                      >
                        <Cog6ToothIcon className="w-5 h-5 mr-3 text-gray-400 dark:text-gray-500" />
                        설정
                      </button>
                    )}
                  </Menu.Item>
                </div>

                <div className="py-1 border-t border-gray-100 dark:border-dark-border">
                  <Menu.Item>
                    {({ active }) => (
                      <button
                        onClick={handleLogout}
                        className={`
                          ${active ? 'bg-gray-50 dark:bg-dark-hover' : ''}
                          flex items-center w-full px-4 py-2 text-sm text-red-600 dark:text-red-400
                        `}
                      >
                        <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
                        로그아웃
                      </button>
                    )}
                  </Menu.Item>
                </div>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </header>
  )
}
