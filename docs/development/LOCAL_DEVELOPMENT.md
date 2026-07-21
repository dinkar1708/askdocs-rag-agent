# Local Development Setup

Quick guide for running the app locally with sample data.

## Prerequisites

- Docker & Docker Compose
- Node.js 18+ & npm
- curl (for testing)

## Quick Start

### 1. Start Backend

```bash
cd app
docker compose up -d
curl http://localhost:8000/health  # Verify
```

### 2. Start Frontend

```bash
cd web-ui
npm install  # First time only
npm run dev  # Runs on http://localhost:3000
```

### 3. Load Sample Data

```bash
# Upload test document
curl -X POST http://localhost:8000/documents/ \
  -F "file=@app/samples/company_policy.pdf"

# Verify
curl http://localhost:8000/documents/
```

## Test the System

```bash
# Ask a question via API
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How many vacation days do employees get?"}'

# Or use the web UI
open http://localhost:3000
```

**Test questions:**
- "How many vacation days do employees get?"
- "What health insurance options are available?"
- "What is the remote work policy?"

## Configuration

**Backend (`app/.env`):**
```bash
LLM_PROVIDER=mock  # No API key needed for local dev
DATABASE_URL=postgresql://postgres:postgres@db:5432/askdocs
```

**LLM Provider Options:**

1. **Mock (default)** - No setup needed
   ```bash
   LLM_PROVIDER=mock
   ```

2. **Ollama (100% local, no API key)**
   ```bash
   # Install Ollama
   brew install ollama
   brew services start ollama
   ollama pull llama3.2

   # Configure
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3.2
   ```

3. **Gemini (cloud)**
   ```bash
   LLM_PROVIDER=gemini
   GEMINI_API_KEY=your-key-here
   ```

## Common Commands

```bash
# View logs
docker logs app-api-1 -f

# Restart backend
docker compose -f app/docker-compose.yml restart api

# Stop everything
docker compose -f app/docker-compose.yml down

# Database shell
docker exec -it app-db-1 psql -U postgres -d askdocs

# Reset database (deletes all data)
docker compose -f app/docker-compose.yml down -v
```

## Verification

- Backend: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

## Troubleshooting

**"GEMINI_API_KEY required" error:**
```bash
# Set LLM_PROVIDER=mock in app/.env, then restart
docker compose -f app/docker-compose.yml down && docker compose -f app/docker-compose.yml up -d
```

**Port already in use:**
```bash
lsof -i :8000  # Find what's using port 8000
lsof -i :3000  # Find what's using port 3000
```

**Database not ready:**
```bash
docker logs app-db-1  # Check for "ready to accept connections"
```

**Frontend can't connect:**
```bash
curl http://localhost:8000/health  # Verify backend is up
# Check browser console (F12) for CORS errors
```

## Skills

Use Claude Code skills for guided setup:
- `local-setup` - Complete local environment setup
- `test` - Run tests
- `lint` - Code quality checks
- `api-test` - Test API endpoints

## Resources

- API Docs: http://localhost:8000/docs
- [Development Guide](./DEVELOPMENT.md)
- [Architecture](../core/architecture/ARCHITECTURE.md)
- [Testing](../testing/README.md)
