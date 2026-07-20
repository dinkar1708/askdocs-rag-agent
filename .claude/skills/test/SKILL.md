---
description: "Run pytest tests with coverage reporting for the RAG system"
---

# Test Runner Skill

Run the complete test suite for the askdocs RAG agent project.

## Steps

1. **Check test environment**:
   - Verify you're in the project root
   - Confirm pytest is available

2. **Run tests with coverage**:
   ```bash
   python -m pytest --cov=app --cov-report=term-missing -v
   ```

3. **Analyze results**:
   - Report pass/fail status with file paths and line numbers
   - Show coverage summary (aim for >80%)
   - Identify any missing test coverage areas

4. **If tests fail**:
   - Read the failure traceback carefully
   - Identify the root cause
   - Suggest fixes with specific file paths
   - Check if it's a test issue or code issue

5. **Auto-generated API docs**:
   - Tests automatically generate API examples in `docs/testing/api-results/`
   - Verify these files are created/updated

## Test Categories

- **Unit tests**: `test_llm_*.py`, `test_embeddings.py`
- **Integration tests**: `test_ask_endpoint.py`, `test_router_integration.py`
- **Router tests**: `test_router.py`
- **Session tests**: `test_sessions.py`

## Best Practices

- ✅ All tests must pass before committing
- ✅ Maintain >80% code coverage
- ✅ Check that API examples are generated
- ✅ Run full test suite, not just specific tests
- ❌ Don't commit failing tests
- ❌ Don't skip tests to make CI pass

## Common Issues

- **Database errors**: Ensure PostgreSQL is running or use SQLite for tests
- **Import errors**: Check virtual environment is activated
- **API key errors**: Mock LLM provider should work without keys
