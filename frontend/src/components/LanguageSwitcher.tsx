'use client'

import { useLocale, useTranslations } from 'next-intl'
import { useRouter, usePathname } from 'next/navigation'
import { Menu, Transition } from '@headlessui/react'
import { Fragment } from 'react'
import { LanguageIcon } from '@heroicons/react/24/outline'

const languages = [
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
]

export function LanguageSwitcher() {
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()
  const t = useTranslations('language')

  const switchLanguage = (newLocale: string) => {
    // 현재 경로에서 locale 변경
    // pathname이 /ko/dashboard이면 /en/dashboard로 변경
    const segments = pathname.split('/')
    segments[1] = newLocale
    const newPath = segments.join('/')
    router.push(newPath)
  }

  const currentLanguage = languages.find((lang) => lang.code === locale)

  return (
    <Menu as="div" className="relative">
      <Menu.Button
        className="flex items-center gap-2 p-2 rounded-lg bg-gray-100 dark:bg-dark-elevated hover:bg-gray-200 dark:hover:bg-dark-hover transition-colors"
        aria-label="Change language"
      >
        <LanguageIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" aria-hidden="true" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {currentLanguage?.flag}
        </span>
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
        <Menu.Items className="absolute right-0 mt-2 w-48 origin-top-right rounded-lg bg-white dark:bg-dark-surface shadow-lg ring-1 ring-black ring-opacity-5 dark:ring-dark-border focus:outline-none z-50">
          <div className="p-1">
            {languages.map((language) => {
              const isActive = locale === language.code

              return (
                <Menu.Item key={language.code}>
                  {({ active }) => (
                    <button
                      onClick={() => switchLanguage(language.code)}
                      className={`
                        ${active ? 'bg-gray-100 dark:bg-dark-hover' : ''}
                        ${isActive ? 'bg-primary-50 dark:bg-primary-900/20' : ''}
                        group flex w-full items-center rounded-md px-3 py-2 text-sm
                        transition-colors
                      `}
                      aria-label={`Switch to ${language.name}`}
                      aria-current={isActive ? 'true' : 'false'}
                    >
                      <span className="mr-3 text-xl" aria-hidden="true">
                        {language.flag}
                      </span>
                      <span
                        className={`
                          ${
                            isActive
                              ? 'text-primary-600 dark:text-primary-400 font-medium'
                              : 'text-gray-900 dark:text-gray-100'
                          }
                        `}
                      >
                        {language.name}
                      </span>
                      {isActive && (
                        <svg
                          className="ml-auto h-5 w-5 text-primary-600 dark:text-primary-400"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                          aria-hidden="true"
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
