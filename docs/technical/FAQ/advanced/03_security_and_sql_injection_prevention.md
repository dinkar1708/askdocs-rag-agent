# Advanced Level: Security, Auth & SQL Injection Defense

---

## 1. SQL Injection Prevention on Dynamic JSON Metadata

### Q1: How does AskDocs prevent SQL injection when querying dynamic JSON metadata?
**Answer:**
In [`app/services/retriever.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/retriever.py), metadata filters allow users to filter documents by custom keys (e.g. `{"department": "HR", "year": "2024"}`).

To prevent SQL injection when building PostgreSQL JSON operators (`->>`):
1. **Strict Regex Validation on Keys**:
   ```python
   SAFE_METADATA_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9_]+$')
   
   for key, value in metadata_filters.items():
       if not SAFE_METADATA_KEY_PATTERN.match(key):
           raise ValueError(f"Invalid metadata key '{key}'. Only alphanumeric and underscores allowed.")
   ```
2. **Parameterized Values**:
   ```python
   # Key is verified safe; value is strictly parameterized
   metadata_conditions.append(f"d.doc_metadata->>'{key}' = :filter_{key}")
   params[f"filter_{key}"] = str(value)
   ```
   Values are never concatenated directly into the SQL string.

---

## 2. API Authentication & Security

### Q2: How is the API secured?
**Answer:**
1. **API Key Authentication**: In [`app/core/auth.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/core/auth.py), FastAPI dependencies enforce valid `X-API-Key` headers on all `/documents` and `/ask` routes.
2. **CORS Security**: Cross-Origin Resource Sharing is locked down via `CORS_ORIGINS` in `app/main.py`.
3. **Upload Guardrails**: Maximum upload size is enforced (50MB) and MIME types are validated before parsing.
