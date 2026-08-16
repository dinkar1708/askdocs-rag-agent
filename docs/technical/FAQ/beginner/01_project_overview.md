# Beginner Level: Project Overview & Value Proposition

---

## 1. Project Purpose & Problem Statement

### Q1: What is AskDocs and what problem does it solve?
**Answer:**
AskDocs is an enterprise Document Q&A system built with **FastAPI**, **LangGraph**, **PostgreSQL with pgvector**, and **Nuxt 3**. 

In modern organizations, employees and customers waste hours searching through company policies, technical manuals, and financial reports. Generic LLMs hallucinate facts about internal procedures and lack persistent memory.

AskDocs implements a **"grounded-or-refuse" architecture**:
- **Persistent Knowledge Base**: Documents are uploaded and indexed once in PostgreSQL with pgvector.
- **Exact Citations**: Answers cite the precise document and page number.
- **Zero Hallucinations**: Out-of-scope or low-confidence queries return explicit refusals (`not_found`).

---

## 2. Minimal Code Walkthrough: End-to-End RAG Concept

Here is a minimal, self-contained Python example illustrating how AskDocs processes documents and answers questions:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# 1. Ingestion: Document chunks
document_chunks = [
    {"doc": "handbook.pdf", "page": 1, "text": "Full-time employees receive 15 days of PTO annually."},
    {"doc": "handbook.pdf", "page": 2, "text": "Working hours are Monday to Friday, 9:00 AM to 5:00 PM."},
    {"doc": "handbook.pdf", "page": 3, "text": "Health insurance covers 80% of dental and vision expenses."}
]

# 2. Embedding: Convert text to 384-dimensional vectors
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
chunk_vectors = model.encode([c["text"] for c in document_chunks])

# 3. Retrieval: Search for user's question
query = "How much paid time off do I get?"
query_vector = model.encode(query)

# Calculate Cosine Similarities (Dot product of normalized vectors)
similarities = np.dot(chunk_vectors, query_vector) / (
    np.linalg.norm(chunk_vectors, axis=1) * np.linalg.norm(query_vector)
)

best_chunk_idx = int(np.argmax(similarities))
best_chunk = document_chunks[best_chunk_idx]
print(f"Top Match: {best_chunk['text']} (Source: {best_chunk['doc']}, Page: {best_chunk['page']})")

# 4. Augmented Generation: Formulate prompt with exact citations
prompt = f"""You are a helpful assistant. Answer ONLY from the context below.
Context:
[{best_chunk['doc']} - Page {best_chunk['page']}]
{best_chunk['text']}

Question: {query}
Answer:"""
print("\nGenerated LLM Prompt:\n", prompt)
```

---

## 3. Comparison: Generic ChatGPT vs AskDocs

| Feature | Generic ChatGPT File Upload | AskDocs RAG Agent |
| :--- | :--- | :--- |
| **Knowledge Persistence** | Ephemeral (must re-upload per chat) | **Persistent** (PostgreSQL + pgvector database) |
| **Citation Guarantee** | May invent citations or summarize broadly | **Exact citations** verified with document & page |
| **Hallucination Behavior** | Tendency to guess or make up facts | **Explicit refusal (`not_found`)** when below threshold |
| **Architecture** | Closed black-box cloud | **Modular & Extensible** (FastAPI + LangGraph) |
| **Deployment & Cost** | Per-seat monthly subscription | **Self-hosted / Cloud Run**, supports free local LLMs (Ollama) |
| **Integration** | Web UI only | **API-first REST endpoints**, Web UI, Slack bot ready |
