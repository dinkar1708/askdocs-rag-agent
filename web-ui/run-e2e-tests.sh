#!/bin/bash

# E2E Test Runner Script
# Starts ISOLATED test environment (separate DB + ports)
# Development can continue on port 8000 while tests run on 8001

set -e  # Exit on error

echo "🚀 Starting ISOLATED E2E Test Environment..."
echo ""

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

echo -e "${BLUE}📋 Test Environment Configuration:${NC}"
echo "   Database: ${TEST_DB_NAME} on port ${TEST_POSTGRES_PORT}"
echo "   Backend API: http://localhost:${TEST_API_PORT}"
echo "   Web UI: http://localhost:${TEST_UI_PORT}"
echo ""

# Check if TEST PostgreSQL is running (separate from dev)
echo "1️⃣  Checking Test PostgreSQL (port ${TEST_POSTGRES_PORT})..."
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

# Check if TEST backend API is running
echo "2️⃣  Checking Test Backend API (port ${TEST_API_PORT})..."

# Always stop any existing test API to ensure clean state
if curl -s http://localhost:${TEST_API_PORT}/health > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Stopping existing test API...${NC}"
    pkill -f "uvicorn app.main:app --port ${TEST_API_PORT}" || true
    sleep 2
fi

cd ..
source venv/bin/activate 2>/dev/null || {
    echo -e "${RED}✗ Virtual environment not found. Please run: python3 -m venv venv${NC}"
    exit 1
}

# Run migrations on test database
echo "   Running database migrations..."
cd app
PYTHONPATH=$PWD/.. DATABASE_URL="postgresql://postgres:postgres@localhost:${TEST_POSTGRES_PORT}/${TEST_DB_NAME}" \
  alembic upgrade head > /tmp/askdocs-test-migrations.log 2>&1
cd ..

# Start TEST backend in background
echo "   Starting test API on port ${TEST_API_PORT}..."
PYTHONPATH=$PWD \
  DATABASE_URL="postgresql://postgres:postgres@localhost:${TEST_POSTGRES_PORT}/${TEST_DB_NAME}" \
  LLM_PROVIDER="mock" \
  API_KEY="test-api-key-not-for-production" \
  uvicorn app.main:app --port ${TEST_API_PORT} > /tmp/askdocs-test-api.log 2>&1 &

API_PID=$!
echo "   Test API starting (PID: $API_PID)..."

# Wait for API to be ready
for i in {1..30}; do
    if curl -s http://localhost:${TEST_API_PORT}/health > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

if ! curl -s http://localhost:${TEST_API_PORT}/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Test API failed to start. Check logs: tail /tmp/askdocs-test-api.log${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Test Backend API running on localhost:${TEST_API_PORT}"
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

# Run Playwright tests (Web UI auto-starts on test port)
echo "3️⃣  Running Playwright E2E Tests..."
echo "   (Web UI will auto-start on localhost:${TEST_UI_PORT})"
echo ""

# Run tests based on argument (with TEST environment variables)
if [ "$1" == "ui" ]; then
    echo "   Opening Playwright UI mode..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npm run test:e2e:ui
elif [ "$1" == "headed" ]; then
    echo "   Running in headed mode (visible browser)..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npm run test:e2e:headed
elif [ "$1" == "debug" ]; then
    echo "   Running in debug mode..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npm run test:e2e:debug
else
    echo "   Running in headless mode..."
    NUXT_PUBLIC_API_BASE="http://localhost:${TEST_API_PORT}" BASE_URL="http://localhost:${TEST_UI_PORT}" API_URL="http://localhost:${TEST_API_PORT}" npm run test:e2e
fi

echo ""
echo -e "${GREEN}✅ Tests complete!${NC}"
echo ""
echo -e "${BLUE}📊 View test report:${NC}"
echo "   npm run test:e2e:report"
echo ""
echo -e "${BLUE}🔍 Check logs:${NC}"
echo "   Backend API: tail -50 /tmp/askdocs-test-api.log"
echo "   Migrations: tail -50 /tmp/askdocs-test-migrations.log"
echo ""
echo -e "${BLUE}🛑 To stop TEST services:${NC}"
echo "   pkill -f 'uvicorn app.main:app --port ${TEST_API_PORT}'"
echo "   docker stop askdocs-postgres-test"
echo ""
echo -e "${GREEN}✨ Your development server (port 8000) is UNAFFECTED!${NC}"
