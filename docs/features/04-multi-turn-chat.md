# Feature: Multi-turn Chat

**What:** Have conversations with follow-up questions while maintaining context.

**Why it matters:** Users can ask "What about that?" and the system understands what "that" refers to.

---

## User Story

```
As a customer,
I want to ask follow-up questions without repeating context,
So I can have a natural conversation instead of rephrasing every question.
```

---

## How It Works

### Start a Conversation

**First question:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-not-for-production" \
  -d '{"message": "What is your return policy?"}'
```

**Response:**
```json
{
  "answer": "Items can be returned within 30 days for a full refund...",
  "sources": [{"document": "terms.pdf", "page": 5}],
  "confidence": 0.91,
  "session_id": "sess_abc123",
  "history": [
    {"role": "user", "content": "What is your return policy?"},
    {"role": "assistant", "content": "Items can be returned within 30 days..."}
  ]
}
```

**Key:** Save the `session_id` for follow-up questions.

---

### Ask Follow-up Questions

**Second question:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-not-for-production" \
  -d '{
    "message": "What about damaged items?",
    "session_id": "sess_abc123"
  }'
```

**Response:**
```json
{
  "answer": "Items damaged during shipping can be returned for a full refund. Please email support with photos...",
  "sources": [{"document": "terms.pdf", "page": 5}],
  "confidence": 0.89,
  "session_id": "sess_abc123",
  "history": [
    {"role": "user", "content": "What is your return policy?"},
    {"role": "assistant", "content": "Items can be returned within 30 days..."},
    {"role": "user", "content": "What about damaged items?"},
    {"role": "assistant", "content": "Items damaged during shipping can be returned..."}
  ]
}
```

**Notice:** The system understood "damaged items" in the context of returns.

---

### Third Question (Pronoun Resolution)

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-not-for-production" \
  -d '{
    "message": "Do I need to pay for return shipping?",
    "session_id": "sess_abc123"
  }'
```

**Response:**
```json
{
  "answer": "No, return shipping is free for damaged items. For other returns, customers are responsible for return shipping costs.",
  "sources": [{"document": "terms.pdf", "page": 5}],
  "confidence": 0.87,
  "session_id": "sess_abc123"
}
```

**Key:** System knows "return shipping" relates to the return policy conversation.

---

## Behind the Scenes

### Context Resolution

```
User: "What about damaged items?"

Without history:
→ "What are damaged items?" (too vague, unclear intent)

With history:
History: ["What is your return policy?", "Items can be returned..."]
→ Contextualized query: "What is the return policy for damaged items?"
→ Search with full context
```

### Session Management

**Session storage (PostgreSQL):**
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    history JSONB NOT NULL,  -- [{role, content}, ...]
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**History format:**
```json
{
  "session_id": "sess_abc123",
  "history": [
    {"role": "user", "content": "What is the refund policy?"},
    {"role": "assistant", "content": "Refunds are processed..."},
    {"role": "user", "content": "How long does it take?"},
    {"role": "assistant", "content": "Refunds take 5-7 business days..."}
  ]
}
```

---

## Configuration

### Conversation History Limit

```bash
# .env
MAX_HISTORY_TURNS=10    # Keep last 10 turns
```

**Why limit?**
- Older context becomes less relevant
- Token limits (LLM context window)
- Performance (less data to process)

**Example:**
```
Turn 1-10: Kept in context
Turn 11+: Dropped (oldest first)
```

---

### Session TTL

```bash
# .env
SESSION_TTL_HOURS=24    # Delete inactive sessions after 24 hours
```

**Cleanup job:**
```sql
DELETE FROM sessions
WHERE updated_at < NOW() - INTERVAL '24 hours';
```

---

## Real-World Example: Customer Support

**Conversation:**

```
User: "What's your shipping policy?"
Bot: "We offer free shipping on orders over $50. Standard shipping takes 3-5 business days."

User: "What about international orders?"
Bot: "International shipping takes 7-14 business days. Additional customs fees may apply. Minimum order $100."

User: "Can I track my package?"
Bot: "Yes, you'll receive a tracking number via email once your order ships. Track at shipping.company.com."

User: "Is tracking available for international orders too?"
Bot: "Yes, tracking is available for both domestic and international orders."
```

**Without multi-turn chat, user would need to ask:**
- "Is tracking available for international orders?"

**With multi-turn, user can naturally ask:**
- "Is it available for international orders too?"

System understands "it" = tracking, "international orders" from context.

---

## Use Cases

### 1. Customer FAQ Bot

```
Customer: "Do you offer gift wrapping?"
Bot: "Yes, gift wrapping is available for $5 per item."

