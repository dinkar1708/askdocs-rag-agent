import { test, expect } from '@playwright/test';

/**
 * Feature: Ask Questions and Get Grounded Answers
 *
 * As a user, I want to ask questions about my documents
 * and receive accurate, cited answers.
 */

test.describe('Feature: Ask Questions and Get Grounded Answers', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Should be on Chat tab by default
    // Wait for session creation to complete (API call in onMounted hook)
    await page.waitForTimeout(2000);
  });

  test('User asks a question and receives an answer', async ({ page }) => {
    // User should see the chat interface
    await expect(page.getByText(/Ask Your Documents/i)).toBeVisible();

    // Find the question input (it's a text input, not textarea)
    const questionInput = page.locator('input[type="text"][placeholder*="question" i]');
    await questionInput.fill('What is the vacation policy?');

    // Click send button
    const sendButton = page.getByRole('button', { name: /Send/i });
    await sendButton.click();

    // User should see the question echoed back (user message in purple bubble)
    await expect(page.getByText('What is the vacation policy?')).toBeVisible({ timeout: 5000 });

    // Wait for answer (can take time with Ollama)
    // Answer appears in gray bubble (assistant message)
    await page.waitForTimeout(2000);

    // Check for any assistant response (gray background)
    const responseArea = page.locator('.bg-gray-100').first();
    await expect(responseArea).toBeVisible({ timeout: 45000 }); // Ollama can be slow
  });

  test('User sees source citations with their answer', async ({ page }) => {
    // Ask a question
    const questionInput = page.locator('input[type="text"][placeholder*="question" i]');
    await questionInput.fill('How many sick days do employees get?');

    const sendButton = page.getByRole('button', { name: /Send/i });
    await sendButton.click();

    // Wait for answer
    await page.waitForTimeout(3000);

    // User should see "Sources:" section
    await expect(page.getByText(/Sources:/i)).toBeVisible({ timeout: 45000 });

    // Should see document icon and filename (use first() to avoid strict mode violation)
    await expect(page.locator('text=📄').first()).toBeVisible();
    await expect(page.locator('text=/page \\d+/i').first()).toBeVisible();
  });

  test('User receives message when no documents found', async ({ page }) => {
    // Ask a very specific question that won't match
    const questionInput = page.locator('input[type="text"][placeholder*="question" i]');
    await questionInput.fill("What is the cryptocurrency mining policy?");

    const sendButton = page.getByRole('button', { name: /Send/i });
    await sendButton.click();

    // Wait for response
    await page.waitForTimeout(3000);

    // Should get some kind of response (even if no sources)
    const responseArea = page.locator('.bg-gray-100').first();
    await expect(responseArea).toBeVisible({ timeout: 45000 });
  });

  test('User cannot submit empty question', async ({ page }) => {
    const questionInput = page.locator('input[type="text"][placeholder*="question" i]');
    const sendButton = page.getByRole('button', { name: /Send/i });

    // Clear input and ensure it's empty
    await questionInput.fill('');
    await questionInput.blur();

    // Send button should be disabled (empty input disables it)
    const isDisabled = await sendButton.isDisabled();
    expect(isDisabled).toBeTruthy();
  });

  test('User can start a new chat', async ({ page }) => {
    // Ask a question first
    const questionInput = page.locator('input[type="text"][placeholder*="question" i]');
    await questionInput.fill('What are the benefits?');

    const sendButton = page.getByRole('button', { name: /Send/i });
    await sendButton.click();

    // Wait for response
    await page.waitForTimeout(5000);

    // Click "New Chat" button
    const newChatButton = page.getByRole('button', { name: /New Chat/i });
    await expect(newChatButton).toBeVisible({ timeout: 5000 });
    await newChatButton.click();

    // Wait for new session to be created (async operation)
    await page.waitForTimeout(2000);

    // Previous question should be cleared (check that it's no longer visible)
    await expect(page.getByText('What are the benefits?')).not.toBeVisible({ timeout: 5000 });
  });
});
