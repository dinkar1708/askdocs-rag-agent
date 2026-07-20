# Architecture

This document explains the system design, data flows, and key architectural decisions.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  Swagger UI · MCP Clients · Web Apps · Slack Bots              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                        │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Ingestion  │  │     RAG      │  │  LangGraph   │         │
│  │   Pipeline   │  │   Retrieval  │  │    Router    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         LLM Provider Adapter (Gemini/Ollama/Azure)       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬──────────────────┬────────────────────────┘
                      │                  │
                      ▼                  ▼
         ┌────────────────────┐  ┌────────────────┐
         │   PostgreSQL +     │  │   External     │
         │     pgvector       │  │   LLM APIs     │
         │                    │  │                │
         │ · documents        │  │ · Gemini       │
         │ · chunks           │  │ · Ollama       │
         │ · embeddings       │  │ · Azure OpenAI │
         └────────────────────┘  └────────────────┘
```

---

## Core Components

### 1. Ingestion Pipeline (`app/ingest/`)

**Responsibility:** Convert uploaded PDFs into searchable vector chunks.

**Flow:**
```
POST /documents
    ↓
PDF File → extract_text() → text + page_metadata
    ↓
chunk_text(text, chunk_size=512, overlap=128)
    ↓
[chunk_1, chunk_2, ...] → embed_chunks()
    ↓
INSERT INTO chunks (document_id, text, embedding, page_num)
```

**Key files:**
- `pdf_extractor.py` - PyPDF2/pdfplumber wrapper with page tracking
- `chunker.py` - Token-based chunking with overlap
- `embedder.py` - sentence-transformers or API-based embeddings

**Design decision:** Chunking happens at ingestion (not query time) to avoid latency. Overlap ensures context isn't lost at chunk boundaries.

---

### 2. RAG Retrieval (`app/rag/`)

**Responsibility:** Find relevant document chunks for a given query.

**Flow:**
```
POST /ask {"question": "..."}
    ↓
embed_query(question) → query_vector
    ↓
SELECT chunks, cosine_similarity(embedding, query_vector) AS score
FROM chunks
ORDER BY score DESC
LIMIT k
    ↓
[{chunk, score, doc_name, page_num}, ...]
```

**Key files:**
- `retriever.py` - pgvector cosine similarity search
- `reranker.py` - (optional) cross-encoder reranking
- `citation_builder.py` - Formats `[doc_name, page_num]` citations

**Design decision:** We use cosine similarity (not dot product) because embeddings are normalized. Top-k=5 is default, configurable.

---

### 3. LangGraph Router (`app/graph/`)

**Responsibility:** Decide how to respond based on query type and retrieval confidence.

**Graph structure:**
```
START
  ↓
classify_query(question)
  ├─ "off_topic" → refuse_node → END (return "not_found")
  ├─ "ambiguous" → clarify_node → END (ask for more info)
  └─ "answerable" → retrieve_node
                      ↓
                   check_confidence(scores)
                      ├─ score < threshold → refuse_node
                      └─ score ≥ threshold → answer_node
                                                ↓
                                             generate_answer(chunks)
                                                ↓
                                              END (answer + citations)
```

**Key files:**
- `router.py` - LangGraph StateGraph definition
- `nodes.py` - classify, retrieve, answer, clarify, refuse nodes
- `state.py` - Graph state (question, chunks, answer, citations)

**Design decision:** Classification happens before retrieval to save costs on obvious off-topic queries. Confidence threshold (default 0.7) is tunable.

---

### 4. LLM Provider Adapter (`app/llm/`)

**Responsibility:** Abstract LLM API calls so cloud/model choice is configuration, not code change.

**Interface:**
```python
class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str, context: list[str]) -> str:
        """Generate completion given prompt and context chunks."""
        pass

    def embed(self, text: str) -> list[float]:
        """Optional: Generate embeddings. Falls back to local model if not implemented."""
        pass
