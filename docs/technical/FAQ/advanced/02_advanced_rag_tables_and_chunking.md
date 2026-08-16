# Advanced Level: Advanced RAG (PDF Tables & Semantic Chunking)

---

## 1. PDF Table Extraction with pdfplumber

### Q1: How does AskDocs extract and convert PDF tables to Markdown?
**Answer:**
In [`app/services/table_processor.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/table_processor.py):

```python
import pdfplumber
from typing import List, Dict, Any

def extract_tables_as_markdown(pdf_path: str) -> List[Dict[str, Any]]:
    """Extract tables from PDF and format as Markdown chunks"""
    table_chunks = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages):
            page_number = page_idx + 1
            tables = page.extract_tables()
            
            for table_idx, table in enumerate(tables):
                if not table or len(table) < 2:
                    continue  # Skip empty or 1-row fragments
                
                # Header row
                header = [str(cell).strip() if cell else "" for cell in table[0]]
                separator = [":---" for _ in header]
                
                md_lines = [
                    "| " + " | ".join(header) + " |",
                    "| " + " | ".join(separator) + " |"
                ]
                
                # Data rows
                for row in table[1:]:
                    clean_row = [str(cell).strip().replace("\n", " ") if cell else "" for cell in row]
                    md_lines.append("| " + " | ".join(clean_row) + " |")
                
                markdown_table = "\n".join(md_lines)
                
                table_chunks.append({
                    "text": markdown_table,
                    "page_number": page_number,
                    "chunk_type": "table",
                    "chunk_metadata": {
                        "table_index": table_idx,
                        "rows": len(table),
                        "columns": len(header)
                    }
                })
                
    return table_chunks
```

---

## 2. Dynamic Metadata SQL Injection Prevention

### Q2: How does AskDocs validate dynamic JSON filter keys?
**Answer:**
In [`app/services/retriever.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/retriever.py):

```python
import re
from typing import Dict, Any, Tuple
from sqlalchemy import text

# Whitelist: only alphanumeric and underscores allowed in JSON keys
SAFE_KEY_REGEX = re.compile(r"^[a-zA-Z0-9_]+$")

def build_safe_metadata_conditions(metadata_filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Build safe SQL WHERE clauses for PostgreSQL JSON metadata"""
    if not metadata_filters:
        return "", {}
        
    conditions = []
    params = {}
    
    for key, val in metadata_filters.items():
        # SECURITY: Validate key against regex pattern
        if not SAFE_KEY_REGEX.match(key):
            raise ValueError(f"Invalid metadata key rejected: '{key}'. Only alphanumeric and underscores allowed.")
            
        param_name = f"filter_{key}"
        # Use PostgreSQL ->> operator with validated key and bound parameter value
        conditions.append(f"d.doc_metadata->>'{key}' = :{param_name}")
        params[param_name] = str(val)
        
    where_sql = " AND " + " AND ".join(conditions)
    return where_sql, params
```
