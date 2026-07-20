# Test Suite

Comprehensive tests for askdocs-rag-agent.

## Running Tests

```bash
# Run all tests
cd app
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_api.py

# Run specific test
pytest tests/test_llm_mock.py::test_mock_generate

# Run with verbose output
pytest -v

# Run tests matching pattern
pytest -k "mock"
```

## Test Files

### test_api.py
Tests for FastAPI endpoints:
- Root endpoint (/)
- Health check (/health)
- Swagger docs availability
- OpenAPI schema

### test_models.py
Tests for database models:
- Document creation
- Chunk creation with embeddings
- Session creation
- Relationships (document-chunks)
- Cascade delete

### test_llm_mock.py
Tests for mock LLM provider:
- Initialization
- Simple generation
- Context-based generation
- Question type detection (vacation, benefits)
- NOT_FOUND responses
- Call counter
- Deterministic responses

### test_llm_factory.py
Tests for LLM provider factory:
- Getting providers by name
- Case-insensitive names
- Unsupported provider errors
- Environment variable config

## Test Coverage

Current coverage areas:
- API endpoints
- Database models and relationships
- Mock LLM provider
- Provider factory

## Fixtures

### conftest.py
Global test fixtures:
- `db_session`: Test database (SQLite in-memory)
- `client`: FastAPI test client
- `mock_llm`: Mock LLM provider instance
- `sample_pdf_path`: Path to sample PDF

## Mock LLM Usage

The mock LLM provider is perfect for:
- **Testing**: No API calls, instant responses
- **Demos**: Works without API keys
- **Development**: No internet required
- **CI/CD**: Consistent, fast test runs

### Example Usage

```python
from app.llm.factory import get_llm_provider

# Get mock provider
llm = get_llm_provider("mock")

# Simple generation
response = llm.generate("What is AI?")

# With document context
result = llm.generate_with_context(
    question="How many vacation days?",
    context="Employee handbook section 5: Employees receive 15 days..."
)

print(result["answer"])      # "According to the employee handbook..."
print(result["confidence"])  # 0.95
print(result["sources"])     # [{"document": "...", "page": 12}]
```

### Switching Providers

```bash
# Use mock (no API calls)
export LLM_PROVIDER=mock

# Use real Gemini (requires API key)
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your-key-here
```

## Adding New Tests

1. Create test file in `tests/`
2. Import fixtures from conftest.py
3. Name tests with `test_` prefix
4. Use descriptive test names
5. Add docstrings explaining what you're testing

Example:
```python
def test_new_feature(client, mock_llm):
    """Test new feature works correctly"""
    response = client.get("/new-endpoint")
    assert response.status_code == 200
```
