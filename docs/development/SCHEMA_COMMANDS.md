# Database Schema Commands - Quick Reference

Quick reference for generating and working with database schema documentation.

---

## Generate Schema Documentation

```bash
# Generate all schema docs (PNG, Mermaid, Text)
python scripts/docs/generate_schema.py
```

**Output:**
- `docs/core/architecture/schema.png` - Visual ERD diagram
- `docs/core/architecture/schema.mmd` - Mermaid diagram
- `docs/core/architecture/schema_details.txt` - Detailed text schema

---

## View Current Schema

```bash
# View in browser (if PNG is generated)
open docs/core/architecture/schema.png

# View text details
cat docs/core/architecture/schema_details.txt

# View Mermaid diagram
cat docs/core/architecture/schema.mmd
```

---

## Database Inspection Commands

```bash
# Connect to local database
psql postgresql://postgres:postgres@localhost:5432/askdocs

# List all tables
\dt

# Describe a table
\d documents
\d chunks
\d sessions
\d messages

# View foreign keys
\d+ chunks    # Shows foreign key to documents
\d+ messages  # Shows foreign key to sessions

# Check indexes
\di

# View table relationships
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

---

## Alembic Migration Commands

```bash
# View current schema version
PYTHONPATH=/Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent \
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
alembic current

# View migration history
PYTHONPATH=/Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent \
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
alembic history

# Create new migration after model changes
PYTHONPATH=/Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent \
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
PYTHONPATH=/Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent \
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
alembic upgrade head
```

---

## Workflow: Modifying Schema

When you change database models:

```bash
# 1. Edit models
vim app/db/models.py

# 2. Create migration
PYTHONPATH=$PWD DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
alembic revision --autogenerate -m "Add new field"

# 3. Review migration
vim alembic/versions/<new_migration>.py

# 4. Apply migration
PYTHONPATH=$PWD DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs" \
alembic upgrade head

# 5. Regenerate schema docs
python scripts/docs/generate_schema.py

# 6. Commit changes
git add app/db/models.py alembic/versions/ docs/core/architecture/schema.*
git commit -m "Add new database field"
```

---

## Relationships Summary

From SQLAlchemy models:

```
documents (1) ──< (many) chunks
    └─ CASCADE DELETE (deleting document deletes all chunks)

sessions (1) ──< (many) messages
    └─ CASCADE DELETE (deleting session deletes all messages)
```

**Foreign Keys:**
- `chunks.document_id` → `documents.id`
- `messages.session_id` → `sessions.id`

---

## Best Practices

1. **Always regenerate after model changes:**
   ```bash
   python scripts/docs/generate_schema.py
   ```

2. **Test migrations on development database first:**
   ```bash
   DATABASE_URL="postgresql://postgres:postgres@localhost:5432/askdocs_test" \
   alembic upgrade head
   ```

3. **Commit schema docs with model changes:**
   ```bash
   git add app/db/models.py docs/core/architecture/schema.*
   ```

4. **Review Alembic migrations before applying:**
   - Check for data loss
   - Verify indexes are created
   - Test rollback capability

---

## See Also

- [docs/development/SCHEMA_GENERATION.md](docs/development/SCHEMA_GENERATION.md) - Full documentation
- [docs/core/architecture/DATABASE_SCHEMA.md](docs/core/architecture/DATABASE_SCHEMA.md) - Schema design
- [app/db/models.py](app/db/models.py) - SQLAlchemy models
