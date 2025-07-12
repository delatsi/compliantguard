import { test, expect } from '@playwright/test';

test('homepage loads successfully', async ({ page }) => {
  await page.goto('/');
  
  // Wait for the page to load and check for basic elements
  await expect(page).toHaveTitle(/ThemisGuard|Vite|React/);
  
  // Check if the page is not blank (has some content)
  const bodyText = await page.textContent('body');
  expect(bodyText.length).toBeGreaterThan(0);
});

test('navigation works', async ({ page }) => {
  await page.goto('/');
  
  // Look for common navigation elements
  // This is a basic test - adjust selectors based on your actual UI
  const hasNavigation = await page.locator('nav, header, [role="navigation"]').count();
  expect(hasNavigation).toBeGreaterThan(0);
});