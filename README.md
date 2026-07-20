# askdocs-rag-agent

> Ask questions to your documents and get grounded, cited answers — a production-style Document Q&A service built with FastAPI, RAG, and LangGraph.

**Stack:** Python 3.12 · FastAPI · LangGraph · PostgreSQL + pgvector · Docker

## Description

A production-ready RAG (Retrieval-Augmented Generation) system that enables natural language Q&A over document collections with guaranteed citation accuracy. Built with enterprise-grade architecture featuring LangGraph-powered query routing, vector similarity search using pgvector, and multi-LLM support (Gemini, Ollama, Azure OpenAI).

**Key Differentiators:**
- **Grounded-or-refuse architecture** - Never hallucinates; returns "not_found" when answers aren't in documents
- **Citation tracking** - Every answer includes exact document and page references
- **Multi-interface support** - REST API, Web UI, Slack bot, and MCP integration for Claude Desktop
- **Production-ready** - Security hardened, cloud-native deployment (GCP/Azure), comprehensive testing
- **Flexible LLM backend** - Swappable providers via adapter pattern (cloud or local)

**Target Use Cases:** HR knowledge bases, customer support documentation, legal/compliance document search, IT helpdesk automation, sales enablement.

**Market Position:** Developer-first alternative to enterprise solutions (Glean, Writer) at 10x lower cost, with full control over deployment and data.

---

## What It Does

Upload PDF documents → Ask questions in natural language → Get answers grounded in those documents with citations, or an honest "not found."

**No hallucinations.** Every answer either cites the exact source (document + page) or explicitly says the information doesn't exist in your documents.

**Example:**
```
Q: "What is the refund policy?"
A: "Refunds are processed within 14 days of purchase."
   Sources: [terms.pdf, page 7]

Q: "What's the weather today?"
A: "not_found - This question cannot be answered from the uploaded documents."
```

---

## Why Build This?

**The Problem:**
- Organizations have thousands of policy documents, manuals, handbooks
- Employees and customers waste hours searching for answers
- Generic AI chat tools hallucinate facts about your specific policies

