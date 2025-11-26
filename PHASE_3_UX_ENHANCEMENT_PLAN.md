# Phase 3: UX 고도화 상세 실행 계획

## 개요

**목표**: 사용자 경험을 프로덕션 수준으로 고도화
**총 Story Points**: 15 pts
**예상 기간**: 2주 (Sprint 6-7)
**의존성**: Phase 1 (백엔드 통합) 완료 권장

---

## Story 3.1: 다크 모드 구현 (3 pts)

### 목표
시스템 설정을 감지하고 사용자 선택을 저장하는 완전한 다크 모드 지원

### 작업 내용

#### 1단계: 라이브러리 설치 및 설정
```bash
npm install next-themes
```

#### 2단계: ThemeProvider 설정

**`src/providers/theme-provider.tsx`** (새 파일)
```typescript
'use client'

import { ThemeProvider as NextThemesProvider } from 'next-themes'
import { type ThemeProviderProps } from 'next-themes/dist/types'

export function ThemeProvider({ children, ...props }: ThemeProviderProps) {
  return <NextThemesProvider {...props}>{children}</NextThemesProvider>
}
```

**`src/app/layout.tsx`** (업데이트)
```typescript
import { ThemeProvider } from '@/providers/theme-provider'

export default function RootLayout({ children }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

#### 3단계: Tailwind 다크 모드 설정

**`tailwind.config.ts`** (업데이트)
```typescript
import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class', // 클래스 기반 다크 모드
  theme: {
    extend: {
      colors: {
        // 다크 모드 전용 색상
        dark: {
          bg: '#0a0a0a',
          surface: '#1a1a1a',
          elevated: '#2a2a2a',
          border: '#333333',
          hover: '#404040',
        },
        // 기존 primary 색상에 다크 모드 variant 추가
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          // ... (기존 색상)
          900: '#1e3a8a',
          950: '#172554', // 다크 모드용
        },
      },
    },
  },
}

export default config
```

#### 4단계: 다크 모드 토글 컴포넌트

**`src/components/ThemeToggle.tsx`** (새 파일, 120 lines)
```typescript
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
        <Menu.Items className="absolute right-0 mt-2 w-56 origin-top-right rounded-lg bg-white dark:bg-dark-surface shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
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
```

#### 5단계: Header에 토글 추가

**`src/components/Header.tsx`** (업데이트)
```typescript
import { ThemeToggle } from './ThemeToggle'

// ... 기존 코드

<div className="flex items-center gap-4">
  <ThemeToggle /> {/* 추가 */}
  <button className="relative p-2">
    <BellIcon className="w-6 h-6 text-gray-600 dark:text-gray-300" />
    {/* ... */}
  </button>
  {/* ... */}
</div>
```

#### 6단계: 모든 컴포넌트에 다크 모드 클래스 추가

**패턴**:
```typescript
// Before
<div className="bg-white text-gray-900 border-gray-200">

// After
<div className="bg-white dark:bg-dark-surface text-gray-900 dark:text-gray-100 border-gray-200 dark:border-dark-border">
```

**업데이트 대상 컴포넌트 (40개 파일)**:
- [ ] `src/components/Sidebar.tsx`
- [ ] `src/components/Header.tsx`
- [ ] `src/components/DashboardLayout.tsx`
- [ ] `src/app/dashboard/page.tsx`
- [ ] `src/app/documents/page.tsx`
- [ ] `src/app/documents/[id]/page.tsx`
- [ ] `src/app/documents/upload/page.tsx`
- [ ] `src/app/query/page.tsx`
- [ ] `src/app/graph/page.tsx`
- [ ] `src/app/customers/page.tsx`
- [ ] `src/app/customers/[id]/page.tsx`
- [ ] `src/components/FileUpload.tsx`
- [ ] `src/components/DocumentSelector.tsx`
- [ ] `src/components/AnswerDisplay.tsx`
- [ ] `src/components/QueryHistory.tsx`
- [ ] `src/components/GraphVisualization.tsx`
- [ ] `src/components/NodeDetail.tsx`
- [ ] `src/components/GraphControls.tsx`
- [ ] `src/styles/globals.css`

**globals.css 다크 모드 스타일 추가**:
```css
/* 다크 모드 스크롤바 */
@layer utilities {
  .dark {
    color-scheme: dark;
  }

  .dark ::-webkit-scrollbar {
    width: 12px;
  }

  .dark ::-webkit-scrollbar-track {
    background: theme('colors.dark.surface');
  }

  .dark ::-webkit-scrollbar-thumb {
    background: theme('colors.dark.border');
    border-radius: 6px;
  }

  .dark ::-webkit-scrollbar-thumb:hover {
    background: theme('colors.dark.hover');
  }
}

