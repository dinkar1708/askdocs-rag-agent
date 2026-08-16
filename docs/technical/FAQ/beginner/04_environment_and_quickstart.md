# Beginner Level: Environment Setup & Quickstart

---

## 1. Quickstart & Service Orchestration

### Q1: How do I run the entire stack locally?
**Answer:**
AskDocs runs using Docker Compose or local Python virtual environment:

```bash
# 1. Start Database & Backend API via Docker
docker compose up -d

# 2. Start Frontend UI (Nuxt 3)
cd web-ui
npm install
npm run dev
```

**Service Access:**
- **Web UI:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **PostgreSQL Database:** `localhost:5432` (`askdocs`)

---

### Q2: How is configuration managed across environments?
**Answer:**
Configuration is driven by Pydantic `BaseSettings` in [`app/core/config.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/core/config.py), reading environment variables:

| Variable | Default / Example | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/askdocs` | PostgreSQL connection string |
| `LLM_PROVIDER` | `ollama` (options: `gemini`, `ollama`, `azure`, `mock`) | Active LLM generation backend |
| `OLLAMA_MODEL` | `llama3.2` | Local Ollama model tag |
| `RERANKING_ENABLED` | `True` | Enables cross-encoder reranking |
| `HYBRID_SEARCH_ENABLED` | `True` | Enables BM25 + pgvector hybrid search |
| `API_KEY` | `dev-api-key-change-in-production` | Secret key for REST API authentication |
