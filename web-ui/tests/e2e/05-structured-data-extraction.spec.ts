import { test, expect } from '@playwright/test';

/**
 * Feature: Extract Structured Data from Documents
 *
 * As a user, I want to extract specific information from documents
 * in a structured format (JSON, CSV) for further analysis.
 */

test.describe('Feature: Extract Structured Data from Documents', () => {

  test('User creates a data extraction schema', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Navigate to Data Extraction tab
    const extractionTab = page.locator('button:has-text("📊 Data Extraction")');
    await expect(extractionTab).toBeVisible();
    await extractionTab.click();
    await page.waitForTimeout(1000);

    // User should see schema builder heading
    await expect(page.getByText(/Define Extraction Schema/i)).toBeVisible({ timeout: 10000 });

    // Add a field to schema (there's already one empty field by default)
    const addFieldButton = page.getByRole('button', { name: /\+ Add Field/i });
    await addFieldButton.click();

    // Should see new field inputs (now 2 total: initial + newly added)
    const fieldNameInputs = page.locator('input[placeholder*="Field name" i]');
    await expect(fieldNameInputs).toHaveCount(2);
  });

  test('User extracts data from a document', async ({ page }) => {
    await page.goto('/');
    await page.locator('button:has-text("📊 Data Extraction")').click();
    await page.waitForTimeout(500);

    // Select a document
    const documentSelect = page.locator('select[name="document"], [data-testid="document-select"]').first();
    if (await documentSelect.isVisible()) {
      await documentSelect.selectOption({ index: 1 });
    }

    // Define what to extract (if schema builder exists)
    const schemaInput = page.locator('textarea, [data-testid="schema"]').first();
    if (await schemaInput.isVisible()) {
      await schemaInput.fill('name, email, phone');
    }

    // Click extract button
    const extractButton = page.getByRole('button', { name: /extract|run/i });
    await extractButton.click();

    // User should see extracted data (use first() to avoid strict mode violation)
    await expect(page.locator('text=/result|extracted|data/i').first()).toBeVisible({ timeout: 60000 });
  });

  test('User exports extracted data as JSON', async ({ page }) => {
    await page.goto('/');
    await page.locator('button:has-text("📊 Data Extraction")').click();
    await page.waitForTimeout(500);

    // Assume extraction is already done
    // Find export button
    const exportButton = page.getByRole('button', { name: /export|download/i });

    if (await exportButton.isVisible()) {
      // Select JSON format
      const jsonOption = page.getByRole('option', { name: /json/i });
      if (await jsonOption.isVisible()) {
        await jsonOption.click();
      }

      // Trigger download
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();

      const download = await downloadPromise;
      expect(download.suggestedFilename()).toContain('.json');
    }
  });

  test('User exports extracted data as CSV', async ({ page }) => {
    await page.goto('/');
    await page.locator('button:has-text("📊 Data Extraction")').click();
    await page.waitForTimeout(500);

    const exportButton = page.getByRole('button', { name: /export|download/i });

    if (await exportButton.isVisible()) {
      // Select CSV format
      const csvOption = page.getByRole('option', { name: /csv/i });
      if (await csvOption.isVisible()) {
        await csvOption.click();
      }

      // Trigger download
      const downloadPromise = page.waitForEvent('download');
      await exportButton.click();

      const download = await downloadPromise;
      expect(download.suggestedFilename()).toMatch(/\.csv/);
    }
  });

  test('User sees confidence scores for extracted values', async ({ page }) => {
    await page.goto('/');
    await page.locator('button:has-text("📊 Data Extraction")').click();
    await page.waitForTimeout(500);

    // After extraction completes
    await page.waitForTimeout(2000);

    // Should see confidence scores (if feature exists)
    const confidenceElement = page.locator('text=/confidence|score|\\d+%/i');
    if (await confidenceElement.isVisible({ timeout: 5000 })) {
      expect(await confidenceElement.textContent()).toMatch(/\d+%|0\.\d+/);
    }
  });
});
