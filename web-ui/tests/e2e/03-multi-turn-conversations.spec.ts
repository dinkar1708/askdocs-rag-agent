import { test, expect } from '@playwright/test';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Feature: Multi-Turn Conversations
 *
 * As a user, I want to have follow-up conversations
 * where the system remembers context from previous questions.
 */

test.describe('Feature: Multi-Turn Conversations', () => {

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

  test('User asks follow-up questions in a conversation', async ({ page }) => {
    // First question
    const questionInput = page.locator('input[type="text"], textarea').first();
    await questionInput.fill('What is the vacation policy?');

    let submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    // Wait for first answer to appear
    await expect(page.locator('.bg-gray-100').first()).toBeVisible({ timeout: 60000 });

    // Follow-up question (using pronoun "it" to refer to previous context)
    await questionInput.fill('Can I carry it over to next year?');
    submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    // User should see both questions in conversation history
    await expect(page.getByText('What is the vacation policy?')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Can I carry it over to next year?')).toBeVisible({ timeout: 5000 });

    // Wait for second answer (should have at least 2 assistant messages)
    await expect(page.locator('.bg-gray-100').nth(1)).toBeVisible({ timeout: 60000 });
  });

  test('User starts a new conversation session', async ({ page }) => {
    // Ask initial question
    const questionInput = page.locator('input[type="text"], textarea').first();
    await questionInput.fill('What are the benefits?');

    const submitButton = page.getByRole('button', { name: /ask|send/i });
    await submitButton.click();

    // Wait for answer
    await page.waitForTimeout(8000);

    // Click "New Conversation" or similar button
    const newConversationButton = page.getByRole('button', {
      name: /new conversation|new chat|clear|start over/i
    });

    await expect(newConversationButton).toBeVisible({ timeout: 5000 });
    await newConversationButton.click();

    // Previous question should be cleared
    await expect(page.getByText('What are the benefits?')).not.toBeVisible({ timeout: 5000 });
  });

  test('User sees conversation history', async ({ page }) => {
    // Ask multiple questions
    const questionInput = page.locator('input[type="text"], textarea').first();
    const questions = [
      'What is vacation?',
      'Sick days?'
    ];

    for (let i = 0; i < questions.length; i++) {
      const question = questions[i];
      await questionInput.fill(question);
      const submitButton = page.getByRole('button', { name: /ask|send/i });
      await submitButton.click();

      // Wait for the question to appear (faster check)
      await expect(page.getByText(question)).toBeVisible({ timeout: 5000 });

      // Wait for AI response (look for gray background)
      await expect(page.locator('.bg-gray-100').nth(i)).toBeVisible({ timeout: 60000 });
    }

    // All questions should be visible in chat history
    for (const question of questions) {
      await expect(page.getByText(question)).toBeVisible({ timeout: 5000 });
    }
  });
});
