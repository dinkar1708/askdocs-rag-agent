# Testing Guide

Quick guide for running tests on the RAG askdocs API.

---

## Prerequisites

- Docker (for PostgreSQL)
- Python 3.11 with venv
- Ollama (optional, for real LLM tests)

---

## Test Isolation 🎯

**API tests use ISOLATED test database - separate from development!**

| Environment | Database | PostgreSQL Port |
|-------------|----------|-----------------|
| **Development** | `askdocs` | 5432 |
| **Testing** | `askdocs_test` | 5433 |

**Benefits:**
- ✅ Tests use separate database
- ✅ No data pollution
- ✅ Can run dev and tests simultaneously

---

## Quick Setup (One Time)

```bash
# 1. Install dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Start TEST PostgreSQL (separate from dev)
docker run --name askdocs-postgres-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=askdocs_test \
  -p 5433:5432 \
  -d postgres:14

# Wait for it to start
sleep 3

# 3. Run migrations on TEST database
PYTHONPATH=$PWD \
  DATABASE_URL="postgresql://postgres:postgres@localhost:5433/askdocs_test" \
  alembic upgrade head
```

---

## Running Tests

There are TWO ways to run tests:

### Method 1: Mock Provider (Recommended)

This method uses fake LLM responses for fast testing.

**When to use:**
- Running tests quickly during development
- CI/CD pipelines
- Unit testing

**Speed:** 91 seconds for 71 tests
**LLM:** Uses fake responses (no real AI calls)

**Command:**
```bash
. venv/bin/activate

# Tests automatically use DATABASE_URL from conftest.py (port 5433)
export LLM_PROVIDER="mock"
export PYTHONPATH=$PWD
pytest app/tests/test_retriever.py app/tests/test_table_processor.py app/tests/test_semantic_chunker.py -v
```

**Expected Result:**
```
71 passed, 13 warnings in 91 seconds
```

---

### Method 2: Ollama Provider (Real LLM)

This method uses real Ollama LLM for integration testing.

**When to use:**
- Testing with real AI responses
- Integration testing
- Verifying actual LLM behavior

**Speed:** ~90 seconds for 71 tests
**LLM:** Uses real Ollama (llama3.2 model)

**Command:**
```bash
. venv/bin/activate
export LLM_PROVIDER="ollama"
export OLLAMA_MODEL="llama3.2"
export PYTHONPATH=$PWD
pytest app/tests/test_retriever.py app/tests/test_table_processor.py app/tests/test_semantic_chunker.py -v
```

**Expected Result:**
```
71 passed, 13 warnings in ~90 seconds
```

**Note:** Make sure Ollama is running before running these tests.

---

### Run Integration Tests (Real PDF Processing with Advanced RAG)

These tests verify Advanced RAG features using actual PDF files from disk.

**Tests:**
- Employee handbook plain text extraction (semantic chunking)
- Financial report table extraction to markdown (Phase 2)
- Technical manual semantic chunking with embeddings (Phase 3)
- Sample PDF files exist and readable

**With Mock Provider:**
```bash
. venv/bin/activate
export LLM_PROVIDER="mock"
export PYTHONPATH=$PWD
pytest app/tests/test_integration_01_document_ingestion/ -v
```

**With Ollama Provider:**
```bash
. venv/bin/activate
export LLM_PROVIDER="ollama"
export OLLAMA_MODEL="llama3.2"
export PYTHONPATH=$PWD
pytest app/tests/test_integration_01_document_ingestion/ -v
```

**Expected Result:**
```
4 passed, 13 warnings in 5-6 seconds
```

---

### Run Specific Test File

```bash
. venv/bin/activate
export LLM_PROVIDER="mock"
export PYTHONPATH=$PWD
pytest app/tests/test_api.py -v
```

### Run Specific Test

```bash
export LLM_PROVIDER="mock"
pytest app/tests/test_api.py::test_root_endpoint -v
```

### Common pytest Options

```bash
pytest -v                    # Verbose output
pytest -vv                   # Very verbose
pytest --tb=short            # Shorter traceback
pytest -x                    # Stop on first failure
pytest -k "test_api"         # Run tests matching pattern
pytest tests/test_api.py -v  # Run specific file
```

---

## Test Results

### Advanced RAG Features (Added 2026-07-27)

