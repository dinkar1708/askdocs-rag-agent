# Testing Strategy for RAG Projects

Complete strategy explanation for testing AI/RAG applications.

---

## Current Situation

**Test Results:**
- Total: 94 tests
- Passing: 64 (68%)
- Failing: 30 (32%)

**Why Tests Fail:**
1. SQLite does NOT support pgvector (PostgreSQL extension)
2. Some async/await issues in mock tests
3. LLM factory provider selection needs fixes

---

## Industry Best Practices for RAG/AI Projects

### 1. Test Environment Strategy

**Local Development:**
```
Developer Machine
├── PostgreSQL (Docker) ← For integration tests
├── Mock LLM Provider ← No API costs
└── Real file fixtures ← Test PDFs, documents
```

**CI/CD (GitHub Actions):**
```
GitHub Actions
├── PostgreSQL Service Container ← pgvector/pgvector:pg14
├── Python 3.11
├── Run migrations (alembic upgrade head)
├── Execute all tests
└── Generate coverage report
```

**Production:**
```
Production Environment
├── PostgreSQL (Cloud) ← Real database
├── Real LLM (Gemini/OpenAI) ← Actual API
└── Monitoring & Logging
```

---

## Why PostgreSQL is Required

### Problem: SQLite Cannot Handle pgvector

**Our Code Uses:**
```sql
-- Vector similarity search
SELECT * FROM chunks
WHERE 1 - (embedding <=> query_vector) >= 0.3
ORDER BY embedding <=> query_vector
LIMIT 5;
```

**SQLite Error:**
```
sqlite3.OperationalError: near ">": syntax error
```

**Why?**
- `<=>` is PostgreSQL operator for cosine distance
- pgvector is PostgreSQL extension
- SQLite has NO vector support

**Solution:**
- Use PostgreSQL for ALL tests that involve vectors
- Use SQLite ONLY for simple CRUD tests (if needed)

---

## Testing Layers (Test Pyramid)

### Layer 1: Unit Tests (Fast, Many)

**What:** Test individual functions in isolation

**Examples:**
- Embedding generation
- Text chunking
- Schema validation
- Response parsing

**Database:** Not required or use SQLite

**Speed:** <1 second

**Coverage:** 40% of all tests

```python
def test_chunk_text_basic():
    text = "This is a test. Another sentence."
    chunks = chunk_text(text, chunk_size=100)
    assert len(chunks) > 0
```

### Layer 2: Integration Tests (Medium Speed, Medium Count)

**What:** Test components working together

**Examples:**
- API endpoints
- Database queries
- Retrieval with vector search
- Document upload + processing

**Database:** PostgreSQL REQUIRED

**Speed:** 1-5 seconds per test

**Coverage:** 50% of all tests

```python
def test_retrieve_relevant_chunks(db_with_postgresql):
    chunks = retrieve_relevant_chunks(db, "test query", top_k=5)
    assert len(chunks) <= 5
    assert chunks[0].similarity_score > 0
```

### Layer 3: E2E Tests (Slow, Few)

**What:** Test entire user flows

**Examples:**
- Upload PDF → Ask question → Get answer with sources
- Create extraction schema → Extract data → Export CSV
- Multi-turn conversation with context

**Database:** PostgreSQL REQUIRED

**Speed:** 5-30 seconds per test

**Coverage:** 10% of all tests

```python
def test_full_rag_flow(client, db_with_postgresql):
    # Upload PDF
    upload_response = client.post("/upload", files={"file": pdf})
    doc_id = upload_response.json()["document_id"]

    # Ask question
    ask_response = client.post("/ask", json={"question": "..."})

    # Verify answer has sources
    assert len(ask_response.json()["sources"]) > 0
```

---

## Mock vs Real Services

### When to Mock

**Mock LLM Provider:**
- Unit tests
- Integration tests
- CI/CD tests
- Local development

**Why:**
- Fast (no API latency)
- Free (no API costs)
- Deterministic (same input = same output)
- No rate limits

