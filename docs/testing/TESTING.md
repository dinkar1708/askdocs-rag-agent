# Testing Guide

How to write and run tests for askdocs-rag-agent.

---

## Test Structure

```
tests/
├── unit/                 # Fast tests, no external dependencies
│   ├── test_chunker.py
│   ├── test_embedder.py
│   ├── test_retriever.py
│   └── test_router.py
│
├── integration/          # Tests with database, API calls
│   ├── test_api.py
│   ├── test_ingestion.py
│   ├── test_rag.py
│   └── test_chat.py
│
├── fixtures/             # Test data
│   ├── sample.pdf
│   └── test_questions.json
│
└── conftest.py           # Shared pytest fixtures
```

---

## Running Tests

```bash
# All tests
docker compose exec api pytest

# Unit tests only (fast)
docker compose exec api pytest tests/unit/

# Integration tests only
docker compose exec api pytest tests/integration/

# Specific test file
docker compose exec api pytest tests/unit/test_chunker.py

# Specific test function
docker compose exec api pytest tests/unit/test_chunker.py::test_chunk_with_overlap

# With verbose output
docker compose exec api pytest -v

# Stop on first failure
docker compose exec api pytest -x

# Run last failed tests
docker compose exec api pytest --lf
```

---

## Test Coverage

```bash
# Generate coverage report
docker compose exec api pytest --cov=app --cov-report=term-missing

# HTML report
docker compose exec api pytest --cov=app --cov-report=html
docker compose cp api:/app/htmlcov ./htmlcov
# Open htmlcov/index.html

# Target: >80% coverage
```

---

## Writing Tests

### Unit Test Example

```python
# tests/unit/test_chunker.py
from app.ingest.chunker import chunk_text

def test_chunk_with_overlap():
    text = "This is a test. " * 100  # ~500 tokens
    chunks = chunk_text(text, chunk_size=200, overlap=50)

    assert len(chunks) > 1, "Should create multiple chunks"
    assert len(chunks[0]) <= 200, "Chunks should respect size limit"

    # Verify overlap
    assert chunks[0][-50:] in chunks[1], "Chunks should overlap"

def test_empty_text():
    chunks = chunk_text("", chunk_size=100)
    assert chunks == [], "Empty text should return empty list"
```

### Integration Test Example

```python
# tests/integration/test_ingestion.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_document():
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = client.post("/documents", files={"file": f})

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["filename"] == "sample.pdf"
    assert data["chunk_count"] > 0

def test_ask_question_after_upload():
    # Upload document first
    with open("tests/fixtures/sample.pdf", "rb") as f:
        client.post("/documents", files={"file": f})

    # Ask question
    response = client.post(
        "/ask",
        json={"question": "What is the main topic?"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["answered", "not_found"]
    if data["status"] == "answered":
        assert len(data["sources"]) > 0
```

---

## Test Fixtures

**Shared fixtures in `conftest.py`:**

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base

@pytest.fixture(scope="session")
def test_db():
    """Create test database."""
    engine = create_engine("postgresql://postgres:postgres@db:5432/test_askdocs")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """Provide clean DB session per test."""
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_pdf():
    """Provide test PDF file."""
    return "tests/fixtures/sample.pdf"
```

**Use in tests:**
```python
def test_with_db(db_session):
    # db_session is a clean database
    from app.db.models import Document
    doc = Document(filename="test.pdf")
    db_session.add(doc)
    db_session.commit()
    assert doc.id is not None
```

---

## Mocking External APIs

### Mock LLM Provider

```python
# tests/unit/test_answer_generation.py
from unittest.mock import Mock, patch

def test_answer_generation():
    with patch("app.llm.factory.get_provider") as mock_provider:
        # Mock LLM response
        mock_llm = Mock()
        mock_llm.complete.return_value = "This is the answer."
        mock_provider.return_value = mock_llm

        # Test your code
        from app.rag.answer import generate_answer
        answer = generate_answer("What is X?", ["chunk 1", "chunk 2"])

        assert answer == "This is the answer."
        mock_llm.complete.assert_called_once()
```

### Mock Database

```python
@pytest.fixture
def mock_retriever():
    with patch("app.rag.retriever.retrieve_chunks") as mock:
        mock.return_value = [
            {"text": "chunk 1", "score": 0.9, "document": "test.pdf", "page": 1},
            {"text": "chunk 2", "score": 0.8, "document": "test.pdf", "page": 2},
        ]
        yield mock
```

---

## Test Markers

```python
# tests/integration/test_slow.py
import pytest

@pytest.mark.slow
def test_large_document_upload():
    # Test that takes >5 seconds
    pass

@pytest.mark.integration
def test_full_rag_pipeline():
    # End-to-end test
    pass
```

**Run specific markers:**
```bash
# Skip slow tests
pytest -m "not slow"

# Only integration tests
pytest -m integration
```

---

## Continuous Integration

**GitHub Actions:** `.github/workflows/test.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v2

      - name: Start services
        run: docker compose up -d

      - name: Wait for DB
        run: sleep 10

      - name: Run tests
        run: docker compose exec -T api pytest --cov=app

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Test Best Practices

### 1. Arrange-Act-Assert

```python
def test_chunk_text():
    # Arrange
    text = "This is a test."
    chunk_size = 100

    # Act
    chunks = chunk_text(text, chunk_size)

    # Assert
    assert len(chunks) == 1
```

### 2. One Assertion Per Test (Guideline)

```python
# Good: Clear what failed
def test_chunk_count():
    chunks = chunk_text("text " * 100, chunk_size=50)
    assert len(chunks) > 1

def test_chunk_size():
    chunks = chunk_text("text " * 100, chunk_size=50)
    assert len(chunks[0]) <= 50

# Acceptable: Related assertions
def test_chunk_properties():
    chunks = chunk_text("text " * 100, chunk_size=50)
    assert len(chunks) > 1
    assert all(len(c) <= 50 for c in chunks)
```

### 3. Test Edge Cases

```python
def test_empty_input():
    assert chunk_text("") == []

def test_single_character():
    assert chunk_text("a") == ["a"]

def test_very_large_chunk_size():
    text = "short text"
    chunks = chunk_text(text, chunk_size=10000)
    assert len(chunks) == 1
```

### 4. Use Fixtures for Setup

```python
@pytest.fixture
def uploaded_document(client):
    """Upload a document and return its ID."""
    with open("tests/fixtures/sample.pdf", "rb") as f:
        response = client.post("/documents", files={"file": f})
    return response.json()["id"]

def test_delete_document(client, uploaded_document):
    response = client.delete(f"/documents/{uploaded_document}")
    assert response.status_code == 200
```

---

## Debugging Tests

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use pytest's built-in debugger
pytest --pdb  # Drop into debugger on failure

# Print output during test
pytest -s  # Show print statements
```

---

## Performance Testing

```python
import time
import pytest

def test_query_performance():
    start = time.time()

    # Run query
    response = client.post("/ask", json={"question": "test"})

    elapsed = time.time() - start

    assert elapsed < 2.0, f"Query took {elapsed}s (expected <2s)"
```

---

## Next Steps

- **Write tests:** Use examples above
- **Run tests:** `docker compose exec api pytest`
- **Check coverage:** `pytest --cov=app`
- **CI/CD:** See `.github/workflows/test.yml`

---

**Target Metrics:**
- Coverage: >80%
- All tests pass
- CI runs on every PR
