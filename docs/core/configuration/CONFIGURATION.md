# Configuration Guide

Environment variables, tuning parameters, and configuration options.

---

## Environment Variables

All configuration is via environment variables (`.env` file or container env vars).

### Required Variables

```bash
# LLM Provider (pick one: gemini, ollama, azure_openai)
LLM_PROVIDER=gemini

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/askdocs
```

### LLM Provider Configs

#### Gemini (Google)

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here

# Optional: Model selection
GEMINI_MODEL=gemini-1.5-flash  # Default: gemini-1.5-flash
# Other options: gemini-1.5-pro, gemini-1.0-pro
```

**Get API key:** https://aistudio.google.com/app/apikey

**Free tier:** 15 requests/minute, 1M tokens/day

---

#### Ollama (Local)

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434  # or http://host.docker.internal:11434 in Docker
OLLAMA_MODEL=llama2  # or mistral, gemma, etc.
```

**Setup:**
```bash
# Install Ollama: https://ollama.ai
ollama pull llama2

# Verify
curl http://localhost:11434/api/generate -d '{"model":"llama2","prompt":"Hi"}'
```

**Note:** Fully offline, zero cost, but slower than cloud APIs.

---

#### Azure OpenAI

```bash
LLM_PROVIDER=azure_openai
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_key_here
AZURE_OPENAI_DEPLOYMENT=gpt-4  # Your deployment name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Setup Azure OpenAI:**
1. Create Azure OpenAI resource
2. Deploy a model (gpt-4, gpt-3.5-turbo)
3. Copy endpoint + key from Azure Portal

---

### Chunking & Embedding

```bash
# Chunking parameters
CHUNK_SIZE=512              # Tokens per chunk
CHUNK_OVERLAP=128           # Overlap between chunks (tokens)

# Embedding model (local)
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384     # Must match model dimension

# Alternative: Use LLM provider's embedding API
USE_LLM_EMBEDDINGS=false    # Set true to use Gemini/Azure embeddings
```

**Tuning chunking:**
- **Larger chunks (1024)** → more context per chunk, but less precise retrieval
- **Smaller chunks (256)** → more precise, but may lose context
- **More overlap (256)** → less information loss, but more storage

---

### Retrieval & Grounding

```bash
# Retrieval
RETRIEVAL_TOP_K=5           # Number of chunks to retrieve
RETRIEVAL_THRESHOLD=0.5     # Min cosine similarity score to include

# Grounding
CONFIDENCE_THRESHOLD=0.7    # Min score to answer (vs "not_found")
MAX_CONTEXT_LENGTH=2048     # Max tokens to send to LLM
```

**Tuning confidence threshold:**
- **Higher (0.9)** → fewer answers, but higher accuracy (fewer hallucinations)
- **Lower (0.5)** → more answers, but risk of low-quality responses

**Finding the right value:**
Run evaluation harness (`python -m eval.run`) and plot answer rate vs groundedness at different thresholds.

---

### Chat & Sessions

```bash
# Multi-turn chat
MAX_HISTORY_TURNS=10        # Keep last N conversation turns
SESSION_TTL_HOURS=24        # Delete inactive sessions after N hours
```

---

### Database

```bash
# PostgreSQL connection
DATABASE_URL=postgresql://user:password@host:port/database

# Connection pooling
DB_POOL_SIZE=10             # Max connections in pool
DB_MAX_OVERFLOW=20          # Additional connections when pool exhausted
DB_POOL_PRE_PING=true       # Check connection health before use
```

**Connection string formats:**

**Local:**
```
postgresql://postgres:postgres@localhost:5432/askdocs
```

**Cloud SQL (GCP):**
```
postgresql://user:password@/askdocs?host=/cloudsql/project:region:instance
```

**Azure:**
```
postgresql://user:password@server.postgres.database.azure.com:5432/askdocs?sslmode=require
```

---

### Security

```bash
# API Keys (future)
API_KEY_ENABLED=false       # Enable API key auth
API_KEYS=key1,key2,key3     # Comma-separated keys

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
# Use "*" for development only

# Rate limiting
RATE_LIMIT_ENABLED=false
RATE_LIMIT_PER_MINUTE=100
```

**Enable API key auth:**
```python
# app/api/middleware.py
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key not in API_KEYS.split(","):
        raise HTTPException(401, "Invalid API key")
```

---

### File Upload

```bash
# Upload limits
MAX_FILE_SIZE_MB=10         # Max PDF size
ALLOWED_EXTENSIONS=.pdf     # Future: .docx, .txt
UPLOAD_TEMP_DIR=/tmp        # Temp storage during processing
```

---

### Logging

```bash
# Log level
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=json             # json or pretty

# Structured logging
LOG_TO_FILE=false
LOG_FILE_PATH=/var/log/askdocs.log
```

**Example structured log:**
```json
{
  "timestamp": "2026-07-20T10:30:00Z",
  "level": "INFO",
  "message": "Document ingested",
  "document_id": "123e4567",
  "chunk_count": 156,
  "latency_ms": 1234
}
```

---

### Performance

```bash
# Background jobs (future)
USE_ASYNC_INGESTION=false   # Process PDFs in background queue
CELERY_BROKER_URL=redis://localhost:6379/0

