# Test Provider Strategy

Official testing strategy for different environments.

---

## Provider Usage by Environment

### Local Development (Your Machine)

**Option 1: Mock Provider (Recommended)**
```bash
export LLM_PROVIDER="mock"
pytest -v
```
- Fast (all tests in ~30 seconds)
- Free (no costs)
- All 94 tests pass

**Option 2: Ollama Provider (Optional)**
```bash
# Start Ollama first
ollama serve

# Run tests
export LLM_PROVIDER="ollama"
export OLLAMA_MODEL="llama3.2"
pytest -v
```
- Slower (all tests in ~7 minutes)
- Free (local model)
- All 94 tests pass
- Tests real LLM behavior

**Use mock for daily work, ollama for final verification**

---

### GitHub Actions (CI/CD on merge to main)

**Always Use: Mock Provider**
```yaml
env:
  LLM_PROVIDER: mock
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/askdocs_test
```
- Fast (tests complete in ~2 minutes)
- Free (no API costs)
- All 94 tests pass
- Deterministic results

**Why not Ollama?**
- Would take too long (~7 minutes)
- GitHub Actions charges by minute for private repos
- Mock is sufficient for CI/CD

---

### Production (Real Users)

**Use: Real LLM Provider**

**Option 1: Ollama (Free, Private)**
```bash
export LLM_PROVIDER="ollama"
export OLLAMA_MODEL="llama3.2"
```
- Zero cost
- Runs locally
- Full data privacy
- Good quality responses

**Option 2: Gemini (Paid, Best Quality)**
```bash
export LLM_PROVIDER="gemini"
export GEMINI_API_KEY="your-real-api-key"
```
- Costs per request
- Best quality responses
- Requires internet
- Rate limits apply

**Never use mock in production!**

---

## Test Passing Requirements

### All Tests MUST Pass With:
- ✅ Mock provider + PostgreSQL
- ✅ Ollama provider + PostgreSQL

### Database Requirements:
- ✅ PostgreSQL with pgvector (required)
- ❌ SQLite (will fail - no pgvector support)

### Provider Requirements:
- ✅ Mock provider (all tests pass)
- ✅ Ollama provider (all tests pass, but slow)
- ⚠️ Gemini provider (not recommended for tests - costs money)

---

## Quick Reference

| Environment | Provider | Database | Speed | Cost |
|-------------|----------|----------|-------|------|
| Local (daily) | Mock | PostgreSQL | Fast (30s) | Free |
| Local (verify) | Ollama | PostgreSQL | Slow (7min) | Free |
| GitHub Actions | Mock | PostgreSQL | Fast (2min) | Free |
| Production | Ollama/Gemini | PostgreSQL | Real-time | Free/Paid |

---

## Configuration Files

### Local: `.env`
```bash
# For daily testing
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/askdocs_test
LLM_PROVIDER=mock

# For verification testing (optional)
# LLM_PROVIDER=ollama
# OLLAMA_MODEL=llama3.2
# OLLAMA_BASE_URL=http://localhost:11434
```

### GitHub Actions: `.github/workflows/tests.yml`
```yaml
env:
  DATABASE_URL: postgresql://postgres:postgres@localhost:5432/askdocs_test
  LLM_PROVIDER: mock  # Always mock for CI/CD
  GEMINI_API_KEY: test-key-not-used
```

### Production: Environment Variables
```bash
# Option 1: Ollama (recommended for privacy/cost)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
DATABASE_URL=postgresql://user:pass@prod-host:5432/askdocs

# Option 2: Gemini (best quality)
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-production-key
DATABASE_URL=postgresql://user:pass@prod-host:5432/askdocs
```

---

## Summary

**The Rule:**
- **Tests**: Use mock provider (fast, free, reliable)
- **Production**: Use real provider (ollama or gemini)

**Never:**
- ❌ Use real LLM for automated tests (slow, expensive)
- ❌ Use mock provider in production (fake responses)
- ❌ Use SQLite for this project (no pgvector)

**Always:**
- ✅ Use PostgreSQL with pgvector
- ✅ Use mock provider for tests
- ✅ Use real provider for production
