# Database Schema Design

High-level database design for askdocs-rag-agent.

---

## Overview

PostgreSQL database with pgvector extension for vector similarity search.

---

## Tables

### 1. documents

Stores uploaded PDF metadata.

**Fields:**
- `id` - Unique document identifier (UUID)
- `filename` - Original filename
- `page_count` - Number of pages
- `uploaded_at` - Upload timestamp
- `tenant_id` - For multi-tenant isolation (optional)
- `metadata` - JSON for custom fields

**Purpose:** Track which documents exist in the system.

---

### 2. chunks

Stores document text chunks with embeddings.

**Fields:**
- `id` - Unique chunk identifier (UUID)
- `document_id` - References documents table
- `text` - The actual text content
- `embedding` - Vector embedding (384 dimensions for sentence-transformers)
- `page_num` - Which page this chunk came from
- `chunk_index` - Order within document (0, 1, 2...)
- `created_at` - When chunk was created

**Purpose:** Store searchable text chunks with vector embeddings.

**Indexes:**
- Vector similarity index on `embedding` (ivfflat or hnsw)
- Foreign key index on `document_id`

---

### 3. sessions (for multi-turn chat)

Stores conversation history.

**Fields:**
- `id` - Session identifier (UUID)
- `history` - JSON array of messages: `[{role, content}, ...]`
- `created_at` - Session start time
- `updated_at` - Last message time

**Purpose:** Maintain conversation context across multiple questions.

---

## Relationships

```
documents (1) ──< (many) chunks
    │
    └─ One document has many chunks

sessions (independent)
    │
    └─ No direct relationship, stores conversation history
```

---

## Multi-Tenant Design (Optional)

If supporting multiple tenants:

**Add to documents table:**
- `tenant_id` - Isolate documents per customer

**Query pattern:**
```
All queries filter by tenant_id:
WHERE tenant_id = :current_tenant
```

**Benefit:** Single database serves multiple customers with data isolation.

---

## Vector Search Strategy

### Embedding Dimensions
- **sentence-transformers:** 384 dimensions
- **OpenAI ada-002:** 1536 dimensions
- **Configurable** via environment variable

### Similarity Metric
- **Cosine similarity** (standard for normalized embeddings)

### Index Type
- **ivfflat** - Good for <1M vectors
- **hnsw** - Better for >1M vectors (faster but more memory)

---

## Storage Estimates

### Per Document
- **Metadata:** ~1KB
- **Chunks (avg 100 per doc):** ~50KB text + ~150KB embeddings
- **Total per doc:** ~200KB

### For 1000 Documents
- **Total storage:** ~200MB

### For 100K Documents
- **Total storage:** ~20GB

---

## Backup & Recovery

**Backup frequency:** Daily
**Retention:** 30 days
**Method:** Cloud SQL automated backups (GCP) or Azure Database backups

---

## Migration Strategy

Use **Alembic** for schema migrations:
- Track schema changes in version control
- Apply migrations on deployment
- Rollback capability

---

## Key Design Decisions

### Why pgvector in PostgreSQL?
- ✅ Single database (simpler than separate vector DB)
- ✅ ACID transactions
- ✅ Foreign key constraints (data integrity)
- ✅ Sufficient performance for <1M documents
- ✅ Easy migration to dedicated vector DB if needed

### Why JSON for metadata/history?
- ✅ Flexible schema (add fields without migrations)
- ✅ PostgreSQL has excellent JSON support
- ✅ Easy to query and index

### Why UUID over auto-increment?
- ✅ Globally unique (multi-tenant safe)
- ✅ No sequential leakage
- ✅ Safe for distributed systems

---

## Next Steps

**Implementation:**
1. Create SQLAlchemy models based on this schema
2. Generate initial Alembic migration
3. Test locally with docker-compose

**Will be updated** after actual implementation with exact column types and constraints.