/* 다크 모드 prose (마크다운) */
.dark .prose {
  --tw-prose-body: theme('colors.gray.300');
  --tw-prose-headings: theme('colors.gray.100');
  --tw-prose-links: theme('colors.primary.400');
  --tw-prose-bold: theme('colors.gray.100');
  --tw-prose-code: theme('colors.pink.400');
  --tw-prose-pre-bg: theme('colors.dark.elevated');
  --tw-prose-pre-code: theme('colors.gray.300');
  --tw-prose-quotes: theme('colors.gray.400');
  --tw-prose-quote-borders: theme('colors.dark.border');
}
```

#### 7단계: 테스트 체크리스트

- [ ] 라이트 모드에서 모든 페이지 확인
- [ ] 다크 모드에서 모든 페이지 확인
- [ ] 시스템 테마 변경 시 자동 전환 확인
- [ ] 페이지 새로고침 시 테마 유지 확인
- [ ] 색상 대비 검증 (WebAIM Contrast Checker)
- [ ] 모든 아이콘이 다크 모드에서 보이는지 확인
- [ ] 그래프 시각화 다크 모드 호환성

### 예상 산출물
- 3개 새 파일 (ThemeProvider, ThemeToggle)
- 40개 파일 업데이트 (dark: 클래스 추가)
- ~500 lines 추가

### Acceptance Criteria
- ✅ 라이트/다크/시스템 3가지 모드 지원
- ✅ 사용자 선택 LocalStorage 저장
- ✅ 모든 페이지 다크 모드 지원
- ✅ 색상 대비 WCAG AA 준수
- ✅ 하이드레이션 불일치 없음

---

## Story 3.2: 국제화 (i18n) 구현 (4 pts)

### 목표
한국어/영어 2개 언어 지원 및 로케일 전환 기능

### 작업 내용

#### 1단계: 라이브러리 설치
```bash
npm install next-intl
```

#### 2단계: Next.js 설정

**`next.config.js`** (업데이트)
```javascript
const createNextIntlPlugin = require('next-intl/plugin')

const withNextIntl = createNextIntlPlugin('./src/i18n.ts')

module.exports = withNextIntl({
  // ... 기존 설정
})
```

#### 3단계: i18n 설정 파일

**`src/i18n.ts`** (새 파일)
```typescript
import { getRequestConfig } from 'next-intl/server'
import { notFound } from 'next/navigation'

export const locales = ['ko', 'en'] as const
export type Locale = (typeof locales)[number]

export default getRequestConfig(async ({ locale }) => {
  if (!locales.includes(locale as Locale)) notFound()

  return {
    messages: (await import(`../locales/${locale}.json`)).default,
  }
})
```

#### 4단계: 번역 파일 생성

**디렉토리 구조**:
```
/locales
  /ko
    common.json      (공통)
    auth.json        (인증)
    documents.json   (문서 관리)
    query.json       (질의응답)
    graph.json       (그래프)
    customers.json   (고객 관리)
  /en
    common.json
    auth.json
    documents.json
    query.json
    graph.json
    customers.json
