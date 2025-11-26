import { SignUp } from '@clerk/nextjs'

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-dark-bg py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary-600 dark:text-primary-400">
            InsureGraph Pro
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            보험 전문가를 위한 AI 분석 플랫폼
          </p>
        </div>

        <SignUp
          routing="hash"
          appearance={{
            elements: {
              rootBox: 'mx-auto',
              card: 'shadow-xl',
            },
          }}
        />
      </div>
    </div>
  )
}
