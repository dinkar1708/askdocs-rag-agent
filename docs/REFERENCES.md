# Official References & Best Practices

This document lists official documentation, research papers, framework guides, and best practices followed in the **AskDocs RAG Agent** project.

Project Repository: [github.com/dinkar1708/askdocs-rag-agent](https://github.com/dinkar1708/askdocs-rag-agent)  
Author / Maintainer: [Dinakar Maurya](https://github.com/dinkar1708)

---

## 1. Project & Core Architecture Links

1. **AskDocs Main Repository** `[Project Core]`
   - https://github.com/dinkar1708/askdocs-rag-agent
   - **Why:** Primary codebase, issue tracker, and project documentation

2. **Nuxt 3 Framework** `[Implemented Frontend]`
   - https://nuxt.com/docs
   - https://nuxt.com/docs/guide/going-further/runtime-config
   - **Why:** Modern Vue 3 SSR/SPA web application framework powering `web-ui/`

3. **Tailwind CSS** `[Implemented Frontend]`
   - https://tailwindcss.com/docs
   - **Why:** Utility-first styling for the responsive document chat interface

4. **pdfplumber (PDF Text & Table Extraction)** `[Implemented Ingestion]`
   - https://github.com/jsvine/pdfplumber
   - **Why:** Visual table bounding box detection and Markdown table conversion in `app/services/table_processor.py`

5. **BGE Reranker v2 m3 (BAAI)** `[Implemented Reranking]`
   - https://huggingface.co/BAAI/bge-reranker-v2-m3
   - **Why:** State-of-the-art multilingual cross-encoder model used in `app/services/reranker.py`

---

## 2. RAG (Retrieval-Augmented Generation)

### Official Papers & Research

6. **RAG Paper (Original)** - Lewis et al., 2020 `[Research & Standards]`
   - https://arxiv.org/abs/2005.11401
   - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
   - **Why:** Foundational paper introducing RAG architecture

7. **HNSW Vector Indexing Paper** - Malkov & Yashunin, 2018 `[Vector Search Foundations]`
   - https://arxiv.org/abs/1603.09320
   - "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs"
   - **Why:** Mathematical foundation for pgvector HNSW index operations

8. **LangChain RAG Documentation** `[Architecture Reference]`
   - https://python.langchain.com/docs/use_cases/question_answering/
   - **Why:** Industry-standard RAG implementation patterns we follow

9. **OpenAI Embeddings & Search** `[Industry Reference]`
   - https://platform.openai.com/docs/guides/embeddings
   - **Why:** Production embedding and retrieval patterns from OpenAI

10. **Anthropic Prompt Engineering & Contextual Retrieval** `[Industry Reference]`
    - https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
    - https://www.anthropic.com/research/contextual-retrieval
    - **Why:** Best practices for grounded generation and contextual retrieval

---

## 3. LLM Integration

### Official LLM Provider Docs

11. **Google Gemini API** `[Implemented Provider]`
    - https://ai.google.dev/gemini-api/docs
    - https://ai.google.dev/gemini-api/docs/text-generation
    - **Why:** Cloud LLM provider in `app/llm/gemini_provider.py`

12. **Ollama Documentation** `[Implemented Provider]`
    - https://github.com/ollama/ollama/blob/main/docs/api.md
    - https://ollama.com/library
    - **Why:** Local/offline LLM support in `app/llm/ollama_provider.py`

13. **Azure OpenAI Service** `[Implemented Provider]`
    - https://learn.microsoft.com/en-us/azure/ai-services/openai/
    - **Why:** Enterprise LLM deployment option in `app/llm/azure_provider.py`

14. **LangGraph Documentation** `[Implemented Orchestration]`
    - https://langchain-ai.github.io/langgraph/
    - https://langchain-ai.github.io/langgraph/concepts/
    - **Why:** StateGraph query routing (`app/graph/query_routing_graph.py`) and async ingestion (`app/services/document_processor_graph.py`)

---

## 4. Vector Search & Embeddings

15. **pgvector Documentation** `[Implemented Storage]`
    - https://github.com/pgvector/pgvector
    - https://github.com/pgvector/pgvector#querying
    - **Why:** Vector similarity search in PostgreSQL (`app/db/models.py`)

16. **Sentence Transformers** `[Implemented Embeddings]`
    - https://www.sbert.net/
    - https://www.sbert.net/docs/pretrained_models.html
    - **Why:** Embedding model (`all-MiniLM-L6-v2`) used in `app/services/embeddings.py`

17. **Embedding Best Practices** - OpenAI `[Industry Reference]`
    - https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
    - **Why:** Vector embedding fundamentals and dimensionality analysis

---

## 5. Python & FastAPI Backend

### Framework Documentation

18. **FastAPI Official Docs** `[Implemented Backend]`
    - https://fastapi.tiangolo.com/
    - https://fastapi.tiangolo.com/tutorial/
    - **Why:** Primary REST API web framework in `app/main.py`

19. **Pydantic V2** `[Implemented Backend]`
    - https://docs.pydantic.dev/latest/
    - https://docs.pydantic.dev/latest/concepts/validators/
    - **Why:** Request/response validation schemas in `app/schemas/`

20. **SQLAlchemy 2.0** `[Implemented Backend]`
    - https://docs.sqlalchemy.org/en/20/
    - https://docs.sqlalchemy.org/en/20/orm/
    - **Why:** Database ORM in `app/db/database.py`

21. **Alembic Migrations** `[Implemented Backend]`
    - https://alembic.sqlalchemy.org/en/latest/
    - **Why:** Database schema migrations in `app/alembic/`

---

## 6. Python Best Practices & Standards

### Official Style Guides

22. **PEP 8 - Style Guide for Python Code** `[Coding Standards]`
    - https://peps.python.org/pep-0008/
    - **Why:** Python code style and formatting standards

23. **PEP 257 - Docstring Conventions** `[Coding Standards]`
    - https://peps.python.org/pep-0257/
    - **Why:** Documentation standards for all functions and modules

24. **PEP 484 - Type Hints** `[Coding Standards]`
    - https://peps.python.org/pep-0484/
    - **Why:** Strict type annotation standards across the backend

25. **Google Python Style Guide** `[Coding Standards]`
    - https://google.github.io/styleguide/pyguide.html
    - **Why:** Additional style conventions and engineering best practices

---

## 7. Testing Best Practices

26. **Pytest Documentation** `[Implemented Testing]`
    - https://docs.pytest.org/en/stable/
    - https://docs.pytest.org/en/stable/how-to/fixtures.html
    - **Why:** Backend testing framework and fixtures in `app/tests/conftest.py`

27. **FastAPI Testing (TestClient)** `[Implemented Testing]`
    - https://fastapi.tiangolo.com/tutorial/testing/
    - **Why:** REST API endpoint testing patterns

28. **Playwright Documentation** `[Implemented E2E Testing]`
    - https://playwright.dev/
    - https://playwright.dev/docs/intro
    - **Why:** E2E testing framework for Web UI in `web-ui/tests/`

29. **Playwright Best Practices** `[Implemented E2E Testing]`
    - https://playwright.dev/docs/best-practices
    - **Why:** Writing reliable, maintainable browser tests

---

## 8. Security Best Practices

30. **OWASP Top 10** `[Security Reference]`
    - https://owasp.org/www-project-top-ten/
    - **Why:** Vulnerability mitigation (injection prevention, broken auth)

31. **FastAPI Security** `[Implemented Security]`
    - https://fastapi.tiangolo.com/tutorial/security/
    - **Why:** API key header authentication in `app/core/auth.py`

32. **GCP Secret Manager & Azure Key Vault** `[Deployment Security]`
    - https://cloud.google.com/secret-manager/docs
    - https://azure.microsoft.com/en-us/products/key-vault
    - **Why:** Production secret injection without storing secrets in git

---

## 9. Evaluation & Observability

33. **RAGAS - RAG Evaluation** `[Planned Evaluation]`
    - https://docs.ragas.io/en/stable/
    - https://github.com/explodinggradients/ragas
    - **Why:** Automated MRR, context recall, and citation precision evaluation

34. **LangSmith** `[Observability Reference]`
    - https://docs.smith.langchain.com/
    - **Why:** LLM workflow tracing and observability

---

## 10. Deployment Best Practices

35. **Docker Best Practices** `[Implemented DevOps]`
    - https://docs.docker.com/develop/dev-best-practices/
    - https://docs.docker.com/build/building/best-practices/
    - **Why:** Container optimization and multi-stage builds

36. **Google Cloud Run** `[Deployment Reference]`
    - https://cloud.google.com/run/docs
    - **Why:** Serverless container deployment for FastAPI backend

37. **Azure Container Apps** `[Deployment Reference]`
    - https://learn.microsoft.com/en-us/azure/container-apps/
    - **Why:** Alternative deployment platform on Microsoft Azure

---

## 11. API Design

38. **REST API Best Practices** `[Architecture Standards]`
    - https://restfulapi.net/
    - https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design
    - **Why:** Resource-based endpoint structure (`/documents`, `/ask`, `/sessions`)

39. **OpenAPI Specification** `[Implemented API Specs]`
    - https://swagger.io/specification/
    - https://spec.openapis.org/oas/latest.html
    - **Why:** Auto-generated interactive documentation at `/docs`

---

## 12. Integrations

### Slack Bot

40. **Slack Bolt for Python** `[Planned Integration]`
    - https://slack.dev/bolt-python/
    - https://github.com/slackapi/bolt-python
    - **Why:** Official Slack framework for events, commands, and request verification

41. **Slack API Documentation** `[Planned Integration]`
    - https://api.slack.com/docs
    - https://api.slack.com/start
    - **Why:** Slack platform fundamentals (scopes, events, slash commands)

---

## 13. Additional Resources

### Advanced RAG Techniques

42. **Chunking Strategies** - Pinecone `[Technical Guide]`
    - https://www.pinecone.io/learn/chunking-strategies/
    - **Why:** Text chunking heuristics and overlap tuning

43. **HyDE (Hypothetical Document Embeddings)** - Gao et al., 2022 `[Planned Feature]`
    - https://arxiv.org/abs/2212.10496
    - **Why:** Zero-shot dense retrieval technique planned for complex questions

44. **Hybrid Search (BM25 + Vector)** `[Implemented Feature]`
    - https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html
    - **Why:** Reciprocal Rank Fusion (RRF) combining keyword and semantic search

---

## 14. Tools & Linters

45. **Ruff Linter** `[Development Tool]`
    - https://docs.astral.sh/ruff/
    - **Why:** Fast Python linter and formatter

46. **MyPy Type Checker** `[Development Tool]`
    - https://mypy-lang.org/
    - **Why:** Static type checker for Python codebase

47. **Google Shell Style Guide** `[Development Tool]`
    - https://google.github.io/styleguide/shellguide.html
    - **Why:** Shell script standards for dev runner scripts

48. **Bash Best Practices** `[Development Tool]`
    - https://bertvv.github.io/cheat-sheets/Bash.html
    - https://sharats.me/posts/shell-script-best-practices/
    - **Why:** Writing maintainable shell scripts in `scripts/`

49. **PostgreSQL Official Documentation** `[Implemented Database]`
    - https://www.postgresql.org/docs/
    - **Why:** Primary relational and vector database

50. **pgAdmin** `[Development Tool]`
    - https://www.pgadmin.org/docs/
    - **Why:** Database GUI management tool

---

## 15. Learning Resources

51. **FastAPI Tutorial (Full Stack)** `[Learning Resource]`
    - https://fastapi.tiangolo.com/tutorial/
    - **Why:** Complete FastAPI fundamentals and dependency injection

52. **RAG from Scratch** `[Learning Resource]`
    - https://github.com/langchain-ai/rag-from-scratch
    - **Why:** Step-by-step conceptual walkthrough of RAG building blocks

53. **LangChain Academy** `[Learning Resource]`
    - https://academy.langchain.com/
    - **Why:** In-depth courses on LLM orchestration and LangGraph state machines

54. **Production Shell Script Examples** `[Learning Resource]`
    - https://github.com/facebook/react/tree/main/scripts (React)
    - https://github.com/nodejs/node/tree/main/tools (Node.js)
    - https://github.com/kubernetes/kubernetes/tree/master/hack (Kubernetes)
    - **Why:** Production-grade shell automation script reference
