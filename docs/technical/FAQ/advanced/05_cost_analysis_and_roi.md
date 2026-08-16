# Advanced Level: Cost Analysis, Business ROI and Feature Roadmap

---

## 1. Operating Cost Breakdown (10,000 Queries / Day)

### Q1: What are the monthly operating costs for running AskDocs?
**Answer:**
AskDocs is designed for cost efficiency compared to commercial SaaS tools.

```
Cost Comparison for 10,000 Queries/Day:
- Cloud LLM (Gemini): ~$72 / month
- Local LLM (Ollama): ~$50 / month
- Commercial Enterprise Search: $15,000 - $25,000 / month
```

| Component | Cloud Setup (Google Gemini) | Local Setup (Ollama / Self-Hosted) |
| :--- | :--- | :--- |
| **API Container (Cloud Run)** | ~$10/mo (scales to zero) | Self-hosted server |
| **PostgreSQL Database (Cloud SQL)** | ~$15/mo (db-f1-micro / db-g1-small) | Local/self-hosted PostgreSQL |
| **PDF Cloud Storage** | ~$5/mo | Local disk storage |
| **LLM Generation Inferences** | ~$42/mo (Gemini Flash token pricing) | $20/mo (Hardware amortized + electricity) |
| **Total Estimated Cost** | **~$72 / month** | **~$50 / month** |

---

## 2. Enterprise ROI Comparison

### Q2: What is the ROI compared to commercial Enterprise Search tools?
**Answer:**
- **Commercial SaaS (Glean, Writer, Moveworks):** Billed at $15-$25 per employee per month. For a 1,000-person company, that is $180,000-$300,000 annually.
- **AskDocs Solution:** Billed on actual query infrastructure usage (~$1,000-$2,000 annually).
- **Cost Reduction:** Over 99% cost savings with data privacy and no vendor lock-in.

---

## 3. Feature Status and Roadmap (TODOs)

Author / Maintainer: [Dinakar Maurya](https://github.com/dinkar1708) ([dinkar1708/askdocs-rag-agent](https://github.com/dinkar1708/askdocs-rag-agent))

### Implemented Today:
- Core RAG Pipeline: Ingestion, PDF parsing, 384d vector generation, pgvector storage ([`app/services/retriever.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/retriever.py)).
- LangGraph Query Router: 3-stage state machine (Answer / Clarify / Refuse) ([`app/graph/query_routing_graph.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/graph/query_routing_graph.py)).
- Cross-Encoder Reranking: BAAI/bge-reranker-v2-m3 integration ([`app/services/reranker.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/reranker.py)).
- Advanced RAG (Tables and Semantic Chunking): PDF table extraction to Markdown and semantic boundary detection ([`app/services/table_processor.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/table_processor.py)).
- Multi-turn Chat: Session and message storage with exact citation JSON ([`app/api/sessions.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/api/sessions.py)).
- Nuxt 3 Frontend: Reactive chat, document manager, and citation inspector ([`web-ui`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/web-ui)).

### Planned for Future Release (TODO Items):

> [!NOTE]
> TODO 1: Hypothetical Document Embeddings (HyDE)
> - Status: Planned for future release.
> - Description: Generate hypothetical answer passages with the LLM before embedding to improve zero-shot vector recall on complex questions.

> [!NOTE]
> TODO 2: Real-Time SSE Token Streaming (/ask/stream)
> - Status: Planned for future release.
> - Description: Server-Sent Events endpoint to stream LLM tokens to the Nuxt frontend in real time.

> [!NOTE]
> TODO 3: Multi-Tenancy and Workspace Isolation
> - Status: Planned for future release.
> - Description: Add tenant_id database partitioning and API token tenant extraction middleware.

> [!NOTE]
> TODO 4: Interactive Slack Bot Webhook Integration
> - Status: Planned for future release.
> - Description: Full bidirectional Slack bot (@askdocs, thread replies, and slash commands).
