import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

// Protected routes - 인증이 필요한 경로
const isProtectedRoute = createRouteMatcher([
  '/dashboard(.*)',
  '/documents(.*)',
  '/query(.*)',
  '/graph(.*)',
  '/customers(.*)',
  '/settings(.*)',
])

// Public routes - 인증 없이 접근 가능한 경로
const isPublicRoute = createRouteMatcher([
  '/',
  '/sign-in(.*)',
  '/sign-up(.*)',
])

export default clerkMiddleware((auth, req) => {
  // Protected 경로는 인증 필수
  if (isProtectedRoute(req)) {
    auth.protect()
  }
})

export const config = {
  matcher: [
    // Next.js 내부 경로 제외
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // API routes 포함
    '/(api|trpc)(.*)',
  ],
}
