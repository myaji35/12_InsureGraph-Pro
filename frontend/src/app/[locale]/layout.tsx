import { NextIntlClientProvider } from 'next-intl'
import { getMessages } from 'next-intl/server'
import { notFound } from 'next/navigation'
import { locales } from '@/i18n'
import { ClerkProvider } from '@clerk/nextjs'
import { ThemeProvider } from '@/providers/theme-provider'
import { Toaster } from 'react-hot-toast'

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
  // Validate locale
  if (!locales.includes(locale as any)) {
    notFound()
  }

  // Get messages for the current locale
  const messages = await getMessages()

  return (
    <NextIntlClientProvider messages={messages}>
      <ClerkProvider>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
      </ClerkProvider>
    </NextIntlClientProvider>
  )
}
