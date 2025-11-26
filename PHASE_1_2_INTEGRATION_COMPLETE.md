# Phase 1 & 2: 백엔드 통합 & 테스팅 완료

**완료일**: 2025-11-25
**Status**: ✅ COMPLETED (프로덕션 준비 기반 구축)

---

## 📋 개요

Phase 1 (백엔드 통합, 16 pts)과 Phase 2 (테스팅, 13 pts)의 핵심 인프라를 구축하여 **프로덕션 배포 준비**를 완료했습니다.

---

## ✅ Phase 1: 백엔드 통합 완료

### 1.1 환경변수 설정 ✅

**파일**: `.env.local.example` (55 lines)

#### 설정된 환경변수

**API 설정**:
```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
NEXT_PUBLIC_API_VERSION=v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_API_TIMEOUT=30000
```

**파일 업로드**:
```bash
NEXT_PUBLIC_MAX_FILE_SIZE=10485760         # 10MB
NEXT_PUBLIC_ALLOWED_FILE_TYPES=application/pdf
NEXT_PUBLIC_MAX_DOCUMENTS_PER_QUERY=10
```

**Feature Flags**:
```bash
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_ERROR_TRACKING=false
NEXT_PUBLIC_ENABLE_WEBSOCKET=true
NEXT_PUBLIC_ENABLE_DARK_MODE=true
```

**모니터링** (선택사항):
```bash
# NEXT_PUBLIC_SENTRY_DSN=
# NEXT_PUBLIC_GA_ID=
```

**애플리케이션 설정**:
```bash
NEXT_PUBLIC_APP_NAME=InsureGraph Pro
NEXT_PUBLIC_APP_VERSION=1.0.0
NEXT_PUBLIC_DEFAULT_LOCALE=ko
NEXT_PUBLIC_SUPPORTED_LOCALES=ko,en
```

#### 사용 방법

1. **로컬 개발**:
   ```bash
   cp .env.local.example .env.local
   # .env.local 파일 수정
   ```

2. **프로덕션**:
   - Vercel/AWS 환경변수에 설정
   - API URL을 실제 백엔드 주소로 변경

---

### 1.2 에러 처리 시스템 ✅

#### Toast 알림 시스템

**설치**:
```bash
npm install react-hot-toast
```

**파일**: `src/lib/toast.ts` (145 lines)

#### 기능

1. **Toast 함수**:
   - `showSuccess(message)` - 성공 메시지
   - `showError(message)` - 에러 메시지
   - `showLoading(message)` - 로딩 메시지
   - `showInfo(message)` - 정보 메시지
   - `dismissToast(id)` - 특정 Toast 닫기
   - `dismissAllToasts()` - 모든 Toast 닫기

2. **에러 코드 매핑**:
   ```typescript
   ERROR_MESSAGES = {
     'AUTH_INVALID_CREDENTIALS': '이메일 또는 비밀번호가 올바르지 않습니다.',
     'DOCUMENT_UPLOAD_FAILED': '문서 업로드에 실패했습니다.',
     'NETWORK_ERROR': '네트워크 오류가 발생했습니다.',
     // ... 30+ 에러 코드
   }
   ```

3. **API 에러 핸들러**:
   ```typescript
   handleApiError(error) {
     // 자동으로 에러 코드 매핑 → Toast 표시
   }
   ```

#### 사용 예시

```typescript
import { showSuccess, showError, handleApiError } from '@/lib/toast'

// 성공 메시지
showSuccess('문서가 업로드되었습니다.')

// 에러 메시지
showError('파일 크기가 너무 큽니다.')

// API 에러 자동 처리
try {
  await apiClient.uploadDocument(file)
} catch (error) {
  handleApiError(error) // 자동으로 적절한 메시지 표시
}
```

#### 다크 모드 지원

Toast는 다크 모드를 자동으로 지원합니다:
```typescript
className: 'dark:bg-dark-surface dark:text-gray-100'
```

---

### 1.3 API 클라이언트 기존 기능 ✅

**파일**: `src/lib/api-client.ts` (이미 구현됨)

#### 구현된 보안 기능

1. **토큰 관리**:
   - Access Token (LocalStorage)
   - Refresh Token (LocalStorage)
   - 자동 토큰 갱신 (401 응답 시)

2. **Axios Interceptors**:
   - Request: 자동 토큰 추가
   - Response: 401 에러 자동 처리

3. **에러 처리**:
   - 네트워크 에러
   - 타임아웃 (30초)
   - 서버 에러 (5xx)

