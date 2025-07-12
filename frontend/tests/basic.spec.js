import { test, expect } from '@playwright/test';

test('homepage loads successfully', async ({ page }) => {
  console.log('Testing URL:', page.url());
  
  // Go to the homepage
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Wait for React to load and render
  await page.waitForSelector('body', { timeout: 30000 });
  
  // Check if the page loaded (look for any content)
  const bodyText = await page.textContent('body');
  console.log('Page content length:', bodyText.length);
  
  // Basic check that page is not blank
  expect(bodyText.length).toBeGreaterThan(50);
  
  // Look for common React app indicators
  const hasReactContent = await page.locator('div#root').count();
  expect(hasReactContent).toBeGreaterThan(0);
});

test('React app renders content', async ({ page }) => {
  await page.goto('/', { waitUntil: 'networkidle' });
  
  // Wait for React app to render
  await page.waitForSelector('div#root', { timeout: 30000 });
  
  // Check that the root div has content
  const rootContent = await page.locator('div#root').textContent();
  expect(rootContent.length).toBeGreaterThan(0);
  
  // Take a screenshot for debugging
  await page.screenshot({ path: 'homepage.png', fullPage: true });
});