```

**`locales/ko.json`** (새 파일, ~400 lines)
```json
{
  "common": {
    "appName": "InsureGraph Pro",
    "dashboard": "대시보드",
    "documents": "문서 관리",
    "query": "질의응답",
    "graph": "지식 그래프",
    "customers": "고객 관리",
    "settings": "설정",
    "logout": "로그아웃",
    "loading": "로딩 중...",
    "error": "오류가 발생했습니다",
    "save": "저장",
    "cancel": "취소",
    "delete": "삭제",
    "edit": "수정",
    "search": "검색",
    "filter": "필터",
    "date": "날짜",
    "status": "상태",
    "actions": "작업"
  },
  "auth": {
    "login": "로그인",
    "register": "회원가입",
    "email": "이메일",
    "password": "비밀번호",
    "confirmPassword": "비밀번호 확인",
    "username": "사용자명",
    "fullName": "전체 이름",
    "organization": "조직",
    "loginButton": "로그인",
    "registerButton": "회원가입",
    "alreadyHaveAccount": "이미 계정이 있으신가요?",
    "dontHaveAccount": "계정이 없으신가요?",
    "loginSuccess": "로그인 성공!",
    "registerSuccess": "회원가입이 완료되었습니다",
    "invalidCredentials": "이메일 또는 비밀번호가 올바르지 않습니다",
    "passwordMismatch": "비밀번호가 일치하지 않습니다",
    "passwordMinLength": "비밀번호는 최소 8자 이상이어야 합니다"
  },
  "documents": {
    "title": "문서 관리",
    "subtitle": "보험 상품 문서를 업로드하고 관리하세요",
    "uploadDocument": "문서 업로드",
    "uploadTitle": "새 문서 업로드",
    "dragAndDrop": "파일을 드래그하거나 클릭하여 선택하세요",
    "supportedFormats": "지원 형식: PDF (최대 10MB)",
    "insurer": "보험사",
    "productName": "상품명",
    "productType": "상품 유형",
    "effectiveDate": "시행일",
    "version": "버전",
    "tags": "태그",
    "description": "설명",
    "status": {
      "pending": "대기 중",
      "processing": "처리 중",
      "ready": "준비됨",
      "failed": "실패"
    },
    "deleteConfirm": "이 문서를 삭제하시겠습니까?",
    "deleteSuccess": "문서가 삭제되었습니다",
    "uploadSuccess": "문서가 업로드되었습니다",
    "noDocuments": "문서가 없습니다",
    "searchPlaceholder": "문서 검색..."
  },
  "query": {
    "title": "질의응답",
    "subtitle": "AI에게 보험 관련 질문을 하세요",
    "askQuestion": "질문하기",
    "questionPlaceholder": "질문을 입력하세요...",
    "selectDocuments": "문서 선택",
    "answer": "답변",
    "confidence": "신뢰도",
    "citations": "인용",
    "processingTime": "처리 시간",
    "history": "질의 내역",
    "exampleQuestions": "예시 질문",
    "noAnswer": "답변이 없습니다",
    "noHistory": "질의 내역이 없습니다"
  },
  "graph": {
    "title": "지식 그래프",
    "subtitle": "보험 지식을 시각화하여 탐색하세요",
    "filters": "필터",
    "nodeTypes": "노드 유형",
    "documents": "문서",
    "entities": "엔티티",
    "concepts": "개념",
    "clauses": "조항",
    "search": "노드 검색",
    "nodeDetails": "노드 상세",
    "properties": "속성",
    "relationships": "관계",
    "statistics": "통계"
  },
  "customers": {
    "title": "고객 관리",
    "subtitle": "고객 정보 및 포트폴리오를 관리하세요",
    "addCustomer": "고객 추가",
    "searchPlaceholder": "이름, 이메일, 전화번호로 검색...",
    "basicInfo": "기본 정보",
    "name": "이름",
    "email": "이메일",
    "phone": "전화번호",
    "birthDate": "생년월일",
    "gender": "성별",
    "occupation": "직업",
    "annualIncome": "연 소득",
    "riskProfile": "위험 프로필",
    "notes": "메모",
    "portfolio": "포트폴리오 요약",
    "totalPremium": "총 보험료",
    "totalCoverage": "총 보장액",
    "insurances": "가입 보험",
    "riskAssessment": "위험 평가",
    "recommendations": "추천 상품",
    "noCustomers": "고객이 없습니다",
    "noInsurances": "가입된 보험이 없습니다"
  }
}
```

**`locales/en.json`** (새 파일, ~400 lines)
```json
{
  "common": {
    "appName": "InsureGraph Pro",
    "dashboard": "Dashboard",
    "documents": "Documents",
    "query": "Query",
    "graph": "Knowledge Graph",
    "customers": "Customers",
    "settings": "Settings",
    "logout": "Logout",
    "loading": "Loading...",
    "error": "An error occurred",
    "save": "Save",
    "cancel": "Cancel",
    "delete": "Delete",
    "edit": "Edit",
    "search": "Search",
    "filter": "Filter",
    "date": "Date",
    "status": "Status",
    "actions": "Actions"
  },
  "auth": {
    "login": "Login",
    "register": "Sign Up",
    "email": "Email",
    "password": "Password",
    "confirmPassword": "Confirm Password",
    "username": "Username",
    "fullName": "Full Name",
    "organization": "Organization",
    "loginButton": "Login",
    "registerButton": "Sign Up",
    "alreadyHaveAccount": "Already have an account?",
    "dontHaveAccount": "Don't have an account?",
    "loginSuccess": "Login successful!",
    "registerSuccess": "Registration completed",
    "invalidCredentials": "Invalid email or password",
    "passwordMismatch": "Passwords do not match",
    "passwordMinLength": "Password must be at least 8 characters"
  },
  "documents": {
    "title": "Document Management",
    "subtitle": "Upload and manage insurance product documents",
    "uploadDocument": "Upload Document",
    "uploadTitle": "Upload New Document",
    "dragAndDrop": "Drag and drop or click to select file",
    "supportedFormats": "Supported formats: PDF (max 10MB)",
    "insurer": "Insurer",
    "productName": "Product Name",
    "productType": "Product Type",
    "effectiveDate": "Effective Date",
    "version": "Version",
    "tags": "Tags",
    "description": "Description",
    "status": {
      "pending": "Pending",
      "processing": "Processing",
      "ready": "Ready",
      "failed": "Failed"
    },
    "deleteConfirm": "Are you sure you want to delete this document?",
    "deleteSuccess": "Document deleted",
    "uploadSuccess": "Document uploaded",
    "noDocuments": "No documents",
    "searchPlaceholder": "Search documents..."
  }
  // ... (나머지 섹션 동일한 패턴으로 번역)
}
```

#### 5단계: 언어 전환 컴포넌트

**`src/components/LanguageSwitcher.tsx`** (새 파일, 95 lines)
```typescript
'use client'

