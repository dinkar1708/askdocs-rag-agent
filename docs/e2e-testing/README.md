# E2E Testing Documentation

End-to-end testing documentation for the AskDocs RAG Agent web UI.

## Documents in this Folder

1. **[running-tests.md](./running-tests.md)** - Complete guide to running E2E tests
   - LLM provider options (Ollama, Mock, Gemini)
   - Database setup (PostgreSQL + pgvector)
   - Quick start commands
   - Troubleshooting guide

2. **[coverage-report.md](./coverage-report.md)** - Test coverage analysis
   - Features covered by E2E tests
   - Features not covered
   - Recommendations for new tests
   - Current test statistics

## Quick Start

### Recommended: Run with Ollama (Local LLM)

```bash
cd web-ui
./run-e2e-with-ollama.sh
```

This command will:
- Check Ollama is installed with llama3.2 model
- Start PostgreSQL (Docker)
- Run database migrations
- Start backend API with Ollama provider
- Upload test document
- Run all Playwright E2E tests
- Show results

### View Tests in Browser (Interactive)

```bash
cd web-ui
npx playwright test --ui --project=chromium
```

### Run Single Test (Visible Browser)

```bash
cd web-ui
npx playwright test --headed --project=chromium --workers=1 --grep="User asks a question"
```

## Test Files Location

All E2E test files are in: `web-ui/tests/e2e/`

- `01-upload-and-manage-documents.spec.ts`
- `02-ask-questions-and-get-answers.spec.ts`
- `03-multi-turn-conversations.spec.ts`
- `04-view-source-citations.spec.ts`
- `05-structured-data-extraction.spec.ts`
- `demo-full-flow.spec.ts` (Complete demo test)

## Current Status

- **11/23 tests passing** with Ollama (llama3.2)
- **5/13 features covered**
- Recommended LLM provider: **Ollama** (local, free, realistic)

## Learn More

See [running-tests.md](./running-tests.md) for detailed setup instructions and [coverage-report.md](./coverage-report.md) for feature coverage analysis.
