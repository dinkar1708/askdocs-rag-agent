# Official References & Best Practices

This document lists official documentation and best practices we follow for building this RAG system.

---

## RAG (Retrieval-Augmented Generation)

### Official Papers & Research

1. **RAG Paper (Original)** - Lewis et al., 2020
   - https://arxiv.org/abs/2005.11401
   - "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"
   - **Why:** Foundational paper introducing RAG architecture

2. **LangChain RAG Documentation**
   - https://python.langchain.com/docs/use_cases/question_answering/
   - **Why:** Industry-standard RAG implementation patterns we follow

3. **OpenAI Embeddings & Search**
   - https://platform.openai.com/docs/guides/embeddings
   - **Why:** Production embedding and retrieval patterns from OpenAI

4. **Anthropic Prompt Engineering**
   - https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering
   - **Why:** Best practices for Claude models (includes retrieval patterns)

---

## LLM Integration

### Official LLM Provider Docs

5. **Google Gemini API**
   - https://ai.google.dev/gemini-api/docs
   - https://ai.google.dev/gemini-api/docs/text-generation
   - **Why:** Primary LLM provider for production

6. **Ollama Documentation**
   - https://github.com/ollama/ollama/blob/main/docs/api.md
   - https://ollama.com/library
   - **Why:** Local/offline LLM support

7. **Azure OpenAI Service**
   - https://learn.microsoft.com/en-us/azure/ai-services/openai/
   - **Why:** Enterprise LLM deployment option

8. **LangGraph Documentation**
   - https://langchain-ai.github.io/langgraph/
   - https://langchain-ai.github.io/langgraph/concepts/
   - **Why:** Query routing and agent workflows

---

## Vector Search & Embeddings

9. **pgvector Documentation**
   - https://github.com/pgvector/pgvector
   - https://github.com/pgvector/pgvector#querying
   - **Why:** Vector similarity search in PostgreSQL

10. **Sentence Transformers**
    - https://www.sbert.net/
    - https://www.sbert.net/docs/pretrained_models.html
    - **Why:** Embedding model (all-MiniLM-L6-v2) we use

11. **Embedding Best Practices** - OpenAI
    - https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
    - **Why:** Vector embedding fundamentals

---

## Python & FastAPI

### Framework Documentation

12. **FastAPI Official Docs**
    - https://fastapi.tiangolo.com/
    - https://fastapi.tiangolo.com/tutorial/
    - **Why:** Primary web framework

13. **Pydantic V2**
    - https://docs.pydantic.dev/latest/
    - https://docs.pydantic.dev/latest/concepts/validators/
    - **Why:** Request/response validation

14. **SQLAlchemy 2.0**
    - https://docs.sqlalchemy.org/en/20/
    - https://docs.sqlalchemy.org/en/20/orm/
    - **Why:** Database ORM

15. **Alembic Migrations**
    - https://alembic.sqlalchemy.org/en/latest/
    - **Why:** Database schema migrations

---

## Python Best Practices

### Official Style Guides

16. **PEP 8 - Style Guide**
    - https://pep8.org/
    - https://peps.python.org/pep-0008/
    - **Why:** Python code style standards

17. **PEP 257 - Docstring Conventions**
    - https://peps.python.org/pep-0257/
    - **Why:** Documentation standards we follow

18. **PEP 484 - Type Hints**
    - https://peps.python.org/pep-0484/
    - **Why:** Type annotation standards

19. **Google Python Style Guide**
    - https://google.github.io/styleguide/pyguide.html
    - **Why:** Additional style conventions

---

## Testing Best Practices

20. **Pytest Documentation**
    - https://docs.pytest.org/en/stable/
    - https://docs.pytest.org/en/stable/how-to/fixtures.html
    - **Why:** Testing framework we use

21. **FastAPI Testing**
    - https://fastapi.tiangolo.com/tutorial/testing/
    - **Why:** API endpoint testing patterns

22. **Playwright Documentation**
    - https://playwright.dev/
    - https://playwright.dev/docs/intro
    - **Why:** E2E testing framework for web UI, simulates real user interactions

23. **Playwright Best Practices**
    - https://playwright.dev/docs/best-practices
    - **Why:** Writing reliable, maintainable E2E tests

---

## Security Best Practices

24. **OWASP Top 10**
    - https://owasp.org/www-project-top-ten/
    - **Why:** Security vulnerabilities we protect against

25. **FastAPI Security**
    - https://fastapi.tiangolo.com/tutorial/security/
    - **Why:** Authentication & authorization patterns

26. **Secrets Management**
    - https://cloud.google.com/secret-manager/docs
    - https://azure.microsoft.com/en-us/products/key-vault
    - **Why:** Production secrets handling

---

## Evaluation & Monitoring

27. **RAGAS - RAG Evaluation**
    - https://docs.ragas.io/en/stable/
    - https://github.com/explodinggradients/ragas
    - **Why:** RAG system evaluation metrics

28. **LangSmith**
    - https://docs.smith.langchain.com/
    - **Why:** LLM application observability (optional)

---

## Deployment Best Practices

29. **Docker Best Practices**
    - https://docs.docker.com/develop/dev-best-practices/
    - https://docs.docker.com/build/building/best-practices/
    - **Why:** Container deployment standards

30. **Google Cloud Run**
    - https://cloud.google.com/run/docs
    - **Why:** Serverless deployment option

31. **Azure Container Apps**
    - https://learn.microsoft.com/en-us/azure/container-apps/
    - **Why:** Alternative deployment platform

