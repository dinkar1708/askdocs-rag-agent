# Quick Start

Essential commands to get started.

---

## Initial Setup

```bash
# Clone repo
git clone https://github.com/dinkar1708/askdocs-rag-agent.git
cd askdocs-rag-agent

# Copy environment file
cp .env.example .env

# Edit .env and add your Gemini API key
# Get key from: https://makersuite.google.com/app/apikey
nano .env  # or use your editor
```

---

## Run Locally

```bash
# Start all services (PostgreSQL + API)
docker compose up --build

# Run in background
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f api
```

**Access:**
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Common Commands

### Database

```bash
# Create migration
docker compose exec api alembic revision --autogenerate -m "description"

# Run migrations
docker compose exec api alembic upgrade head

# Rollback migration
docker compose exec api alembic downgrade -1

# Connect to database
docker compose exec db psql -U postgres -d askdocs

# Check tables
docker compose exec db psql -U postgres -d askdocs -c "\dt"
```

### Testing

```bash
# Run all tests
docker compose exec api pytest

# Run with coverage
docker compose exec api pytest --cov=app

# Run specific test
docker compose exec api pytest tests/test_api.py

# Run evaluation
docker compose exec api python -m eval.run
```

### Development

```bash
# Install dependencies locally (for IDE)
pip install -r requirements.txt

# Format code
docker compose exec api ruff format app/

# Lint code
docker compose exec api ruff check app/

# Type check
docker compose exec api mypy app/
```

### API Testing

```bash
# Health check
curl http://localhost:8000/health

# Upload document
curl -X POST http://localhost:8000/documents \
  -F "file=@samples/handbook.pdf"

# Ask question
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'

# List documents
curl http://localhost:8000/documents

# Search
curl "http://localhost:8000/search?q=vacation"
```

### Cleanup

```bash
# Stop and remove containers
docker compose down

# Remove volumes (deletes database)
docker compose down -v

# Remove images
docker compose down --rmi all

# Clean everything
docker compose down -v --rmi all
```

---

## Troubleshooting

**Port already in use:**
```bash
# Check what's using port 8000
lsof -i :8000

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

**Database connection error:**
```bash
# Check database is running
docker compose ps

# Restart database
docker compose restart db

# Check logs
docker compose logs db
```

**Module not found:**
```bash
# Rebuild containers
docker compose up --build
```

---

## First Time Setup (Complete Flow)

```bash
# 1. Clone and setup
git clone https://github.com/dinkar1708/askdocs-rag-agent.git
cd askdocs-rag-agent
cp .env.example .env

# 2. Add Gemini API key to .env
echo "GEMINI_API_KEY=your-key-here" >> .env

# 3. Start services
docker compose up --build

# 4. In another terminal, run migrations
docker compose exec api alembic upgrade head

# 5. Test API
curl http://localhost:8000/health

# 6. Open Swagger UI
open http://localhost:8000/docs
```

---

## Development Workflow

```bash
# 1. Make code changes in app/

# 2. API auto-reloads (no restart needed)

# 3. If you change requirements.txt:
docker compose up --build

# 4. If you change database models:
docker compose exec api alembic revision --autogenerate -m "change description"
docker compose exec api alembic upgrade head

# 5. Run tests
docker compose exec api pytest

# 6. Commit
git add .
git commit -m "Your message"
```

---

## See Also

- Full setup: [docs/getting-started/LOCAL_DEVELOPMENT.md](docs/getting-started/LOCAL_DEVELOPMENT.md)
- API docs: [docs/core/architecture/API.md](docs/core/architecture/API.md)
- Configuration: [docs/core/configuration/CONFIGURATION.md](docs/core/configuration/CONFIGURATION.md)
