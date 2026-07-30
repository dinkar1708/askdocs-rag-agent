# Test Isolation Setup - Complete Guide

## ✅ What Was Implemented

We've implemented **FULL test isolation** following industry best practices. Tests now run in a completely separate environment from development.

## 🎯 Test vs Development Environments

| Component | Development | Testing |
|-----------|-------------|---------|
| **Database Name** | `askdocs` | `askdocs_test` |
| **PostgreSQL Port** | `5432` | `5433` |
| **Docker Container** | `askdocs-postgres` | `askdocs-postgres-test` |
| **Backend API Port** | `8000` | `8001` |
| **Web UI Port** | `3000` | `3001` |
| **Environment File** | `.env` | `.env.test` |

## 🚀 Benefits

### 1. **Simultaneous Development & Testing**
```bash
# Terminal 1: Development
uvicorn app.main:app --port 8000

# Terminal 2: E2E Tests (runs on port 8001)
cd web-ui && ./run-e2e-tests.sh
```

### 2. **No Data Pollution**
- Development data stays in `askdocs` database
- Test data goes to `askdocs_test` database
- Clean slate for every test run

### 3. **No Port Conflicts**
- Dev API: `http://localhost:8000`
- Test API: `http://localhost:8001`
- Dev UI: `http://localhost:3000`
- Test UI: `http://localhost:3001`

### 4. **Industry Standard**
This matches how professional projects handle testing:
- Rails: `database_test` vs `database_development`
- Django: `TEST_` prefix databases
- Node.js: Separate `TEST_DATABASE_URL`
- GitLab: `gitlab_test` vs `gitlab_development`

## 📁 Files Modified

### 1. **Shell Scripts**
- `web-ui/run-e2e-tests.sh`
  - Uses port 5433 for PostgreSQL
  - Uses port 8001 for API
  - Uses port 3001 for UI
  - Container: `askdocs-postgres-test`

- `web-ui/run-e2e-with-ollama.sh`
  - Same test isolation
  - Uses real Ollama LLM instead of mock

### 2. **Playwright Configuration**
- `web-ui/playwright.config.ts`
  - `baseURL`: `http://localhost:3001`
  - `apiURL`: `http://localhost:8001`
  - `webServer.command`: Starts on port 3001

### 3. **Pytest Configuration**
- `app/tests/conftest.py`
  - `DATABASE_URL`: `postgresql://postgres:postgres@localhost:5433/askdocs_test`
  - All API tests use port 5433 automatically

### 4. **CI/CD Workflow**
- `.github/workflows/e2e-tests.yml`
  - PostgreSQL service on port 5433
  - Database: `askdocs_test`
  - API runs on port 8001
  - UI runs on port 3001

### 5. **Environment Files** (in `app/` folder)
- `app/.env.example` - Template for development
- `app/.env.test` - Test configuration (committed to repo)
- `app/.env` - Local development (ignored by git)

### 6. **Documentation**
- `docs/e2e-testing/running-tests.md` - Updated with test isolation info
- `docs/testing/README.md` - Updated for API tests

## 🔧 How to Use

### Running E2E Tests

```bash
cd web-ui

# With mock LLM (fast)
./run-e2e-tests.sh

# With Ollama (realistic)
./run-e2e-with-ollama.sh

# Visual debugging
./run-e2e-tests.sh ui
```

### Running API Tests (pytest)

```bash
# Setup (one time)
docker run --name askdocs-postgres-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=askdocs_test \
  -p 5433:5432 \
  -d postgres:14

PYTHONPATH=$PWD \
  DATABASE_URL="postgresql://postgres:postgres@localhost:5433/askdocs_test" \
  alembic upgrade head

# Run tests
export LLM_PROVIDER="mock"
export PYTHONPATH=$PWD
pytest app/tests/ -v
```

### Checking What's Running

