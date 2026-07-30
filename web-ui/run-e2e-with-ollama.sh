#!/bin/bash

# E2E Test Runner with Ollama (Local LLM)
# Starts ISOLATED test environment (separate DB + ports) with real LLM
# Development can continue on port 8000 while tests run on 8001

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test-specific configuration
TEST_DB_NAME="askdocs_test"
TEST_POSTGRES_PORT="5433"
TEST_API_PORT="8001"
TEST_UI_PORT="3001"

echo -e "${BLUE}🚀 Starting ISOLATED E2E Tests with Ollama...${NC}"
echo ""

echo -e "${BLUE}📋 Test Environment Configuration:${NC}"
echo "   Database: ${TEST_DB_NAME} on port ${TEST_POSTGRES_PORT}"
echo "   Backend API: http://localhost:${TEST_API_PORT}"
echo "   Web UI: http://localhost:${TEST_UI_PORT}"
echo "   LLM: Ollama (llama3.2)"
echo ""

# 1. Check Ollama
echo -e "${BLUE}1️⃣  Checking Ollama...${NC}"
if ! command -v ollama &> /dev/null; then
    echo -e "${RED}✗ Ollama not found. Install it:${NC}"
    echo "  brew install ollama"
    exit 1
fi

if ! ollama list | grep -q "llama3.2"; then
    echo -e "${YELLOW}⚠️  llama3.2 not found. Downloading (this may take a while)...${NC}"
    ollama pull llama3.2
fi
echo -e "${GREEN}✓${NC} Ollama ready with llama3.2"
echo ""

# 2. Check Test PostgreSQL (separate from dev)
echo -e "${BLUE}2️⃣  Checking Test PostgreSQL (port ${TEST_POSTGRES_PORT})...${NC}"
if ! pg_isready -h localhost -p ${TEST_POSTGRES_PORT} > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Test PostgreSQL not running. Starting with Docker...${NC}"

    # Stop and remove if exists
    docker stop askdocs-postgres-test 2>/dev/null || true
    docker rm askdocs-postgres-test 2>/dev/null || true

    docker run --name askdocs-postgres-test \
      -e POSTGRES_PASSWORD=postgres \
      -e POSTGRES_DB=${TEST_DB_NAME} \
      -p ${TEST_POSTGRES_PORT}:5432 \
      -d pgvector/pgvector:pg16 > /dev/null 2>&1

    echo "   Waiting for PostgreSQL to be ready..."
    for i in {1..10}; do
        if pg_isready -h localhost -p ${TEST_POSTGRES_PORT} > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # Create pgvector extension
    PGPASSWORD=postgres psql -h localhost -p ${TEST_POSTGRES_PORT} -U postgres -d ${TEST_DB_NAME} -c "CREATE EXTENSION IF NOT EXISTS vector;" > /dev/null 2>&1
fi
echo -e "${GREEN}✓${NC} Test PostgreSQL running on localhost:${TEST_POSTGRES_PORT}"
echo ""

# 3. Start Test Backend API with Ollama
echo -e "${BLUE}3️⃣  Starting Test Backend API with Ollama (port ${TEST_API_PORT})...${NC}"

# Always stop any existing test API to ensure clean state
if curl -s http://localhost:${TEST_API_PORT}/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Stopping existing test API...${NC}"
    pkill -f "uvicorn app.main:app --port ${TEST_API_PORT}" || true
    sleep 2
fi

cd ..

# Activate venv
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtual environment not found. Please run: python3 -m venv venv${NC}"
    exit 1
fi

source venv/bin/activate

# Run migrations on test database
echo "   Running database migrations..."
cd app
PYTHONPATH=$PWD/.. DATABASE_URL="postgresql://postgres:postgres@localhost:${TEST_POSTGRES_PORT}/${TEST_DB_NAME}" \
  alembic upgrade head > /tmp/askdocs-test-migrations-ollama.log 2>&1
cd ..