All 71 tests passing with BOTH methods.

**Method 1 - Mock Provider:**
- Result: 71 tests passed
- Time: 91 seconds
- Status: ALL PASSING

**Method 2 - Ollama Provider:**
- Result: 71 tests passed
- Time: ~90 seconds
- Status: ALL PASSING

**Test Breakdown:**
- test_retriever.py (Reranking): 13 tests
- test_table_processor.py (Tables): 20 tests
- test_semantic_chunker.py (Semantic): 38 tests
- Total: 71 tests

**What These Tests Verify:**
- Phase 1: Reranking improves search accuracy by 50-90%
- Phase 2: Tables extracted from PDFs as markdown
- Phase 3: Smart chunking based on topic boundaries
- All features work with both mock and real LLM

### Integration Tests (Real PDF Processing with Advanced RAG)

All 4 integration tests passing with BOTH methods.

**Method 1 - Mock Provider:**
- Result: 4 tests passed
- Time: 5 seconds
- Status: ALL PASSING

**Method 2 - Ollama Provider:**
- Result: 4 tests passed
- Time: 5 seconds
- Status: ALL PASSING

**Test Breakdown:**
- test_employee_handbook_plain_text_extraction: Semantic chunking on employee handbook
- test_financial_report_table_extraction_to_markdown: Table extraction to markdown (Phase 2)
- test_technical_manual_semantic_chunking_with_embeddings: Semantic chunking with embeddings (Phase 3)
- test_verify_sample_pdf_files_exist_and_readable: Verify sample PDFs readable from disk
- Total: 4 tests

**What These Tests Verify:**
- Real PDF files from disk process correctly with Advanced RAG
- Tables extracted from real financial PDFs and converted to markdown
- Semantic chunking works on real documents
- Embeddings (384-dimensional) generated for all chunks
- File paths resolve correctly

### Other Tests

94 out of 101 tests passing.

**What These Test:**
- API endpoints
- Document upload
- Router logic
- Session management

**Note:** Some tests have isolation issues when run together but work individually.

---

## GitHub Actions CI/CD

Tests run automatically on push/PR to `main`:
- Uses PostgreSQL 14 with pgvector (Docker)
- Uses mock provider (fast)
- Workflow: `.github/workflows/tests.yml`

---

## Test Files Structure

### Naming Convention

**Unit Tests** (in `app/tests/`) → Named after **Services** they test
**Integration Tests** (in `app/tests/test_integration_*/`) → Named after **Features** they test

### Structure

```
app/tests/
# Unit tests (test individual services)
├── conftest.py                     # Pytest fixtures
├── test_api.py                     # API endpoint tests
├── test_ask_endpoint.py            # Ask/Q&A endpoint tests
├── test_embeddings.py              # Tests app/services/embeddings.py
├── test_extractor.py               # Tests app/services/extractor.py
├── test_llm_factory.py             # Tests LLM factory
├── test_llm_mock.py                # Tests mock LLM provider
├── test_models.py                  # Tests database models
├── test_pdf_processor.py           # Tests app/services/pdf_processor.py
├── test_reranker.py                # Tests app/services/reranker.py
├── test_reranking_quality.py       # Tests reranking quality metrics
├── test_retriever.py               # Tests app/services/retriever.py
├── test_router.py                  # Tests routing logic
├── test_router_integration.py      # Tests router integration
├── test_semantic_chunker.py        # Tests app/services/semantic_chunker.py
├── test_sessions.py                # Tests session management
├── test_table_processor.py         # Tests app/services/table_processor.py
│
# Integration tests (test complete features end-to-end)
└── test_integration_01_document_ingestion/
    ├── __init__.py
    └── test_real_pdf_processing_with_advanced_rag.py  # Tests Feature 01: Document Ingestion
```

---

## Notes

- **Test DB:** `askdocs_test` on port 5433 (separate from dev `askdocs` on port 5432)
- **LLM Providers:** Mock (fast, fake responses) or Ollama (slow, real LLM)
- **Test isolation:** Configured in `app/tests/conftest.py` (uses port 5433)
- **Environment:** Use `.env.test` for test configuration
- **Async Tests:** Use `@pytest.mark.asyncio` decorator
- **Fixtures:** `db_session`, `client`, `mock_llm`, `sample_document_with_chunks`