**The Solution:**
- **Grounded answers only** - responses use retrieved document chunks, with confidence thresholds
- **Persistent knowledge base** - upload once, query forever (unlike ChatGPT's per-conversation uploads)
- **API-first** - integrate into Slack, web apps, customer support tools
- **Production-ready** - typed code, tests, CI/CD, cloud deployment paths

**What makes this different from ChatGPT/Claude?**
See [Why Not Just Use ChatGPT?](docs/getting-started/WHY.md) for detailed comparison.

---

## Key Features

- **Grounded Q&A** - Answers only from retrieved chunks, with `[doc, page]` citations
- **Honest refusal** - Returns "not_found" if confidence is too low (no guessing)
- **LangGraph router** - Classifies queries: answer / clarify / refuse
- **Multi-turn chat** - Conversation history for follow-up questions
- **MCP integration** - Tools for AI assistants (Claude Desktop, etc.)
- **Swappable LLM** - Gemini, Ollama, Azure OpenAI via adapter pattern
- **pgvector** - Vector embeddings in PostgreSQL (no separate vector DB)

---

## Quick Start (Local)

**Prerequisites:**
- Docker & Docker Compose
- LLM provider (pick one):
  - **Gemini API** (free tier) - best quality
  - **Ollama** (local) - 100% offline, zero cost

**Run it:**
```bash
git clone https://github.com/dinkar1708/askdocs-rag-agent.git
cd askdocs-rag-agent

# Configure LLM provider
cp .env.example .env
# Edit .env: set LLM_PROVIDER=gemini and add your GEMINI_API_KEY
# OR set LLM_PROVIDER=ollama for fully offline mode

# Start services
docker compose up --build

# Open Swagger UI
# → http://localhost:8000/docs
```

**Test the service:**
1. **Upload a document** - `POST /documents` with a PDF file
2. **Ask a question** - `POST /ask` with `{"question": "what is X?"}`
3. **Verify grounding** - Check the `sources` array in the response
4. **Test refusal** - Ask an off-topic question, expect `"not_found"`

Sample PDFs are in `samples/` directory.

**Verify it works:**
```bash
# Run tests (auto-generates API examples in docs/testing/api-results/)
docker compose exec api pytest

# Check API documentation examples
cat docs/testing/api-results/health.json

# Run evaluation (retrieval quality metrics)
docker compose exec api python -m eval.run
```

See [Local Development Guide](docs/LOCAL_DEVELOPMENT.md) for detailed setup.

---

## How It Works

**Ingestion Pipeline:**
```
PDF → Extract text (with page numbers) → Chunk (512 tokens, 128 overlap)
    → Embed (sentence-transformers) → Store (PostgreSQL + pgvector)
```

**Query Pipeline:**
```
Question → Embed → Vector search (top-k chunks) → LangGraph router
    ├─ High confidence → Generate answer + citations
    ├─ Ambiguous → Ask for clarification
    └─ Low confidence → Return "not_found"
```

**Key Design Decisions:**
- **Grounded-or-refuse** - Trust is the product; never improvise answers
- **LLM adapter pattern** - Cloud/model choice is config, not code change
- **pgvector in PostgreSQL** - Single database for relational + vector data
- **MCP-first** - API endpoints also exposed as AI assistant tools

See [Architecture Guide](docs/core/architecture/ARCHITECTURE.md) for deep dive.

---

## Project Structure

```
askdocs-rag-agent/
├── app/
│   ├── api/               # FastAPI routes
│   ├── ingest/            # PDF extraction, chunking, embedding
│   ├── rag/               # Retrieval, answer generation, citations
│   ├── graph/             # LangGraph query router
│   ├── llm/               # Provider adapters (Gemini/Ollama/Azure)
│   ├── mcp/               # MCP server
│   ├── db/                # SQLAlchemy models, pgvector setup
│   ├── core/              # Config, logging
│   └── tests/             # pytest suites with auto-generated API docs
├── docs/
│   ├── testing/
│   │   └── api-results/   # Auto-generated API request/response examples
│   ├── core/              # Architecture, deployment guides
│   └── interfaces/        # API, Web UI, Slack bot docs
├── samples/               # Sample PDFs for testing
└── docker-compose.yml
```

---

## Deployment

**GCP (Primary):**
- Cloud Run (stateless API, scales to zero)
- Cloud SQL (PostgreSQL + pgvector)
- Gemini API / Vertex AI

See [Deployment Guide](docs/core/deployment/DEPLOYMENT.md) for step-by-step.

**Azure (Supported):**
- Azure Container Apps
- Azure Database for PostgreSQL Flexible Server
- Azure OpenAI

Brief setup: [docs/core/deployment/AZURE.md](docs/core/deployment/AZURE.md)

---

## Documentation

**All documentation is in the [`/docs`](docs/) folder.**

| Document | Description |
|---|---|
| [Documentation Index](docs/README.md) | Start here - Complete navigation guide |
| [Architecture](docs/core/architecture/ARCHITECTURE.md) | System design, data flow, key decisions |
| [Development](docs/development/DEVELOPMENT.md) | Developer quick reference |
| [Local Setup](docs/getting-started/LOCAL_DEVELOPMENT.md) | Detailed setup, testing, debugging |
| [API Guide](docs/interfaces/api/) | API integration guide with examples |
| [Web UI](docs/interfaces/web-ui/) | Browser interface for end users |
| [Configuration](docs/core/configuration/CONFIGURATION.md) | Environment variables, tuning |
| [Deployment](docs/core/deployment/) | GCP (detailed), Azure (brief) |
| [Features](docs/features/) | User-focused feature docs |
| [Security](docs/core/security/) | Security guidelines & checklist |
| [Business](docs/business/) | Sales materials, pricing, ROI |
| [Why This?](docs/getting-started/WHY.md) | vs ChatGPT/Claude |

---

## Roadmap

- [ ] Core RAG API (ingest, ask, grounded answers)
- [ ] LangGraph router (answer/clarify/refuse)
- [ ] Multi-turn chat with memory
- [ ] MCP server tools
- [ ] Evaluation harness
- [ ] GCP Cloud Run deployment + CI/CD
- [ ] Azure Container Apps deployment
- [ ] Multi-tenant support
- [ ] Japanese document support

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](docs/CONTRIBUTING.md)

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Author

**Dinakar Maurya** — Solution Architect / AI Engineer, Tokyo

- GitHub: [@dinkar1708](https://github.com/dinkar1708)
- Medium: [@dinkar1708](https://medium.com/@dinkar1708)
- LinkedIn: [in/dinkar1708](https://www.linkedin.com/in/dinkar1708)

---

**Questions?** Open an issue on [GitHub](https://github.com/dinkar1708/askdocs-rag-agent).
