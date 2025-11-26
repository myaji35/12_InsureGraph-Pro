'use client'

import Link from 'next/link'
import { SignedIn, SignedOut, UserButton } from '@clerk/nextjs'

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="text-center">
        <h1 className="text-5xl font-bold mb-4">
          InsureGraph Pro
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          GraphRAG 기반 보험 약관 분석 플랫폼
        </p>

        {/* 로그인하지 않은 상태 */}
        <SignedOut>
          <div className="flex gap-4 justify-center">
            <Link
              href="/sign-in"
              className="btn-primary"
            >
              로그인
            </Link>
            <Link
              href="/sign-up"
              className="btn-secondary"
            >
              회원가입
            </Link>
          </div>
        </SignedOut>

        {/* 로그인한 상태 */}
        <SignedIn>
          <div className="flex flex-col gap-4 items-center">
            <p className="text-green-600 font-medium">로그인되었습니다!</p>
            <div className="flex gap-4 items-center">
              <Link
                href="/dashboard"
                className="btn-primary"
              >
                대시보드로 이동
              </Link>
              <UserButton afterSignOutUrl="/" />
            </div>
          </div>
        </SignedIn>
      </div>
    </main>
  )
}