import { useLocale } from 'next-intl'
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

  const switchLanguage = (newLocale: string) => {
    // 현재 경로에서 locale 변경
    const newPath = pathname.replace(`/${locale}`, `/${newLocale}`)
    router.push(newPath)
  }

  const currentLanguage = languages.find((lang) => lang.code === locale)

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="flex items-center gap-2 p-2 rounded-lg bg-gray-100 dark:bg-dark-elevated hover:bg-gray-200 dark:hover:bg-dark-hover transition-colors">
        <LanguageIcon className="w-5 h-5 text-gray-700 dark:text-gray-300" />
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
        <Menu.Items className="absolute right-0 mt-2 w-48 origin-top-right rounded-lg bg-white dark:bg-dark-surface shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
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
                    >
                      <span className="mr-3 text-xl">{language.flag}</span>
                      <span
                        className={`
                          ${isActive ? 'text-primary-600 dark:text-primary-400 font-medium' : 'text-gray-900 dark:text-gray-100'}
                        `}
                      >
                        {language.name}
                      </span>
                      {isActive && (
                        <svg
                          className="ml-auto h-5 w-5 text-primary-600 dark:text-primary-400"
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
```

#### 6단계: App Router 구조 변경

**새 구조**:
```
/src/app
  /[locale]          # locale 세그먼트 추가
    /dashboard
    /documents
    /query
    /graph
    /customers
    /login
    /register
    layout.tsx       # locale별 레이아웃
  layout.tsx         # 루트 레이아웃
```

**`src/app/[locale]/layout.tsx`** (새 파일)
```typescript
import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { locales } from '@/i18n'

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }))
}

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode
  params: { locale: string }
}) {
  if (!locales.includes(locale as any)) {
    notFound()
  }

  const messages = await getMessages()

  return (
    <NextIntlClientProvider messages={messages}>
      {children}
    </NextIntlClientProvider>
  )
}
```

#### 7단계: 모든 페이지에 번역 적용

**예시 - `src/app/[locale]/dashboard/page.tsx`** (업데이트)
```typescript
import { useTranslations } from 'next-intl'

export default function DashboardPage() {
  const t = useTranslations('common')
  const tDash = useTranslations('dashboard')

  return (
    <DashboardLayout>
      <h2>{t('dashboard')}</h2>
      <p>{tDash('welcomeMessage')}</p>
      {/* ... */}
    </DashboardLayout>
  )
}
```

#### 8단계: 날짜/통화 포맷팅

**`src/lib/utils.ts`** (업데이트)
```typescript
import { useLocale } from 'next-intl'

