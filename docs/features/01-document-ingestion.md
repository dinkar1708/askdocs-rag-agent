# Feature: Document Ingestion

**What:** Upload PDF documents and automatically index them for question answering.

**Who needs it:** Anyone with policy documents, manuals, handbooks, or technical docs that need to be searchable.

---

## User Story

```
As a business owner,
I want to upload my policy documents once,
So that customers can ask questions and get accurate answers without me manually searching.
```

---

## How It Works

### 1. Upload a PDF

**Via API:**
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@employee-handbook.pdf"
```

**Via Swagger UI:**
1. Open http://localhost:8000/docs
2. Click `POST /documents`
3. Click "Try it out"
4. Choose your PDF file
5. Click "Execute"

**Result:**
```json
{
  "id": "doc_123",
  "filename": "employee-handbook.pdf",
  "page_count": 42,
  "chunk_count": 156,
  "uploaded_at": "2026-07-20T10:30:00Z",
  "content_hash": "sha256:abc123..."
}
```

**Duplicate Upload Prevention:**
If you try to upload the same file again:
```json
{
  "detail": "Document already exists with ID 42. Upload date: 2026-07-20T10:30:00Z",
  "status_code": 409
}
```

### 2. What Happens Behind the Scenes

```
Your PDF
    ↓
1. Calculate SHA-256 hash (duplicate detection)
    ↓
2. Check if document already exists
    ↓
3. Extract text from each page using PyPDF2 (preserves page numbers)
    ↓
4. Split text into chunks (512 tokens each, 128 token overlap)
    ↓
5. Convert each chunk to a 384-dim vector embedding (all-MiniLM-L6-v2)
    ↓
6. Store in PostgreSQL with pgvector (atomic transaction)
    ↓
Ready for questions!
```

**Technical Details:**
- **Duplicate Detection:** SHA-256 content hashing (prevents duplicate uploads)
- **Text Extraction:** PyPDF2's `extract_text()` - works well for text-based PDFs
- **Chunking:** Fixed-size token chunking (512 tokens, 128 overlap)
- **Embedding Model:** sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
- **Vector Index:** pgvector with HNSW (Hierarchical Navigable Small World) for fast similarity search
- **Atomic Uploads:** Document and chunks saved in single transaction (no orphan documents)

**Example chunks from a handbook:**

```
Chunk 1 (page 7):
"Employees receive 15 days of paid vacation per year. Unused vacation
days can be carried over up to a maximum of 5 days..."

Chunk 2 (page 7-8):  ← 50 character overlap with Chunk 1
"...days can be carried over up to a maximum of 5 days. Sick leave is
separate and employees receive 10 days of paid sick leave annually..."

