# askdocs-rag-agent

> Ask questions to your documents and get grounded, cited answers — a production-style Document Q&A service built with FastAPI, RAG, and LangGraph.

**Stack:** Python 3.12 · FastAPI · LangGraph · PostgreSQL + pgvector · Nuxt 4 · Tailwind CSS · Docker

## Description

A production-style RAG (Retrieval-Augmented Generation) system that enables natural language Q&A over document collections with guaranteed citation accuracy. Built with enterprise-grade architecture featuring LangGraph-powered query routing, vector similarity search using pgvector, and multi-LLM support (Gemini, Ollama, Azure OpenAI).

**Key Differentiators:**
- **Grounded-or-refuse architecture** - Never hallucinates; returns "not_found" when answers aren't in documents
- **Citation tracking** - Every answer includes exact document and page references
- **Multi-interface support** - REST API, Web UI, Slack bot, and MCP integration for Claude Desktop
- **Production-style** - Security hardened, cloud-native deployment (GCP/Azure), comprehensive testing
- **Flexible LLM backend** - Swappable providers via adapter pattern (cloud or local)

**Target Use Cases:** HR knowledge bases, customer support documentation, legal/compliance document search, IT helpdesk automation, sales enablement.

**Market Position:** Developer-first, self-hosted alternative to enterprise search products (Glean, Writer) — full data control and per-query costs instead of per-seat licensing. See docs/business for cost model.

---

## 📸 Demo Screenshots

<div align="center">

| ![Demo 1](docs/screenshots/demo-question-1.png) | ![Demo 2](docs/screenshots/demo-question-2.png) | ![Demo 3](docs/screenshots/demo-question-3.png) |
|:-------------------------:|:------------------------:|:----------------------:|
| *Chat Page* | *Chat QA* | *Upload Document* |

</div>

**See it in action:** Each question returns a unique answer with exact citations (document + page). Try it yourself with [sample questions](docs/QUICK_DEMO.md)!

> **Note:** Screenshots show mock mode (no API key needed). With real LLM (Gemini), answers are even more contextually accurate. See [DEMO_QUESTIONS.md](docs/DEMO_QUESTIONS.md) for mock vs real LLM comparison.

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
- **Production-style** - typed code, tests, CI/CD, cloud deployment paths

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

**Run Backend API:**
```bash
git clone https://github.com/dinkar1708/askdocs-rag-agent.git
cd askdocs-rag-agent

# Configure LLM provider
cp .env.example .env
# Edit .env: set LLM_PROVIDER=gemini and add your GEMINI_API_KEY
# OR set LLM_PROVIDER=ollama for fully offline mode

# Start backend services
docker compose up --build

# API available at http://localhost:8000
# Swagger UI at http://localhost:8000/docs
```

**Run Web UI (optional):**
```bash
cd web-ui
npm install
npm run dev

# Web UI available at http://localhost:3000
```

**Test the service:**
1. **Upload a document** - `POST /documents` with a PDF file
2. **Ask a question** - `POST /ask` with `{"question": "what is X?"}`
3. **Verify grounding** - Check the `sources` array in the response

**Try the demo with sample data:**
```bash
# Upload sample company policy document
curl -X POST http://localhost:8000/documents/ \
  -F "file=@app/samples/company_policy.pdf"

# Ask a test question
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How many vacation days do employees get?"}'

# Expected: "15 days of paid vacation per year" with citations
```

📋 **Quick Demo:** See [docs/QUICK_DEMO.md](docs/QUICK_DEMO.md) for copy-paste questions with expected answers.

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
├── app/                   # Backend (Python/FastAPI)
│   ├── api/               # FastAPI routes
│   ├── ingest/            # PDF extraction, chunking, embedding
│   ├── rag/               # Retrieval, answer generation, citations
│   ├── graph/             # LangGraph query router
│   ├── llm/               # Provider adapters (Gemini/Ollama/Azure)
│   ├── mcp/               # MCP server
│   ├── db/                # SQLAlchemy models, pgvector setup
│   ├── core/              # Config, logging
│   └── tests/             # pytest suites with auto-generated API docs
├── web-ui/                # Frontend (Nuxt 4/Vue/Tailwind)
│   ├── app/               # Vue components and pages
│   ├── composables/       # Vue composables and API services
│   ├── public/            # Static assets
│   └── nuxt.config.ts     # Nuxt configuration
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
- [ ] Web UI (Nuxt 4 + Tailwind CSS)
- [ ] User authentication & authorization
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
