# Local Development Guide

Complete setup, testing, and debugging guide for local development.

---

## Prerequisites

- **Docker & Docker Compose** (v20+)
- **Python 3.12** (if running outside Docker)
- **Git**
- **LLM Provider** (pick one):
  - Gemini API key (free tier: https://aistudio.google.com/app/apikey)
  - Ollama installed locally (https://ollama.ai)

---

## First-Time Setup

### 1. Clone and Configure

```bash
git clone https://github.com/dinkar1708/askdocs-rag-agent.git
cd askdocs-rag-agent

# Create environment file
cp .env.example .env
```

### 2. Configure LLM Provider

**Option A: Gemini (Recommended)**
```bash
# Edit .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
```

**Option B: Ollama (Fully Offline)**
```bash
# Start Ollama and pull a model
ollama pull llama2

# Edit .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama2
```

**Option C: Azure OpenAI**
```bash
# Edit .env
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4
```

### 3. Start Services

```bash
docker compose up --build
```

**What starts:**
- `api` service - FastAPI app on port 8000
- `db` service - PostgreSQL 15 with pgvector extension

**First run takes 2-3 minutes** (downloading base images + installing dependencies).

### 4. Verify Setup

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "database": "connected"}
```

**Swagger UI:** http://localhost:8000/docs

---

## Running Without Docker

Useful for debugging with IDE breakpoints.

### Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL (requires local install or Docker)
docker compose up db  # or use local PostgreSQL

# Apply migrations
alembic upgrade head

# Run API
uvicorn app.main:app --reload --port 8000
```

---

## Development Workflow

### Making Code Changes

**1. Edit code** (changes auto-reload with `--reload` flag)

**2. Verify changes:**
```bash
# Lint
docker compose exec api ruff check .

# Format
docker compose exec api ruff format .

# Type check
docker compose exec api mypy app/
```

**3. Add tests:**
```bash
# Run tests
docker compose exec api pytest

# With coverage
docker compose exec api pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

**4. Commit:**
```bash
git add .
git commit -m "feat: add X"
```

---

## Database Management

### Migrations

```bash
# Create new migration (auto-detect model changes)
docker compose exec api alembic revision --autogenerate -m "add_field_X"

# Apply migrations
docker compose exec api alembic upgrade head

# Rollback last migration
docker compose exec api alembic downgrade -1

# View migration history
docker compose exec api alembic history
```

### Direct DB Access

```bash
# PostgreSQL shell
docker compose exec db psql -U postgres -d askdocs

# Useful commands:
\dt                  # List tables
\d chunks            # Describe chunks table
SELECT COUNT(*) FROM chunks;
\q                   # Quit
```

### Reset Database

```bash
# Stop containers
docker compose down

# Delete volume (WARNING: destroys all data)
docker volume rm askdocs-rag-agent_postgres_data

# Restart
docker compose up --build
```

---

## Testing

### Run All Tests

```bash
docker compose exec api pytest
```

### Test Structure

```
tests/
├── unit/
│   ├── test_chunker.py       # Chunking logic
│   ├── test_embedder.py      # Embedding generation
│   └── test_retriever.py     # Vector search
├── integration/
│   ├── test_api.py           # API endpoints
│   ├── test_ingestion.py     # End-to-end ingestion
│   └── test_rag.py           # End-to-end Q&A
└── fixtures/
    └── sample.pdf             # Test documents
```

### Run Specific Tests

```bash
# Unit tests only
docker compose exec api pytest tests/unit/

# Specific file
docker compose exec api pytest tests/integration/test_api.py

# Specific test
docker compose exec api pytest tests/unit/test_chunker.py::test_chunk_with_overlap

# With verbose output
docker compose exec api pytest -v

# Stop on first failure
docker compose exec api pytest -x
```

### Test Coverage

```bash
# Generate coverage report
docker compose exec api pytest --cov=app --cov-report=term-missing

# HTML report
docker compose exec api pytest --cov=app --cov-report=html
# Copy report out of container
docker compose cp api:/app/htmlcov ./htmlcov
# Open htmlcov/index.html
```

---

## Debugging

### View Logs

```bash
# All services
docker compose logs -f

# API only
docker compose logs -f api

# Last 100 lines
docker compose logs --tail=100 api
```

### Python Debugger (pdb)

Add breakpoint in code:
```python
import pdb; pdb.set_trace()
```

Run in attached mode:
```bash
# docker-compose.yml: add `stdin_open: true` and `tty: true` to api service
docker compose up

# In another terminal
docker attach askdocs-rag-agent-api-1
```

### IDE Debugging (VS Code)

`.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/askdocs"
      }
    }
  ]
}
```

---

## Manual Testing

### Upload a Document

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@samples/handbook.pdf"

# Response:
# {
#   "id": "123e4567-e89b-12d3-a456-426614174000",
#   "filename": "handbook.pdf",
#   "page_count": 10,
#   "chunk_count": 45
# }
```

### Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'

# Response:
# {
#   "answer": "Employees receive 15 days of paid vacation per year...",
#   "sources": [
#     {"document": "handbook.pdf", "page": 7}
#   ],
#   "confidence": 0.92
# }
```

### Test Refusal

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the weather today?"}'

# Response:
# {
#   "answer": "not_found",
#   "message": "The documents do not contain information to answer this question."
# }
```

---

## Evaluation

Run the evaluation harness to measure retrieval and answer quality:

```bash
docker compose exec api python -m eval.run
```

**Output:** `eval/report.md`

| Metric | Score |
|---|---|
| Retrieval hit-rate @ k=5 | 0.85 |
| Answer groundedness | 0.92 |
| Correct refusals | 1.00 |

**What it tests:**
- `eval/questions.json` - Labeled Q&A set (questions + expected doc/page)
- **Retrieval hit-rate** - Does top-k include the correct chunk?
- **Groundedness** - Does answer only use retrieved context?
- **Refusals** - Does it return "not_found" for off-topic questions?

---

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'app'`

**Cause:** Python path not set.

**Fix:**
```bash
# Add to .env
PYTHONPATH=/app
```

### Issue: `psycopg2.OperationalError: could not connect to server`

**Cause:** Database not ready.

**Fix:**
```bash
# Wait for DB to start (check logs)
docker compose logs db

# Or add health check to docker-compose.yml
healthcheck:
  test: ["CMD", "pg_isready", "-U", "postgres"]
  interval: 5s
```

### Issue: `vector extension does not exist`

**Cause:** pgvector not installed.

**Fix:**
```bash
# Enter DB container
docker compose exec db psql -U postgres -d askdocs

# Install extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: PDF extraction returns empty text

**Cause:** Scanned PDF (images, not text).

**Future:** Add OCR support (pytesseract).

**Workaround:** Use text-based PDFs for now.

### Issue: Slow embedding generation

**Cause:** CPU-based sentence-transformers on large documents.

**Fix:**
```bash
# Use GPU (if available)
docker compose --profile gpu up

# Or switch to API-based embeddings
LLM_PROVIDER=gemini  # Gemini can also generate embeddings
```

---

## Development Tips

### Hot Reload

Code changes auto-reload with `--reload` flag (in docker-compose.yml).

Exceptions:
- `.env` changes - restart container
- Database schema changes - run migrations
- Dependency changes - rebuild image

### Seed Data

```bash
# Upload sample documents
docker compose exec api python -m scripts.seed_data
```

Creates test documents + questions for development.

### Performance Profiling

```bash
# Add to route
from line_profiler import LineProfiler

@app.post("/ask")
def ask(question: str):
    profiler = LineProfiler()
    profiler.add_function(retrieve_chunks)
    profiler.enable()
    result = retrieve_chunks(question)
    profiler.disable()
    profiler.print_stats()
    return result
```

### SQL Query Logging

```bash
# Edit .env
SQLALCHEMY_ECHO=true
```

Logs all SQL queries (helpful for debugging pgvector searches).

---

## Next Steps

- **Write code** - See [Architecture](ARCHITECTURE.md) for design
- **Test API** - See [API Reference](API.md) for endpoints
- **Deploy** - See [Deployment](DEPLOYMENT.md) for cloud setup

---

**Need help?** Open an issue on GitHub.
