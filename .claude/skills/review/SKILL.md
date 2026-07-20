---
description: "Comprehensive code review before committing changes"
---

# Code Review Skill

Perform a thorough code review of uncommitted changes for the RAG system.

## Steps

1. **Examine changes**:
   ```bash
   git status
   git diff
   git diff --staged
   ```

2. **Security review** (CRITICAL for RAG systems):
   - ❌ **Prompt injection**: Check user input sanitization in `app/api/questions.py`
   - ❌ **SQL injection**: Verify all queries use SQLAlchemy ORM, no raw SQL
   - ❌ **Path traversal**: Check file upload paths in `app/ingest/`
   - ❌ **API key exposure**: Ensure no keys in code, only in `.env`
   - ❌ **XSS**: Validate any web UI rendering of user content
   - ❌ **Sensitive data**: No `.env` files, API keys, or credentials
   - ✅ **Input validation**: All Pydantic models have proper constraints

3. **RAG-specific checks**:
   - **Grounding**: Answers only from retrieved chunks, no hallucination
   - **Citations**: All answers include proper source tracking
   - **Router logic**: Intent classification works correctly (answer/clarify/refuse)
   - **Chunking**: Verify chunk size and overlap are appropriate
   - **Embeddings**: Check embedding model is consistent
   - **Vector search**: Verify similarity thresholds are reasonable

4. **Code quality**:
   - **Type hints**: All functions have proper type annotations
   - **Error handling**: Try-except blocks for external calls (LLM, DB)
   - **Logging**: Appropriate log levels (DEBUG, INFO, WARNING, ERROR)
   - **Docstrings**: Public functions have clear documentation
   - **Naming**: Clear, descriptive variable/function names

5. **Testing**:
   - New features have corresponding tests in `app/tests/`
   - Integration tests for API endpoints
   - Unit tests for core logic (router, retriever, LLM)
   - Test coverage doesn't decrease

6. **Documentation**:
   - API changes reflected in OpenAPI/Swagger docs
   - README updated if setup changed
   - Examples in `docs/testing/api-results/` are current

7. **Performance**:
   - No N+1 queries in database operations
   - Appropriate use of async/await
   - Vector search limits set (top_k)
   - No blocking operations in async functions

8. **Generate commit message**:
   - Follow conventional commits format
   - Include co-authorship for Claude Code
   - Reference related features/issues

## RAG System Security Checklist

- [ ] User questions sanitized before LLM
- [ ] Document uploads validated (file type, size)
- [ ] No system prompts exposed in API responses
- [ ] LLM responses don't leak internal context
- [ ] Rate limiting considered for API endpoints
- [ ] Authentication/authorization properly implemented

## Best Practices

- ✅ Run tests before reviewing: `python -m pytest`
- ✅ Check linting: `ruff check app/`
- ✅ Verify no secrets with: `git diff | grep -i "api_key\|password\|secret"`
- ✅ Read diffs carefully, don't just approve
- ❌ Never commit broken code "to fix later"
- ❌ Don't skip security checks "because it's internal"

## Commit Message Format

```
<type>: <short description>

<detailed description>

Changes:
- Point 1
- Point 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`