Chunk 3 (page 8):
"...paid sick leave annually. To request time off, employees must
submit a request via the HR portal at least 2 weeks in advance..."
```

---

## What Documents Work Best?

### ✅ Good for Ingestion
- Text-based PDFs (created from Word, Google Docs, etc.)
- Policy documents, handbooks, terms & conditions
- Technical manuals, user guides
- Contract templates, legal documents

### ⚠️ Limited Support
- **Tables in PDFs** - Text is extracted but table structure is lost
- **Images/Diagrams** - Currently ignored, only text is extracted (tested for robustness)
  - Test case: `test_pdf_with_embedded_images_robustness`
  - Test file: `app/samples/test-files/pdf-with-image.pdf`
  - Verifies: Text extraction works correctly even with embedded images present
- **Complex layouts** - Multi-column or hierarchical content may lose structure

### ❌ Not Currently Supported
- Scanned PDFs (images, not text) - OCR required
- Password-protected PDFs
- Excel/CSV files with structured data
- DOCX, TXT, Markdown files
- Files over 50MB (current limit)
- PDFs with forms or interactive elements

---

## Configuration

**Chunk size (in code, not configurable via .env yet):**
```python
# app/services/embeddings.py
chunk_size = 500        # Characters per chunk (not tokens)
overlap = 50            # Character overlap between chunks
```

**Note:** Chunking parameters are currently hardcoded. Configuration via environment variables is planned for a future release.

**Tuning recommendations:**
- **Current implementation** works well for most text-based documents
- For documents with tables or technical content, consider the advanced chunking roadmap below

---

## Verify Ingestion Worked

**Check document was indexed:**
```bash
curl http://localhost:8000/documents
```

**Search for a chunk:**
```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "vacation policy", "top_k": 3}'
```

**Expected:** You should see relevant chunks with high scores (>0.7).

---

## Real-World Example

**Company:** Mid-size tech company with 200 employees

**Problem:**
- 80-page employee handbook
- HR gets 50+ questions/week about policies
- Employees waste time searching PDF manually

**Solution:**
1. Upload handbook via `POST /documents`
2. Indexed in ~30 seconds (80 pages → 287 chunks)
3. Hook up Slack bot to `/ask` endpoint
4. Employees ask questions in Slack, get instant cited answers

**Result:**
- HR questions reduced by 60%
- Average response time: 2 seconds (vs 10+ minutes manual search)

---

## Limitations & Future Plans

### Current Limitations

**Architecture:**
- Synchronous upload (blocks until complete)
- No multi-file upload
- Simple character-based chunking (doesn't respect semantic boundaries)

**Document Types:**
- PDFs only (DOCX, Excel, TXT not supported)
- Text extraction only (tables lose structure, images ignored)
- No OCR for scanned PDFs

**Chunking Strategy:**
- Fixed 500-character chunks (not semantically aware)
- No hierarchical relationships (sections, subsections)
- Tables split arbitrarily across chunks

### Planned Enhancements

**Phase 1: Better Document Processing** (High Priority)
- [ ] **Table extraction** - Preserve table structure using pdfplumber
- [ ] **Semantic chunking** - Chunk by topic/section instead of character count
- [ ] **Document structure preservation** - Track headers, lists, hierarchies
- [ ] **Excel/CSV ingestion** - Support structured data files
- [ ] Sample test files for tables, images, Excel

**Phase 2: Advanced Features**
- [ ] **Reranking** - Two-stage retrieval for better relevance
- [ ] **Multimodal support** - Extract and index images/diagrams
- [ ] **OCR for scanned PDFs** - Support image-based PDFs
- [ ] DOCX, TXT, Markdown support

**Phase 3: Operational Improvements**
- [ ] Async ingestion (background queue)
- [ ] Bulk upload endpoint
- [ ] Document versioning (track changes over time)
- [ ] Configurable chunking via environment variables

See [ROADMAP.md](../ROADMAP.md) for detailed technical plans.

---

## TODO: LangGraph-Based Background Async Ingestion

**Status:** Will be implemented later

**What:** Background job processing for document uploads using LangGraph state machine to handle extraction → chunking → embedding → indexing pipeline asynchronously.

**Current Problem:**
- Document upload blocks HTTP request for entire pipeline
- Large PDFs (100+ pages) tie up API workers
- No progress tracking or retry logic
- User must wait for completion (10-30 seconds for large docs)

**Why LangGraph:**
- Job state machine with clear stages: queued → extracting → chunking → embedding → indexing → complete
- Automatic error handling with exponential backoff retries
- Progress tracking at each stage
- Conditional paths for different file types (PDF vs DOCX vs TXT)

**Implementation Plan:**

1. **StateGraph Architecture:**
   ```
   Accept Job (return job_id immediately)
     ↓
   Extract Text (PDF → text, page by page)
     ↓
   Chunk Text (semantic chunking)
     ↓
   Batch Embed (all chunks at once)
     ↓
   Store in DB (atomic transaction)
     ↓
   Mark Complete (or retry on error)
   ```

2. **API Changes:**
   - `POST /documents` - Returns `job_id` immediately, processes in background
   - `GET /documents/jobs/{job_id}` - Poll for progress and status
   - Frontend shows progress bar: "Extracting text... 40%"

3. **Benefits:**
   - Non-blocking uploads (API responds instantly)
   - Better resource utilization (batch processing)
   - Progress tracking for UX
   - Automatic retries on transient failures
   - Scales to very large documents

---

## Next Steps

After uploading documents:
→ [Grounded Q&A](02-grounded-qa.md) - Ask questions and get cited answers
→ [Document Management](03-document-management.md) - List, view, delete documents
