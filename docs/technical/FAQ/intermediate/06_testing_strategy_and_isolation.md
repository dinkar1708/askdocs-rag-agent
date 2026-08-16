# Intermediate Level: Testing Strategy & Environment Isolation

---

## 1. Test Isolation Architecture

### Q1: How does AskDocs isolate test data from development data?
**Answer:**
AskDocs strictly separates development and testing database instances and ports:

| Environment | Database Name | Port | Purpose |
| :--- | :--- | :--- | :--- |
| **Development** | `askdocs` | `5432` | Local dev and UI interaction |
| **Testing** | `askdocs_test` | `5433` | Isolated Pytest and Playwright runs |

Configured in [`app/tests/conftest.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/tests/conftest.py), pytest automatically runs against port `5433`, rolling back or deleting test data per fixture to prevent test pollution.

---

## 2. Test Execution Modes

### Q2: What are the two test execution modes in AskDocs?
**Answer:**
1. **Mock Provider Mode (`LLM_PROVIDER="mock"`)**:
   - Uses `MockLLMProvider` returning fast, deterministic responses in milliseconds.
   - Ideal for CI/CD pipelines, regression testing, and local unit test validation.
2. **Real LLM Mode (`LLM_PROVIDER="ollama"`, `OLLAMA_MODEL="llama3.2"`)**:
   - Executes real local inferences against the running Ollama model.
   - Validates end-to-end model output quality, grounding, and formatting.
