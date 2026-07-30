# Shell Scripts Guide

## What to Commit

**YES - Commit these:**
- Test runners: `run-tests.sh`, `run-e2e-tests.sh`
- Setup scripts: `setup.sh`, `install-deps.sh`
- Build/deploy: `build.sh`, `deploy.sh`

**NO - Don't commit:**
- Scripts with secrets/passwords
- Personal shortcuts: `my-*.sh`
- Machine-specific paths: `/Users/yourname/...`

## Best Practices

### Good Script
```bash
#!/bin/bash
set -e

# Use relative paths
cd "$(dirname "$0")/.."

# Environment variables with defaults
DATABASE_URL="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/askdocs}"

# Check dependencies
if ! command -v ollama &> /dev/null; then
    echo "Error: Ollama not found"
    exit 1
fi

# Run tests
npx playwright test
```

### Bad Script
```bash
# Missing shebang, absolute paths, hardcoded secrets
cd /Users/yourname/project
export DATABASE_PASSWORD="secret123"
python run_tests.py
```

### Running Scripts

**Always use `./` prefix:**
```bash
# ✅ Correct
./run-e2e-tests.sh

# ❌ Wrong - command not found
run-e2e-tests.sh
```

**Why?** Shell doesn't run scripts from current directory without `./` for security.

## Industry Standard

Major projects commit shell scripts:
- **Kubernetes**: 200+ scripts in `hack/`, `test/e2e/`
- **React**: 15+ scripts in `scripts/`
- **Next.js**: 20+ scripts in `test/`, `scripts/`
- **VS Code**: 30+ scripts in `build/`, `scripts/`

**Why?** Same script works for local dev AND CI:

```bash
# Local
./run-e2e-tests.sh

# CI (GitHub Actions)
- run: ./run-e2e-tests.sh
```

Benefits:
- Single source of truth
- Local = CI (no drift)
- Easy to debug (run same script locally)

## This Project

**Our scripts:**
```bash
web-ui/run-e2e-tests.sh          # Mock LLM (fast)
web-ui/run-e2e-with-ollama.sh   # Ollama (realistic)
```

**Run them:**
```bash
cd web-ui

# Fast tests with mock LLM
./run-e2e-tests.sh

# Realistic tests with Ollama
./run-e2e-with-ollama.sh

# With different modes
./run-e2e-tests.sh ui          # Visual UI mode
./run-e2e-tests.sh headed      # See browser
./run-e2e-tests.sh debug       # Debug mode
```

**Stop services after testing:**
```bash
pkill -f uvicorn              # Stop backend API
docker stop askdocs-postgres  # Stop PostgreSQL
```

**Commit them:**
```bash
chmod +x web-ui/*.sh
git add web-ui/*.sh
git commit -m "Add E2E test runner scripts"
```

## Checklist

- [ ] No secrets/passwords
- [ ] Relative paths only
- [ ] Has shebang `#!/bin/bash`
- [ ] Executable `chmod +x`
- [ ] Documented
- [ ] Works on any machine
