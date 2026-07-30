import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * DEMO: Full Flow - Upload PDF and Ask Question
 *
 * This test demonstrates the complete user journey:
 * 1. Upload a PDF document
 * 2. Ask a question about the document
 * 3. Receive AI-generated answer with citations
 */

test('DEMO: Upload PDF and ask question with AI response', async ({ page }) => {
  // Go to home page
  await page.goto('/');
  await page.waitForLoadState('networkidle');

  console.log('📍 Step 1: Navigating to Documents tab...');

  // Navigate to Documents tab
  const docsTab = page.locator('button:has-text("📁 Documents")');
  await expect(docsTab).toBeVisible();
  await docsTab.click();
  await page.waitForTimeout(2000); // Wait 2 seconds so you can see

  // Verify we're on documents tab
  await expect(page.getByText(/Upload Documents/i)).toBeVisible({ timeout: 5000 });

  console.log('📍 Step 2: Uploading PDF document...');

  // Upload a test document from project samples
  const fileInput = page.locator('input[type="file"]');
  const testFilePath = path.join(__dirname, '../fixtures/sample-policy.pdf');

  await fileInput.setInputFiles(testFilePath);

  // Wait for upload to complete
  console.log('⏳ Uploading and processing PDF...');

  // Wait for document to appear in the list (more reliable than waiting for progress text)
  await expect(page.locator('text=sample-policy.pdf').first()).toBeVisible({ timeout: 30000 });

  console.log('✅ PDF uploaded successfully!');

  console.log('📍 Step 3: Switching to Chat tab...');

  // Switch to Chat tab
  const chatTab = page.locator('button:has-text("💬 Chat")');
  await chatTab.click();
  await page.waitForTimeout(2000);

  // Verify we're on chat
  await expect(page.getByText(/Ask Your Documents/i)).toBeVisible();

  console.log('📍 Step 4: Typing question...');

  // Find the question input
  const questionInput = page.locator('input[type="text"][placeholder*="question" i]');

  // Type the question slowly (character by character)
  await questionInput.click();
  await page.waitForTimeout(500);

  const question = 'What is the vacation policy?';
  await questionInput.type(question, { delay: 100 }); // Type with 100ms delay between chars

  await page.waitForTimeout(1000);

  console.log('📍 Step 5: Sending question to AI...');

  // Click send button
  const sendButton = page.getByRole('button', { name: /Send/i });
  await sendButton.click();

  // User should see the question echoed back (user message in purple bubble)
  await expect(page.getByText(question)).toBeVisible({ timeout: 5000 });

  console.log('⏳ Waiting for AI response from Ollama (this may take 10-30 seconds)...');

  // Wait for answer from Ollama (can take time)
  await page.waitForTimeout(3000);

  // Check for assistant response (gray background)
  const responseArea = page.locator('.bg-gray-100').first();
  await expect(responseArea).toBeVisible({ timeout: 45000 }); // Ollama can be slow

  console.log('✅ Got AI response!');

  console.log('📍 Step 6: Checking for source citations...');

  // Check if there are sources
  const sourcesText = page.getByText(/Sources:/i);
  if (await sourcesText.isVisible()) {
    console.log('✅ Sources/citations found!');

    // Should see document icon and page number
    await expect(page.locator('text=📄').first()).toBeVisible();
    await expect(page.locator('text=/page \\d+/i').first()).toBeVisible();
  } else {
    console.log('ℹ️  No sources section (may not have matched document)');
  }

  // Wait 3 seconds at the end so you can see the final result
  console.log('🎉 Demo complete! Waiting 3 seconds...');
  await page.waitForTimeout(3000);
});
