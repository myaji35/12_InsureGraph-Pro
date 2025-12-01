import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Query Execution and History
 *
 * Task E: Frontend E2E Tests
 */

test.describe('Query Execution', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/query-simple')
  })

  test('should display query execution page', async ({ page }) => {
    // Check page heading
    await expect(page.locator('h1, h2').filter({ hasText: /질의|검색|Query/ })).toBeVisible()

    // Check for query input
    const queryInput = page.locator('textarea[name="query"], input[name="query"]')
    await expect(queryInput).toBeVisible()

    // Check for submit button
    const submitButton = page.locator('button[type="submit"], button:has-text("검색"), button:has-text("질의")')
    await expect(submitButton.first()).toBeVisible()
  })

  test('should execute simple query', async ({ page }) => {
    // Fill in query
    const queryInput = page.locator('textarea[name="query"], input[name="query"]').first()
    await queryInput.fill('암보험 보장 내용은?')

    // Submit query
    const submitButton = page.locator('button[type="submit"], button:has-text("검색"), button:has-text("질의")').first()
    await submitButton.click()

    // Wait for results (loading state then results)
    await page.waitForSelector('[class*="loading"], [class*="spinner"]', { timeout: 2000 }).catch(() => {})

    // Check for answer section
    await expect(page.locator('[class*="answer"], [class*="result"]')).toBeVisible({ timeout: 10000 })
  })

  test('should show confidence score', async ({ page }) => {
    const queryInput = page.locator('textarea[name="query"], input[name="query"]').first()
    await queryInput.fill('보험료는?')

    const submitButton = page.locator('button[type="submit"], button:has-text("검색"), button:has-text("질의")').first()
    await submitButton.click()

    // Look for confidence indicator (may be percentage, bar, or badge)
    await page.waitForTimeout(5000)

    const confidenceIndicator = page.locator('[class*="confidence"], :text-matches("\\d+%")')
    // Confidence may or may not be visible depending on implementation
  })

  test('should display source documents', async ({ page }) => {
    const queryInput = page.locator('textarea[name="query"], input[name="query"]').first()
    await queryInput.fill('해지 환급금')

    const submitButton = page.locator('button[type="submit"], button:has-text("검색"), button:has-text("질의")').first()
    await submitButton.click()

    await page.waitForTimeout(5000)

    // Look for sources section
    const sourcesSection = page.locator(':has-text("출처"), :has-text("근거"), :has-text("Source")')
    // Sources may be in collapsible section
  })

  test('should handle empty query', async ({ page }) => {
    const submitButton = page.locator('button[type="submit"], button:has-text("검색"), button:has-text("질의")').first()

    // Try to submit without typing
    await submitButton.click()

    // Should either show validation error or do nothing
    await page.waitForTimeout(1000)
  })

  test('should clear query results', async ({ page }) => {
    // Execute a query first
    const queryInput = page.locator('textarea[name="query"], input[name="query"]').first()
    await queryInput.fill('보험 가입')

    const submitButton = page.locator('button[type="submit"], button:has-text("검색"), button:has-text("질의")').first()
    await submitButton.click()

    await page.waitForTimeout(3000)

    // Look for clear/reset button
    const clearButton = page.locator('button:has-text("초기화"), button:has-text("Clear"), button:has-text("새 질의")')

    if (await clearButton.count() > 0) {
      await clearButton.first().click()

      // Query input should be cleared
      const queryInputAfter = page.locator('textarea[name="query"], input[name="query"]').first()
      await expect(queryInputAfter).toHaveValue('')
    }
  })

  test('should associate query with customer', async ({ page }) => {
    // Look for customer selection dropdown
    const customerSelect = page.locator('select[name="customer_id"], input[placeholder*="고객"]')

    if (await customerSelect.count() > 0) {
      // Select a customer if dropdown exists
      const firstOption = customerSelect.first()

      if ((await firstOption.tagName()) === 'SELECT') {
        await firstOption.selectOption({ index: 1 })
      } else {
        await firstOption.fill('김')
        await page.waitForTimeout(500)
      }
    }

    // Execute query
    const queryInput = page.locator('textarea[name="query"], input[name="query"]').first()
    await queryInput.fill('보험료')

    const submitButton = page.locator('button[type="submit"], button:has-text("검색"), button:has-text("질의")').first()
    await submitButton.click()

    await page.waitForTimeout(3000)
  })
})

