#!/bin/bash

# Local Test Runner for askdocs-rag-agent
# Automatically sets up PostgreSQL and runs tests

set -e  # Exit on error

PROJECT_ROOT="/Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent"
DB_CONTAINER="askdocs-test-db"
DB_NAME="askdocs_test"
DB_URL="postgresql://postgres:postgres@localhost:5432/${DB_NAME}"

echo "=========================================="
echo "RAG Application Test Runner"
echo "=========================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

# Check if PostgreSQL container exists
if docker ps -a --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    echo "✓ PostgreSQL container exists"

    # Check if it's running
    if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
        echo "  Starting existing container..."
        docker start ${DB_CONTAINER}
        sleep 3
    else
        echo "  Container already running"
    fi
else
    echo "Creating new PostgreSQL container with pgvector..."
    docker run -d \
        --name ${DB_CONTAINER} \
        -e POSTGRES_USER=postgres \
        -e POSTGRES_PASSWORD=postgres \
        -e POSTGRES_DB=${DB_NAME} \
        -p 5432:5432 \
        pgvector/pgvector:pg14

    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Wait for PostgreSQL to accept connections
echo "Checking PostgreSQL connection..."
for i in {1..10}; do
    if docker exec ${DB_CONTAINER} pg_isready -U postgres > /dev/null 2>&1; then
        echo "✓ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ PostgreSQL failed to start"
        exit 1
    fi
    sleep 1
done

# Set environment variables
export DATABASE_URL="${DB_URL}"
export LLM_PROVIDER="mock"
export GEMINI_API_KEY="test-key-not-used"
export PYTHONPATH="${PROJECT_ROOT}"

echo ""
echo "Running database migrations..."
cd ${PROJECT_ROOT}/app
if alembic upgrade head 2>&1 | grep -q "FAILED"; then
    echo "❌ Migration failed"
    exit 1
fi
echo "✓ Migrations complete"

echo ""
echo "=========================================="
echo "Running Tests"
echo "=========================================="
echo ""
echo "Provider: ${LLM_PROVIDER}"
echo "Database: ${DB_URL}"
echo ""

# Run tests
pytest -v --tb=short --cov=. --cov-report=term --cov-report=html

TEST_EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Saving Test Results"
echo "=========================================="

# Save results using the Python script
python ${PROJECT_ROOT}/app/run_tests_with_results.py

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ All tests passed!"
    echo ""
    echo "Coverage report: ${PROJECT_ROOT}/app/htmlcov/index.html"
    echo "Test results: ${PROJECT_ROOT}/docs/testing/api-results/latest.txt"
else
    echo "❌ Some tests failed (exit code: ${TEST_EXIT_CODE})"
    echo ""
    echo "Check details: ${PROJECT_ROOT}/docs/testing/api-results/latest.txt"
fi

echo ""
echo "=========================================="
echo "Cleanup Options:"
echo "  Stop database:  docker stop ${DB_CONTAINER}"
echo "  Remove database: docker rm ${DB_CONTAINER}"
echo "=========================================="

exit $TEST_EXIT_CODE
