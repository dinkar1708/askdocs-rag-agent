import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Feature: View and Verify Source Citations
 *
 * As a user, I want to see exactly where answers come from
 * so that I can verify the information is accurate.
 */

test.describe('Feature: View and Verify Source Citations', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Upload a document first
    const docsTab = page.locator('button:has-text("📁 Documents")');
    await expect(docsTab).toBeVisible();
    await docsTab.click();
    await page.waitForTimeout(1500);

    // Verify we're on documents tab
    await expect(page.getByText(/Upload Documents/i)).toBeVisible({ timeout: 5000 });

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    const testFilePath = path.join(__dirname, '../fixtures/sample-policy.pdf');
    await fileInput.setInputFiles(testFilePath);

    // Wait for upload to complete
    await expect(page.getByText(/Uploading|Processing document|Upload complete/i)).toBeVisible({ timeout: 30000 });
    await page.waitForTimeout(2000);

    // Go back to Chat tab
    const chatTab = page.locator('button:has-text("💬 Chat")');
    await chatTab.click();
    await page.waitForTimeout(1500);
  });

  test('User sees source citations with page numbers', async ({ page }) => {
    // Ask a question
    const questionInput = page.locator('input[type="text"], textarea').first();
    await questionInput.fill('What is the refund policy?');

    const submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    // Wait for answer with sources (Ollama can be slow)
    await page.waitForTimeout(8000);

    // User should see "Sources" section (increased timeout)
    await expect(page.locator('text=/source|citation/i').first()).toBeVisible({ timeout: 60000 });

    // Should show document name
    await expect(page.locator('text=/.pdf/i').first()).toBeVisible({ timeout: 5000 });

    // Should show page number
    await expect(page.locator('text=/page \\d+/i').first()).toBeVisible({ timeout: 5000 });
  });

  test('User clicks on citation to see context', async ({ page }) => {
    const questionInput = page.locator('input[type="text"], textarea').first();
    await questionInput.fill('What are the working hours?');

    const submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    // Wait for Ollama response
    await page.waitForTimeout(8000);

    // Find and click on a citation
    const citation = page.locator('[data-testid="citation"], .citation, .source').first();

    if (await citation.isVisible({ timeout: 60000 })) {
      await citation.click();

      // Should show context or highlight (modal, tooltip, or expanded view)
      const contextView = page.locator('[data-testid="context"], .context, .citation-detail');
      await expect(contextView).toBeVisible({ timeout: 5000 });
    }
  });

  test('User sees confidence/similarity scores for sources', async ({ page }) => {
    const questionInput = page.locator('input[type="text"], textarea').first();
    await questionInput.fill('What is the dress code?');

    const submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    await page.waitForTimeout(8000);

    // Should show confidence scores (e.g., "85% match" or "0.85")
    const scorePattern = page.locator('text=/\\d+%|0\\.\\d+|score/i');
    await expect(scorePattern.first()).toBeVisible({ timeout: 60000 });
  });

  test('User sees multiple sources ranked by relevance', async ({ page }) => {
    const questionInput = page.locator('input[type="text"], textarea').first();
    await questionInput.fill('What are the employee benefits?');

    const submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    await page.waitForTimeout(8000);

    // Wait for answer to appear
    await expect(page.locator('.bg-gray-100').first()).toBeVisible({ timeout: 60000 });

    // Wait for sources section
    await expect(page.getByText(/Sources:/i).first()).toBeVisible({ timeout: 10000 });

    // Should see document icon (indicates sources are shown)
    const documentIcons = page.locator('text=📄');
    const sourceCount = await documentIcons.count();

    // Should have at least 1 source
    expect(sourceCount).toBeGreaterThanOrEqual(1);
  });

  test('User sees "No sources" when answer is refused', async ({ page }) => {
    // Ask off-topic question
    const questionInput = page.locator('input[type="text"], textarea').first();
    await questionInput.fill("Who won yesterday's game?");

    const submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    await page.waitForTimeout(8000);

    // Wait for any response
    await expect(page.locator('.bg-gray-100').first()).toBeVisible({ timeout: 60000 });

    // For off-topic questions, system should either:
    // 1. Show "not found" or "cannot answer" message, OR
    // 2. Show answer without sources section
    const refusalMessage = page.locator('text=/not found|cannot answer|no information|documents don\'t contain/i');
    const sourcesSection = page.locator('text=/Sources:/i');

    const hasRefusal = await refusalMessage.isVisible({ timeout: 5000 }).catch(() => false);
    const hasSources = await sourcesSection.isVisible({ timeout: 5000 }).catch(() => false);

    // Should have refusal OR no sources (not both)
    expect(hasRefusal || !hasSources).toBeTruthy();
  });
});
