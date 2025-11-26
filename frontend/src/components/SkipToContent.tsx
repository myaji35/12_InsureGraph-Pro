'use client'

import { useTranslations } from 'next-intl'

/**
 * Skip to Content Link
 * 접근성을 위한 본문 바로가기 링크
 * 키보드 사용자가 Tab 키를 누르면 가장 먼저 포커스되며,
 * Enter 키를 누르면 메인 콘텐츠로 바로 이동할 수 있습니다.
 */
export function SkipToContent() {
  const t = useTranslations('common')

  return (
    <a
      href="#main-content"
      className="
        sr-only
        focus:not-sr-only
        focus:absolute
        focus:top-4
        focus:left-4
        focus:z-50
        focus:px-4
        focus:py-2
        focus:bg-primary-600
        focus:text-white
        focus:rounded-md
        focus:shadow-lg
        focus:outline-none
        focus:ring-2
        focus:ring-primary-500
        focus:ring-offset-2
        transition-all
        duration-150
      "
      tabIndex={0}
    >
      {t('skipToContent') || '본문으로 건너뛰기'}
    </a>
  )
}
