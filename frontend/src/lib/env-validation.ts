/**
 * Environment Variable Validation
 *
 * 개발 초기부터 환경 설정 누락으로 인한 에러를 방지합니다.
 * 필수 환경 변수가 없으면 명확한 에러 메시지를 표시합니다.
 */

interface EnvConfig {
  // Clerk Authentication
  NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: string
  CLERK_SECRET_KEY?: string

  // API Configuration
  NEXT_PUBLIC_API_BASE_URL: string
  NEXT_PUBLIC_API_VERSION: string

  // Environment
  NEXT_PUBLIC_ENVIRONMENT: string
  NODE_ENV: string
}

/**
 * 필수 환경 변수 목록
 */
const requiredEnvVars = [
  'NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY',
  'NEXT_PUBLIC_API_BASE_URL',
  'NEXT_PUBLIC_ENVIRONMENT',
] as const

/**
 * 환경 변수 검증
 * 앱 시작 시 한 번 실행되어 필수 환경 변수를 확인합니다.
 */
export function validateEnv(): EnvConfig {
  const missingVars: string[] = []

  // 필수 환경 변수 확인
  for (const varName of requiredEnvVars) {
    if (!process.env[varName]) {
      missingVars.push(varName)
    }
  }

  // 누락된 환경 변수가 있으면 명확한 에러 메시지
  if (missingVars.length > 0) {
    const errorMessage = `
╔════════════════════════════════════════════════════════════╗
║  환경 변수 설정 오류 - Environment Configuration Error   ║
╚════════════════════════════════════════════════════════════╝

다음 환경 변수가 설정되지 않았습니다:
${missingVars.map(v => `  ❌ ${v}`).join('\n')}

해결 방법:
1. .env.local.example 파일을 .env.local로 복사하세요
   $ cp .env.local.example .env.local

2. .env.local 파일을 열어 실제 값을 입력하세요

3. 서버를 재시작하세요
   $ npm run dev

자세한 내용은 README.md를 참고하세요.
    `.trim()

    console.error(errorMessage)

    // 개발 모드에서는 경고만 표시하고 계속 진행 (Clerk keyless mode 활용)
    if (process.env.NODE_ENV === 'development') {
      console.warn('⚠️  개발 모드: Clerk keyless mode로 계속 진행합니다.')
      console.warn('⚠️  프로덕션 배포 전에 반드시 환경 변수를 설정하세요!')
    } else {
      // 프로덕션에서는 앱 시작 차단
      throw new Error('필수 환경 변수가 설정되지 않았습니다. 위 메시지를 확인하세요.')
    }
  }

  return {
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY || '',
    CLERK_SECRET_KEY: process.env.CLERK_SECRET_KEY,
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api',
    NEXT_PUBLIC_API_VERSION: process.env.NEXT_PUBLIC_API_VERSION || 'v1',
    NEXT_PUBLIC_ENVIRONMENT: process.env.NEXT_PUBLIC_ENVIRONMENT || 'development',
    NODE_ENV: process.env.NODE_ENV || 'development',
  }
}

/**
 * 타입 안전한 환경 변수 접근
 */
export const env = validateEnv()

/**
 * 개발 모드 여부 확인
 */
export const isDevelopment = env.NODE_ENV === 'development'
export const isProduction = env.NODE_ENV === 'production'

/**
 * API URL 생성 헬퍼
 */
export function getApiUrl(endpoint: string): string {
  const baseUrl = env.NEXT_PUBLIC_API_BASE_URL
  const version = env.NEXT_PUBLIC_API_VERSION
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`

  return `${baseUrl}/${version}${cleanEndpoint}`
}
