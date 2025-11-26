import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'
import createIntlMiddleware from 'next-intl/middleware'
import { NextRequest, NextResponse } from 'next/server'
import { locales } from './i18n'

// i18n middleware 생성
const intlMiddleware = createIntlMiddleware({
  locales,
  defaultLocale: 'ko',
  localePrefix: 'always',
})

// Protected routes - 인증이 필요한 경로 (locale prefix 포함)
const isProtectedRoute = createRouteMatcher([
  '/:locale/dashboard(.*)',
  '/:locale/documents(.*)',
  '/:locale/query(.*)',
  '/:locale/graph(.*)',
  '/:locale/customers(.*)',
  '/:locale/settings(.*)',
])

// Public routes - 인증 없이 접근 가능한 경로 (locale prefix 포함)
const isPublicRoute = createRouteMatcher([
  '/',
  '/:locale',
  '/:locale/sign-in(.*)',
  '/:locale/sign-up(.*)',
])

export default clerkMiddleware(async (auth, req: NextRequest) => {
  const { pathname } = req.nextUrl

  // Legacy routes redirect - /login, /register를 Clerk 페이지로 리디렉션
  if (pathname === '/login' || pathname.match(/^\/[a-z]{2}\/login$/)) {
    const locale = pathname.startsWith('/en') ? 'en' : 'ko'
    return NextResponse.redirect(new URL(`/${locale}/sign-in`, req.url))
  }
  if (pathname === '/register' || pathname.match(/^\/[a-z]{2}\/register$/)) {
    const locale = pathname.startsWith('/en') ? 'en' : 'ko'
    return NextResponse.redirect(new URL(`/${locale}/sign-up`, req.url))
  }

  // i18n middleware 먼저 실행
  const intlResponse = intlMiddleware(req)

  // Public 경로는 인증 체크 안 함
  if (isPublicRoute(req)) {
    return intlResponse
  }

  // Protected 경로는 인증 필수
  if (isProtectedRoute(req)) {
    await auth.protect()
  }

  return intlResponse
})

export const config = {
  matcher: [
    // Next.js 내부 경로 제외
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // API routes 포함
    '/(api|trpc)(.*)',
  ],
}