export const formatDate = (date: string, locale: string) => {
  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(date))
}

export const formatCurrency = (amount: number, locale: string) => {
  const currency = locale === 'ko' ? 'KRW' : 'USD'
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency,
  }).format(amount)
}
```

### 예상 산출물
- 2개 번역 파일 (ko.json, en.json) - ~800 lines
- 1개 새 컴포넌트 (LanguageSwitcher)
- App Router 구조 변경
- 40개 파일 업데이트 (useTranslations 적용)

### Acceptance Criteria
- ✅ 한국어/영어 완전 번역
- ✅ 언어 전환 버튼
- ✅ 날짜/통화 로케일 처리
- ✅ URL에 locale 반영
- ✅ 브라우저 언어 감지

---

## Story 3.3: 접근성 강화 (3 pts)

### 목표
WCAG 2.1 AAA 레벨 달성

### 작업 내용

#### 1단계: 접근성 도구 설치
```bash
npm install -D @axe-core/react
npm install -D eslint-plugin-jsx-a11y
```

#### 2단계: ESLint 설정

**`.eslintrc.json`** (업데이트)
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:jsx-a11y/recommended"
  ],
  "plugins": ["jsx-a11y"],
  "rules": {
    "jsx-a11y/anchor-is-valid": "error",
    "jsx-a11y/alt-text": "error",
    "jsx-a11y/aria-props": "error",
    "jsx-a11y/aria-proptypes": "error",
    "jsx-a11y/aria-unsupported-elements": "error",
    "jsx-a11y/click-events-have-key-events": "error",
    "jsx-a11y/heading-has-content": "error",
    "jsx-a11y/html-has-lang": "error",
    "jsx-a11y/interactive-supports-focus": "error",
    "jsx-a11y/label-has-associated-control": "error",
    "jsx-a11y/no-noninteractive-element-interactions": "error",
    "jsx-a11y/role-has-required-aria-props": "error"
  }
}
```

#### 3단계: Skip to Content 링크

**`src/components/SkipToContent.tsx`** (새 파일)
```typescript
export function SkipToContent() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary-600 focus:text-white focus:rounded-md"
    >
      본문으로 건너뛰기
    </a>
  )
}
```

#### 4단계: ARIA 라벨 추가

**업데이트 패턴**:
```typescript
// Before
<button onClick={handleDelete}>
  <TrashIcon className="w-5 h-5" />
</button>

// After
<button
  onClick={handleDelete}
  aria-label="문서 삭제"
  title="문서 삭제"
>
  <TrashIcon className="w-5 h-5" aria-hidden="true" />
</button>
```

#### 5단계: 키보드 네비게이션 개선

**Focus Trap 구현 (모달)**:
```bash
npm install focus-trap-react
```

**`src/components/Modal.tsx`** (새 파일)
```typescript
import FocusTrap from 'focus-trap-react'
import { useEffect } from 'react'

export function Modal({ isOpen, onClose, children }) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <FocusTrap>
      <div
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        role="dialog"
        aria-modal="true"
      >
        <div
          className="bg-white dark:bg-dark-surface rounded-lg p-6 max-w-lg w-full"
          role="document"
        >
          {children}
        </div>
      </div>
    </FocusTrap>
  )
}
```

#### 6단계: 색상 대비 검증

**도구**: WebAIM Contrast Checker

**업데이트 대상**:
- [ ] 모든 텍스트 색상 (gray-600 → gray-700)
- [ ] 링크 색상 (대비 4.5:1 이상)
- [ ] 버튼 색상 (대비 3:1 이상)
- [ ] 폼 입력 필드 (테두리 대비)

#### 7단계: Live Region (동적 콘텐츠 알림)

**`src/components/LiveRegion.tsx`** (새 파일)
```typescript
export function LiveRegion({ message, type = 'polite' }: {
  message: string
  type?: 'polite' | 'assertive'
}) {
  return (
    <div
      role="status"
      aria-live={type}
      aria-atomic="true"
      className="sr-only"
    >
      {message}
    </div>
  )
}
```

