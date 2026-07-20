# Feature: Advanced Filters & Metadata

**What:** Add custom metadata to documents and filter queries by department, date, type, version, or any custom field.

**Why it matters:** Search only relevant documents (e.g., only GG11 job descriptions, only 2026 policies) to improve answer quality and reduce noise.

---

## User Story

```
As a recruiter,
I want to filter job descriptions by grade level and department,
So I only get answers about relevant roles without mixing junior and senior requirements.
```

---

## How It Works

### Upload Document with Metadata

**Request:**
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@job_description.pdf" \
  -F 'metadata={
    "department": "Engineering",
    "grade": "GG11",
    "type": "job_description",
    "effective_date": "2026-01-01",
    "version": "2.1",
    "tags": ["AI", "remote", "leadership"]
  }'
```

**Response:**
```json
{
  "id": "doc_123",
  "filename": "job_description.pdf",
  "page_count": 3,
  "chunk_count": 12,
  "metadata": {
    "department": "Engineering",
    "grade": "GG11",
    "type": "job_description",
    "effective_date": "2026-01-01",
    "version": "2.1",
    "tags": ["AI", "remote", "leadership"]
  },
  "uploaded_at": "2026-07-20T10:30:00Z"
}
```

---

### Query with Filters

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the experience requirements?",
    "filters": {
      "department": "Engineering",
      "grade": ["GG10", "GG11"],
      "type": "job_description"
    }
  }'
```

**Response:**
```json
{
  "answer": "For GG11 Engineering roles, 8+ years of experience with 4+ years in AI/ML leadership is required. For GG10, 5-7 years with 2+ years in ML/AI.",
  "sources": [
    {
      "document": "job_gg11.pdf",
      "page": 1,
      "metadata": {"grade": "GG11", "department": "Engineering"}
    },
    {
      "document": "job_gg10.pdf",
      "page": 1,
      "metadata": {"grade": "GG10", "department": "Engineering"}
    }
  ],
  "documents_searched": 2,
  "documents_filtered_out": 15
}
```

**Notice:** Only searched 2 documents (GG10, GG11 Engineering) instead of all 17 uploaded documents.

---

### Filter by Date Range

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the vacation policy?",
    "filters": {
      "type": "employee_handbook",
      "effective_date": {
        "gte": "2026-01-01"
      }
    }
  }'
```

**Result:** Only searches handbooks effective from January 2026 onwards (ignores outdated 2025 policies).

---

### Filter by Tags

**Request:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What remote work options are available?",
    "filters": {
      "tags": ["remote"]
    }
  }'
```

**Result:** Only searches documents tagged with "remote".

---

## Behind the Scenes

### Database Schema Update

**Add metadata column to documents table:**
```sql
ALTER TABLE documents
ADD COLUMN metadata JSONB DEFAULT '{}';

-- Index for fast filtering
CREATE INDEX idx_documents_metadata ON documents USING GIN (metadata);
```

---

### Filtering Pipeline

```
User Query + Filters
    ↓
1. Apply document-level filters
   SELECT * FROM documents
   WHERE metadata->>'department' = 'Engineering'
     AND metadata->>'grade' IN ('GG10', 'GG11')
   → Returns: 2 documents
    ↓
2. Retrieve chunks ONLY from filtered documents
   SELECT * FROM chunks
   WHERE document_id IN (filtered_document_ids)
   → Returns: 24 chunks (from 2 docs)
    ↓
3. Vector search within filtered chunks
   → Top-5 chunks from filtered set
    ↓
4. Generate answer using filtered chunks
    ↓
Return answer + metadata about filtering
```

---

## Use Cases

### Use Case 1: Job Board Filtering

**Scenario:** HR portal with 100+ job descriptions.

**Without filters:**
```bash
POST /ask
{"question": "What are the AI engineer requirements?"}

# Returns: Mixed results from GG7, GG9, GG10, GG11 (confusing!)
```

**With filters:**
```bash
POST /ask
{
  "question": "What are the AI engineer requirements?",
  "filters": {"grade": "GG11", "department": "Engineering"}
}

# Returns: Only GG11 Engineering requirements (precise!)
```

---

### Use Case 2: Policy Version Control

**Scenario:** Company updates handbook annually.

**Problem:** Both 2025 and 2026 handbooks are uploaded. User asks about vacation policy.

**Without filters:**
```
Answer: "Employees receive 15 days of vacation..." (from 2025 - OUTDATED!)
```

**With filters:**
```bash
POST /ask
{
  "question": "What is the vacation policy?",
  "filters": {
    "type": "employee_handbook",
    "effective_date": {"gte": "2026-01-01"}
  }
}

# Returns: "Employees receive 18 days..." (from 2026 - CURRENT!)
```

---

### Use Case 3: Multi-Tenant Isolation

**Scenario:** SaaS product serving multiple companies.

**Implementation:**
```bash
# Company A uploads document
POST /documents
metadata: {"tenant_id": "company_a"}

# Company A queries
POST /ask
filters: {"tenant_id": "company_a"}

# Company B queries
POST /ask
filters: {"tenant_id": "company_b"}

# Result: Perfect tenant isolation
```

---

## Metadata Schema Examples

### Job Descriptions

```json
{
  "type": "job_description",
  "department": "Engineering",
  "grade": "GG11",
  "location": "Remote",
  "employment_type": "Full-time",
  "posted_date": "2026-07-15",
  "tags": ["AI", "ML", "leadership"]
}
```

---

### Employee Handbook

```json
{
  "type": "employee_handbook",
  "version": "2026.1",
  "effective_date": "2026-01-01",
  "expiry_date": "2026-12-31",
  "department": null,
  "tags": ["HR", "policies"]
}
```

---

### Contract

