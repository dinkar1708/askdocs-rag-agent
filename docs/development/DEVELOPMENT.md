# Development Guide

Quick reference for developers working on askdocs-rag-agent.

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/dinkar1708/askdocs-rag-agent.git
cd askdocs-rag-agent

# Configure
cp .env.example .env
# Edit .env with your LLM provider (Gemini/Ollama)

# Start services
docker compose up --build

# In another terminal - verify
curl http://localhost:8000/health
```

---

## Project Structure

```
askdocs-rag-agent/
├── app/                      # Application code
│   ├── api/                  # FastAPI routes
│   │   ├── routes/
│   │   │   ├── documents.py  # Document upload/list/delete
│   │   │   ├── ask.py        # Question answering
│   │   │   ├── chat.py       # Multi-turn chat
│   │   │   └── health.py     # Health checks
│   │   └── middleware/       # CORS, auth, rate limiting
│   │
│   ├── ingest/               # Document ingestion pipeline
│   │   ├── pdf_extractor.py  # PDF → text + page metadata
│   │   ├── chunker.py        # Text → overlapping chunks
│   │   └── embedder.py       # Chunks → vector embeddings
│   │
│   ├── rag/                  # RAG (Retrieval-Augmented Generation)
│   │   ├── retriever.py      # Vector similarity search
│   │   ├── reranker.py       # Optional cross-encoder reranking
│   │   └── citation_builder.py  # Extract [doc, page] citations
│   │
│   ├── graph/                # LangGraph query router
│   │   ├── router.py         # StateGraph definition
│   │   ├── nodes.py          # classify, retrieve, answer, clarify, refuse
│   │   └── state.py          # Graph state schema
│   │
│   ├── llm/                  # LLM provider adapter pattern
│   │   ├── base.py           # Abstract LLMProvider interface
│   │   ├── gemini_provider.py
│   │   ├── ollama_provider.py
│   │   ├── azure_openai_provider.py
│   │   └── factory.py        # Provider selection logic
│   │
│   ├── mcp/                  # Model Context Protocol server
│   │   └── server.py         # Exposes search_documents, ask_question tools
│   │
│   ├── db/                   # Database layer
│   │   ├── models.py         # SQLAlchemy models (documents, chunks, sessions)
│   │   ├── database.py       # Engine, session management
│   │   └── migrations/       # Alembic migrations
│   │
│   └── core/                 # Core utilities
│       ├── config.py         # Environment variable loading
│       └── logging.py        # Structured logging setup
│
├── tests/                    # Test suites
│   ├── unit/                 # Unit tests (fast, no DB)
│   │   ├── test_chunker.py
│   │   ├── test_embedder.py
│   │   └── test_retriever.py
│   └── integration/          # Integration tests (with DB)
│       ├── test_api.py
│       ├── test_ingestion.py
│       └── test_rag.py
│
├── eval/                     # Evaluation harness
│   ├── questions.json        # Labeled test questions
│   ├── run.py                # Run evaluation, generate report
│   └── tune_threshold.py     # Optimize confidence threshold
│
├── deploy/                   # Deployment configurations
│   ├── gcp/
│   │   ├── deploy.sh         # Cloud Run deployment script
│   │   └── README.md         # GCP setup guide
│   └── azure/
│       ├── deploy.sh         # Azure Container Apps script
│       └── README.md         # Azure setup guide
│
├── docs/                     # Technical documentation
│   ├── ARCHITECTURE.md       # System design
│   ├── DEVELOPMENT.md        # This file
│   ├── LOCAL_DEVELOPMENT.md  # Detailed local setup
│   ├── API.md                # REST API reference
│   ├── CONFIGURATION.md      # Environment variables
│   ├── DEPLOYMENT.md         # Cloud deployment
│   ├── MCP.md                # MCP integration
│   └── WHY.md                # Product positioning
│
├── features/                 # User-focused feature docs
│   ├── 01-document-ingestion.md
│   ├── 02-grounded-qa.md
│   ├── 03-document-management.md
│   ├── 04-multi-turn-chat.md
│   ├── 05-query-routing.md
│   ├── 06-mcp-integration.md
│   └── 07-evaluation.md
│
├── samples/                  # Sample PDFs for testing
│   ├── handbook.pdf
│   └── terms.pdf
│
├── .env.example              # Environment template
├── docker-compose.yml        # Local dev stack
├── Dockerfile                # API container
├── requirements.txt          # Python dependencies
└── README.md                 # Main project README
```

---

## Common Tasks

### Add a New API Endpoint

**1. Create route file:**
```python
# app/api/routes/my_feature.py
from fastapi import APIRouter

