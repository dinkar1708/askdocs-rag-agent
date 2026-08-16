# Technical FAQ and Knowledge Base - AskDocs RAG Agent

This documentation is structured into three progressive difficulty tiers (Beginner, Intermediate, Advanced) following a modular, question-and-answer design.

---

## FAQ Navigation by Tier

### 1. Beginner Tier (Foundations and Concepts)
Essential concepts, project overview, RAG basics, and local environment setup.

- [01. Project Overview and Value Proposition](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/beginner/01_project_overview.md)
  - Problem AskDocs solves vs generic ChatGPT
  - High-level architecture and design
  - Persistent knowledge base and grounded citation model
- [02. RAG and Embeddings Fundamentals](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/beginner/02_rag_and_embeddings_fundamentals.md)
  - Definition and workflow of RAG (Retrieval-Augmented Generation)
  - Vector embeddings (384 dimensions, sentence-transformers)
  - Cosine distance vs dot product
- [03. Chunking and Tokenization](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/beginner/03_chunking_and_tokenization.md)
  - Fixed-size vs semantic chunking
  - Token counts, overlap strategies (512 tokens, 128 overlap)
- [04. Environment Setup and Configuration](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/beginner/04_environment_and_quickstart.md)
  - Docker Compose setup (PostgreSQL, FastAPI, Nuxt 3)
  - Pydantic configuration and environment variable management

---

### 2. Intermediate Tier (Implementation and Architecture)
Core backend implementation, database schemas, LangGraph state machines, and testing.

- [01. Vector Database and pgvector](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/intermediate/01_vector_database_and_pgvector.md)
  - Database schema (documents, chunks, sessions, messages)
  - pgvector HNSW indexing vs flat scan
  - Alembic migrations and hybrid search TSVECTOR
- [02. Retrieval and Cross-Encoder Reranking Pipeline](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/intermediate/02_retrieval_and_reranking_pipeline.md)
  - Two-stage retrieval (Bi-encoder candidate search -> Cross-encoder rerank)
  - BAAI/bge-reranker-v2-m3 integration
  - Latency vs relevance accuracy trade-offs
- [03. Query Routing and LangGraph State Machine](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/intermediate/03_query_routing_and_langgraph.md)
  - LangGraph StateGraph query routing implementation
  - The 3 paths: ANSWER, CLARIFY, REFUSE
  - Confidence scoring and hallucination prevention
- [04. LLM Adapter and Strategy Pattern](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/intermediate/04_llm_adapter_pattern.md)
  - Strategy Pattern with BaseLLMProvider
  - Google Gemini, Ollama (local llama3.2), Azure OpenAI, Mock
  - Swappable configuration via LLM_PROVIDER
- [05. API Design and Multi-Turn Sessions](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/intermediate/05_api_design_and_sessions.md)
  - FastAPI endpoints (/documents, /ask, /sessions)
  - Multi-turn conversation state and history management
  - CORS middleware, OpenAPI Swagger docs
- [06. Testing Strategy and Environment Isolation](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/intermediate/06_testing_strategy_and_isolation.md)
  - Unit tests, integration tests, and Playwright E2E tests
  - Test database isolation (port 5433 vs dev port 5432)
  - Deterministic testing with Mock LLM vs real Ollama

---

### 3. Advanced Tier (Scale, Security and Production)
Enterprise system design, PDF table parsing, security audits, cloud deployment, and business ROI.

- [01. System Design: Scaling to 1 Million Users](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/advanced/01_system_design_scaling_1m_users.md)
  - Horizontal scaling (Cloud Run, PgBouncer, Redis caching)
  - Vector quantization and database read replicas
  - Multi-tenancy isolation models
- [02. Advanced RAG: PDF Table Parsing and Semantic Chunking](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/advanced/02_advanced_rag_tables_and_chunking.md)
  - PDF table extraction to Markdown (pdfplumber)
  - Semantic boundary detection and hierarchical chunking
  - Asynchronous background document ingestion graph
- [03. Security, Auth and SQL Injection Defense](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/advanced/03_security_and_sql_injection_prevention.md)
  - Regex validation on dynamic JSON metadata keys
  - Parameterized queries with SQLAlchemy
  - API key authentication header middleware
- [04. Cloud Deployment (GCP Cloud Run and Azure)](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/advanced/04_cloud_deployment_gcp_azure.md)
  - Serverless container deployment on Google Cloud Run
  - Managed PostgreSQL with pgvector (Cloud SQL / Azure Flexible Server)
  - CI/CD GitHub Actions workflows
- [05. Cost Analysis, Business ROI and Roadmap](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/docs/technical/FAQ/advanced/05_cost_analysis_and_roi.md)
  - Cloud vs Local LLM cost modeling ($72/mo vs $50/mo)
  - Enterprise search ROI (>99% savings vs per-seat licenses)
  - Future roadmap (HyDE, Slack bot, Evaluation harness)