**사용 예시**:
```typescript
// 문서 업로드 성공 시
{uploadSuccess && (
  <LiveRegion message="문서가 업로드되었습니다" type="polite" />
)}
```

### 예상 산출물
- 4개 새 컴포넌트 (SkipToContent, Modal, LiveRegion)
- 40개 파일 업데이트 (ARIA 라벨, 색상 대비)
- ESLint 규칙 추가

### Acceptance Criteria
- ✅ WCAG 2.1 AAA 준수
- ✅ 키보드로 모든 기능 사용 가능
- ✅ 스크린 리더 호환
- ✅ 색상 대비 7:1 이상 (AAA)
- ✅ Focus visible on all interactive elements

---

## Story 3.4: 고급 UI 컴포넌트 (5 pts)

### 목표
프로덕션급 고급 UI 컴포넌트 구현

### 작업 내용

#### 1단계: 데이터 테이블 (TanStack Table)

```bash
npm install @tanstack/react-table
```

**`src/components/DataTable.tsx`** (새 파일, 250 lines)
```typescript
'use client'

import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  flexRender,
  ColumnDef,
} from '@tanstack/react-table'
import {
  ChevronUpIcon,
  ChevronDownIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline'

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  searchPlaceholder?: string
  onRowClick?: (row: TData) => void
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchPlaceholder = '검색...',
  onRowClick,
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState([])
  const [globalFilter, setGlobalFilter] = React.useState('')

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    onSortingChange: setSorting,
    onGlobalFilterChange: setGlobalFilter,
    state: {
      sorting,
      globalFilter,
    },
  })

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={globalFilter}
          onChange={(e) => setGlobalFilter(e.target.value)}
          placeholder={searchPlaceholder}
          className="input-field pl-10"
        />
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-dark-border">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-dark-elevated">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider"
                  >
                    {header.isPlaceholder ? null : (
                      <div
                        className={
                          header.column.getCanSort()
                            ? 'flex items-center gap-2 cursor-pointer select-none'
                            : ''
                        }
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {header.column.getCanSort() && (
                          <span className="flex flex-col">
                            <ChevronUpIcon
                              className={`w-3 h-3 ${
                                header.column.getIsSorted() === 'asc'
                                  ? 'text-primary-600'
                                  : 'text-gray-300'
                              }`}
                            />
                            <ChevronDownIcon
                              className={`w-3 h-3 -mt-1 ${
                                header.column.getIsSorted() === 'desc'
                                  ? 'text-primary-600'
                                  : 'text-gray-300'
                              }`}
                            />
                          </span>
                        )}
                      </div>
                    )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="bg-white dark:bg-dark-surface divide-y divide-gray-200 dark:divide-dark-border">
            {table.getRowModel().rows.map((row) => (
              <tr
                key={row.id}
                className="hover:bg-gray-50 dark:hover:bg-dark-hover transition-colors cursor-pointer"
                onClick={() => onRowClick?.(row.original)}
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100"
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-700 dark:text-gray-300">
          {table.getFilteredRowModel().rows.length}개 중{' '}
          {table.getState().pagination.pageIndex *
            table.getState().pagination.pageSize +
            1}
          -
          {Math.min(
            (table.getState().pagination.pageIndex + 1) *
              table.getState().pagination.pageSize,
            table.getFilteredRowModel().rows.length
          )}
          개 표시
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="btn-secondary"
          >
            이전
          </button>
          <button
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
            className="btn-secondary"
          >
            다음
          </button>
        </div>
      </div>
    </div>
  )
}
```

**사용 예시 - Documents 페이지 업데이트**:
```typescript
import { DataTable } from '@/components/DataTable'
import { ColumnDef } from '@tanstack/react-table'

const columns: ColumnDef<Document>[] = [
  {
    accessorKey: 'product_name',
    header: '상품명',
  },
  {
    accessorKey: 'insurer',
    header: '보험사',
  },
  {
    accessorKey: 'status',
    header: '상태',
    cell: ({ row }) => <StatusBadge status={row.original.status} />,
  },
  {
    accessorKey: 'created_at',
    header: '등록일',
    cell: ({ row }) => formatDate(row.original.created_at),
  },
]

<DataTable
  columns={columns}
  data={documents}
  onRowClick={(doc) => router.push(`/documents/${doc.document_id}`)}
/>
```

#### 2단계: 고급 차트 (Recharts)