```bash
# PostgreSQL
pg_isready -h localhost -p 5432   # Dev
pg_isready -h localhost -p 5433   # Test

# Backend API
curl http://localhost:8000/health  # Dev
curl http://localhost:8001/health  # Test

# Docker containers
docker ps | grep postgres
```

### Stopping Services

```bash
# Stop ONLY test services (dev keeps running)
pkill -f 'uvicorn app.main:app --port 8001'
docker stop askdocs-postgres-test

# Stop ALL services
pkill -f uvicorn
docker stop askdocs-postgres askdocs-postgres-test
```

## 📊 Verification Steps

### 1. Check Test Isolation

```bash
# Start dev PostgreSQL on 5432
docker run --name askdocs-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=askdocs \
  -p 5432:5432 \
  -d postgres:14

# Start dev API on 8000
PYTHONPATH=$PWD \
  DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
  uvicorn app.main:app --port 8000

# In another terminal, run tests (should use 5433 and 8001)
cd web-ui && ./run-e2e-tests.sh
```

### 2. Verify Separate Databases

```bash
# Connect to dev database
psql -h localhost -p 5432 -U postgres -d askdocs

# Connect to test database
psql -h localhost -p 5433 -U postgres -d askdocs_test

# They should have different data
```

### 3. Verify Test Passes

```bash
cd web-ui
./run-e2e-tests.sh

# Should see:
# - Test PostgreSQL on port 5433
# - Test API on port 8001
# - Test UI on port 3001
# - 24/24 tests passing
```

## 🎓 Best Practices Applied

### 1. **Separate Test Database**
- ✅ Industry standard (Rails, Django, Node.js all do this)
- ✅ Prevents data pollution
- ✅ Allows parallel dev and testing

### 2. **Separate Ports**
- ✅ No port conflicts
- ✅ Can run both simultaneously
- ✅ Easy to identify which service is which

### 3. **Environment-Based Configuration**
- ✅ `.env.test` for test config (committed)
- ✅ `.env` for dev config (ignored)
- ✅ `.env.example` for template (committed)

### 4. **Docker Containers**
- ✅ Separate containers for dev and test
- ✅ Easy to tear down and rebuild
- ✅ Consistent across environments

### 5. **CI/CD Integration**
- ✅ GitHub Actions uses same test ports
- ✅ Same database name
- ✅ Consistent behavior local vs CI

## 🔍 Troubleshooting

### Port Already in Use

```bash
# Find what's using the port
lsof -i :8001
lsof -i :5433

# Kill it
pkill -f 'uvicorn app.main:app --port 8001'
docker stop askdocs-postgres-test
```

### Tests Can't Connect to Database

```bash
# Check if test PostgreSQL is running
pg_isready -h localhost -p 5433

# If not, start it
docker run --name askdocs-postgres-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=askdocs_test \
  -p 5433:5432 \
  -d postgres:14
```

### Tests Using Wrong Ports

Check the scripts and config files:
- `web-ui/run-e2e-tests.sh` → Should use 5433, 8001, 3001
- `web-ui/playwright.config.ts` → Should use 3001 and 8001
- `app/tests/conftest.py` → Should use 5433

## 📚 References

- **Running E2E Tests**: `docs/e2e-testing/running-tests.md`
- **Running API Tests**: `docs/testing/README.md`
- **CI/CD Configuration**: `.github/workflows/e2e-tests.yml`
- **Environment Template**: `.env.example`
- **Test Environment**: `.env.test`

## ✨ Summary

You now have **production-grade test isolation**:

- ✅ Separate databases (dev vs test)
- ✅ Separate ports (no conflicts)
- ✅ Separate Docker containers
- ✅ Environment-based configuration
- ✅ Industry best practices
- ✅ Can develop and test simultaneously
- ✅ CI/CD ready

**Next Steps:**
1. Start Docker Desktop
2. Run `cd web-ui && ./run-e2e-tests.sh`
3. Verify 24/24 tests pass with isolated environment!