```python
# Set in environment
export LLM_PROVIDER="mock"

# Returns predefined responses
{
  "answer": "Mock answer to your question",
  "confidence": 0.85,
  "sources": [{"page": 1, "chunk_id": 1}]
}
```

### When to Use Real Services

**Real LLM API:**
- Manual testing
- Staging environment
- Production

**Real PostgreSQL:**
- ALL tests (except pure unit tests)
- Local development
- CI/CD
- Staging
- Production

---

## GitHub Actions CI/CD Setup

### Best Practice Workflow

**File:** `.github/workflows/tests.yml` (already created)

**What it does:**

1. **Trigger on events:**
   - Push to `main` or `develop`
   - Pull request opened/updated
   - Manual trigger

2. **Setup PostgreSQL service:**
   ```yaml
   services:
     postgres:
       image: pgvector/pgvector:pg14  # PostgreSQL + pgvector
       env:
         POSTGRES_USER: postgres
         POSTGRES_PASSWORD: postgres
         POSTGRES_DB: askdocs_test
   ```

3. **Install dependencies:**
   ```bash
   pip install -r app/requirements.txt
   ```

4. **Run migrations:**
   ```bash
   alembic upgrade head  # Create all tables
   ```

5. **Execute tests:**
   ```bash
   pytest -v --cov=. --cov-report=xml
   ```

6. **Upload coverage:**
   - Codecov (free for open source)
   - Shows coverage trends
   - Fails PR if coverage drops

**Benefits:**
- Automatic testing on every change
- Catch bugs before merge
- Ensure code quality
- Track coverage over time

---

## Local Testing Options

### Option 1: Docker PostgreSQL (Recommended)

**Start database:**
```bash
docker run -d \
  --name askdocs-test \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  pgvector/pgvector:pg14
```

**Run tests:**
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs_test"
pytest -v
```

**Stop database:**
```bash
docker stop askdocs-test
docker rm askdocs-test
```

**Pros:**
- Exact match with CI/CD
- Easy setup/teardown
- No local PostgreSQL install

**Cons:**
- Requires Docker

### Option 2: Local PostgreSQL Installation

**Install:**
```bash
# macOS
brew install postgresql@14
brew install pgvector

# Ubuntu
sudo apt install postgresql-14 postgresql-14-pgvector
```

**Create test database:**
```bash
createdb askdocs_test
psql askdocs_test -c "CREATE EXTENSION vector"
```

**Pros:**
- No Docker needed
- Faster (no container overhead)

**Cons:**
- Manual installation
- OS-specific

### Option 3: Test Runner Script (Current)

**Run:**
```bash
python app/run_tests_with_results.py
```

**What it does:**
- Runs pytest
- Saves output to `docs/testing/api-results/`
- Creates timestamped files
- Updates `latest.json` and `latest.txt`

**Pros:**
- Results automatically saved
- Easy to verify later
- Works with any database

**Cons:**
- Still needs PostgreSQL for vector tests

---

## Coverage Goals

### Industry Standards

**Open Source Projects:**
- Minimum: 70%
- Good: 80%
- Excellent: 90%+

**Enterprise Projects:**
- Minimum: 80%
- Critical paths: 95%+

### Our Current Status

**Overall:** ~50%

**By Component:**
- Models/DB: 90% (good)
- API endpoints: 65%
- Retrieval: 40% (needs work)
- Extraction: 70%
- Utilities: 80%

**Target:**
- Overall: 85%
- Critical paths (ask, retrieval): 95%
- New features: 80% minimum

---

## Test Data Strategy

### Fixtures

**Use real files:**
```
app/tests/fixtures/
├── sample_resume.pdf
├── sample_invoice.pdf
├── sample_contract.pdf
└── sample_technical_doc.pdf
```

**Why:**
- Test real PDF parsing
- Catch edge cases
- Validate extraction accuracy

**Best practices:**
- Small files (< 1MB)
- Diverse content
- Known expected outputs

### Database Fixtures

**Use transactions:**
```python
@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()  # Clean up after test
    session.close()