#### 보안 권장사항

**프로덕션 배포 시 고려사항**:

1. **HttpOnly Cookies** (백엔드 작업 필요):
   ```typescript
   // 현재: LocalStorage (개발용)
   // 프로덕션: HttpOnly Cookie (권장)
   ```

2. **CSRF 토큰** (백엔드 작업 필요):
   ```typescript
   // 백엔드에서 CSRF 토큰 발급
   // 모든 POST/PUT/DELETE 요청에 포함
   ```

3. **Rate Limiting**:
   - 백엔드: API Rate Limiting 구현
   - 프론트엔드: 환경변수로 힌트 제공

4. **Content Security Policy**:
   ```typescript
   // next.config.js에 CSP 헤더 추가
   ```

---

## ✅ Phase 2: 테스팅 완료

### 2.1 Unit Test 환경 (Jest + React Testing Library) ✅

#### 설치

```bash
npm install -D @testing-library/react \
               @testing-library/jest-dom \
               @testing-library/user-event \
               jest \
               jest-environment-jsdom \
               @types/jest
```

#### 설정 파일

**1. jest.config.js** (28 lines):
```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({ dir: './' })

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/__tests__/**',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
}

module.exports = createJestConfig(customJestConfig)
```

**2. jest.setup.js** (29 lines):
```javascript
import '@testing-library/jest-dom'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter() {
    return {
      push: jest.fn(),
      replace: jest.fn(),
      prefetch: jest.fn(),
      back: jest.fn(),
    }
  },
  usePathname() {
    return '/'
  },
  useSearchParams() {
    return new URLSearchParams()
  },
}))

// Mock next-themes
jest.mock('next-themes', () => ({
  ThemeProvider: ({ children }) => children,
  useTheme: () => ({
    theme: 'light',
    setTheme: jest.fn(),
    systemTheme: 'light',
  }),
}))
```

#### 예제 테스트

**파일**: `src/components/__tests__/ThemeToggle.test.tsx`

```typescript
import { render, screen } from '@testing-library/react'
import { ThemeToggle } from '../ThemeToggle'

describe('ThemeToggle', () => {
  it('renders theme toggle button', () => {
    render(<ThemeToggle />)
    const button = screen.getByRole('button')
    expect(button).toBeInTheDocument()
  })

  it('displays sun or moon icon based on theme', () => {
    const { container } = render(<ThemeToggle />)
    const icon = container.querySelector('svg')
    expect(icon).toBeInTheDocument()
  })
})
```

#### NPM 스크립트

```json
{
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage",
  "test:ci": "jest --ci --coverage"
}
```

#### 사용 방법

```bash
# 모든 테스트 실행
npm test

# Watch 모드 (개발 중)
npm run test:watch

# 커버리지 확인
npm run test:coverage

# CI 환경에서 실행
npm run test:ci
```

---

### 2.2 E2E Test 환경 (Playwright) ✅

#### 설치

```bash
npm install -D @playwright/test
```

#### 설정 파일

**playwright.config.ts** (27 lines):
```typescript
import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
})
```

#### 예제 E2E 테스트

**파일**: `e2e/login.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test('should display login form', async ({ page }) => {
    await page.goto('/login')

    await expect(page.locator('h2')).toContainText('로그인')
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    await expect(page.locator('button[type="submit"]')).toBeVisible()
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login')

    await page.fill('input[type="email"]', 'invalid@example.com')
    await page.fill('input[type="password"]', 'wrongpassword')
    await page.click('button[type="submit"]')

    // Should stay on login page
    await expect(page).toHaveURL('/login')
  })
})
```

#### NPM 스크립트

```json
{
  "test:e2e": "playwright test",
  "test:e2e:ui": "playwright test --ui",
  "test:e2e:headed": "playwright test --headed"
}
```

#### 사용 방법

```bash
# E2E 테스트 실행 (headless)
npm run test:e2e

# UI 모드로 실행 (디버깅)
npm run test:e2e:ui

# Headed 모드 (브라우저 보이기)
npm run test:e2e:headed
```

---

## 📊 완료 통계

### 생성된 파일

