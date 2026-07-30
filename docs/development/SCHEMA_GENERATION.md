# Database Schema Documentation Generation

This guide explains how to automatically generate database schema documentation from SQLAlchemy models.

---

## Quick Start

Generate all schema documentation with a single command:

```bash
python scripts/docs/generate_schema.py
```

This will create:
- `docs/core/architecture/schema.png` - Visual ERD diagram
- `docs/core/architecture/schema.mmd` - Mermaid diagram (for GitHub/GitLab)
- `docs/core/architecture/schema_details.txt` - Detailed text schema

---

## What Gets Generated

### 1. PNG Diagram (schema.png)

A visual Entity-Relationship Diagram showing:
- All database tables
- Columns with their types
- Primary keys (PK)
- Foreign keys (FK)
- Relationships between tables

**Use case:** Include in presentations, documentation sites, or wikis.

### 2. Mermaid Diagram (schema.mmd)

A text-based diagram that renders in:
- GitHub markdown files
- GitLab markdown files
- Documentation sites (MkDocs, Docusaurus, etc.)

**Use case:** Include in README.md or technical documentation.

**Example:**
```markdown
\`\`\`mermaid
erDiagram
    DOCUMENTS ||--o{ CHUNKS : "has many"
    SESSIONS ||--o{ MESSAGES : "has many"
\`\`\`
```

### 3. Detailed Text Schema (schema_details.txt)

Complete schema specification with:
- Table descriptions
- Column types, nullability, defaults
- Primary and foreign keys
- Relationships and cascade options
- Index information

**Use case:** Reference for developers, database administrators.

---

## Prerequisites

The schema generation tool requires:

```bash
# Install dependencies
pip install eralchemy2 pydot graphviz

# macOS: Install graphviz system dependency
brew install graphviz

# Linux (Ubuntu/Debian):
sudo apt-get install graphviz

# Linux (RHEL/CentOS):
sudo yum install graphviz
```

---

## When to Regenerate

Regenerate schema documentation when you:

1. ✅ Add a new SQLAlchemy model
2. ✅ Modify existing model fields
3. ✅ Change relationships between models
4. ✅ Add/remove indexes
5. ✅ Update foreign key constraints

**Best practice:** Run `python scripts/docs/generate_schema.py` before committing database model changes.

---

## Integration with Development Workflow

### Pre-commit Hook (Recommended)

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
# Regenerate schema if models changed
if git diff --cached --name-only | grep -q "app/db/models.py"; then
    echo "📊 Database models changed, regenerating schema..."
    python scripts/docs/generate_schema.py
    git add docs/core/architecture/schema.*
fi
```

### CI/CD Integration

Add to your GitHub Actions workflow:

```yaml
- name: Check schema is up to date
  run: |
    python scripts/docs/generate_schema.py
    git diff --exit-code docs/core/architecture/
```

This ensures schema docs are never out of sync with models.

---

## How It Works

The `generate_schema.py` script:

1. **Imports SQLAlchemy models** from `app/db/models.py`
2. **Uses eralchemy2** to generate PNG from model metadata
3. **Creates Mermaid diagram** from relationship definitions
4. **Inspects models** to generate detailed text documentation

**Advantages:**
- ✅ Always accurate (generated from code)
- ✅ No manual updates required
- ✅ Multiple output formats
- ✅ Fast and automated

---

## Customization

### Change Output Directory

Edit `generate_schema.py`:

```python
output_dir = Path("docs/custom/path")
```

### Change Diagram Style

For PNG, customize eralchemy2 options:

```python
from eralchemy2 import render_er

render_er(
    Base,
    output_path,
    mode='graph',  # or 'erd'
    include_tables=['documents', 'chunks']  # Filter specific tables
)
```

### Add Database Connection

To generate from live database instead of models:

```python
from eralchemy2 import render_er

db_url = "postgresql://user:pass@localhost/dbname"
render_er(db_url, "schema.png")
```

---

## Alternative Tools

If `eralchemy2` doesn't meet your needs, consider:

### dbdocs.io
- Web-based collaborative documentation
- Uses DBML format
- Team sharing and versioning

### SchemaSpy
- Java-based tool
- Generates HTML documentation
- Supports many database types

### PlantUML
- Text-to-diagram tool
- More customization options
- Requires Java

### DBeaver
- GUI database tool
- Export ERD from live database
- Visual schema editor

---

## Troubleshooting

### "Command 'dot' not found"

Install graphviz system dependency:
```bash
# macOS
brew install graphviz

# Linux
sudo apt-get install graphviz
```

### "No module named 'eralchemy2'"

Install Python dependencies:
```bash
pip install eralchemy2 pydot
```

### "Permission denied: generate_schema.py"

Make script executable:
```bash
chmod +x generate_schema.py
```

### PNG is empty or corrupted

Ensure graphviz is properly installed:
```bash
dot -V  # Should show version
```

---

## Best Practices

1. **Version control schema artifacts**
   - Commit generated `.png`, `.mmd`, and `.txt` files
   - Track schema evolution over time

2. **Automate generation**
   - Use pre-commit hooks
   - Add to CI/CD pipeline

3. **Keep documentation in sync**
   - Regenerate after model changes
   - Review diffs before committing

4. **Use multiple formats**
   - PNG for presentations
   - Mermaid for GitHub/docs
   - Text for detailed reference

5. **Document custom indexes**
   - Update script to include custom indexes
   - Add performance notes

---

## See Also

- [DATABASE_SCHEMA.md](../core/architecture/DATABASE_SCHEMA.md) - Current schema design
- [app/db/models.py](../../app/db/models.py) - SQLAlchemy models
- [Alembic Migrations](../../alembic/versions/) - Schema migration history