```json
{
  "type": "contract",
  "contract_type": "NDA",
  "version": "3.2",
  "effective_date": "2025-06-01",
  "parties": ["Company", "Vendor"],
  "tags": ["confidential", "legal"]
}
```

---

### Support Documentation

```json
{
  "type": "support_doc",
  "product": "askdocs",
  "category": "API",
  "version": "v1.2",
  "last_updated": "2026-07-20",
  "tags": ["technical", "developer"]
}
```

---

## Filter Operators

### Equality

```json
{
  "filters": {
    "department": "Engineering"
  }
}
```

**SQL:** `metadata->>'department' = 'Engineering'`

---

### In Array

```json
{
  "filters": {
    "grade": ["GG10", "GG11"]
  }
}
```

**SQL:** `metadata->>'grade' IN ('GG10', 'GG11')`

---

### Date Comparison

```json
{
  "filters": {
    "effective_date": {
      "gte": "2026-01-01",
      "lt": "2027-01-01"
    }
  }
}
```

**SQL:** `metadata->>'effective_date' >= '2026-01-01' AND metadata->>'effective_date' < '2027-01-01'`

---

### Tag Contains

```json
{
  "filters": {
    "tags": ["remote"]
  }
}
```

**SQL:** `metadata->'tags' ? 'remote'` (JSONB contains operator)

---

### Null/Exists Check

```json
{
  "filters": {
    "department": {"exists": true}
  }
}
```

**SQL:** `metadata ? 'department'`

---

## Configuration

### Default Metadata Fields

```bash
# .env
REQUIRED_METADATA_FIELDS=type  # Enforce 'type' field on all documents
METADATA_SCHEMA_VALIDATION=true  # Validate metadata against schema
```

---

### Auto-Metadata Extraction

```bash
# .env
AUTO_EXTRACT_METADATA=true  # Use LLM to extract metadata from document
```

**Example:**
```bash
# Upload without metadata
POST /documents -F "file=@handbook.pdf"

# System auto-extracts:
{
  "type": "employee_handbook",
  "version": "2026",
  "detected_topics": ["vacation", "benefits", "remote work"]
}
```

---

## List Documents with Filters

**Request:**
```bash
curl "http://localhost:8000/documents?department=Engineering&grade=GG11"
```

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "job_gg11.pdf",
      "metadata": {"department": "Engineering", "grade": "GG11"}
    }
  ],
  "total": 1,
  "filtered_from": 17
}
```

---

## Update Document Metadata

**Request:**
```bash
curl -X PATCH http://localhost:8000/documents/doc_123 \
  -H "Content-Type: application/json" \
  -d '{
    "metadata": {
      "status": "archived",
      "archived_date": "2026-07-20"
    }
  }'
```

**Use case:** Mark outdated documents without deleting them.

---

## Analytics with Metadata

### Documents by Type

```bash
curl http://localhost:8000/analytics/documents/by-metadata?field=type
```

**Response:**
```json
{
  "job_description": 25,
  "employee_handbook": 3,
  "contract": 15,
  "support_doc": 8
}
```

---

### Documents by Department

```bash
curl http://localhost:8000/analytics/documents/by-metadata?field=department
```

**Response:**
```json
{
  "Engineering": 30,
  "HR": 10,
  "Legal": 8,
  null: 5
}
```

---

## Real-World Example: Multi-Department HR Portal

**Company:** 500-employee company with centralized HR portal

**Documents:**
- 50 job descriptions (Engineering, Sales, Marketing, HR)
- 5 employee handbooks (one per department + company-wide)
- 100+ policy documents

**Implementation:**

**1. Tag all documents:**
```bash
# Engineering docs
metadata: {"department": "Engineering", "type": "job_description"}

# HR policies
metadata: {"department": null, "type": "policy", "applies_to": "all"}
```

**2. Department-specific queries:**
```bash
# Engineering employee asks:
POST /ask
{
  "question": "What are the vacation days?",
  "filters": {
    "department": ["Engineering", null]  # Eng-specific + company-wide
  }
}
```

**3. Role-specific queries:**
```bash
# Recruiter asks:
POST /ask
{
  "question": "What are senior engineering requirements?",
  "filters": {
    "department": "Engineering",
    "grade": ["GG10", "GG11"],
    "type": "job_description"
  }
}
```

---

## Limitations & Future Plans

**Current limitations:**
- Metadata must be added at upload time (can't auto-extract complex metadata)
- No nested filter queries (e.g., "department=Eng AND (grade=GG10 OR location=Remote)")
- No metadata versioning (can't track changes to metadata over time)

**Future enhancements:**
- [ ] Auto-extract metadata using LLM on upload
- [ ] Complex filter queries (AND, OR, NOT logic)
- [ ] Metadata versioning and history
- [ ] Metadata templates per document type
- [ ] Metadata validation schemas
- [ ] Bulk metadata updates
- [ ] Metadata-based access control (RBAC)

---

## API Reference

### POST /documents (with metadata)

**Request:**
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@doc.pdf" \
  -F 'metadata={"key": "value"}'
```

---

### POST /ask (with filters)

**Request:**
```json
{
  "question": "string",
  "filters": {
    "field": "value",
    "field2": ["value1", "value2"],
    "date_field": {"gte": "2026-01-01"}
  }
}
```

---

### GET /documents (with filters)

**Request:**
```bash
curl "http://localhost:8000/documents?field=value&field2=value2"
```

---

### PATCH /documents/{id}

**Request:**
```json
{
  "metadata": {
    "key": "new_value"
  }
}
```

---

## Next Steps

→ [Structured Extraction](08-structured-extraction.md) - Extract metadata from documents
→ [Comparative Analysis](09-comparative-analysis.md) - Compare filtered documents
→ [Document Management](03-document-management.md) - CRUD operations
