'use client'

/**
 * SkipToContent component for keyboard navigation
 *
 * Provides a "Skip to main content" link that appears when focused,
 * allowing keyboard users to bypass navigation and go directly to main content.
 * This is a WCAG 2.1 Level A requirement.
 *
 * @example
 * // In your layout:
 * <body>
 *   <SkipToContent />
 *   <nav>...</nav>
 *   <main id="main-content" tabIndex={-1}>...</main>
 * </body>
 */
export function SkipToContent() {
  const handleSkip = (event: React.MouseEvent<HTMLAnchorElement>) => {
    event.preventDefault()
    const mainContent = document.getElementById('main-content')
    if (mainContent) {
      // Set focus to main content
      mainContent.focus()
      // Smooth scroll into view
      mainContent.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <a
      href="#main-content"
      onClick={handleSkip}
      className="skip-to-content"
      aria-label="Skip to main content"
    >
      본문으로 건너뛰기
    </a>
  )
}