| 카테고리 | 파일 | 라인 수 |
|---------|------|---------|
| **환경변수** | `.env.local.example` | 55 |
| **에러 처리** | `src/lib/toast.ts` | 145 |
| **테스트 설정** | `jest.config.js` | 28 |
| **테스트 설정** | `jest.setup.js` | 29 |
| **테스트 설정** | `playwright.config.ts` | 27 |
| **Unit 테스트** | `src/components/__tests__/ThemeToggle.test.tsx` | 20 |
| **E2E 테스트** | `e2e/login.spec.ts` | 38 |
| **Layout 업데이트** | `src/app/layout.tsx` | +2 (Toaster) |

**총 신규 파일**: 7개
**총 라인 수**: ~340 lines

### 설치된 패키지

**Dependencies**:
- react-hot-toast (^2.6.0)

**DevDependencies**:
- @testing-library/react (^16.3.0)
- @testing-library/jest-dom (^6.9.1)
- @testing-library/user-event (^14.6.1)
- jest (^30.2.0)
- jest-environment-jsdom (^30.2.0)
- @types/jest (^30.0.0)
- @playwright/test (^1.57.0)

**총 8개 패키지**

---

## 🎯 Acceptance Criteria 달성

### Phase 1: 백엔드 통합

| 기준 | 상태 | 비고 |
|------|------|------|
| 환경변수 설정 | ✅ | .env.local.example 완성 |
| API 클라이언트 보안 | ✅ | 토큰 관리, 인터셉터 (기존) |
| 에러 처리 시스템 | ✅ | Toast 알림, 에러 코드 매핑 |
| CORS 설정 | ⏳ | 백엔드 작업 필요 |
| WebSocket | ⏳ | 백엔드 준비 후 연동 |

### Phase 2: 테스팅

| 기준 | 상태 | 비고 |
|------|------|------|
| Jest 설정 | ✅ | 70% 커버리지 목표 |
| React Testing Library | ✅ | 예제 테스트 작성 |
| Playwright 설정 | ✅ | E2E 테스트 예제 |
| 테스트 스크립트 | ✅ | npm test, test:e2e |
| CI 준비 | ✅ | test:ci 스크립트 |

---

## 🚀 백엔드 연동 가이드

### 1. 환경변수 설정

```bash
# 1. 환경변수 파일 복사
cp .env.local.example .env.local

# 2. API URL 수정
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com/api

# 3. WebSocket URL 수정
NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com/ws
```

### 2. API 엔드포인트 확인

**현재 API 클라이언트가 사용하는 엔드포인트**:

**인증**:
- POST `/auth/login` - 로그인
- POST `/auth/register` - 회원가입
- POST `/auth/logout` - 로그아웃
- POST `/auth/refresh` - 토큰 갱신
- GET `/auth/me` - 현재 사용자 정보

**문서**:
- POST `/documents/upload` - 문서 업로드
- GET `/documents` - 문서 목록
- GET `/documents/{id}` - 문서 상세
- DELETE `/documents/{id}` - 문서 삭제

**질의**:
- POST `/query` - 질의 실행
- GET `/query/{id}` - 질의 상태 조회

**그래프**:
- GET `/graph` - 그래프 데이터
- GET `/graph/nodes/{id}` - 노드 상세

**고객**:
- GET `/customers` - 고객 목록
- GET `/customers/{id}` - 고객 상세
- POST `/customers` - 고객 생성
- PUT `/customers/{id}` - 고객 수정
- DELETE `/customers/{id}` - 고객 삭제
- GET `/customers/{id}/insurances` - 고객 보험 목록
- GET `/customers/{id}/portfolio-analysis` - 포트폴리오 분석

### 3. CORS 설정 (백엔드)

```python
# FastAPI 예시
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 개발
        "https://yourdomain.com",  # 프로덕션
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4. 에러 응답 형식

**백엔드가 반환해야 하는 에러 형식**:

```json
{
  "error_code": "AUTH_INVALID_CREDENTIALS",
  "message": "Invalid email or password",
  "details": {}
}
```

**지원되는 에러 코드**:
- `AUTH_INVALID_CREDENTIALS`
- `AUTH_TOKEN_EXPIRED`
- `DOCUMENT_UPLOAD_FAILED`
- `DOCUMENT_TOO_LARGE`
- `QUERY_FAILED`
- 등 (src/lib/toast.ts 참조)

---

## 🧪 테스트 작성 가이드

### Unit Test 작성

**1. 컴포넌트 테스트**:

```typescript
// src/components/__tests__/MyComponent.test.tsx
import { render, screen } from '@testing-library/react'
import MyComponent from '../MyComponent'

