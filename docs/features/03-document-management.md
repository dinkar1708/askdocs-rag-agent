# Feature: Document Management

**What:** List, view, and delete uploaded documents via API.

**Why it matters:** Keep your document library up to date as policies change.

---

## User Story

```
As a content manager,
I want to see which documents are uploaded and remove outdated ones,
So that users only get answers from current policies.
```

---

## List All Documents

**Request:**
```bash
curl http://localhost:8000/documents
```

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_123",
      "filename": "employee-handbook-2026.pdf",
      "page_count": 42,
      "chunk_count": 156,
      "uploaded_at": "2026-07-20T10:30:00Z"
    },
    {
      "id": "doc_456",
      "filename": "terms-and-conditions.pdf",
      "page_count": 15,
      "chunk_count": 58,
      "uploaded_at": "2026-07-15T14:22:00Z"
    }
  ],
  "total": 2
}
```

**Pagination:**
```bash
curl "http://localhost:8000/documents?limit=10&offset=0"
```

---

## View Document Details

**Request:**
```bash
curl http://localhost:8000/documents/doc_123
```

**Response:**
```json
{
  "id": "doc_123",
  "filename": "employee-handbook-2026.pdf",
  "page_count": 42,
  "chunk_count": 156,
  "uploaded_at": "2026-07-20T10:30:00Z",
  "metadata": {},
  "chunks_preview": [
    {
      "id": "chunk_001",
      "text": "Employees are entitled to 15 days of paid vacation...",
      "page_num": 7,
      "chunk_index": 0
    }
  ]
}
```

**Use case:** Debug which chunks are indexed for a document.

---

## Delete a Document

**Request:**
```bash
curl -X DELETE http://localhost:8000/documents/doc_123
```

**Response:**
```json
{
  "deleted": true,
  "document_id": "doc_123",
  "chunks_removed": 156
}
```

**What happens:**
- Document record deleted from database
- All associated chunks deleted (cascade)
- Vector embeddings removed
- Future questions won't retrieve from this document

**Important:** This is irreversible. No soft delete.

---

## Real-World Workflow: Policy Update

**Scenario:** Your company updates its employee handbook every January.

**Workflow:**

### 1. Check Current Version
```bash
curl http://localhost:8000/documents
# Shows: "employee-handbook-2025.pdf" uploaded on 2025-01-15
```

### 2. Upload New Version
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@employee-handbook-2026.pdf"
# Response: doc_id = "doc_789"
```

### 3. Test New Document
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'
```

**Problem:** Answer might blend 2025 and 2026 policies (both indexed)!

### 4. Delete Old Version
```bash
curl -X DELETE http://localhost:8000/documents/doc_123
# Removes 2025 handbook
```

### 5. Verify
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'
# Now only cites 2026 handbook
```

---

## Document Metadata (Future)

**Current:** Metadata field exists but unused.

**Future use cases:**
```json
{
  "metadata": {
    "version": "2026-v1",
    "department": "HR",
    "effective_date": "2026-01-01",
    "expiry_date": "2026-12-31",
    "tags": ["employee", "handbook", "policies"]
  }
}
```

**Future features:**
- Filter documents by tag: `GET /documents?tag=HR`
- Auto-expire old documents
- Version tracking (see all versions of a doc)

---

## Multi-Tenant Isolation (Future)

**Current:** All documents shared.

**Future:** Isolate documents per tenant.

**Example:**
```python
# Tenant A uploads handbook
POST /documents (with header: X-Tenant-ID: tenant_a)

# Tenant B asks question
POST /ask (with header: X-Tenant-ID: tenant_b)
# Only searches tenant_b's documents, not tenant_a's
```

---

## Bulk Operations (Future)

**Upload multiple documents:**
```bash
POST /documents/bulk
Content-Type: multipart/form-data

files: [file1.pdf, file2.pdf, file3.pdf]
```

**Delete multiple documents:**
```bash
DELETE /documents/bulk
Content-Type: application/json

{"ids": ["doc_1", "doc_2", "doc_3"]}
```

---

## Limitations & Future Plans

**Current limitations:**
- No document versioning
- No soft delete (can't restore)
- No change tracking

**Future enhancements:**
- [ ] Document versioning (track history)
- [ ] Soft delete with restore
- [ ] Change notifications (webhook when doc updated)
- [ ] Document expiry dates
- [ ] Bulk upload/delete

---

## Next Steps

→ [Grounded Q&A](02-grounded-qa.md) - Ask questions about uploaded docs
→ [Configuration](../docs/CONFIGURATION.md) - Advanced settings
