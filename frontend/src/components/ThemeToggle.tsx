'use client'

import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'
import { SunIcon, MoonIcon, ComputerDesktopIcon } from '@heroicons/react/24/outline'
import { Menu, Transition } from '@headlessui/react'
import { Fragment } from 'react'

export function ThemeToggle() {
  const [mounted, setMounted] = useState(false)
  const { theme, setTheme, systemTheme } = useTheme()

  // 하이드레이션 불일치 방지
  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return (
      <div className="w-9 h-9 rounded-lg bg-gray-100 dark:bg-dark-elevated animate-pulse" />
    )
  }

  const currentTheme = theme === 'system' ? systemTheme : theme

  const themes = [
    {
      name: '라이트',
      value: 'light',
      icon: SunIcon,
      description: '밝은 테마',
    },
    {
      name: '다크',
      value: 'dark',
      icon: MoonIcon,
      description: '어두운 테마',
    },
    {
      name: '시스템',
      value: 'system',
      icon: ComputerDesktopIcon,
      description: '시스템 설정 따라가기',
    },
  ]

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="p-2 rounded-lg bg-gray-100 dark:bg-dark-elevated hover:bg-gray-200 dark:hover:bg-dark-hover transition-colors">
        {currentTheme === 'dark' ? (
          <MoonIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        ) : (
          <SunIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
        )}
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
        <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-lg bg-white dark:bg-dark-surface shadow-lg ring-1 ring-black ring-opacity-5 dark:ring-white dark:ring-opacity-10 focus:outline-none z-10">
          <div className="p-1">
            {themes.map((item) => {
              const Icon = item.icon
              const isActive = theme === item.value

              return (
                <Menu.Item key={item.value}>
                  {({ active }) => (
                    <button
                      onClick={() => setTheme(item.value)}
                      className={`
                        ${active ? 'bg-gray-100 dark:bg-dark-hover' : ''}
                        ${isActive ? 'bg-primary-50 dark:bg-primary-900/20' : ''}
                        group flex w-full items-center rounded-md px-3 py-2 text-sm
                        transition-colors
                      `}
                    >
                      <Icon
                        className={`
                          mr-3 h-5 w-5
                          ${isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500'}
                        `}
                        aria-hidden="true"
                      />
                      <div className="flex-1 text-left">
                        <p className={`
                          font-medium
                          ${isActive ? 'text-primary-600 dark:text-primary-400' : 'text-gray-900 dark:text-gray-100'}
                        `}>
                          {item.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {item.description}
                        </p>
                      </div>
                      {isActive && (
                        <svg
                          className="h-5 w-5 text-primary-600 dark:text-primary-400"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </button>
                  )}
                </Menu.Item>
              )
            })}
          </div>
        </Menu.Items>
      </Transition>
    </Menu>
  )
}
