import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright E2E Test Configuration
 *
 * Tests user flows from a real user's perspective:
 * - Document upload and management
 * - Question asking and answer verification
 * - Source citations and grounding
 * - Multi-turn conversations
 *
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }]
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    // ISOLATED TEST ENVIRONMENT: Uses port 3001 for testing (dev uses 3000)
    baseURL: process.env.BASE_URL || 'http://localhost:3001',

    // API endpoint for backend tests
    // ISOLATED TEST ENVIRONMENT: Uses port 8001 for testing (dev uses 8000)
    apiURL: process.env.API_URL || 'http://localhost:8001',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    // Uncomment if you need Firefox/Safari testing
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },

    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    // Mobile viewports (optional - uncomment if needed)
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  // Run your local dev server before starting the tests
  // ISOLATED TEST ENVIRONMENT: Starts on port 3001 (dev uses 3000)
  webServer: {
    // Set NUXT_PUBLIC_API_BASE to point to test API on port 8001
    command: `NUXT_PUBLIC_API_BASE=${process.env.API_URL || 'http://localhost:8001'} npm run dev -- -p 3001`,
    url: 'http://localhost:3001',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
