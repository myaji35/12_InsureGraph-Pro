import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { ClerkProvider } from '@clerk/nextjs'
import { ThemeProvider } from '@/providers/theme-provider'
import { QueryProvider } from '@/providers/query-provider'
import { Toaster } from '@/lib/toast-config'
import { CyberParticles } from '@/components/CyberParticles'
import ErrorBoundary from '@/components/ErrorBoundary'
import { ToastProvider, ToastContainer } from '@/components/Toast'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

// Force dynamic rendering - skip static generation at build time
export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'InsureGraph Pro - FP Workspace',
  description: 'GraphRAG-powered insurance policy analysis platform for Financial Planners',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.variable}>
        <CyberParticles />
        <ClerkProvider>
          <QueryProvider>
            <ThemeProvider
              attribute="class"
              defaultTheme="system"
              enableSystem
              disableTransitionOnChange
            >
              <ErrorBoundary>
                <ToastProvider>
                  {children}
                  <ToastContainer />
                  <Toaster />
                </ToastProvider>
              </ErrorBoundary>
            </ThemeProvider>
          </QueryProvider>
        </ClerkProvider>
      </body>
    </html>
  )
}
