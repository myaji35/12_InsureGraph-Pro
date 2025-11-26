'use client'

import { useEffect, useRef, ReactNode } from 'react'

interface FocusTrapProps {
  children: ReactNode
  active?: boolean
  restoreFocus?: boolean
  className?: string
}

/**
 * FocusTrap component for accessible modals and dialogs
 *
 * Traps keyboard focus within the component when active,
 * ensuring users can't tab out of modals accidentally.
 * Complies with WCAG 2.1 Level AAA requirements.
 *
 * @param active - Whether the focus trap is active
 * @param restoreFocus - Whether to restore focus to the previously focused element when deactivated
 * @param children - The content to wrap with focus trap
 *
 * @example
 * <FocusTrap active={isModalOpen} restoreFocus>
 *   <div role="dialog" aria-modal="true">
 *     Modal content...
 *   </div>
 * </FocusTrap>
 */
export function FocusTrap({
  children,
  active = true,
  restoreFocus = true,
  className,
}: FocusTrapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const previousFocusRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (!active) return

    // Store the previously focused element
    previousFocusRef.current = document.activeElement as HTMLElement

    const container = containerRef.current
    if (!container) return

    // Get all focusable elements within the container
    const getFocusableElements = (): HTMLElement[] => {
      const focusableSelectors = [
        'a[href]',
        'area[href]',
        'input:not([disabled]):not([type="hidden"])',
        'select:not([disabled])',
        'textarea:not([disabled])',
        'button:not([disabled])',
        'iframe',
        'object',
        'embed',
        '[contenteditable]',
        '[tabindex]:not([tabindex^="-"])',
      ].join(',')

      return Array.from(
        container.querySelectorAll<HTMLElement>(focusableSelectors)
      ).filter((element) => {
        // Filter out elements that are not visible
        return (
          element.offsetWidth > 0 &&
          element.offsetHeight > 0 &&
          window.getComputedStyle(element).visibility !== 'hidden'
        )
      })
    }

    // Focus the first focusable element
    const focusableElements = getFocusableElements()
    if (focusableElements.length > 0) {
      focusableElements[0].focus()
    }

    // Handle Tab key navigation
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return

      const focusableElements = getFocusableElements()
      if (focusableElements.length === 0) return

      const firstElement = focusableElements[0]
      const lastElement = focusableElements[focusableElements.length - 1]
      const activeElement = document.activeElement

      // Shift + Tab: moving backwards
      if (event.shiftKey) {
        if (activeElement === firstElement) {
          event.preventDefault()
          lastElement.focus()
        }
      }
      // Tab: moving forwards
      else {
        if (activeElement === lastElement) {
          event.preventDefault()
          firstElement.focus()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    // Cleanup function
    return () => {
      document.removeEventListener('keydown', handleKeyDown)

      // Restore focus to the previously focused element
      if (restoreFocus && previousFocusRef.current) {
        previousFocusRef.current.focus()
      }
    }
  }, [active, restoreFocus])

  return (
    <div ref={containerRef} className={className}>
      {children}
    </div>
  )
}
