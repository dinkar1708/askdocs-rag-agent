# Running E2E Tests

## Quick Start

### One Command (Recommended)

```bash
cd web-ui
./run-e2e-with-ollama.sh
```

This automatically starts all services and runs tests with Ollama (local LLM).

### With Mock LLM (Faster)

```bash
cd web-ui
./run-e2e-tests.sh
```

Uses mock LLM provider for instant responses.

## Test Isolation 🎯

**Tests run in ISOLATED environment - separate from development!**

| Environment | Database | PostgreSQL Port | API Port | UI Port |
|-------------|----------|-----------------|----------|---------|
| **Development** | `askdocs` | 5432 | 8000 | 3000 |
| **Testing** | `askdocs_test` | 5433 | 8001 | 3001 |

**Benefits:**
- ✅ Develop on port 8000 while tests run on 8001
- ✅ No data pollution between dev and tests
- ✅ Can run both simultaneously
- ✅ Separate PostgreSQL instances

## What You Need Running

```
Playwright → Web UI (3001) → Backend API (8001) → PostgreSQL (5433/askdocs_test)
```

The shell scripts handle all of this automatically.

## Manual Setup

If you prefer to start services manually:

### 1. Start Test PostgreSQL

```bash
# IMPORTANT: Use TEST database on port 5433 (not dev port 5432)
docker run --name askdocs-postgres-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=askdocs_test \
  -p 5433:5432 \
  -d postgres:14
```

### 2. Start Test Backend API

```bash
cd /path/to/askdocs-rag-agent
source venv/bin/activate

# IMPORTANT: Use TEST database + TEST port 8001 (not dev port 8000)
PYTHONPATH=$PWD \
  DATABASE_URL="postgresql://postgres:postgres@localhost:5433/askdocs_test" \
  LLM_PROVIDER="mock" \
  uvicorn app.main:app --port 8001
```

### 3. Run Tests

```bash
cd web-ui

# Tests automatically use port 3001 for UI (configured in playwright.config.ts)
npm run test:e2e          # Headless
npm run test:e2e:ui       # Visual (best for debugging)
npm run test:e2e:headed   # See browser
```

The Web UI starts automatically on port 3001 when tests run.

## Test Modes

| Command | Use Case |
|---------|----------|
| `./run-e2e-tests.sh` | Fast tests with mock LLM |
| `./run-e2e-with-ollama.sh` | Realistic tests with local LLM |
| `npm run test:e2e:ui` | Visual debugging mode |
| `npm run test:e2e:headed` | Watch browser |
| `npx playwright test --grep "upload"` | Run specific tests |

## LLM Providers

### Ollama (Recommended for Local)

**Pros:** Local, free, realistic
**Cons:** Slower (10-30s per response)

```bash
# Setup
brew install ollama
ollama pull llama3.2

# Run tests
./run-e2e-with-ollama.sh
```

### Mock (Recommended for CI)

**Pros:** Instant (<100ms), no setup
**Cons:** Not realistic LLM behavior

```bash
./run-e2e-tests.sh
```

## Troubleshooting

### Connection refused

**Check services are running:**

```bash
# PostgreSQL
pg_isready -h localhost -p 5432

# Backend API
curl http://localhost:8000/health

# If not running, start them manually (see Manual Setup)
```

### Tests timeout

**Increase timeout for slow Ollama responses:**

Tests already use 60s timeouts. If still timing out, check your machine isn't overloaded.

### File not found

**Ensure test fixture exists:**

```bash
ls web-ui/tests/fixtures/sample-policy.pdf
```

## Stop Services

```bash
# Stop TEST services (leaves dev services running)
pkill -f 'uvicorn app.main:app --port 8001'
docker stop askdocs-postgres-test

# Or stop all services
pkill -f uvicorn
docker stop askdocs-postgres askdocs-postgres-test
```

## Environment Configuration

The project uses environment files in the `app/` folder:

- `app/.env.example` - Template with all available options
- `app/.env.test` - Test environment configuration (ports 5433, 8001, 3001)
- `app/.env.dev` - Development configuration (create from .env.example)

**Best Practice:** Use `app/.env.test` for tests, `app/.env.dev` for development.

```bash
# Copy example for development
cp app/.env.example app/.env.dev

# Tests automatically use app/.env.test
./run-e2e-tests.sh
```

## CI/CD

See `.github/workflows/e2e-tests.yml` for GitHub Actions configuration.

**CI uses:**
- Mock LLM provider (speed and reliability)
- Test database `askdocs_test` on port 5433
- API on port 8001
- UI on port 3001

## Current Test Status

**24/24 tests passing (100%)**

All tests stable with both mock and Ollama providers.