Customer: "Can I add a custom message?"
Bot: "Yes, you can include a custom gift message at no extra cost. Enter it during checkout."

Customer: "Is there a character limit?"
Bot: "Gift messages are limited to 200 characters."
```

---

### 2. Employee Self-Service

```
Employee: "How do I request vacation?"
Bot: "Submit form HR-101 to your manager at least 2 weeks before your desired start date."

Employee: "Where do I find that form?"
Bot: "Form HR-101 is available on the HR portal under Forms > Time Off > Vacation Request."

Employee: "What if my manager is out of office?"
Bot: "If your manager is unavailable, submit to your department head or HR directly."
```

---

### 3. Technical Support

```
User: "How do I reset my password?"
Bot: "Click 'Forgot Password' on the login page. Enter your email and follow the reset link sent to you."

User: "I didn't get the email"
Bot: "Check your spam folder. If still not received, contact support@company.com or call 1-800-XXX-XXXX."

User: "What's the support hours?"
Bot: "Support is available Monday-Friday, 9am-5pm EST."
```

---

## Limitations & Future Plans

**Current limitations:**
- Session stored in database (not distributed)
- No session sharing (can't resume on different device)
- History truncated (no infinite context)

**Future enhancements:**
- [ ] Redis-based session storage (distributed)
- [ ] Session export/import (resume anywhere)
- [ ] Conversation branching (explore alternate paths)
- [x] ✅ Context summarization (keep more history in compressed form) - **IMPLEMENTED**

---

## ✅ Context Summarization

**Status:** ✅ IMPLEMENTED

**Implementation:** `app/services/context_summarizer.py`

**What:** Automatically compress long conversation histories while preserving important context.

Instead of dropping old messages when hitting context limits, we summarize them intelligently.

### How It Works

**Problem:** Long conversations exceed LLM context windows
- Typical limit: 10-20 message pairs
- Old messages get dropped completely
- Loses important context from earlier in conversation

**Solution:** Summarize old messages
```
Messages 1-10: "User asked about vacation policy, learned about 15 days PTO"
Messages 11-20: [Keep unsummarized - most recent context]
```

### Two Strategies

#### 1. Simple Summarization
- Keep last N turns unchanged
- Summarize everything older into a concise summary
- Fast and predictable

#### 2. Adaptive Summarization (Recommended)
- Identifies important messages (questions, key facts, citations)
- Preserves important messages even if old
- Summarizes only less important exchanges
- Smarter context preservation

### Configuration

```bash
# .env
CONTEXT_SUMMARIZATION_ENABLED=true
CONTEXT_SUMMARIZATION_STRATEGY=adaptive  # or "simple"
MAX_HISTORY_TURNS=10  # Keep last 10 turns unsummarized
IMPORTANCE_THRESHOLD=0.7  # For adaptive: preserve messages scoring > 0.7
```

### Usage

```python
from app.services.context_summarizer import create_summarizer

# Create summarizer
summarizer = create_summarizer(
    llm_provider,
    strategy="adaptive",
    max_history_turns=10
)

# Summarize history
compressed = summarizer.summarize_history(messages)

# Before: 50 messages
# After: 1 summary + 10 recent messages = 11 total
```

### Benefits

✅ **Longer conversations** - Maintain context for 100+ turn conversations
✅ **Better context** - Preserve important info instead of just recent
✅ **Token efficiency** - Reduce LLM costs by compressing history
✅ **Automatic** - Works transparently in multi-turn chat

### Example

**Without summarization (10 turn limit):**
```
Turn 1-10: [Kept]
Turn 11+: [Dropped - context lost!]
```

**With adaptive summarization:**
```
Summary: "User asked about vacation (15 days), sick leave (10 days), remote work policy"
Turn 5: [Kept - important question with citation]
Turn 11-20: [Kept - recent context]
```

### Tests

`app/tests/test_context_summarizer.py` (12 test cases)
- Simple summarization
- Adaptive importance scoring
- Message deduplication
- Order preservation

---

## API Reference

See [API.md](../docs/API.md#multi-turn-chat) for detailed endpoint docs.

---

## Next Steps

→ [Query Routing](05-query-routing.md) - How the system decides: answer / clarify / refuse
→ [MCP Integration](06-mcp-integration.md) - Use in Claude Desktop