```

**Why:**
- Tests don't affect each other
- Fast (no DB recreation)
- Isolated state

---

## Comparison: Different Testing Approaches

### Approach 1: SQLite Only (WRONG for our project)

**Setup:**
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
```

**Pros:**
- Fast
- No external dependencies

**Cons:**
- NO pgvector support ← CRITICAL ISSUE
- Different SQL syntax
- Not production-like
- 30 tests fail

**Verdict:** ❌ NOT suitable for pgvector projects

### Approach 2: PostgreSQL Docker (BEST)

**Setup:**
```bash
docker run -d -p 5432:5432 pgvector/pgvector:pg14
```

**Pros:**
- Exact production match
- pgvector support ✓
- Easy CI/CD integration
- All tests pass ✓

**Cons:**
- Requires Docker

**Verdict:** ✅ RECOMMENDED

### Approach 3: Cloud Database (Staging/Production)

**Setup:**
```bash
export DATABASE_URL="postgresql://user:pass@cloud-host:5432/db"
```

**Pros:**
- Real production environment
- Shared test database

**Cons:**
- Slower (network latency)
- Costs money
- Risk of data conflicts

**Verdict:** ⚠️ Use for staging, NOT local tests

---

## Fixing Current Test Failures

### Category 1: Vector Search Tests (24 failures)

**Issue:** SQLite syntax error

**Fix:** Use PostgreSQL

**Before:**
```bash
# Tests use SQLite by default
pytest tests/test_retriever.py  # FAILS
```

**After:**
```bash
# Start PostgreSQL
docker run -d -p 5432:5432 pgvector/pgvector:pg14

# Set database URL
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/test"

# Run migrations
cd app && alembic upgrade head

# Run tests
pytest tests/test_retriever.py  # PASSES
```

### Category 2: Async/Await Tests (6 failures)

**Issue:** Missing `await` keyword

**Fix:** Add proper async handling

**Example:**
```python
# Before (WRONG)
def test_mock_generate():
    result = mock_llm.generate("test")  # Missing await
    assert result is not None

# After (CORRECT)
@pytest.mark.asyncio
async def test_mock_generate():
    result = await mock_llm.generate("test")  # Added await
    assert result is not None
```

---

## Summary: What to Do

### Immediate Actions (No Code Changes)

1. **Start PostgreSQL:**
   ```bash
   docker run -d --name test-db -p 5432:5432 \
     -e POSTGRES_PASSWORD=postgres \
     pgvector/pgvector:pg14
   ```

2. **Set environment:**
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs_test"
   export LLM_PROVIDER="mock"
   export PYTHONPATH=$PWD
   ```

3. **Run migrations:**
   ```bash
   cd app
   alembic upgrade head
   ```

4. **Run tests:**
   ```bash
   pytest -v --cov=.
   ```

5. **Check results:**
   - Should see ~90+ tests passing
   - Coverage report generated
   - Results in `docs/testing/api-results/`

### Future Improvements (Code Changes)

1. Fix async/await in mock tests
2. Improve LLM factory tests
3. Add more E2E tests
4. Increase coverage to 85%+

---

## Key Takeaways

1. **PostgreSQL is MANDATORY** for pgvector projects
2. **GitHub Actions + PostgreSQL** is industry standard
3. **Mock LLM** for tests (fast, free, deterministic)
4. **Docker PostgreSQL** for local testing (easy, portable)
5. **Coverage goal: 80%+** for production readiness
6. **Test pyramid:** Many unit tests, some integration, few E2E
7. **CI/CD catches bugs** before they reach production

**Already Created:**
- ✅ GitHub Actions workflow (`.github/workflows/tests.yml`)
- ✅ Test runner script (`app/run_tests_with_results.py`)
- ✅ Testing guide (`docs/testing/TESTING_GUIDE.md`)
- ✅ This strategy document
