# API Reference

Complete REST API documentation with request/response examples.

---

## Base URL

**Local:** `http://localhost:8000`
**Production:** `https://your-service.run.app` (or your deployed URL)

**Swagger UI:** `{base_url}/docs`
**OpenAPI JSON:** `{base_url}/openapi.json`

---

## Authentication

Currently open (no auth). For production, add:
- API key header: `X-API-Key: your_key`
- JWT tokens for multi-tenant
- OAuth2 for user-facing apps

See [Configuration](CONFIGURATION.md#security) for setup.

---

## Endpoints

### Health Check

```http
GET /health
```

Check API and database connectivity.

**Response 200:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-07-20T10:30:00Z"
}
```

**Response 503 (unhealthy):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "could not connect to database"
}
```

---

### Upload Document

```http
POST /documents
Content-Type: multipart/form-data
```

Upload a PDF document for ingestion and indexing.

**Request:**
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@samples/handbook.pdf"
```

**Response 201:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "handbook.pdf",
  "page_count": 42,
  "chunk_count": 156,
  "uploaded_at": "2026-07-20T10:30:00Z",
  "metadata": {}
}
```

**Error Responses:**

| Status | Meaning |
|---|---|
| `400` | Invalid file (not a PDF) |
| `413` | File too large (>10MB default) |
| `422` | PDF extraction failed (corrupt file or scanned PDF) |
| `500` | Server error during ingestion |

**Notes:**
- Ingestion is **synchronous** (blocks until complete)
- Large PDFs (>100 pages) may timeout (use background jobs for production)
- File is not stored permanently (only extracted text + embeddings)

---

### List Documents

```http
GET /documents
```

Retrieve all uploaded documents.

**Response 200:**
```json
{
  "documents": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "filename": "handbook.pdf",
      "page_count": 42,
      "chunk_count": 156,
      "uploaded_at": "2026-07-20T10:30:00Z"
    },
    {
      "id": "987fcdeb-51a2-43f1-b123-987654321000",
      "filename": "terms.pdf",
      "page_count": 15,
      "chunk_count": 58,
      "uploaded_at": "2026-07-19T14:22:00Z"
    }
  ],
  "total": 2
}
```

**Query Parameters:**
- `limit` (int) - Max documents to return (default: 100)
- `offset` (int) - Pagination offset (default: 0)

**Example:**
```bash
curl "http://localhost:8000/documents?limit=10&offset=0"
```

---

### Get Document

```http
GET /documents/{document_id}
```

Retrieve details for a specific document.

**Response 200:**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "filename": "handbook.pdf",
  "page_count": 42,
  "chunk_count": 156,
  "uploaded_at": "2026-07-20T10:30:00Z",
  "metadata": {},
  "chunks_preview": [
    {
      "id": "chunk_001",
      "text": "Employees are entitled to...",
      "page_num": 7,
      "chunk_index": 0
    }
  ]
}
```

**Response 404:**
```json
{
  "detail": "Document not found"
}
```

---

### Delete Document

```http
DELETE /documents/{document_id}
```

Delete a document and all its chunks.

**Response 200:**
```json
{
  "deleted": true,
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "chunks_removed": 156
}
```

**Response 404:**
```json
{
  "detail": "Document not found"
}
```

**Notes:**
- Cascading delete removes all associated chunks
- Irreversible (no soft delete)

---

### Ask Question

```http
POST /ask
Content-Type: application/json
```

Ask a question and get a grounded answer with citations.

**Request:**
```json
{
  "question": "What is the vacation policy?",
  "top_k": 5
}
```

**Parameters:**
- `question` (string, required) - The question to answer
- `top_k` (int, optional) - Number of chunks to retrieve (default: 5)

**Response 200 (answer found):**
```json
{
  "answer": "Employees receive 15 days of paid vacation per year. Unused vacation days can be carried over up to a maximum of 5 days.",
  "sources": [
    {
      "document": "handbook.pdf",
      "page": 7,
      "chunk_id": "chunk_042"
    },
    {
      "document": "handbook.pdf",
      "page": 8,
      "chunk_id": "chunk_043"
    }
  ],
  "confidence": 0.89,
  "status": "answered"
}
```

**Response 200 (not found):**
```json
{
  "answer": "not_found",
  "message": "The documents do not contain information to answer this question.",
  "confidence": 0.12,
  "status": "not_found"
}
```

**Response 200 (clarification needed):**
```json
{
  "answer": "clarify",
  "message": "Your question is ambiguous. Can you provide more context? For example, are you asking about vacation, sick leave, or parental leave?",
  "status": "clarify"
}
```

**Error Responses:**

| Status | Meaning |
|---|---|
| `400` | Missing or empty question |
| `500` | LLM API error or database error |

**Example:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the refund policy?"}'
```

---

### Multi-turn Chat

```http
POST /chat
Content-Type: application/json
```

Ask a question with conversation history for follow-up queries.

**Request:**
```json
{
  "message": "What about international orders?",
  "session_id": "sess_abc123"
}
```

**Parameters:**
- `message` (string, required) - The user's message
- `session_id` (string, optional) - Session ID for conversation history (generated if not provided)

