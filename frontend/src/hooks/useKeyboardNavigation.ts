'use client'

import { useEffect, useCallback } from 'react'

export interface KeyboardShortcut {
  key: string
  ctrlKey?: boolean
  altKey?: boolean
  shiftKey?: boolean
  metaKey?: boolean
  action: (event: KeyboardEvent) => void
  description: string
}

/**
 * Hook for implementing keyboard navigation and shortcuts
 *
 * Provides comprehensive keyboard navigation support for accessibility.
 * Supports common patterns like Escape to close, Arrow keys for navigation, etc.
 *
 * @param shortcuts - Array of keyboard shortcuts to register
 * @param enabled - Whether the shortcuts are currently enabled
 *
 * @example
 * useKeyboardNavigation([
 *   {
 *     key: 'Escape',
 *     action: () => closeModal(),
 *     description: 'Close modal'
 *   },
 *   {
 *     key: 's',
 *     ctrlKey: true,
 *     action: (e) => { e.preventDefault(); saveDocument() },
 *     description: 'Save document'
 *   }
 * ])
 */
export function useKeyboardNavigation(
  shortcuts: KeyboardShortcut[],
  enabled = true
) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return

      for (const shortcut of shortcuts) {
        const keyMatches = event.key === shortcut.key
        const ctrlMatches = shortcut.ctrlKey ? event.ctrlKey : !event.ctrlKey
        const altMatches = shortcut.altKey ? event.altKey : !event.altKey
        const shiftMatches = shortcut.shiftKey ? event.shiftKey : !event.shiftKey
        const metaMatches = shortcut.metaKey ? event.metaKey : !event.metaKey

        if (
          keyMatches &&
          ctrlMatches &&
          altMatches &&
          shiftMatches &&
          metaMatches
        ) {
          shortcut.action(event)
          break
        }
      }
    },
    [shortcuts, enabled]
  )

  useEffect(() => {
    if (!enabled) return

    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [handleKeyDown, enabled])
}

/**
 * Hook for Escape key to close modals/dialogs
 *
 * @param onEscape - Callback function to execute when Escape is pressed
 * @param enabled - Whether the listener is currently enabled
 *
 * @example
 * useEscapeKey(() => setIsModalOpen(false), isModalOpen)
 */
export function useEscapeKey(onEscape: () => void, enabled = true) {
  useKeyboardNavigation(
    [
      {
        key: 'Escape',
        action: onEscape,
        description: 'Close',
      },
    ],
    enabled
  )
}

/**
 * Hook for Arrow key navigation
 *
 * @param options - Configuration for arrow key navigation
 * @param enabled - Whether the navigation is enabled
 *
 * @example
 * useArrowNavigation({
 *   onArrowUp: () => navigateToPrevious(),
 *   onArrowDown: () => navigateToNext(),
 *   onArrowLeft: () => navigateToPreviousPage(),
 *   onArrowRight: () => navigateToNextPage(),
 * })
 */
export function useArrowNavigation(
  options: {
    onArrowUp?: () => void
    onArrowDown?: () => void
    onArrowLeft?: () => void
    onArrowRight?: () => void
  },
  enabled = true
) {
  const shortcuts: KeyboardShortcut[] = []

  if (options.onArrowUp) {
    shortcuts.push({
      key: 'ArrowUp',
      action: (e) => {
        e.preventDefault()
        options.onArrowUp!()
      },
      description: 'Navigate up',
    })
  }

  if (options.onArrowDown) {
    shortcuts.push({
      key: 'ArrowDown',
      action: (e) => {
        e.preventDefault()
        options.onArrowDown!()
      },
      description: 'Navigate down',
    })
  }

  if (options.onArrowLeft) {
    shortcuts.push({
      key: 'ArrowLeft',
      action: (e) => {
        e.preventDefault()
        options.onArrowLeft!()
      },
      description: 'Navigate left',
    })
  }

  if (options.onArrowRight) {
    shortcuts.push({
      key: 'ArrowRight',
      action: (e) => {
        e.preventDefault()
        options.onArrowRight!()
      },
      description: 'Navigate right',
    })
  }

  useKeyboardNavigation(shortcuts, enabled)
}
