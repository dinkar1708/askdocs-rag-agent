# Scripts Directory

Utility scripts for development, database management, and documentation generation.

---

## Directory Structure

```
scripts/
├── db/          # Database utilities
├── docs/        # Documentation generation
└── dev/         # Development helpers
```

---

## Database Scripts (`db/`)

Currently empty - use Alembic for database migrations:

```bash
# Initialize or update database schema
PYTHONPATH=$PWD DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
  alembic upgrade head
```

**Note:** Custom database utility scripts can be added here as needed.

---

## Documentation Scripts (`docs/`)

### `generate_schema.py`
Generate database schema diagrams from SQLAlchemy models.

```bash
python scripts/docs/generate_schema.py
```

**Generates:**
- `docs/core/architecture/schema.png` - Visual ERD diagram
- `docs/core/architecture/schema.mmd` - Mermaid diagram for GitHub
- `docs/core/architecture/schema_details.txt` - Detailed text schema

**Run when:**
- Database models change
- Before committing model updates
- Need updated documentation

**See:** [docs/development/SCHEMA_GENERATION.md](../docs/development/SCHEMA_GENERATION.md)

---

## Development Scripts (`dev/`)

### `create_sample_pdf.py`
Create sample PDF files for testing document upload.

```bash
python scripts/dev/create_sample_pdf.py
```

**Creates:**
- Sample PDFs in `outputs/` directory
- Test documents with various content types

**Use when:**
- Testing PDF upload functionality
- Need test documents
- Development and debugging

---

### `demo_reranking.py`
Demonstrate reranking feature for two-stage retrieval.

```bash
python scripts/dev/demo_reranking.py
```

**Shows:**
- How reranking improves search results
- Comparison before/after reranking
- Example of semantic search improvement

**Use when:**
- Understanding reranking concept
- Demonstrating features
- Training purposes

---

## Common Workflows

### Before Committing Model Changes
```bash
# 1. Update models in app/db/models.py

# 2. Create migration
PYTHONPATH=$PWD DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
  alembic revision --autogenerate -m "Description"

# 3. Regenerate schema docs
python scripts/docs/generate_schema.py

# 4. Commit all changes
git add app/db/models.py alembic/versions/ docs/core/architecture/schema.*
```

### Daily Development
```bash
# Update database schema (if models changed)
PYTHONPATH=$PWD DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
  alembic upgrade head

# Generate schema docs
python scripts/docs/generate_schema.py
```

---

## Environment Variables

All scripts respect these environment variables:

```bash
export DATABASE_NAME="askdocs"
export DATABASE_USER="postgres"
export DATABASE_PASSWORD="postgres"
export DATABASE_HOST="localhost"
export DATABASE_PORT="5432"
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs"
```

Or use a `.env` file in project root.

---

## Adding New Scripts

When adding new scripts:

1. **Choose the right directory:**
   - `db/` - Database operations (migrations, backups, queries)
   - `docs/` - Documentation generation
   - `dev/` - Development utilities

2. **Make scripts executable:**
   ```bash
   chmod +x scripts/db/your_script.sh
   ```

3. **Add shebang line:**
   - Shell scripts: `#!/bin/bash`
   - Python scripts: `#!/usr/bin/env python3`

4. **Update this README** with usage instructions

5. **Add error handling:**
   - Shell: `set -e` (exit on error)
   - Python: try/except blocks

---

## See Also

- [docs/development/SCHEMA_GENERATION.md](../docs/development/SCHEMA_GENERATION.md) - Schema generation guide
- [docs/development/SCHEMA_COMMANDS.md](../docs/development/SCHEMA_COMMANDS.md) - DB command reference
- [docs/development/TESTING_AND_SCRIPTS.md](../docs/development/TESTING_AND_SCRIPTS.md) - Testing scripts
