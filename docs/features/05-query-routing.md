# Feature: LangGraph Query Router

**Status:** 100% IMPLEMENTED

**What:** Intelligent routing that classifies questions into: answer / clarify / refuse paths using LangGraph state machine.

**Why it matters:** Prevents wasted LLM calls on unanswerable questions and guides users to better questions.

**Implementation:** `app/graph/query_routing_graph.py`

---

## User Story

```
As a system architect,
I want the system to detect off-topic or ambiguous questions early,
So we don't waste API calls generating bad answers or hallucinating.
```

---

## The Three Paths

### 1. Answer Path (Happy Path)

**Trigger:** Question is clear and answerable from documents.

**Example:**
```
Q: "What is the vacation policy?"
→ Route: ANSWER
→ Retrieve chunks → Generate answer → Return with citations
```

---

### 2. Clarify Path

**Trigger:** Question is ambiguous or lacks context.

**Examples:**
```
Q: "What about that?"
→ Route: CLARIFY
→ Response: "Can you clarify what you're asking about?"

Q: "Leave policy"
→ Route: CLARIFY
→ Response: "Are you asking about vacation leave, sick leave, or parental leave?"
```

**Why this helps:**
- User gets a better answer when they rephrase
- Saves LLM token costs on doomed queries

---

### 3. Refuse Path (Out of Scope)

**Trigger:** Question is off-topic or not in documents.

**Examples:**
```
Q: "What's the weather today?"
→ Route: REFUSE
→ Response: "not_found - This question cannot be answered from the uploaded documents."

Q: "Write me a Python script"
→ Route: REFUSE
→ Response: "This service only answers questions about uploaded documents."
```

**Why we refuse:**
- Prevents hallucinations
- Sets clear expectations (document Q&A only, not general assistant)

---

## How It Works

### LangGraph State Machine

```
                        START
                          │
                          ▼
                   classify_query()
                          │
          ┌───────────────┼───────────────┐
          │               │               │
      off_topic       ambiguous       answerable
          │               │               │
          ▼               ▼               ▼
     refuse_node    clarify_node    retrieve_node
          │               │               │
          ▼               ▼               ▼
         END             END       check_confidence()
                                          │
                                   ┌──────┴──────┐
                                   │             │
                              score < 0.7    score ≥ 0.7
                                   │             │
                                   ▼             ▼
                             refuse_node    answer_node
                                   │             │
                                   ▼             ▼
                                  END           END
```

---

## Classification Logic

### classify_query() Node

**How it classifies:**

```python
def classify_query(state):
    question = state["question"]

    # Check for off-topic patterns
    if any(word in question.lower() for word in ["weather", "sports", "news", "write code"]):
        return "off_topic"

    # Check for ambiguity
    if any(word in question.lower() for word in ["that", "it", "they", "those"]):
        # Without chat history, pronouns are ambiguous
        return "ambiguous"

    if len(question.split()) < 3:  # Too vague
        return "ambiguous"

    # Otherwise, assume answerable
    return "answerable"
```

**In production:** Use an LLM classifier instead of keyword matching:

```python
def classify_query_llm(question):
    prompt = f"""
    Classify this question into one of:
    - "answerable": Can be answered from policy/handbook documents
    - "ambiguous": Needs clarification (too vague, uses pronouns without context)
    - "off_topic": Not related to policies/documents (weather, news, general questions)

    Question: {question}
    Classification:
    """
    classification = llm.complete(prompt)
    return classification.strip()
```

---

## Confidence Check

**After retrieval:**

```python
def check_confidence(state):
    chunks = state["retrieved_chunks"]

    if not chunks:
        return "refuse"

    # Check top score
    top_score = chunks[0]["score"]

    if top_score < CONFIDENCE_THRESHOLD:  # Default: 0.7
        return "refuse"

    return "answer"
```

**Why two refusal points?**
1. **Before retrieval** (classify_query): Save retrieval costs on obvious off-topic
2. **After retrieval** (check_confidence): Catch questions where retrieval failed

---

## Configuration

```bash
# .env
CONFIDENCE_THRESHOLD=0.7    # Min retrieval score to answer
ENABLE_CLARIFY=true         # Enable clarification path (vs always refusing)
```

---

## Real-World Examples

### Example 1: E-commerce Support

**Answerable:**
```
Q: "What's your return policy?"
→ ANSWER: "Items can be returned within 30 days..."
```

**Clarify:**
```
Q: "Return policy"
→ CLARIFY: "Are you asking about return timeframes, return shipping costs, or refund processing?"
```

