/**
 * Internationalization formatting utilities
 * 날짜, 통화, 숫자를 로케일에 맞게 포맷팅하는 유틸리티 함수들
 */

/**
 * 날짜를 로케일에 맞게 포맷팅
 * @param date - Date 객체 또는 날짜 문자열
 * @param locale - 로케일 ('ko' | 'en')
 * @param options - Intl.DateTimeFormat 옵션
 * @returns 포맷팅된 날짜 문자열
 *
 * @example
 * formatDate(new Date(), 'ko') // "2025년 11월 26일"
 * formatDate(new Date(), 'en') // "November 26, 2025"
 */
export function formatDate(
  date: Date | string,
  locale: string,
  options?: Intl.DateTimeFormatOptions
): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date

  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }

  return new Intl.DateTimeFormat(locale, options || defaultOptions).format(dateObj)
}

/**
 * 짧은 형식으로 날짜 포맷팅
 * @example
 * formatDateShort(new Date(), 'ko') // "2025. 11. 26."
 * formatDateShort(new Date(), 'en') // "11/26/2025"
 */
export function formatDateShort(date: Date | string, locale: string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(dateObj)
}

/**
 * 시간을 포함한 날짜 포맷팅
 * @example
 * formatDateTime(new Date(), 'ko') // "2025년 11월 26일 오후 3:45"
 * formatDateTime(new Date(), 'en') // "November 26, 2025 at 3:45 PM"
 */
export function formatDateTime(date: Date | string, locale: string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date

  return new Intl.DateTimeFormat(locale, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: locale === 'en',
  }).format(dateObj)
}

/**
 * 상대적인 시간 포맷팅 (예: "3일 전", "2시간 후")
 * @example
 * formatRelativeTime(new Date(Date.now() - 1000 * 60 * 60 * 24 * 3), 'ko') // "3일 전"
 * formatRelativeTime(new Date(Date.now() - 1000 * 60 * 60 * 24 * 3), 'en') // "3 days ago"
 */
export function formatRelativeTime(date: Date | string, locale: string): string {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const now = new Date()
  const diffInSeconds = Math.floor((now.getTime() - dateObj.getTime()) / 1000)

  const rtf = new Intl.RelativeTimeFormat(locale, { numeric: 'auto' })

  // 초
  if (Math.abs(diffInSeconds) < 60) {
    return rtf.format(-diffInSeconds, 'second')
  }

  // 분
  const diffInMinutes = Math.floor(diffInSeconds / 60)
  if (Math.abs(diffInMinutes) < 60) {
    return rtf.format(-diffInMinutes, 'minute')
  }

  // 시간
  const diffInHours = Math.floor(diffInMinutes / 60)
  if (Math.abs(diffInHours) < 24) {
    return rtf.format(-diffInHours, 'hour')
  }

  // 일
  const diffInDays = Math.floor(diffInHours / 24)
  if (Math.abs(diffInDays) < 30) {
    return rtf.format(-diffInDays, 'day')
  }

  // 월
  const diffInMonths = Math.floor(diffInDays / 30)
  if (Math.abs(diffInMonths) < 12) {
    return rtf.format(-diffInMonths, 'month')
  }

  // 년
  const diffInYears = Math.floor(diffInMonths / 12)
  return rtf.format(-diffInYears, 'year')
}

/**
 * 통화를 로케일에 맞게 포맷팅
 * @param amount - 금액
 * @param locale - 로케일 ('ko' | 'en')
 * @param currency - 통화 코드 (기본값: locale에 따라 자동 설정)
 * @returns 포맷팅된 통화 문자열
 *
 * @example
 * formatCurrency(10000, 'ko') // "₩10,000"
 * formatCurrency(10000, 'en') // "$10,000.00"
 */
export function formatCurrency(
  amount: number,
  locale: string,
  currency?: string
): string {
  const currencyCode = currency || (locale === 'ko' ? 'KRW' : 'USD')

  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: currencyCode,
    minimumFractionDigits: currencyCode === 'KRW' ? 0 : 2,
    maximumFractionDigits: currencyCode === 'KRW' ? 0 : 2,
  }).format(amount)
}

/**
 * 월 단위 통화 포맷팅 (보험료 표시용)
 * @example
 * formatMonthlyPremium(50000, 'ko') // "₩50,000 / 월"
 * formatMonthlyPremium(50000, 'en') // "$50,000.00 / month"
 */
export function formatMonthlyPremium(amount: number, locale: string): string {
  const formatted = formatCurrency(amount, locale)
  const suffix = locale === 'ko' ? ' / 월' : ' / month'
  return formatted + suffix
}

/**
 * 숫자를 로케일에 맞게 포맷팅
 * @example
 * formatNumber(1234567, 'ko') // "1,234,567"
 * formatNumber(1234567, 'en') // "1,234,567"
 */
export function formatNumber(value: number, locale: string): string {
  return new Intl.NumberFormat(locale).format(value)
}

/**
 * 백분율 포맷팅
 * @example
 * formatPercent(0.856, 'ko') // "85.6%"
 * formatPercent(0.856, 'en') // "85.6%"
 */
export function formatPercent(
  value: number,
  locale: string,
  decimals: number = 1
): string {
  return new Intl.NumberFormat(locale, {
    style: 'percent',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value)
}

/**
 * 파일 크기 포맷팅
 * @example
 * formatFileSize(1234567, 'ko') // "1.18 MB"
 * formatFileSize(1234567, 'en') // "1.18 MB"
 */
export function formatFileSize(bytes: number, locale: string): string {
  const units = locale === 'ko'
    ? ['바이트', 'KB', 'MB', 'GB', 'TB']
    : ['Bytes', 'KB', 'MB', 'GB', 'TB']

  if (bytes === 0) return `0 ${units[0]}`

  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const value = bytes / Math.pow(k, i)

  return `${value.toFixed(2)} ${units[i]}`
}

/**
 * 보험 상품 타입을 한글/영문으로 변환
 */
export function formatProductType(type: string, locale: string): string {
  const types: Record<string, { ko: string; en: string }> = {
    life: { ko: '생명보험', en: 'Life Insurance' },
    health: { ko: '건강보험', en: 'Health Insurance' },
    cancer: { ko: '암보험', en: 'Cancer Insurance' },
    ci: { ko: '중대질병보험', en: 'Critical Illness Insurance' },
    accident: { ko: '상해보험', en: 'Accident Insurance' },
    annuity: { ko: '연금보험', en: 'Annuity Insurance' },
  }

  return types[type]?.[locale as 'ko' | 'en'] || type
}

/**
 * 문서 상태를 한글/영문으로 변환
 */
export function formatDocumentStatus(status: string, locale: string): string {
  const statuses: Record<string, { ko: string; en: string }> = {
    pending: { ko: '대기 중', en: 'Pending' },
    processing: { ko: '처리 중', en: 'Processing' },
    ready: { ko: '준비됨', en: 'Ready' },
    failed: { ko: '실패', en: 'Failed' },
  }

  return statuses[status]?.[locale as 'ko' | 'en'] || status
}

/**
 * 위험 프로필을 한글/영문으로 변환
 */
export function formatRiskLevel(level: string, locale: string): string {
  const levels: Record<string, { ko: string; en: string }> = {
    low: { ko: '낮음', en: 'Low' },
    medium: { ko: '보통', en: 'Medium' },
    high: { ko: '높음', en: 'High' },
  }

  return levels[level]?.[locale as 'ko' | 'en'] || level
}