```bash
npm install recharts
```

**`src/components/PremiumChart.tsx`** (새 파일, 140 lines)
```typescript
'use client'

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface PremiumChartProps {
  data: {
    product_type: string
    premium: number
    coverage: number
  }[]
}

export function PremiumChart({ data }: PremiumChartProps) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="product_type" />
        <YAxis />
        <Tooltip
          formatter={(value: number) => formatCurrency(value)}
          contentStyle={{
            backgroundColor: 'var(--tw-color-white)',
            border: '1px solid var(--tw-color-gray-200)',
            borderRadius: '8px',
          }}
        />
        <Legend />
        <Bar dataKey="premium" fill="#3b82f6" name="보험료" />
        <Bar dataKey="coverage" fill="#10b981" name="보장액" />
      </BarChart>
    </ResponsiveContainer>
  )
}
```

#### 3단계: PDF 뷰어

```bash
npm install react-pdf
```

**`src/components/PDFViewer.tsx`** (새 파일, 180 lines)
```typescript
'use client'

import { Document, Page, pdfjs } from 'react-pdf'
import { useState } from 'react'
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MagnifyingGlassPlusIcon,
  MagnifyingGlassMinusIcon,
} from '@heroicons/react/24/outline'

// PDF.js worker 설정
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

interface PDFViewerProps {
  url: string
}

export function PDFViewer({ url }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState<number>(1)
  const [scale, setScale] = useState<number>(1.0)

  function onDocumentLoadSuccess({ numPages }: { numPages: number }) {
    setNumPages(numPages)
  }

  return (
    <div className="flex flex-col items-center gap-4">
      {/* Controls */}
      <div className="flex items-center gap-4 p-4 bg-white dark:bg-dark-surface rounded-lg shadow-sm">
        <button
          onClick={() => setPageNumber(Math.max(1, pageNumber - 1))}
          disabled={pageNumber <= 1}
          className="btn-secondary"
          aria-label="이전 페이지"
        >
          <ChevronLeftIcon className="w-5 h-5" />
        </button>

        <span className="text-sm text-gray-700 dark:text-gray-300">
          {pageNumber} / {numPages}
        </span>

        <button
          onClick={() => setPageNumber(Math.min(numPages, pageNumber + 1))}
          disabled={pageNumber >= numPages}
          className="btn-secondary"
          aria-label="다음 페이지"
        >
          <ChevronRightIcon className="w-5 h-5" />
        </button>

        <div className="w-px h-6 bg-gray-300 dark:bg-dark-border" />

        <button
          onClick={() => setScale(Math.max(0.5, scale - 0.1))}
          className="btn-secondary"
          aria-label="축소"
        >
          <MagnifyingGlassMinusIcon className="w-5 h-5" />
        </button>

        <span className="text-sm text-gray-700 dark:text-gray-300">
          {Math.round(scale * 100)}%
        </span>

        <button
          onClick={() => setScale(Math.min(2.0, scale + 0.1))}
          className="btn-secondary"
          aria-label="확대"
        >
          <MagnifyingGlassPlusIcon className="w-5 h-5" />
        </button>
      </div>

      {/* PDF Document */}
      <div className="border border-gray-200 dark:border-dark-border rounded-lg overflow-hidden">
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          className="flex justify-center"
        >
          <Page pageNumber={pageNumber} scale={scale} />
        </Document>
      </div>
    </div>
  )
}
```

#### 4단계: 무한 스크롤

```bash
npm install react-intersection-observer
```

**`src/components/InfiniteDocumentList.tsx`** (새 파일, 110 lines)
```typescript
'use client'

import { useEffect } from 'react'
import { useInView } from 'react-intersection-observer'
import { useDocumentStore } from '@/store/document-store'

export function InfiniteDocumentList() {
  const { documents, fetchDocuments, pagination, isLoading } = useDocumentStore()
  const { ref, inView } = useInView()

  useEffect(() => {
    if (inView && pagination?.has_next && !isLoading) {
      fetchDocuments({
        page: (pagination.current_page || 0) + 1,
        page_size: 20,
      })
    }
  }, [inView, pagination, isLoading])

  return (
    <div className="space-y-4">
      {documents.map((doc) => (
        <DocumentCard key={doc.document_id} document={doc} />
      ))}

      {/* Infinite scroll trigger */}
      <div ref={ref} className="h-20 flex items-center justify-center">
        {isLoading && (
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
        )}
      </div>
    </div>
  )
}
```

