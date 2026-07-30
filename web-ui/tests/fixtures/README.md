# Test Fixtures

This directory contains test files used by Playwright E2E tests.

## Files

- `sample-policy.pdf` - Sample company policy document for testing upload and Q&A features

## Adding Test Files

Place test documents here that will be used by E2E tests:

1. **PDFs for upload testing** - Small PDFs (1-5 pages) with known content
2. **Expected outputs** - JSON/CSV files for extraction validation
3. **Mock responses** - API response fixtures for offline testing

## Usage in Tests

```typescript
import { test } from '@playwright/test';

test('upload document', async ({ page }) => {
  await page.setInputFiles('input[type="file"]', 'tests/fixtures/sample-policy.pdf');
});
```

## Best Practices

- Keep files small (< 1MB) for fast tests
- Use descriptive filenames
- Document what each fixture contains
- Don't commit sensitive data