**Refuse:**
```
Q: "What's the best laptop to buy?"
→ REFUSE: "not_found - This question is not covered in our policy documents."
```

---

### Example 2: HR Handbook

**Answerable:**
```
Q: "How many vacation days do employees get?"
→ ANSWER: "Employees receive 15 days per year..."
```

**Clarify:**
```
Q: "Leave"
→ CLARIFY: "Are you asking about vacation leave, sick leave, or parental leave?"
```

**Refuse:**
```
Q: "What's the stock price?"
→ REFUSE: "not_found - Financial information is not in the employee handbook."
```

---

## Evaluation

**Test routing accuracy:**

```bash
# eval/routing_tests.json
[
  {
    "question": "What is the refund policy?",
    "expected_route": "answer"
  },
  {
    "question": "Policy",
    "expected_route": "clarify"
  },
  {
    "question": "What's the weather?",
    "expected_route": "refuse"
  }
]

# Run test
python -m eval.test_routing
# Output:
# Routing accuracy: 95% (19/20 correct)
```

---

## Advanced: Custom Routing Logic

**Add domain-specific rules:**

```python
# app/graph/classifiers.py

def classify_hr_query(question):
    """Custom classifier for HR documents."""

    # HR-specific topics
    hr_topics = ["vacation", "leave", "benefits", "handbook", "salary", "hours"]

    if any(topic in question.lower() for topic in hr_topics):
        return "answerable"

    # Needs more context
    if question.endswith("?") is False:
        return "clarify"

    # Default: off-topic
    return "off_topic"
```

---

## ✅ Implementation Status

**Status:** ✅ **COMPLETE - LangGraph Implementation**

**What was implemented:**
- ✅ Full LangGraph state machine for query routing
- ✅ LLM-based classification (Ollama/Gemini/Azure)
- ✅ Fallback to threshold-based routing (fast, deterministic)
- ✅ Configuration via environment variables
- ✅ Integration with `/ask` API endpoint
- ✅ Comprehensive testing (18 test cases)

**Files created/modified:**
1. `app/graph/query_routing_graph.py` - LangGraph state machine (320 lines)
2. `app/api/questions.py` - Updated to use LangGraph router
3. `app/core/config.py` - Added routing configuration
4. `app/.env.example` - Added routing settings
5. `app/llm/mock_provider.py` - Added test support
6. `app/tests/test_query_routing.py` - 18 comprehensive tests

**Configuration:**
```bash
# Enable LLM-based classification (recommended)
QUERY_ROUTING_USE_LLM=True

# Confidence thresholds
QUERY_ROUTING_HIGH_CONFIDENCE=0.5  # Min score for "answer"
QUERY_ROUTING_LOW_CONFIDENCE=0.3   # Below this = "refuse"

# Enable clarification path
QUERY_ROUTING_ENABLE_CLARIFY=True
```

**Usage:**
```python
from app.graph.query_routing_graph import route_query
from app.llm.factory import get_llm_provider

# Route a query
result = await route_query(
    question="What is the vacation policy?",
    chunks=retrieved_chunks,
    llm_provider=get_llm_provider(),
    use_llm_classification=True
)

# Returns:
# {
#     "intent": "answer",  # or "clarify" or "refuse"
#     "confidence": 0.85,
#     "reason": "High confidence match found",
#     "classification_method": "llm",  # or "threshold"
#     "llm_reasoning": "Clear policy question"
# }
```

## Limitations & Future Plans

**Current capabilities:**
- ✅ LLM-based classification (smarter routing)
- ✅ Fallback threshold-based routing
- ✅ Configurable confidence thresholds
- ✅ Clarification path for ambiguous questions

**Future enhancements:**
- [ ] Multi-step query handling (decompose complex questions)
- [ ] Domain-specific classifiers (HR, legal, support, etc.)
- [ ] Confidence explanation (why did we refuse?)
- [ ] Query rewriting suggestions

---

## Metrics to Track

**Production monitoring:**

```python
# Log routing decisions
{
  "question": "What is the refund policy?",
  "route": "answer",
  "retrieval_score": 0.89,
  "answer_status": "success"
}

# Aggregate metrics:
# - % of queries answered (vs clarify/refuse)
# - % of refusals (high = docs incomplete or bad queries)
# - % of clarifications (high = users need guidance)
```

**Target metrics:**
- Answer rate: 70-85%
- Refusal rate: 10-20%
- Clarify rate: 5-10%

---

## Next Steps

→ [Multi-turn Chat](04-multi-turn-chat.md) - Resolve pronouns with history
→ [Evaluation](07-evaluation.md) - Test routing + groundedness