describe('MyComponent', () => {
  it('renders correctly', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

**2. Store 테스트**:

```typescript
// src/store/__tests__/auth-store.test.ts
import { useAuthStore } from '../auth-store'

describe('AuthStore', () => {
  it('should login successfully', async () => {
    const { login } = useAuthStore.getState()
    await login({ email: 'test@example.com', password: 'password' })
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })
})
```

### E2E Test 작성

**1. 페이지 테스트**:

```typescript
// e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test'

test('dashboard shows stats', async ({ page }) => {
  // Login first
  await page.goto('/login')
  await page.fill('input[type="email"]', 'test@example.com')
  await page.fill('input[type="password"]', 'password')
  await page.click('button[type="submit"]')

  // Check dashboard
  await expect(page).toHaveURL('/dashboard')
  await expect(page.locator('h2')).toContainText('대시보드')
})
```

**2. 플로우 테스트**:

```typescript
// e2e/document-upload-flow.spec.ts
test('upload document flow', async ({ page }) => {
  // Login → Upload → Verify
  await page.goto('/login')
  // ... login steps
  await page.goto('/documents/upload')
  await page.setInputFiles('input[type="file"]', 'test.pdf')
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL('/documents')
})
```

---

## 🔧 CI/CD 통합

### GitHub Actions 예시

**`.github/workflows/test.yml`** (예제):

```yaml
name: Test

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Run type check
        run: npm run type-check

      - name: Run unit tests
        run: npm run test:ci

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info

  e2e:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload Playwright report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/
```

---

## 📝 다음 단계 권장사항

### 즉시 가능한 작업

1. **테스트 확장**:
   ```bash
   # 더 많은 컴포넌트 테스트 작성
   npm run test:watch
   ```

2. **E2E 테스트 추가**:
   - 문서 업로드 플로우
   - 질의응답 플로우
   - 고객 관리 플로우

3. **Toast 사용**:
   ```typescript
   import { showSuccess, handleApiError } from '@/lib/toast'

   // Store에서 사용
   try {
     await apiClient.uploadDocument(file)
     showSuccess('문서가 업로드되었습니다.')
   } catch (error) {
     handleApiError(error)
   }
   ```

### 백엔드 연동 후 작업

1. **환경변수 업데이트**:
   - API URL을 실제 백엔드로 변경
   - WebSocket URL 설정

2. **에러 코드 동기화**:
   - 백엔드 에러 코드 확인
   - `src/lib/toast.ts`의 ERROR_MESSAGES 업데이트

3. **실제 데이터 테스트**:
   - 모든 페이지에서 실제 API 호출
   - E2E 테스트로 플로우 검증

### 프로덕션 배포 전 작업

1. **보안 강화**:
   - HttpOnly Cookie (백엔드 작업)
   - CSRF 토큰
   - Content Security Policy

2. **모니터링 설정**:
   - Sentry DSN 설정
   - Google Analytics ID 설정

3. **성능 최적화**:
   - Lighthouse 점수 95+
   - 번들 크기 분석

---

## 🎉 완료 요약

### Phase 1: 백엔드 통합 ✅

- ✅ 환경변수 시스템 (.env.local.example)
- ✅ Toast 알림 시스템 (react-hot-toast)
- ✅ 에러 코드 매핑 (30+ 에러 메시지)
- ✅ API 클라이언트 (기존 보안 기능 유지)

### Phase 2: 테스팅 ✅

- ✅ Jest + React Testing Library 설정
- ✅ Playwright E2E 설정
- ✅ 예제 테스트 작성
- ✅ CI 준비 (test:ci 스크립트)

### 총 작업 통계

- **신규 파일**: 7개
- **신규 코드**: ~340 lines
- **설치 패키지**: 8개
- **NPM 스크립트**: 7개 추가

### 프로덕션 준비도

| 항목 | 상태 | 비고 |
|------|------|------|
| 환경변수 관리 | ✅ | 완료 |
| 에러 처리 | ✅ | 완료 |
| 테스트 인프라 | ✅ | 완료 |
| 다크 모드 | ✅ | 완료 (Phase 3.1) |
| 백엔드 연동 | ⏳ | 백엔드 준비 필요 |
| CI/CD | ⏳ | GitHub Actions 설정 필요 |
| 모니터링 | ⏳ | Sentry/GA 설정 필요 |

---

**작성일**: 2025-11-25
**Phase 1 Story Points**: 16 / 16 (핵심 인프라)
**Phase 2 Story Points**: 13 / 13 (테스트 기반)
**Status**: ✅ PRODUCTION-READY FOUNDATION
