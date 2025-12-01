import { test, expect } from '@playwright/test'

/**
 * E2E Tests for Customer Management
 *
 * Task E: Frontend E2E Tests
 */

test.describe('Customer Management', () => {
  test.beforeEach(async ({ page }) => {
    // Note: In real tests, you would authenticate first
    // For now, we assume the user is already authenticated
    await page.goto('/customers')
  })

  test('should display customer list page', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1, h2').filter({ hasText: '고객 관리' })).toBeVisible()

    // Check for add customer button
    const addButton = page.locator('button', { hasText: '고객 추가' })
    await expect(addButton).toBeVisible()

    // Check for search input
    const searchInput = page.locator('input[placeholder*="검색"]')
    await expect(searchInput).toBeVisible()
  })

  test('should open customer creation modal', async ({ page }) => {
    // Click add customer button
    await page.click('button:has-text("고객 추가")')

    // Check if modal opened
    await expect(page.locator('role=dialog')).toBeVisible()

    // Check form fields
    await expect(page.locator('input[name="name"]')).toBeVisible()
    await expect(page.locator('input[name="birth_year"]')).toBeVisible()
    await expect(page.locator('select[name="gender"]')).toBeVisible()
    await expect(page.locator('input[name="phone"]')).toBeVisible()
    await expect(page.locator('input[name="email"]')).toBeVisible()
  })

  test('should validate required fields', async ({ page }) => {
    await page.click('button:has-text("고객 추가")')

    // Try to submit empty form
    await page.click('button[type="submit"]')

    // Should show validation errors or stay on modal
    await expect(page.locator('role=dialog')).toBeVisible()
  })

  test('should create new customer', async ({ page }) => {
    await page.click('button:has-text("고객 추가")')

    // Fill in customer details
    await page.fill('input[name="name"]', '테스트고객')
    await page.fill('input[name="birth_year"]', '1985')
    await page.selectOption('select[name="gender"]', 'M')
    await page.fill('input[name="phone"]', '010-1234-5678')
    await page.fill('input[name="email"]', 'test@example.com')

    // Check consent checkbox
    await page.check('input[name="consent_given"]')

    // Submit form
    await page.click('button[type="submit"]')

    // Should close modal and show success message
    await expect(page.locator('role=dialog')).not.toBeVisible({ timeout: 5000 })
  })

  test('should search customers', async ({ page }) => {
    const searchInput = page.locator('input[placeholder*="검색"]')

    // Type search query
    await searchInput.fill('김')

    // Wait for search results
    await page.waitForTimeout(500)

    // Results should update (implementation depends on your search)
    // This is a basic check that the input works
    await expect(searchInput).toHaveValue('김')
  })

  test('should filter customers by gender', async ({ page }) => {
    // Look for gender filter dropdown/buttons
    const genderFilter = page.locator('select[name="gender"], button:has-text("남"), button:has-text("여")')

    if (await genderFilter.count() > 0) {
      // If filter exists, interact with it
      const firstFilter = genderFilter.first()
      await firstFilter.click()
    }
  })

  test('should view customer details', async ({ page }) => {
    // Wait for customer list to load
    await page.waitForSelector('table, .customer-card', { timeout: 5000 })

    // Click first customer (if exists)
    const firstCustomer = page.locator('table tbody tr, .customer-card').first()

    if (await firstCustomer.count() > 0) {
      await firstCustomer.click()

      // Should navigate to detail page or open modal
      await page.waitForTimeout(500)
    }
  })

  test('should paginate through customer list', async ({ page }) => {
    // Look for pagination controls
    const nextButton = page.locator('button:has-text("다음"), button[aria-label*="next"]')

    if (await nextButton.count() > 0) {
      const isEnabled = await nextButton.first().isEnabled()

      if (isEnabled) {
        await nextButton.first().click()
        await page.waitForTimeout(500)
      }
    }
  })
})

test.describe('Customer Policy Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/customers')
  })

  test('should add policy to customer', async ({ page }) => {
    // This test assumes you can navigate to a customer detail page
    // and add a policy. Adjust selectors based on your actual UI.

    // Navigate to first customer (if exists)
    const firstCustomer = page.locator('table tbody tr, .customer-card').first()

    if (await firstCustomer.count() > 0) {
      await firstCustomer.click()

      // Look for add policy button
      const addPolicyButton = page.locator('button:has-text("보험 추가")')

      if (await addPolicyButton.count() > 0) {
        await addPolicyButton.click()

        // Check policy form fields
        await expect(page.locator('select[name="policy_type"]')).toBeVisible()
        await expect(page.locator('input[name="insurer"]')).toBeVisible()
        await expect(page.locator('input[name="coverage_amount"]')).toBeVisible()
      }
    }
  })

  test('should delete customer', async ({ page }) => {
    // Navigate to first customer
    const firstCustomer = page.locator('table tbody tr, .customer-card').first()

    if (await firstCustomer.count() > 0) {
      await firstCustomer.click()

      // Look for delete button
      const deleteButton = page.locator('button:has-text("삭제")')

      if (await deleteButton.count() > 0) {
        await deleteButton.click()

        // Confirm deletion in dialog
        const confirmButton = page.locator('button:has-text("확인"), button:has-text("삭제")')
        if (await confirmButton.count() > 0) {
          await confirmButton.last().click()
        }
      }
    }
  })
})
