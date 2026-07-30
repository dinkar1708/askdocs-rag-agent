# Why Shell Scripts for E2E Testing

## The Problem

Running E2E tests requires multiple services in the correct order:

1. PostgreSQL database running on port 5432
2. Backend API with correct environment variables on port 8000
3. Web UI development server on port 3000
4. Playwright test execution

Without automation, every developer must manually execute 10+ commands in the right sequence every time they want to run tests.

## The Solution: Shell Scripts

Shell scripts automate the entire test setup and execution process. One command replaces many.

### Without Shell Scripts

```bash
# Check PostgreSQL
pg_isready -h localhost -p 5432

# If not running, start it
docker run --name askdocs-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=askdocs \
  -p 5432:5432 \
  -d postgres:14

# Wait for PostgreSQL
sleep 5

# Activate virtual environment
cd /path/to/project
source venv/bin/activate

# Run migrations
PYTHONPATH=$PWD DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
  alembic upgrade head

# Start backend API
PYTHONPATH=$PWD \
  DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
  LLM_PROVIDER="mock" \
  uvicorn app.main:app --port 8000 &

# Wait for API to be ready
for i in {1..30}; do
  curl -s http://localhost:8000/health && break
  sleep 1
done

# Navigate to web-ui
cd web-ui

# Run tests
npm run test:e2e

# Remember to stop services
pkill -f uvicorn
docker stop askdocs-postgres
```

Problems:
- Time consuming and error prone
- Easy to forget steps or use wrong environment variables
- Inconsistent between developers
- Hard to debug when something goes wrong

### With Shell Scripts

```bash
./run-e2e-tests.sh
```

The script automatically:
- Checks if PostgreSQL is running and starts it if needed
- Checks if Backend API is running and starts it if needed
- Sets all required environment variables correctly
- Waits for services to be ready before proceeding
- Runs the tests
- Provides helpful output and instructions

## Why Same Script Works for Local and CI

### Key Principle: Environment Agnostic

The shell scripts check the environment state rather than assuming it. This makes them work in any environment.

```bash
# Instead of assuming PostgreSQL is running
# The script CHECKS first
if ! pg_isready -h localhost -p 5432; then
    echo "Starting PostgreSQL..."
    docker run --name askdocs-postgres ...
fi
```

This pattern works because:
- Local development: Script starts missing services
- CI environment: Script starts missing services or finds them already running
- Same logic applies to both contexts

### Local Development Usage

```bash
cd web-ui
./run-e2e-tests.sh          # Fast tests with mock LLM
./run-e2e-with-ollama.sh    # Realistic tests with Ollama
```

Benefits:
- Developer runs one command
- Consistent environment every time
- No need to remember complex setup
- Fast iteration during development

### CI Usage

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install Python dependencies
        run: pip install -r requirements.txt

      - name: Install Playwright
        run: cd web-ui && npm install && npx playwright install --with-deps

      - name: Run E2E tests
        run: cd web-ui && ./run-e2e-tests.sh
```

Benefits:
- CI uses exact same setup as developers
- No duplication of setup logic in CI config
- If script changes, CI automatically uses updated version
- Easy to debug CI failures by running same script locally

## Single Source of Truth

### Without Shell Scripts

Setup logic exists in two places:
- Developer documentation: "Here's how to run tests locally"
- CI configuration: Separate implementation of same logic

Problems:
- Documentation gets outdated
- CI config drifts from local setup
- Changes require updating multiple places
- Local environment differs from CI leading to "works on my machine" issues

### With Shell Scripts

Setup logic exists in one place:
- The shell script itself

Benefits:
- Script is the documentation
- Local and CI are guaranteed identical
- Changes are made once
- Reduces maintenance burden

## Industry Standard Pattern

Major open source projects use this exact pattern:

### Kubernetes
- Local: `./test/e2e/e2e.sh`
- CI: `./test/e2e/e2e.sh`
- 200+ shell scripts in repository

### Next.js
- Local: `./test/run-tests.sh`
- CI: `./test/run-tests.sh`
- 20+ shell scripts in repository

### React
- Local: `./scripts/test.sh`
- CI: `./scripts/test.sh`
- 15+ shell scripts in repository

### VS Code
- Local: `./scripts/test.sh`
- CI: `./scripts/test.sh`
- 30+ shell scripts in repository

All these projects commit their shell scripts to version control because:
- Automation is essential for productivity
- Consistency between environments prevents bugs
- One source of truth reduces maintenance
- Standard practice that developers expect

## Best Practices Applied

Our shell scripts follow industry best practices:

### Portable
- Use relative paths, not absolute paths
- Check for dependencies before using them
- Provide helpful error messages when dependencies are missing

### Configurable
- Use environment variables with sensible defaults
- Support different modes (headless, headed, UI mode)
- Allow customization without modifying script

### Idempotent
- Check if services are already running before starting them
- Safe to run multiple times
- Clean error handling and exit codes

### Self-Documenting
- Clear output messages showing progress
- Helpful instructions at the end
- Show how to stop services and view logs

## Comparison Table

| Aspect | Manual Commands | Shell Scripts |
|--------|----------------|---------------|
| Number of commands | 10+ commands | 1 command |
| Consistency | Varies by developer | Always same |
| Error rate | High | Low |
| Onboarding time | Hours to learn | Minutes to run |
| Maintenance | Update docs + CI | Update one script |
| Debugging | Hard to reproduce | Easy to reproduce |
| Local vs CI | Often different | Always identical |

## Conclusion

Shell scripts for E2E testing provide:
- Automation that saves time and reduces errors
- Consistency between local development and CI
- Single source of truth for test environment setup
- Industry standard approach used by all major projects

The investment in creating these scripts pays off immediately and continues to save time for every developer on every test run.
