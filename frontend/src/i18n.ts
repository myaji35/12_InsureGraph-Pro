import { getRequestConfig } from 'next-intl/server'
import { notFound } from 'next/navigation'

export const locales = ['ko', 'en'] as const
export type Locale = (typeof locales)[number]

export default getRequestConfig(async ({ locale }) => {
  // Validate that the incoming `locale` parameter is valid
  const validatedLocale = locale && locales.includes(locale as Locale) ? locale : 'ko'

  if (!locale || !locales.includes(locale as Locale)) notFound()

  return {
    locale: validatedLocale,
    messages: (await import(`../locales/${validatedLocale}.json`)).default,
  }
})
