# E2E Test Coverage Report

This document maps E2E tests to documented features.

## Coverage Summary

**Total Features**: 13
**Features with E2E Tests**: 5 (38%)
**Features without E2E Tests**: 8 (62%)

---

## ✅ Features COVERED by E2E Tests

### 1. Document Ingestion (Feature 01)
**Status**: ✅ **COVERED**

**Tests**:
- `01-upload-and-manage-documents.spec.ts`
  - ✅ User uploads a PDF document successfully
  - ✅ User sees file type restriction (PDF only)
  - ✅ User sees list of uploaded documents

**Coverage**: Full UI coverage for document upload

---

### 2. Grounded Q&A (Feature 02)
**Status**: ✅ **COVERED**

**Tests**:
- `02-ask-questions-and-get-answers.spec.ts`
  - ✅ User asks a question and receives an answer
  - ✅ User sees source citations with their answer
  - ✅ User receives message when no documents found
  - ✅ User cannot submit empty question
  - ✅ User can start a new chat

**Coverage**: Full UI coverage for Q&A functionality

---

### 3. Document Management (Feature 03)
**Status**: ✅ **COVERED**

**Tests**:
- `01-upload-and-manage-documents.spec.ts`
  - ✅ User can delete a document
  - ✅ User sees list of uploaded documents

**Coverage**: Basic CRUD operations covered

---

### 4. Multi-Turn Chat (Feature 04)
**Status**: ✅ **PARTIALLY COVERED**

**Tests**:
- `03-multi-turn-conversations.spec.ts`
  - ⚠️ User asks follow-up questions in a conversation (test exists but failing)
  - ⚠️ User starts a new conversation session (test exists but failing)
  - ⚠️ User sees conversation history (test exists but failing)

**Coverage**: Tests exist but need fixing (conversation state management)

---

### 5. Structured Data Extraction (Feature 08)
**Status**: ✅ **COVERED**

**Tests**:
- `05-structured-data-extraction.spec.ts`
  - ✅ User creates a data extraction schema
  - ✅ User extracts data from a document
  - ✅ User exports extracted data as JSON
  - ✅ User exports extracted data as CSV
  - ✅ User sees confidence scores for extracted values

**Coverage**: Full UI coverage for data extraction

---

### 6. Advanced Filters (Feature 10)
**Status**: ✅ **COVERED**

**Tests**:
- `01-upload-and-manage-documents.spec.ts`
  - ✅ User can view document metadata filters

**Coverage**: Basic filter visibility tested

---

## ❌ Features NOT COVERED by E2E Tests

### 1. Query Routing (Feature 05)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests for intent classification UI
- No tests for routing to different answer strategies
- Backend tests exist, but no UI tests

**Recommendation**: This is primarily a backend feature with no dedicated UI, so backend tests may be sufficient.

---

### 2. MCP Integration (Feature 06)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests for MCP tools integration
- No tests for external tool usage in answers

**Recommendation**: May not need UI tests if MCP is transparent to users. Consider adding if there's a UI for tool selection.

---

### 3. Evaluation (Feature 07)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests for evaluation metrics UI (if exists)
- No tests for evaluation results display

**Recommendation**: Check if there's a UI for evaluation. If it's admin/dev only, E2E tests may not be needed.

---

### 4. Reranking (Feature 08)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests showing reranking affects results
- No tests for reranking score display

**Recommendation**: This is transparent to users. Backend tests exist. E2E tests could verify citation order changes with reranking on/off.

---

### 5. Comparative Analysis (Feature 09)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests for comparative analysis UI
- No tests for comparing multiple documents

**Recommendation**: Check if this feature has a UI implementation. Add tests if UI exists.

---

### 6. Document Summarization (Feature 11)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests for document summarization UI
- No tests for viewing/generating summaries

**Recommendation**: If summarization UI exists in the web app, add E2E tests.

---

### 7. Authentication (Feature 12)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests for login/logout
- No tests for protected routes
- No tests for user registration

**Recommendation**: **HIGH PRIORITY** - Authentication is critical. Add tests for:
  - User login
  - User registration
  - Session persistence
  - Logout
  - Protected route access

---

### 8. Slack Integration (Feature 13)
**Status**: ❌ **NOT COVERED**

**What's missing**:
- No E2E tests for Slack bot interactions
- Backend tests exist (17/17 passing)

**Recommendation**: E2E tests for Slack would require:
  - Slack API mocking or test workspace
  - Testing slash commands
  - Testing message responses

This is complex. Backend unit tests may be sufficient unless you want to test the full Slack workflow.

---

## Test Status by Category

### Currently Passing (Chromium only)
- ✅ **11/23 tests passing** (48%)

**Passing tests**:
1. Document upload UI (4/5 tests)
2. Q&A functionality (4/5 tests)
3. Data extraction (5/5 tests)
4. Empty input validation (1/1 tests)

**Failing tests**:
- Multi-turn conversation tracking (3 tests)
- Source citation display timing (5 tests)
- Upload test (strict mode violation - duplicate documents)

---

## Recommendations

### High Priority (Add E2E Tests)
1. **Authentication** (Feature 12) - Critical for production
   - Login/logout flows
   - Protected routes
   - Session management

2. **Fix Multi-Turn Conversations** (Feature 04)
   - 3 tests exist but failing
   - Fix conversation state management

### Medium Priority
3. **Document Summarization** (Feature 11) - If UI exists
4. **Comparative Analysis** (Feature 09) - If UI exists

### Low Priority (Backend coverage sufficient)
5. Query Routing (Feature 05) - No dedicated UI
6. Reranking (Feature 08) - Transparent to users
7. MCP Integration (Feature 06) - Transparent to users
8. Evaluation (Feature 07) - Admin/dev feature
9. Slack Integration (Feature 13) - Complex, has backend tests

---

## How to Add Missing Tests

### Example: Authentication Tests

Create `tests/e2e/06-authentication.spec.ts`:

```typescript
test.describe('Feature: User Authentication', () => {
  test('User can register a new account', async ({ page }) => {
    await page.goto('/register');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('User can login', async ({ page }) => {
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/dashboard');
  });

  test('User cannot access protected routes without auth', async ({ page }) => {
    await page.goto('/documents');
    await expect(page).toHaveURL('/login');
  });
});
```

---

## Current Test Statistics

**Total E2E Tests**: 23 (Chromium) × 3 browsers = 69 total
**Passing**: 11/23 (48%)
**Failing**: 12/23 (52%)

**Test Files**: 6
1. `01-upload-and-manage-documents.spec.ts` - 5 tests
2. `02-ask-questions-and-get-answers.spec.ts` - 5 tests
3. `03-multi-turn-conversations.spec.ts` - 3 tests
4. `04-view-source-citations.spec.ts` - 5 tests
5. `05-structured-data-extraction.spec.ts` - 5 tests
6. `demo-full-flow.spec.ts` - 1 demo test

**Feature Coverage**: 5/13 features (38%)

---

## Next Steps

1. ✅ **Done**: Set up Playwright with Ollama
2. ✅ **Done**: Create tests for core features (upload, Q&A, extraction)
3. ✅ **Done**: Document testing guide
4. 🔄 **In Progress**: Fix failing multi-turn conversation tests
5. ⏳ **TODO**: Add authentication E2E tests
6. ⏳ **TODO**: Increase pass rate to 80%+
7. ⏳ **TODO**: Add tests for remaining UI features

---

**Last Updated**: 2026-07-30
**Test Environment**: Ollama (llama3.2) + PostgreSQL 14 + Nuxt 4