---

## API Design

32. **REST API Best Practices**
    - https://restfulapi.net/
    - https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design
    - **Why:** RESTful API design standards we follow

33. **OpenAPI Specification**
    - https://swagger.io/specification/
    - https://spec.openapis.org/oas/latest.html
    - **Why:** API documentation standard (FastAPI uses this)

---

## Integrations

### Slack Bot

34. **Slack Bolt for Python**
    - https://slack.dev/bolt-python/
    - https://github.com/slackapi/bolt-python
    - **Why:** Official framework for Slack bots, handles events, commands, and request verification

35. **Slack API Documentation**
    - https://api.slack.com/docs
    - https://api.slack.com/start
    - **Why:** Slack platform fundamentals (scopes, events, slash commands)

---

## Additional Resources

### RAG-Specific Patterns

36. **Advanced RAG Techniques**
    - https://www.anthropic.com/research/contextual-retrieval
    - "Contextual Retrieval" - Anthropic research
    - **Why:** Improving retrieval accuracy

37. **Chunking Strategies**
    - https://www.pinecone.io/learn/chunking-strategies/
    - **Why:** Text chunking best practices

38. **Hybrid Search**
    - https://www.elastic.co/guide/en/elasticsearch/reference/current/knn-search.html
    - **Why:** Combining keyword + semantic search (future feature)

---

## Tools We Use

### Code Quality

39. **Ruff Linter**
    - https://docs.astral.sh/ruff/
    - **Why:** Fast Python linter (replaces flake8, isort, etc.)

40. **MyPy Type Checker**
    - https://mypy-lang.org/
    - https://mypy.readthedocs.io/
    - **Why:** Static type checking

41. **Google Shell Style Guide**
    - https://google.github.io/styleguide/shellguide.html
    - **Why:** Shell script (.sh) coding standards we follow

42. **Bash Best Practices**
    - https://bertvv.github.io/cheat-sheets/Bash.html
    - https://sharats.me/posts/shell-script-best-practices/
    - **Why:** Writing reliable, maintainable shell scripts

### Database

43. **PostgreSQL Documentation**
    - https://www.postgresql.org/docs/
    - **Why:** Primary database

44. **pgAdmin**
    - https://www.pgadmin.org/docs/
    - **Why:** Database management tool

---

## Learning Resources

### For New Developers

45. **FastAPI Tutorial (Full Stack)**
    - https://fastapi.tiangolo.com/tutorial/
    - **Start here:** Complete FastAPI fundamentals

46. **RAG from Scratch**
    - https://github.com/langchain-ai/rag-from-scratch
    - **Why:** Understand RAG components step-by-step

47. **LangChain Academy**
    - https://academy.langchain.com/
    - **Why:** Free courses on LLM applications

48. **Real-World Shell Script Examples**
    - https://github.com/facebook/react/tree/main/scripts (React)
    - https://github.com/nodejs/node/tree/main/tools (Node.js)
    - https://github.com/kubernetes/kubernetes/tree/master/hack (Kubernetes)
    - **Why:** Examples of production shell scripts from major projects

---

## How We Apply These References

### Code Quality
- Follow **PEP 8** for all Python code
- Use **type hints (PEP 484)** on all functions
- Write **docstrings (PEP 257)** for public APIs
- Lint with **Ruff**, type-check with **MyPy**

### API Design
- Follow **REST best practices** (resource-based URLs)
- Use **FastAPI** patterns (dependency injection, async/await)
- Validate with **Pydantic** schemas
- Document with **OpenAPI/Swagger** (auto-generated)

### RAG Architecture
- Based on **Lewis et al. 2020** RAG paper
- Query routing with **LangGraph**
- Vector search with **pgvector**
- Embeddings with **Sentence Transformers**
- LLM integration following **provider docs** (Gemini, Ollama)

### Testing
- **Pytest** for all tests
- Test coverage target: **80%+**
- Integration tests with **TestClient** (FastAPI)
- Mock LLM calls for unit tests

### Security
- Follow **OWASP Top 10** guidelines
- API authentication (planned)
- Input validation (Pydantic)
- Secrets in environment variables (never commit)

### Deployment
- **Docker** best practices (multi-stage builds)
- Cloud-native (**Cloud Run** or **Container Apps**)
- Environment-based configuration
- Health checks and monitoring

---

## Quick Reference Card

**When adding a feature:**
1. Check **FastAPI docs** for API patterns
2. Check **Pydantic docs** for validation
3. Check **SQLAlchemy docs** for database
4. Check **LangChain/LangGraph** for RAG patterns
5. Check **project DEVELOPMENT.md** for local patterns

**When writing code:**
1. Follow **PEP 8** style
2. Add **type hints (PEP 484)**
3. Write **docstrings (PEP 257)**
4. Add **tests (pytest)**
5. Run **ruff check** and **mypy**

**When deploying:**
1. Check **Docker best practices**
2. Follow **cloud provider docs** (GCP/Azure)
3. Use **environment variables** for config
4. Enable **logging & monitoring**

---

## Keeping This Updated

This document should be updated when:
- We adopt a new tool/framework
- We change LLM providers
- We discover important best practices
- Official docs move to new URLs

**Maintenance:** Update when adopting new tools or discovering new best practices

---

## Getting Help

If you need clarification on any standard:
1. Check the official doc link above
2. See `docs/development/DEVELOPMENT.md` for project-specific patterns
3. Ask in GitHub issues or team chat

---

**Note:** If a link is broken, please update this document.
