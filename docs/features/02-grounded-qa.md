# Feature: Grounded Question Answering

**What:** Ask questions in natural language and get answers grounded in your uploaded documents with citations.

**Why it matters:** No hallucinations. Answers come only from your documents, or you get an honest "not found."

---

## User Story

```
As a customer support agent,
I want to ask "What is the refund policy for damaged items?"
So that I get the exact policy from our terms document with page numbers,
Instead of guessing or searching manually.
```

---

## How It Works

### Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'
```

### Response Types

#### 1. Answer Found (Grounded)

```json
{
  "answer": "Employees receive 15 days of paid vacation per year. Unused vacation days can be carried over up to a maximum of 5 days.",
  "sources": [
    {"document": "handbook.pdf", "page": 7},
    {"document": "handbook.pdf", "page": 8}
  ],
  "confidence": 0.89,
  "status": "answered"
}
```

**Key points:**
- Answer is **grounded** - uses only retrieved chunks
- **Citations** show exact source (document + page)
- **Confidence score** shows retrieval quality

---

#### 2. Not Found (Honest Refusal)

```json
{
  "answer": "not_found",
  "message": "The documents do not contain information to answer this question.",
  "confidence": 0.12,
  "status": "not_found"
}
```

**When this happens:**
- Question is off-topic (e.g., "What's the weather?")
- Information genuinely not in documents
- Retrieval confidence below threshold (default 0.7)

**This is a feature, not a bug.** Better to say "I don't know" than make up policies.

---

#### 3. Clarification Needed

```json
{
  "answer": "clarify",
  "message": "Your question is ambiguous. Are you asking about vacation leave, sick leave, or parental leave?",
  "status": "clarify"
}
```

**When this happens:**
- Question is too vague (e.g., "What about that?")
- Multiple possible interpretations

---

## Behind the Scenes

### The RAG Pipeline

```
Your Question: "What is the vacation policy?"
    ↓
1. Embed query → convert to vector
    ↓
2. Search database for similar chunks (top-5 by cosine similarity)
    ↓
3. LangGraph router evaluates query:
   ├─ Off-topic? → Refuse
   ├─ Ambiguous? → Clarify
   └─ Answerable? → Continue...
    ↓
4. Check retrieval confidence
   ├─ Score < 0.7? → "not_found"
   └─ Score ≥ 0.7? → Generate answer
    ↓
5. Build prompt:
   "Answer based ONLY on these chunks:
    [chunk 1 text]
    [chunk 2 text]
    Question: What is the vacation policy?"
    ↓
6. LLM generates answer → Extract citations → Return
```

---

## Grounding Guarantee

**How we prevent hallucinations:**

1. **Context-only prompts:** LLM only sees retrieved chunks, not general knowledge
2. **Confidence threshold:** If retrieval score <0.7, refuse to answer
3. **Citation tracking:** Every answer must cite source chunks
4. **Evaluation harness:** Automated tests check groundedness

**Example of what we DON'T do:**
```
❌ Bad prompt: "Answer this question about vacation policy: ..."
   → LLM might improvise based on general knowledge

✅ Good prompt: "Answer ONLY using these excerpts: [chunks]. If not covered, say 'not found'."
   → LLM restricted to provided context
```

---

## Configuration

### Tune Confidence Threshold

```bash
# .env
CONFIDENCE_THRESHOLD=0.7
```

**Effect:**
- **Higher (0.9):** Fewer answers, but extremely accurate (almost no hallucinations)
- **Lower (0.5):** More answers, but risk of lower-quality responses

**Finding the right value:**
```bash
# Run evaluation at different thresholds
python -m eval.tune_threshold

# Output:
# Threshold 0.5: 92% answer rate, 78% groundedness
# Threshold 0.7: 85% answer rate, 95% groundedness ← Sweet spot
# Threshold 0.9: 60% answer rate, 99% groundedness
```

---

### Tune Retrieval

```bash
# .env
RETRIEVAL_TOP_K=5          # Retrieve top-5 chunks
RETRIEVAL_THRESHOLD=0.5    # Min similarity score to include
```

**Effect:**
- **More chunks (top-10):** Better chance of finding answer, but more noise
- **Fewer chunks (top-3):** Faster, cleaner context, but might miss answer

---

## Real-World Examples

### Example 1: Customer Support

**Question:** "What's your return policy for damaged items?"

**Answer:**
```
"Items damaged during shipping can be returned within 30 days for a full
refund. Please email support@company.com with photos of the damage and
your order number."

Sources: [terms.pdf, page 5]
Confidence: 0.91
```

**Impact:** Support agent gets exact answer in 2 seconds vs 5 minutes searching docs.

---

### Example 2: HR Portal

**Question:** "How do I request parental leave?"

**Answer:**
```
"Employees are entitled to 12 weeks of parental leave. To request leave,
submit form HR-101 to your manager at least 30 days before the intended
start date."

Sources: [handbook.pdf, page 23]
Confidence: 0.88
```

**Impact:** Employee self-serves, HR team saves 10+ hours/week on FAQs.

---

### Example 3: Legal Contract Review

**Question:** "What's the standard termination clause for NDA contracts?"

**Answer:**
```
"This agreement remains in effect for 2 years from the date of signing
and may be terminated by either party with 30 days written notice."

Sources: [nda-template-v3.pdf, page 4]
Confidence: 0.94
```

**Impact:** Lawyer finds precedent instantly vs manual search through 100s of contracts.

---

## When It Says "Not Found"

**Common reasons:**

1. **Truly not in documents**
   - Solution: Upload missing document or update existing docs

2. **Question phrased differently than document**
   - Try rephrasing: "vacation policy" vs "paid time off"

3. **Information split across chunks**
   - Increase `RETRIEVAL_TOP_K` to capture more context

4. **Threshold too strict**
   - Lower `CONFIDENCE_THRESHOLD` (but test groundedness!)

---

## Testing Groundedness

**Run evaluation:**
```bash
docker compose exec api python -m eval.run
```

**Output:**
```
Retrieval Hit-Rate: 85% (17/20 questions found correct chunk in top-5)
Answer Groundedness: 95% (19/20 answers only used retrieved chunks)
Correct Refusals: 100% (5/5 off-topic questions refused)
```

**What to optimize:**
- Hit-rate <80% → Tune chunking or embeddings
- Groundedness <90% → Raise confidence threshold
- Too many refusals → Lower threshold or improve docs

---

## Limitations & Future Plans

**Current limitations:**
- Single-turn only (no conversation history)
- English-optimized (multilingual works but less accurate)
- No image/table understanding (text only)

**Future enhancements:**
- [ ] Multi-turn chat (see [Multi-turn Chat](04-multi-turn-chat.md))
- [ ] Multi-language optimization
- [ ] Table extraction and understanding
- [ ] Follow-up question suggestions

---

## Next Steps

→ [Multi-turn Chat](04-multi-turn-chat.md) - Ask follow-up questions
→ [Evaluation](07-evaluation.md) - Measure and improve quality