router = APIRouter()

@router.post("/my-endpoint")
def my_endpoint():
    return {"status": "ok"}
```

**2. Register in main app:**
```python
# app/main.py
from app.api.routes import my_feature

app.include_router(my_feature.router, prefix="/api", tags=["my_feature"])
```

**3. Add tests:**
```python
# tests/integration/test_my_feature.py
def test_my_endpoint(client):
    response = client.post("/my-endpoint")
    assert response.status_code == 200
```

---

### Add a New LLM Provider

**1. Create provider class:**
```python
# app/llm/my_provider.py
from app.llm.base import LLMProvider

class MyProvider(LLMProvider):
    def complete(self, prompt: str, context: list[str]) -> str:
        # Implement API call
        return "answer"

    def embed(self, text: str) -> list[float]:
        # Optional: implement embeddings
        return [0.1, 0.2, ...]
```

**2. Register in factory:**
```python
# app/llm/factory.py
def get_provider() -> LLMProvider:
    if LLM_PROVIDER == "my_provider":
        return MyProvider()
```

**3. Update config:**
```bash
# .env
LLM_PROVIDER=my_provider
MY_PROVIDER_API_KEY=xxx
```

---

### Add a Database Migration

```bash
# 1. Edit models
# app/db/models.py
class Document(Base):
    # Add new field
    version = Column(String, nullable=True)

# 2. Generate migration
docker compose exec api alembic revision --autogenerate -m "add_document_version"

# 3. Review generated migration
# Edit app/db/migrations/versions/xxx_add_document_version.py

# 4. Apply migration
docker compose exec api alembic upgrade head

# 5. Verify
docker compose exec db psql -U postgres -d askdocs -c "\d documents"
```

---

### Run Tests

```bash
# All tests
docker compose exec api pytest

# Specific test file
docker compose exec api pytest tests/unit/test_chunker.py

# Specific test function
docker compose exec api pytest tests/unit/test_chunker.py::test_chunk_with_overlap

# With coverage
docker compose exec api pytest --cov=app --cov-report=html

# Integration tests only
docker compose exec api pytest tests/integration/

# Unit tests only
docker compose exec api pytest tests/unit/
```

---

### Code Quality

```bash
# Lint
docker compose exec api ruff check .

# Format
docker compose exec api ruff format .

# Type check
docker compose exec api mypy app/

# All at once
docker compose exec api sh -c "ruff check . && mypy app/ && pytest"
```

---

### Debug Locally (Without Docker)

```bash
# Setup virtual env
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start database only
docker compose up db

# Run API with debugger
python -m uvicorn app.main:app --reload --port 8000

# Set breakpoint in code
import pdb; pdb.set_trace()
```

---

### View Logs

```bash
# All services
docker compose logs -f

# API only
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api

# Search logs
docker compose logs api | grep "ERROR"
```

---

### Database Access

```bash
# PostgreSQL shell
docker compose exec db psql -U postgres -d askdocs

