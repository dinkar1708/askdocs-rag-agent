# Intermediate Level: API Design & Multi-Turn Sessions

---

## 1. REST Endpoints

### Q1: What REST API endpoints are provided by AskDocs?
**Answer:**
Defined across [`app/api/`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/api):

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/documents/` | Upload and asynchronously index a PDF file |
| `GET` | `/documents/` | List all uploaded documents with metadata |
| `GET` | `/documents/{id}` | Retrieve document details and chunk stats |
| `DELETE` | `/documents/{id}` | Cascade delete document and its vector chunks |
| `POST` | `/ask/` | Ask questions with LangGraph routing and source citations |
| `POST` | `/sessions/` | Create a multi-turn chat session |
| `GET` | `/sessions/{id}` | Retrieve session message history with citations |
| `DELETE` | `/sessions/{id}` | Delete a chat session and all messages |

---

## 2. Multi-Turn Session Architecture

### Q2: How are conversation sessions tracked across turns?
**Answer:**
When a `session_id` is passed to `/ask/`:
1. The user's question and assistant's answer (along with full JSON source citations) are atomically inserted into the `messages` table linked to `session_id`.
2. The session's `last_accessed` timestamp is updated.
3. In conversational mode, previous chat history can be summarized or passed to the query routing graph to resolve conversational pronouns (e.g. *"What about that?"* referring to an earlier subject).
