#!/usr/bin/env python3
"""
Generate database schema diagrams from SQLAlchemy models.

This script creates:
1. PNG diagram (ERD with relationships)
2. Mermaid diagram (for GitHub/GitLab markdown)
3. Text-based schema documentation

Usage:
    python generate_schema.py

Output:
    - docs/core/architecture/schema.png
    - docs/core/architecture/schema.mmd
    - docs/core/architecture/schema_details.txt
"""

import os
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from app.db.models import Base, Document, Chunk, Session, Message
from eralchemy2 import render_er


def generate_png_diagram(output_path: str):
    """Generate PNG ERD using eralchemy2."""
    print(f"📊 Generating PNG diagram: {output_path}")

    # Use SQLAlchemy models directly
    render_er(Base, output_path)
    print(f"✅ PNG diagram created: {output_path}")


def generate_mermaid_diagram(output_path: str):
    """Generate Mermaid ERD for markdown rendering."""
    print(f"📊 Generating Mermaid diagram: {output_path}")

    mermaid = """erDiagram
    DOCUMENTS ||--o{ CHUNKS : "has many"
    SESSIONS ||--o{ MESSAGES : "has many"

    DOCUMENTS {
        int id PK "Primary Key"
        string filename "VARCHAR(255)"
        int page_count "Number of pages"
        timestamp uploaded_at "Upload timestamp"
        json doc_metadata "Custom metadata (dept, grade, tags)"
    }

    CHUNKS {
        int id PK "Primary Key"
        int document_id FK "Foreign Key to documents"
        text text "Chunk text content"
        int page_number "Page number"
        vector embedding "Vector(384) - MiniLM embeddings"
        string chunk_type "Type: text or table"
        json chunk_metadata "Headers, bbox, etc."
        timestamp created_at "Creation timestamp"
    }

    SESSIONS {
        int id PK "Primary Key"
        timestamp created_at "Session start time"
        timestamp last_accessed "Last activity (auto-updated)"
    }

    MESSAGES {
        int id PK "Primary Key"
        int session_id FK "Foreign Key to sessions"
        string role "user or assistant"
        text content "Message text"
        json sources "Source citations (nullable)"
        timestamp created_at "Message timestamp"
    }
"""

    with open(output_path, 'w') as f:
        f.write(mermaid)

    print(f"✅ Mermaid diagram created: {output_path}")


def generate_text_schema(output_path: str):
    """Generate detailed text-based schema documentation."""
    print(f"📊 Generating text schema: {output_path}")

    # Inspect models
    from sqlalchemy import inspect as sql_inspect

    schema_text = "# Database Schema Details\n\n"
    schema_text += "Auto-generated from SQLAlchemy models\n\n"
    schema_text += "---\n\n"

    models = [Document, Chunk, Session, Message]

    for model in models:
        mapper = sql_inspect(model)
        schema_text += f"## {model.__tablename__.upper()}\n\n"
        schema_text += f"**Model:** {model.__name__}\n\n"

        if model.__doc__:
            schema_text += f"**Description:** {model.__doc__.strip()}\n\n"

        schema_text += "**Columns:**\n\n"
        schema_text += "| Column | Type | Nullable | Default | Description |\n"
        schema_text += "|--------|------|----------|---------|-------------|\n"

        for column in mapper.columns:
            col_name = column.name
            col_type = str(column.type)
            nullable = "Yes" if column.nullable else "No"

            # Get default value
            default = "None"
            if column.default is not None:
                default = str(column.default.arg) if hasattr(column.default, 'arg') else str(column.default)

            # Check if primary key or foreign key
            description = []
            if column.primary_key:
                description.append("🔑 Primary Key")
            if column.foreign_keys:
                fk = list(column.foreign_keys)[0]
                description.append(f"🔗 FK → {fk.column}")
            if column.index:
                description.append("📇 Indexed")

            desc_str = ", ".join(description) if description else "-"

            schema_text += f"| `{col_name}` | {col_type} | {nullable} | {default} | {desc_str} |\n"

        # Add relationships
        if mapper.relationships:
            schema_text += "\n**Relationships:**\n\n"
            for rel_name, rel in mapper.relationships.items():
                cascade = rel.cascade if hasattr(rel, 'cascade') else "None"
                schema_text += f"- `{rel_name}` → {rel.mapper.class_.__name__} (cascade: {cascade})\n"

        schema_text += "\n---\n\n"

    # Add indexes information
    schema_text += "## Indexes\n\n"
    schema_text += "- `documents.id` - B-tree (primary key)\n"
    schema_text += "- `chunks.id` - B-tree (primary key)\n"
    schema_text += "- `chunks.document_id` - B-tree (foreign key)\n"
    schema_text += "- `sessions.id` - B-tree (primary key)\n"
    schema_text += "- `messages.id` - B-tree (primary key)\n"
    schema_text += "- `messages.session_id` - B-tree (foreign key)\n"
    schema_text += "\n**Note:** Vector similarity index should be added in production for performance.\n\n"

    with open(output_path, 'w') as f:
        f.write(schema_text)

    print(f"✅ Text schema created: {output_path}")


def main():
    """Main function to generate all schema documentation."""
    # Create output directory
    output_dir = Path("docs/core/architecture")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("🔧 Database Schema Generator")
    print("=" * 60)
    print()

    # Generate PNG diagram
    png_path = output_dir / "schema.png"
    try:
        generate_png_diagram(str(png_path))
    except Exception as e:
        print(f"⚠️  Failed to generate PNG: {e}")
        print("   Make sure graphviz is installed: brew install graphviz")

    print()

    # Generate Mermaid diagram
    mermaid_path = output_dir / "schema.mmd"
    generate_mermaid_diagram(str(mermaid_path))

    print()

    # Generate text schema
    text_path = output_dir / "schema_details.txt"
    generate_text_schema(str(text_path))

    print()
    print("=" * 60)
    print("✅ All schema documentation generated successfully!")
    print("=" * 60)
    print()
    print("📁 Output files:")
    print(f"   - {png_path}")
    print(f"   - {mermaid_path}")
    print(f"   - {text_path}")
    print()
    print("💡 To view the Mermaid diagram:")
    print("   Add the .mmd content to any GitHub/GitLab markdown file")
    print()


if __name__ == "__main__":
    main()