```

**Implementations:**
- `gemini_provider.py` - Google Gemini API
- `ollama_provider.py` - Local Ollama server
- `azure_openai_provider.py` - Azure OpenAI

**Selection:**
```python
# app/core/config.py
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# app/llm/factory.py
def get_provider() -> LLMProvider:
    if LLM_PROVIDER == "gemini":
        return GeminiProvider()
    elif LLM_PROVIDER == "ollama":
        return OllamaProvider()
    elif LLM_PROVIDER == "azure_openai":
        return AzureOpenAIProvider()
```

**Design decision:** No provider-specific logic leaks into RAG or graph code. Switching from Gemini to Azure is an env var change.

---

## Data Model

### PostgreSQL Schema

```sql
-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    filename TEXT NOT NULL,
    page_count INT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Chunks table (with pgvector extension)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    embedding VECTOR(384),  -- sentence-transformers dimension
    page_num INT,
    chunk_index INT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast vector search
CREATE INDEX chunks_embedding_idx ON chunks
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Sessions table (for multi-turn chat)
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    history JSONB NOT NULL,  -- [{role, content}, ...]
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Design decision:**
- Embeddings stored directly in PostgreSQL (not a separate vector DB) to reduce operational complexity
- `ON DELETE CASCADE` ensures deleting a document removes all its chunks
- `ivfflat` index trades recall for speed (acceptable for k=5 retrieval)

---

## Key Flows

### Document Ingestion

```
1. Client uploads PDF → POST /documents (multipart/form-data)
2. API saves file temporarily
3. extract_text(pdf) → [(page_1_text, 1), (page_2_text, 2), ...]
4. For each page:
     chunk_text(page_text) → [chunk_1, chunk_2, ...]
     embed_chunks([chunk_1, chunk_2, ...]) → [vec_1, vec_2, ...]
5. INSERT INTO chunks (text, embedding, page_num, ...)
6. DELETE temp file
7. Return {id, filename, page_count, chunk_count}
```

**Error handling:**
- Invalid PDF → 400 Bad Request
- Extraction failure → 422 Unprocessable Entity
- Embedding API timeout → Retry with exponential backoff

---

### Question Answering

```
1. Client asks question → POST /ask {"question": "..."}
2. embed_query(question) → query_vector
3. retrieve(query_vector, top_k=5) → [chunks with scores]
4. LangGraph START:
     a. classify_query("what is X?") → "answerable"
     b. check_confidence([0.89, 0.85, ...]) → PASS (all > 0.7)
     c. answer_node:
          - Build prompt: "Answer based only on:\n{chunk_1}\n{chunk_2}..."
          - llm.complete(prompt) → answer_text
          - Extract citations from chunks → [{doc, page}, ...]
5. Return {answer, sources, confidence: 0.89}
```

**Edge cases:**
- No chunks found → confidence=0 → "not_found"
- Top score < threshold → "not_found"
- Ambiguous question (e.g., "what about that?") → "Please clarify..."
- Off-topic (e.g., "weather today") → "not_found"

---

### Multi-turn Chat

```
1. POST /chat {"message": "...", "session_id": "abc"}
2. Load session history from DB
3. Append user message to history
4. Build contextualized query:
     - If "that" / "it" in message → resolve with history
5. Run same RAG pipeline as /ask
6. Append assistant answer to history
7. UPDATE sessions SET history = ..., updated_at = NOW()
8. Return {answer, sources, session_id}
```

**Context window management:**
- Keep last N turns (default 10)
- Truncate oldest messages if context exceeds token limit

---

## Design Decisions

### 1. Grounded-or-Refuse Over Best-Effort

**Decision:** Return "not_found" if confidence < threshold, instead of generating a low-confidence answer.

**Rationale:**
- Trust is the product. Hallucinating a refund policy could be legally problematic.
- Users prefer "I don't know" over a wrong answer in high-stakes domains (finance, legal, HR).

**Trade-off:** Lower answer rate, but zero hallucination risk.

---

### 2. pgvector in PostgreSQL Over Dedicated Vector DB

**Decision:** Store embeddings in PostgreSQL with pgvector extension.

**Rationale:**
- Simpler ops: One database to manage (not Postgres + Pinecone/Qdrant)
- Transactional integrity: Delete document → chunks auto-deleted (foreign keys)
- Sufficient scale: pgvector handles millions of vectors with ivfflat indexing
- Clean migration path: If scale demands it, swap to Pinecone without changing app code (adapter pattern)

