# E2E Tests

End-to-end tests for the AskDocs web UI using Playwright.

## Quick Start

```bash
# Run tests with Ollama (recommended)
./run-e2e-with-ollama.sh

# Or with mock provider (fast)
./run-e2e-tests.sh
```

## Structure

```
tests/e2e/              # Test specs (feature-based)
tests/fixtures/         # Test PDFs
playwright.config.ts    # Playwright configuration
```

## Documentation

**For complete details, see:** [`docs/e2e-testing/`](../../docs/e2e-testing/)

- **[Running Tests](../../docs/e2e-testing/running-tests.md)** - Setup, commands, troubleshooting
- **[Coverage Report](../../docs/e2e-testing/coverage-report.md)** - Test status, feature coverage
- **[Test Fixtures](./fixtures/README.md)** - Sample test files