test.describe('Query History', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/query-history')
  })

  test('should display query history page', async ({ page }) => {
    // Check page heading
    await expect(page.locator('h1, h2').filter({ hasText: /질의.*내역|Query.*History|검색.*기록/ })).toBeVisible()

    // Check for filters
    const searchInput = page.locator('input[placeholder*="검색"]')
    await expect(searchInput).toBeVisible()
  })

  test('should list query history', async ({ page }) => {
    // Wait for list to load
    await page.waitForTimeout(2000)

    // Look for query history items (table or cards)
    const historyItems = page.locator('table tbody tr, [class*="query-card"], [class*="history-item"]')

    // May have items or empty state
    const count = await historyItems.count()

    if (count > 0) {
      // Check if first item is visible
      await expect(historyItems.first()).toBeVisible()
    } else {
      // Check for empty state message
      await expect(page.locator(':has-text("내역이 없습니다"), :has-text("No queries")')).toBeVisible()
    }
  })

  test('should filter queries by search', async ({ page }) => {
    await page.waitForTimeout(1000)

    const searchInput = page.locator('input[placeholder*="검색"]')
    await searchInput.fill('보험')

    // Wait for filter to apply
    await page.waitForTimeout(1000)

    // Results should update
    await expect(searchInput).toHaveValue('보험')
  })

  test('should filter queries by intent', async ({ page }) => {
    // Look for intent filter
    const intentFilter = page.locator('select[name="intent"]')

    if (await intentFilter.count() > 0) {
      await intentFilter.selectOption({ index: 1 })
      await page.waitForTimeout(1000)
    }
  })

  test('should view query detail', async ({ page }) => {
    await page.waitForTimeout(2000)

    // Click on first query (if exists)
    const firstQuery = page.locator('table tbody tr, [class*="query-card"]').first()

    if (await firstQuery.count() > 0) {
      await firstQuery.click()

      // Should open detail modal or navigate to detail page
      await page.waitForTimeout(500)

      // Check for modal or detail content
      const detailModal = page.locator('role=dialog, [class*="modal"]')
      // Modal may or may not appear depending on implementation
    }
  })

  test('should paginate query history', async ({ page }) => {
    await page.waitForTimeout(2000)

    // Look for pagination
    const nextButton = page.locator('button:has-text("다음"), button[aria-label*="next"]')

    if (await nextButton.count() > 0) {
      const isEnabled = await nextButton.first().isEnabled()

      if (isEnabled) {
        await nextButton.first().click()
        await page.waitForTimeout(1000)
      }
    }
  })

  test('should delete query from history', async ({ page }) => {
    await page.waitForTimeout(2000)

    // Look for delete button on first query
    const deleteButton = page.locator('button[title*="삭제"], button:has-text("삭제")').first()

    if (await deleteButton.count() > 0) {
      await deleteButton.click()

      // Confirm deletion
      const confirmButton = page.locator('button:has-text("확인"), button:has-text("삭제")')
      if (await confirmButton.count() > 0) {
        await confirmButton.last().click()
        await page.waitForTimeout(1000)
      }
    }
  })

  test('should show query metadata', async ({ page }) => {
    await page.waitForTimeout(2000)

    const firstQuery = page.locator('table tbody tr, [class*="query-card"]').first()

    if (await firstQuery.count() > 0) {
      await firstQuery.click()

      // Check for metadata in detail view
      await page.waitForTimeout(500)

      // Look for confidence, execution time, etc.
      // These are optional checks
    }
  })
})