# Start TEST API with Ollama
echo "   Starting test API with Ollama (llama3.2)..."
PYTHONPATH=$PWD \
  DATABASE_URL="postgresql://postgres:postgres@localhost:${TEST_POSTGRES_PORT}/${TEST_DB_NAME}" \
  LLM_PROVIDER="ollama" \
  OLLAMA_MODEL="llama3.2" \
  OLLAMA_BASE_URL="http://localhost:11434" \
  API_KEY="test-api-key-not-for-production" \
  uvicorn app.main:app --port ${TEST_API_PORT} > /tmp/askdocs-test-api-ollama.log 2>&1 &

API_PID=$!
echo "   Test API starting (PID: $API_PID)..."

# Wait for API
for i in {1..30}; do
    if curl -s http://localhost:${TEST_API_PORT}/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! curl -s http://localhost:${TEST_API_PORT}/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Test API failed to start. Check logs: tail -50 /tmp/askdocs-test-api-ollama.log${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Test Backend API running on localhost:${TEST_API_PORT} with Ollama"
echo ""

# 4. Upload test document
echo -e "${BLUE}4️⃣  Uploading test document...${NC}"

# Check if test document exists
TEST_PDF="app/samples/company_policy.pdf"
if [ ! -f "$TEST_PDF" ]; then
    echo -e "${YELLOW}⚠️  Test PDF not found at $TEST_PDF${NC}"
    echo "   Tests will still run, but may not have documents to query."
else
    # Upload document to TEST API
    UPLOAD_RESULT=$(curl -s -X POST http://localhost:${TEST_API_PORT}/documents/ \
      -F "file=@$TEST_PDF" 2>&1)

    if echo "$UPLOAD_RESULT" | grep -q '"id"'; then
        echo -e "${GREEN}✓${NC} Test document uploaded successfully"
    else
        echo -e "${YELLOW}⚠️  Document upload may have failed. Continuing anyway...${NC}"
    fi
fi

# Copy test fixture
mkdir -p web-ui/tests/fixtures
cp $TEST_PDF web-ui/tests/fixtures/sample-policy.pdf 2>/dev/null || true

echo ""

# 5. Run Playwright tests
echo -e "${BLUE}5️⃣  Running Playwright E2E Tests...${NC}"
echo "   (Web UI will auto-start on localhost:${TEST_UI_PORT})"
echo ""
echo -e "${YELLOW}📝 NOTE: Ollama responses can take 10-30 seconds. Tests have 60s timeout.${NC}"
echo ""

cd web-ui

# Prepare Nuxt with test environment variables
echo "   Preparing Nuxt with test environment..."
# Clear cache to ensure fresh build with test API URL
rm -rf .nuxt
# Build Nuxt with test environment (this creates required tsconfig files)
NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" npx nuxi prepare
echo "   ✓ Nuxt prepared with test API URL"
echo ""

# Run tests based on argument (with TEST environment variables)
if [ "$1" == "ui" ]; then
    echo "   Opening Playwright UI mode..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npm run test:e2e:ui
elif [ "$1" == "headed" ]; then
    echo "   Running in headed mode (visible browser)..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npm run test:e2e:headed
elif [ "$1" == "chromium" ]; then
    echo "   Running Chromium only (faster)..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npx playwright test --project=chromium
else
    echo "   Running all browsers..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npm run test:e2e
fi

echo ""
echo -e "${GREEN}✅ Tests complete!${NC}"
echo ""

# Show summary
echo -e "${BLUE}📊 Test Results:${NC}"
echo "   View HTML report: npm run test:e2e:report"
echo ""

echo -e "${BLUE}🔍 Check logs:${NC}"
echo "   Backend API: tail -50 /tmp/askdocs-test-api-ollama.log"
echo "   Migrations: tail -50 /tmp/askdocs-test-migrations-ollama.log"
echo ""

echo -e "${BLUE}🛑 To stop TEST services:${NC}"
echo "   pkill -f 'uvicorn app.main:app --port ${TEST_API_PORT}'"
echo "   docker stop askdocs-postgres-test"
echo ""

echo -e "${GREEN}✨ Your development server (port 8000) is UNAFFECTED!${NC}"
