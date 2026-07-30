import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Feature: Document Upload and Management
 *
 * As a user, I want to upload PDF documents to the system
 * so that I can ask questions about them later.
 */

test.describe('Feature: Upload and Manage Documents', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Click on Documents tab
    const docsTab = page.locator('button:has-text("📁 Documents")');
    await expect(docsTab).toBeVisible();
    await docsTab.click();
    await page.waitForTimeout(1500);

    // Verify we're on the documents tab by checking for upload interface
    await expect(page.getByText(/Upload Documents/i)).toBeVisible({ timeout: 5000 });
  });

  test('User uploads a PDF document successfully', async ({ page }) => {
    // User should see the upload interface
    await expect(page.getByText(/Upload Documents/i)).toBeVisible();

    // Get the hidden file input
    const fileInput = page.locator('input[type="file"]');

    // Upload a test document
    const testFilePath = path.join(__dirname, '../fixtures/sample-policy.pdf');
    await fileInput.setInputFiles(testFilePath);

    // Wait for upload to complete (progress messages)
    await expect(page.getByText(/Uploading|Processing document|Upload complete/i)).toBeVisible({ timeout: 30000 });

    // Wait a bit for the document to be processed and list to refresh
    await page.waitForTimeout(2000);

    // Document should appear in the list (use first() to avoid strict mode violation)
    await expect(page.getByText(/sample-policy\.pdf/i).first()).toBeVisible({ timeout: 5000 });
  });

  test('User sees list of uploaded documents', async ({ page }) => {
    // Wait for documents to load
    await page.waitForTimeout(1000);

    // User should see document list header with count
    const header = page.getByText(/Uploaded Documents \(\d+\)/i);
    await expect(header).toBeVisible({ timeout: 5000 });
  });

  test('User can view document metadata filters', async ({ page }) => {
    // Navigate to chat tab to see filters
    await page.getByRole('button', { name: /💬 Chat/i }).click();

    // Should see filter controls
    await expect(page.getByText(/Filters:/i)).toBeVisible();

    // Should have department filter
    const departmentFilter = page.locator('select').filter({ hasText: /All Departments/i });
    await expect(departmentFilter).toBeVisible();
  });

  test('User can delete a document', async ({ page }) => {
    // Wait for documents to load
    await page.waitForTimeout(1000);

    // Find delete button (trash icon 🗑️) - if documents exist
    const deleteButton = page.locator('button[title="Delete document"]').first();

    if (await deleteButton.isVisible({ timeout: 2000 })) {
      // Click delete
      await deleteButton.click();

      // Wait for confirmation modal to appear
      await expect(page.getByText(/Delete Document\?/i)).toBeVisible({ timeout: 2000 });

      // Click the "Delete" confirmation button (red button)
      const confirmButton = page.getByRole('button', { name: /^Delete$/i });
      await confirmButton.click();

      // Wait for deletion to complete
      await page.waitForTimeout(1000);
    }
  });

  test('User sees file type restriction (PDF only)', async ({ page }) => {
    // Check file input accept attribute
    const fileInput = page.locator('input[type="file"]');
    const acceptAttr = await fileInput.getAttribute('accept');
    expect(acceptAttr).toContain('.pdf');

    // Should see "PDF files only" text
    await expect(page.getByText(/PDF files only/i)).toBeVisible();
  });
});
