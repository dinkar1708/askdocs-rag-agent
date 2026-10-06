# AskDocs RAG Agent - Agent Instructions & Workspace Rules

This file provides workspace context, coding standards, and operational guidelines for AI agents working in this repository.

---

## 🛠️ Project Overview
AskDocs is an enterprise-grade Document Q&A system built with FastAPI, LangGraph, pgvector, and Nuxt 3.

- **Backend:** FastAPI (Python 3.11), SQLAlchemy, Alembic, PostgreSQL with pgvector
- **Workflow & Routing:** LangGraph state machines
- **Frontend:** Nuxt 3 (Vue 3, TypeScript) on port 3000
- **AI/LLMs:** Google Gemini, Ollama, Azure OpenAI

---

## 🚀 Common Commands

### Running Services
- **Full Stack (Docker):** `docker compose up -d`
- **Backend API:** `http://localhost:8000`
- **API Docs (Swagger):** `http://localhost:8000/docs`
- **Frontend (Web UI):** `http://localhost:3000`

### Testing & Quality
- **Run backend tests:** `pytest` or `docker compose exec api pytest`
- **Run specific test file:** `pytest app/tests/test_query_routing.py`
- **Linting & Formatting:** `black app/`, `flake8 app/`, `mypy app/`

### Database Migrations
- **Create migration:** `alembic revision --autogenerate -m "description"`
- **Apply migrations:** `alembic upgrade head`
- **Rollback:** `alembic downgrade -1`

---

## 📋 Coding Guidelines & Rules
1. **Preserve Compatibility:** Always maintain clean API response schemas defined in `app/schemas/`.
2. **Atomic DB Transactions:** Always manage DB sessions cleanly; flush before commit when IDs are needed.
3. **Error Handling:** All endpoints must catch exceptions, log stack traces, and return standard HTTP error responses.
4. **LangGraph State Management:** Ensure state definitions use `TypedDict` and all node functions are deterministic and safe.
