import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' })

export const metadata: Metadata = {
  title: 'InsureGraph Pro - FP Workspace',
  description: 'GraphRAG-powered insurance policy analysis platform for Financial Planners',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.variable}>
        {children}
      </body>
    </html>
  )
}