# Caching
ENABLE_CACHE=false
CACHE_BACKEND=redis         # redis or memory
CACHE_TTL_SECONDS=3600      # 1 hour
```

**Enable caching:**
```python
# Cache identical questions for 1 hour
from functools import lru_cache

@lru_cache(maxsize=1000)
def ask_cached(question: str):
    return ask(question)
```

---

## Complete .env.example

```bash
# === LLM Provider ===
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_api_key_here
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama2
# AZURE_OPENAI_ENDPOINT=https://xxx.openai.azure.com/
# AZURE_OPENAI_KEY=xxx
# AZURE_OPENAI_DEPLOYMENT=gpt-4

# === Database ===
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/askdocs
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# === Chunking & Embedding ===
CHUNK_SIZE=512
CHUNK_OVERLAP=128
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
EMBEDDING_DIMENSION=384

# === Retrieval & Grounding ===
RETRIEVAL_TOP_K=5
RETRIEVAL_THRESHOLD=0.5
CONFIDENCE_THRESHOLD=0.7
MAX_CONTEXT_LENGTH=2048

# === Chat ===
MAX_HISTORY_TURNS=10
SESSION_TTL_HOURS=24

# === Upload ===
MAX_FILE_SIZE_MB=10
UPLOAD_TEMP_DIR=/tmp

# === Logging ===
LOG_LEVEL=INFO
LOG_FORMAT=json

# === Security ===
CORS_ORIGINS=*
# API_KEY_ENABLED=false
# API_KEYS=key1,key2

# === Performance ===
ENABLE_CACHE=false
```

---

## Configuration by Environment

### Development

```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=pretty
CORS_ORIGINS=*
CONFIDENCE_THRESHOLD=0.6    # Lower for testing
```

### Staging

```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
CORS_ORIGINS=https://staging.yourdomain.com
CONFIDENCE_THRESHOLD=0.7
API_KEY_ENABLED=true
```

### Production

```bash
LOG_LEVEL=WARNING
LOG_FORMAT=json
CORS_ORIGINS=https://yourdomain.com
CONFIDENCE_THRESHOLD=0.8    # Higher for production
API_KEY_ENABLED=true
RATE_LIMIT_ENABLED=true
ENABLE_CACHE=true
DB_POOL_SIZE=20
```

---

## Advanced Tuning

### Optimizing Retrieval Quality

**Problem:** Relevant chunks not in top-k.

**Solutions:**
1. Increase `RETRIEVAL_TOP_K` (5 → 10)
2. Decrease `RETRIEVAL_THRESHOLD` (0.5 → 0.3)
3. Tune chunking (try 256 or 1024 tokens)
4. Add reranking (cross-encoder model)

**Evaluate:**
```bash
python -m eval.run
# Check retrieval hit-rate metric
```

---

### Balancing Answer Rate vs Quality

**Problem:** Too many "not_found" responses.

**Solution:** Lower `CONFIDENCE_THRESHOLD` (0.7 → 0.6)

**Problem:** Answers are hallucinated/low-quality.

**Solution:** Raise `CONFIDENCE_THRESHOLD` (0.7 → 0.8)

**Find optimal value:**
```python
# eval/tune_threshold.py
for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
    CONFIDENCE_THRESHOLD = threshold
    results = run_evaluation()
    print(f"Threshold {threshold}: {results['answer_rate']} answers, {results['groundedness']} groundedness")
```

---

### Multi-Tenant Configuration

**Per-tenant settings:**
```python
# app/core/config.py
TENANT_CONFIGS = {
    "tenant_1": {
        "confidence_threshold": 0.8,  # Higher for legal docs
        "retrieval_top_k": 10
    },
    "tenant_2": {
        "confidence_threshold": 0.6,  # Lower for casual Q&A
        "retrieval_top_k": 5
    }
}
```

**Filter documents by tenant:**
```sql
SELECT * FROM chunks
WHERE document_id IN (
    SELECT id FROM documents WHERE tenant_id = :tenant_id
)
```

---

## Environment-Specific Secrets

**DO NOT commit secrets to git.**

**Use:**
- **Local:** `.env` (git-ignored)
- **GCP:** Secret Manager
- **Azure:** Key Vault
- **Kubernetes:** Secrets / ConfigMaps

**Example (GCP Secret Manager):**
```bash
# Store secret
echo "your_api_key" | gcloud secrets create gemini-api-key --data-file=-

# Mount in Cloud Run
gcloud run services update askdocs-api \
  --update-secrets=GEMINI_API_KEY=gemini-api-key:latest
```

---

## Validation

**On startup, the app validates:**
- Required env vars are set
- LLM provider is reachable
- Database connection works
- Embedding model loads

**Check logs for:**
```
INFO: Configuration loaded: LLM_PROVIDER=gemini, CHUNK_SIZE=512
INFO: Database connected
INFO: Embedding model loaded: paraphrase-multilingual-MiniLM-L12-v2
INFO: Application ready
```

---

## Next Steps

- **Deploy:** See [Deployment](DEPLOYMENT.md) for production setup
- **Monitor:** Track metrics (answer rate, latency, error rate)
- **Tune:** Run evaluation harness to optimize parameters

---

**Questions?** Open an issue on [GitHub](https://github.com/dinkar1708/askdocs-rag-agent/issues).