**Trade-off:** Slightly slower than specialized vector DBs at >10M vectors (acceptable for MVP).

---

### 3. LLM Provider Adapter Over Direct API Calls

**Decision:** Abstract LLM calls behind an interface with swappable implementations.

**Rationale:**
- Cloud portability: Gemini in dev, Azure OpenAI in prod, no code change
- Cost optimization: Switch to cheaper model (or local Ollama) by changing env var
- Vendor lock-in avoidance: Not tied to one provider's pricing or API limits

**Implementation cost:** +50 lines of code for the adapter factory, but provides significant flexibility when switching providers.

---

### 4. Token-based Chunking Over Sentence/Paragraph Splitting

**Decision:** Chunk by token count (512 tokens) with overlap (128 tokens).

**Rationale:**
- LLM context windows are token-based, not character-based
- Fixed size ensures consistent retrieval (vs. variable-length paragraphs)
- Overlap prevents information loss at chunk boundaries

**Example:**
```
Chunk 1: tokens [0:512]
Chunk 2: tokens [384:896]  ← 128 overlap with Chunk 1
Chunk 3: tokens [768:1280] ← 128 overlap with Chunk 2
```

---

### 5. MCP as First-Class Interface

**Decision:** Expose document Q&A as MCP tools, not just REST endpoints.

**Rationale:**
- AI assistants (Claude Desktop, etc.) can use the service directly
- Same code serves both web apps (REST) and AI tools (MCP)
- Future-proofs for LLM-as-interface paradigm

**Tools exposed:**
- `search_documents(query)` - raw retrieval
- `ask_question(question)` - full RAG pipeline

---

## Scalability Considerations

### Current Design (MVP)
- **Ingestion:** Synchronous (blocks request until indexing completes)
- **Database:** Single PostgreSQL instance
- **API:** Stateless, can scale horizontally

### Future Optimizations (if needed)

**Problem:** PDF upload times out on large documents.
**Solution:** Background job queue (Celery + Redis). Return 202 Accepted, poll `/documents/{id}/status`.

**Problem:** pgvector slow at >1M chunks.
**Solution:** Migrate to Pinecone/Qdrant via adapter swap. Zero app code change.

**Problem:** Multi-tenant isolation needed.
**Solution:** Add `tenant_id` to documents/chunks, filter all queries. Or: separate DB per tenant.

**Problem:** LLM API rate limits.
**Solution:** Caching layer (Redis) for identical questions. Rate limiter (slowapi).

---

## Security

- **SQL injection:** SQLAlchemy ORM with parameterized queries
- **File upload:** Validate PDF magic bytes, limit file size (10MB default)
- **API keys:** Never logged, stored in env vars or secrets manager
- **CORS:** Restricted origins in production (wildcard in dev)
- **DoS:** Rate limiting on `/ask` endpoint (100 req/min per IP)

---

## Observability

**Logging:**
- Structured JSON logs (timestamp, level, message, context)
- Log retrieval scores for debugging threshold tuning

**Metrics (future):**
- Request latency (p50, p95, p99)
- Retrieval confidence distribution
- "not_found" rate (too high → tune chunking or threshold)

**Tracing (future):**
- LangSmith for LangGraph execution traces
- Trace IDs for request correlation

---

## Technology Choices

| Component | Technology | Why |
|---|---|---|
| **Web framework** | FastAPI | Async, auto docs, typed |
| **Vector search** | pgvector | Simpler ops than dedicated DB |
| **LLM orchestration** | LangGraph | Stateful routing, debuggable |
| **Embeddings** | sentence-transformers | Free, multilingual, offline |
| **DB ORM** | SQLAlchemy | Industry standard, migrations |
| **Containerization** | Docker | Reproducible envs |
| **Cloud (primary)** | GCP Cloud Run | Scale-to-zero, cheap |
| **Cloud (secondary)** | Azure Container Apps | Customer requirement support |

---

**Next:** See [Local Development](LOCAL_DEVELOPMENT.md) for setup, or [API Reference](API.md) for endpoint details.