**Response 200:**
```json
{
  "answer": "For international orders, shipping typically takes 7-14 business days. Additional customs fees may apply.",
  "sources": [
    {
      "document": "terms.pdf",
      "page": 12
    }
  ],
  "confidence": 0.91,
  "session_id": "sess_abc123",
  "history": [
    {
      "role": "user",
      "content": "What is the shipping policy?"
    },
    {
      "role": "assistant",
      "content": "We offer free shipping on orders over $50..."
    },
    {
      "role": "user",
      "content": "What about international orders?"
    },
    {
      "role": "assistant",
      "content": "For international orders, shipping typically takes 7-14 business days..."
    }
  ]
}
```

**Notes:**
- Session history stored in database
- Last 10 turns kept (configurable)
- Follow-up questions resolved with context ("that", "it", etc.)

**Example:**
```bash
# First question
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the return policy?"}'

# Follow-up (use session_id from previous response)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What about damaged items?", "session_id": "sess_abc123"}'
```

---

### Search Documents (Raw Retrieval)

```http
POST /search
Content-Type: application/json
```

Retrieve relevant chunks without answer generation (for debugging).

**Request:**
```json
{
  "query": "vacation policy",
  "top_k": 5,
  "threshold": 0.5
}
```

**Response 200:**
```json
{
  "chunks": [
    {
      "id": "chunk_042",
      "text": "Employees receive 15 days of paid vacation per year...",
      "document": "handbook.pdf",
      "page": 7,
      "score": 0.89
    },
    {
      "id": "chunk_043",
      "text": "Unused vacation days can be carried over...",
      "document": "handbook.pdf",
      "page": 8,
      "score": 0.85
    }
  ],
  "total_found": 2
}
```

**Use case:** Debugging retrieval quality, building custom frontends.

---

## Response Schemas

### Document

```typescript
{
  id: string           // UUID
  filename: string
  page_count: number
  chunk_count: number
  uploaded_at: string  // ISO 8601 timestamp
  metadata?: object    // Custom metadata (future)
}
```

### Source Citation

```typescript
{
  document: string     // Filename
  page: number         // Page number (1-indexed)
  chunk_id?: string    // Internal chunk ID (optional)
}
```

### Answer

```typescript
{
  answer: string                 // Generated answer or "not_found"
  sources: Source[]              // Citations
  confidence: number             // 0.0-1.0
  status: "answered" | "not_found" | "clarify"
  message?: string               // Clarification request
}
```

### Chat Response

```typescript
{
  answer: string
  sources: Source[]
  confidence: number
  session_id: string
  history: Message[]             // Conversation history
}

type Message = {
  role: "user" | "assistant"
  content: string
}
```

---

## Rate Limiting

**Current:** None (open API)

**Production recommendation:**
```python
# Add slowapi middleware
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/ask")
@limiter.limit("100/minute")
def ask(question: str):
    ...
```

See [Configuration](CONFIGURATION.md#rate-limiting) for setup.

---

## Error Handling

All errors return:
```json
{
  "detail": "Human-readable error message",
  "error_code": "INTERNAL_ERROR_CODE",
  "timestamp": "2026-07-20T10:30:00Z"
}
```

**Common error codes:**

| Code | Meaning | Fix |
|---|---|---|
| `INVALID_FILE` | Not a PDF | Upload .pdf file |
| `EXTRACTION_FAILED` | PDF corrupt or scanned | Use text-based PDF |
| `EMBEDDING_ERROR` | LLM API failed | Check API key, retry |
| `NO_DOCUMENTS` | No documents ingested | Upload at least one document |
| `DB_ERROR` | Database connection issue | Check DATABASE_URL |

---

## Example Client (Python)

```python
import requests

BASE_URL = "http://localhost:8000"

# Upload document
with open("handbook.pdf", "rb") as f:
    resp = requests.post(f"{BASE_URL}/documents", files={"file": f})
    doc = resp.json()
    print(f"Uploaded {doc['filename']} with {doc['chunk_count']} chunks")

# Ask question
resp = requests.post(
    f"{BASE_URL}/ask",
    json={"question": "What is the vacation policy?"}
)
result = resp.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {result['sources']}")

# Multi-turn chat
session_id = None
for question in ["What is the return policy?", "What about damaged items?"]:
    resp = requests.post(
        f"{BASE_URL}/chat",
        json={"message": question, "session_id": session_id}
    )
    result = resp.json()
    session_id = result["session_id"]
    print(f"Q: {question}")
    print(f"A: {result['answer']}\n")
```

---

## Example Client (JavaScript)

```javascript
const BASE_URL = "http://localhost:8000";

// Upload document
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const resp = await fetch(`${BASE_URL}/documents`, {
    method: "POST",
    body: formData
  });
  return resp.json();
}

// Ask question
async function ask(question) {
  const resp = await fetch(`${BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  });
  return resp.json();
}

// Usage
const result = await ask("What is the refund policy?");
console.log(result.answer);
console.log(result.sources);
```

---

## Webhook Integration (Future)

**POST /webhooks/document_processed**

Notify external system when document ingestion completes.

**Payload:**
```json
{
  "event": "document.processed",
  "document_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "success",
  "chunk_count": 156
}
```

---

## Next Steps

- **Integrate:** Use these endpoints in your web app, Slack bot, etc.
- **Extend:** See [Architecture](ARCHITECTURE.md) for adding custom logic
- **Deploy:** See [Deployment](DEPLOYMENT.md) for production setup

---

**Questions?** Open an issue on [GitHub](https://github.com/dinkar1708/askdocs-rag-agent/issues).
