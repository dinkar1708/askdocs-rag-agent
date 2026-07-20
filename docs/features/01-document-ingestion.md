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
  "uploaded_at": "2026-07-20T10:30:00Z"
}
```

### 2. What Happens Behind the Scenes

```
Your PDF
    ↓
1. Extract text from each page (preserves page numbers)
    ↓
2. Split text into chunks (512 tokens each, 128 overlap)
    ↓
3. Convert each chunk to a vector embedding
    ↓
4. Store in PostgreSQL with pgvector
    ↓
Ready for questions!
```

**Example chunks from a handbook:**

```
Chunk 1 (page 7):
"Employees receive 15 days of paid vacation per year. Unused vacation
days can be carried over up to a maximum of 5 days..."

Chunk 2 (page 7-8):  ← 128 token overlap with Chunk 1
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

### ❌ Not Currently Supported
- Scanned PDFs (images, not text) - OCR coming soon
- Password-protected PDFs
- Files over 10MB (configurable)

---

## Configuration

**Chunk size:**
```bash
# .env
CHUNK_SIZE=512         # Tokens per chunk
CHUNK_OVERLAP=128      # Overlap between chunks
```

**Tune chunking based on your documents:**
- **Long documents (100+ pages):** Use smaller chunks (256) for precision
- **Short documents (<10 pages):** Use larger chunks (1024) for context
- **Multi-language:** Keep default (512) - works well for most cases

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

**Current limitations:**
- Synchronous upload (blocks until complete)
- No multi-file upload
- PDFs only

**Future enhancements:**
- [ ] Async ingestion (background queue)
- [ ] Bulk upload endpoint
- [ ] DOCX, TXT, Markdown support
- [ ] OCR for scanned PDFs
- [ ] Document versioning (track changes over time)

---

## Next Steps

After uploading documents:
→ [Grounded Q&A](02-grounded-qa.md) - Ask questions and get cited answers
→ [Document Management](03-document-management.md) - List, view, delete documents