### 예상 산출물
- 5개 새 컴포넌트 (DataTable, PremiumChart, PDFViewer, InfiniteList)
- 10개 페이지 업데이트 (새 컴포넌트 적용)
- ~800 lines 추가

### Acceptance Criteria
- ✅ 정렬/필터/검색 가능한 데이터 테이블
- ✅ 반응형 차트
- ✅ PDF 미리보기
- ✅ 무한 스크롤
- ✅ 모든 컴포넌트 접근성 준수

---

## 📅 Sprint 계획

### Week 1 (Sprint 6)
- **Day 1-2**: Story 3.1 다크 모드 (3 pts)
  - ThemeProvider, ThemeToggle 구현
  - 모든 컴포넌트 dark: 클래스 적용

- **Day 3-5**: Story 3.2 국제화 (4 pts)
  - next-intl 설정
  - 번역 파일 작성
  - 모든 페이지 번역 적용

### Week 2 (Sprint 7)
- **Day 1-2**: Story 3.3 접근성 (3 pts)
  - ARIA 라벨 추가
  - 색상 대비 개선
  - 키보드 네비게이션 테스트

- **Day 3-5**: Story 3.4 고급 UI (5 pts)
  - DataTable 구현
  - 차트 구현
  - PDF 뷰어 구현

---

## 🎯 성공 지표

### 기술 지표
- [ ] Lighthouse Accessibility: 100점
- [ ] WCAG 2.1 AAA 준수
- [ ] 다크 모드 모든 페이지 지원
- [ ] 2개 언어 100% 번역

### 사용자 경험
- [ ] 다크 모드 사용률 30%+
- [ ] 영어 사용자 10%+
- [ ] 키보드 사용자 만족도
- [ ] 스크린 리더 호환성

---

## 🔍 테스트 체크리스트

### 다크 모드
- [ ] 모든 페이지 다크 모드 확인
- [ ] 색상 대비 검증
- [ ] 시스템 테마 전환 테스트
- [ ] 새로고침 시 테마 유지

### 국제화
- [ ] 모든 텍스트 번역 확인
- [ ] 날짜 포맷 로케일별 확인
- [ ] 통화 포맷 확인
- [ ] URL locale 동작 확인

### 접근성
- [ ] 키보드로 모든 기능 사용
- [ ] 스크린 리더 테스트 (NVDA/JAWS)
- [ ] 색상 대비 검증
- [ ] Focus visible 확인
- [ ] ARIA 라벨 확인

### 고급 UI
- [ ] 데이터 테이블 정렬/필터
- [ ] 차트 반응형 확인
- [ ] PDF 뷰어 동작
- [ ] 무한 스크롤 성능

---

## 📦 최종 산출물

### 새 파일 (18개)
1. `src/providers/theme-provider.tsx`
2. `src/components/ThemeToggle.tsx`
3. `src/i18n.ts`
4. `locales/ko.json`
5. `locales/en.json`
6. `src/components/LanguageSwitcher.tsx`
7. `src/app/[locale]/layout.tsx`
8. `src/components/SkipToContent.tsx`
9. `src/components/Modal.tsx`
10. `src/components/LiveRegion.tsx`
11. `src/components/DataTable.tsx`
12. `src/components/PremiumChart.tsx`
13. `src/components/PDFViewer.tsx`
14. `src/components/InfiniteDocumentList.tsx`
15. (+ 기타 locale별 페이지들)

### 업데이트 파일 (~50개)
- 모든 페이지 (다크 모드, i18n)
- 모든 컴포넌트 (접근성)
- tailwind.config.ts
- next.config.js
- .eslintrc.json
- globals.css

### 총 라인 수
- 새 코드: ~2,500 lines
- 업데이트: ~1,500 lines
- **총합: ~4,000 lines**

---

## 🚀 다음 단계

Phase 3 완료 후:
1. **Phase 1: 백엔드 통합** (실제 API 연동)
2. **Phase 2: 테스팅** (자동화 테스트)
3. **Phase 5: DevOps** (CI/CD)

---

**작성일**: 2025-11-25
**Story Points**: 15 pts
**예상 기간**: 2주