# Useful commands:
\dt                           # List tables
\d documents                  # Describe table
\d+ chunks                    # Detailed table info
SELECT COUNT(*) FROM chunks;  # Query
\q                            # Quit
```

---

## Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feat/my-feature

# 2. Write code
# app/...

# 3. Add tests
# tests/...

# 4. Run tests locally
docker compose exec api pytest

# 5. Check code quality
docker compose exec api ruff check .

# 6. Commit
git add .
git commit -m "feat: add my feature"

# 7. Push and create PR
git push origin feat/my-feature
```

---

### Bug Fix Workflow

```bash
# 1. Create bug branch
git checkout -b fix/bug-description

# 2. Add failing test
# tests/test_bug.py
def test_bug_reproduction():
    # Reproduce the bug
    assert expected == actual

# 3. Fix the bug
# app/...

# 4. Verify test passes
docker compose exec api pytest tests/test_bug.py

# 5. Commit
git commit -m "fix: resolve bug description"
```

---

## Environment Management

### Development
```bash
# .env
LOG_LEVEL=DEBUG
CONFIDENCE_THRESHOLD=0.6  # Lower for testing
CORS_ORIGINS=*
```

### Production
```bash
# .env (or cloud secrets)
LOG_LEVEL=WARNING
CONFIDENCE_THRESHOLD=0.8  # Higher for production
CORS_ORIGINS=https://yourdomain.com
API_KEY_ENABLED=true
```

---

## Performance Profiling

```bash
# Add timing decorator
from functools import wraps
import time

def timed(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"{func.__name__}: {time.time() - start:.2f}s")
        return result
    return wrapper

@timed
def retrieve_chunks(query):
    # ...
```

---

## Git Workflow

### Commit Message Format

```
type(scope): short description

Longer description if needed

Fixes #123
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code restructuring
- `test`: Add/update tests
- `chore`: Build, deps, tooling

**Examples:**
```
feat(api): add multi-turn chat endpoint
fix(retrieval): handle empty query edge case
docs(features): update grounded-qa examples
refactor(llm): extract provider factory
test(rag): add retrieval hit-rate tests
```

---

## CI/CD

### GitHub Actions

**Workflow:** `.github/workflows/ci.yml`

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v2
      - run: docker compose up -d
      - run: docker compose exec -T api pytest
      - run: docker compose exec -T api ruff check .
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'app'"

**Fix:**
```bash
# Add to .env
PYTHONPATH=/app

# Or run with module syntax
python -m app.main
```

### "Database connection refused"

**Fix:**
```bash
# Wait for DB to be ready
docker compose logs db

# Check health
docker compose exec db pg_isready -U postgres
```

### "Vector extension does not exist"

**Fix:**
```bash
docker compose exec db psql -U postgres -d askdocs -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

---

## Documentation Standards

### Code Comments

```python
def chunk_text(text: str, chunk_size: int = 512) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Input text to chunk
        chunk_size: Maximum tokens per chunk (default: 512)

    Returns:
        List of text chunks with overlap

    Example:
        >>> chunk_text("Long text...", chunk_size=100)
        ['chunk 1...', 'chunk 2...']
    """
```

### API Documentation

Use FastAPI's built-in docs:
```python
@router.post("/ask", response_model=AnswerResponse)
def ask_question(
    question: str = Body(..., description="Question to answer"),
    top_k: int = Body(5, description="Number of chunks to retrieve")
):
    """
    Ask a question and get a grounded answer with citations.

    Returns "not_found" if confidence is below threshold.
    """
```

---

## Getting Help

- **Documentation:** See `docs/` folder
- **Features:** See `features/` folder
- **Issues:** [GitHub Issues](https://github.com/dinkar1708/askdocs-rag-agent/issues)
- **Architecture questions:** See `docs/ARCHITECTURE.md`
- **Deployment help:** See `docs/DEPLOYMENT.md`

---

## Next Steps

- **New developer?** Start with [Local Development](LOCAL_DEVELOPMENT.md)
- **Adding features?** See feature docs in `features/`
- **Deploying?** See [Deployment](DEPLOYMENT.md)
- **Contributing?** See `CONTRIBUTING.md`
