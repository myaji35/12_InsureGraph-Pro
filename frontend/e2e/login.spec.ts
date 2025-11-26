import { test, expect } from '@playwright/test'

test.describe('Login Page', () => {
  test('should display login form', async ({ page }) => {
    await page.goto('/login')

    // Check if login page title exists
    await expect(page.locator('h2')).toContainText('로그인')

    // Check if email input exists
    const emailInput = page.locator('input[type="email"]')
    await expect(emailInput).toBeVisible()

    // Check if password input exists
    const passwordInput = page.locator('input[type="password"]')
    await expect(passwordInput).toBeVisible()

    // Check if login button exists
    const loginButton = page.locator('button[type="submit"]')
    await expect(loginButton).toBeVisible()
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login')

    // Fill in invalid credentials
    await page.fill('input[type="email"]', 'invalid@example.com')
    await page.fill('input[type="password"]', 'wrongpassword')

    // Click login button
    await page.click('button[type="submit"]')

    // Should stay on login page (no redirect to dashboard)
    await expect(page).toHaveURL('/login')
  })
})
