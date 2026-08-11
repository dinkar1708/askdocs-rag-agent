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
  -H "X-API-Key: test-api-key-not-for-production" \
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
1. Embed query → convert to 384-dim vector (all-MiniLM-L6-v2)
    ↓
2. Search database for similar chunks (top-5 by cosine similarity)
    ↓
3. Query router evaluates query (simple threshold-based logic):
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

**Note:** Current query routing uses simple threshold-based logic (custom Python class). LangGraph implementation for advanced multi-step routing is planned. Single-stage retrieval is used; reranking is planned for Phase 2 (see roadmap below).

---

## Grounding Guarantee

**How we prevent hallucinations:**

1. **Context-only prompts:** LLM only sees retrieved chunks, not general knowledge
2. **Confidence threshold:** If retrieval score <0.7, refuse to answer
3. **Citation tracking:** Every answer must cite source chunks

> **Note:** Automated evaluation harness for groundedness testing will be implemented later. See [Evaluation](07-evaluation.md) for planned metrics.

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

Test different thresholds manually by changing the `.env` value and observing answer quality. Automated threshold tuning will be implemented later as part of the evaluation harness.

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

> **Note:** Automated evaluation harness will be implemented later. See [Feature 07: Evaluation](07-evaluation.md) for planned implementation.

**Manual testing:**
1. Ask test questions from your documents
2. Verify answers cite correct sources
3. Try off-topic questions - should return "not_found"
4. Check that citations match actual document content

**Metrics to track** (when evaluation harness is implemented):
- Retrieval Hit-Rate: % of questions where correct chunk in top-k
- Answer Groundedness: % of answers using only retrieved chunks
- Correct Refusals: % of off-topic questions correctly refused

**What to optimize:**
- Low accuracy → Tune chunking or embeddings
- Hallucinations → Raise confidence threshold
- Too many refusals → Lower threshold or improve docs

---

## Limitations & Future Plans

### Current Limitations

**Retrieval:**
- Single-stage retrieval (no reranking)
- Cosine similarity only (no hybrid search with BM25)
- Fixed top-k (no dynamic retrieval based on query complexity)

**Understanding:**
- Single-turn only (no conversation history - see [Multi-turn Chat](04-multi-turn-chat.md))
- English-optimized (multilingual works but less accurate)
- No table structure understanding (tables extracted as plain text)
- Images/diagrams ignored completely

**Answer Quality:**
- May miss answers if they're split across chunks poorly
- No cross-document synthesis (answers from single document only)

### Planned Enhancements

**Phase 1: Better Retrieval** (High Priority)
- [ ] **Reranking** - Two-stage retrieval (retrieve 20-50, rerank to top 5-10)
  - Cross-encoder models (bge-reranker-v2-m3)
  - Better relevance scoring
- [ ] **Hybrid search** - Combine semantic search + BM25 keyword matching
- [ ] **Query expansion** - Generate multiple query variants for better recall

**Phase 2: Better Understanding**
- [ ] Table-aware retrieval - Understand and query table structures
- [ ] Hierarchical retrieval - Use document structure for better context
- [ ] Cross-document synthesis - Combine answers from multiple sources

**Phase 3: UX Improvements**
- [ ] Follow-up question suggestions
- [ ] Explanation of retrieval (why these chunks were selected)
- [ ] Multi-language optimization

See [ROADMAP.md](../ROADMAP.md) for technical implementation details.

---

## TODO: LangGraph-Based Citation Verification

**Status:** Will be implemented later

**What:** Multi-step verification workflow using LangGraph to validate that LLM-generated citations actually exist in retrieved chunks and semantically support the claims made in answers.

**Current Problem:**
- Citations returned are just the retrieved chunks, not verified against what LLM actually used
- If model drifts or hallucinates, we don't catch citation mismatches
- No semantic verification that cited chunk actually supports the claim
- Risk of "citation hallucination" (citing documents that don't support the answer)

**Why LangGraph:**
- Multi-step workflow: Generate answer → Extract claimed citations → Verify existence → Semantic check → Flag/Accept
- Conditional branching: Different paths for verified vs suspicious citations
- State management: Track verification status across multiple LLM calls
- Potential retry loops: Re-verify with different prompts if ambiguous

**Implementation Plan:**

1. **StateGraph Architecture:**
   ```
   Generate Answer (with context)
     ↓
   Extract Claimed Citations (parse [doc.pdf, p.5] patterns)
     ↓
   Verify Against Context (check if cited chunks were in retrieval results)
     ├─ Found? → Semantic Verify (does chunk support claim?)
     │           ├─ Match? → ✅ Accept citation
     │           └─ No match? → ⚠️ Flag as suspicious
     └─ Not Found? → 🚨 Flag as hallucination
   ```

2. **State Definition:**
   ```python
   class CitationVerificationState(TypedDict):
       question: str
       context_chunks: List[Dict]
       generated_answer: str
       claimed_citations: List[Dict]
       verified_citations: List[Dict]
       flagged_citations: List[Dict]
   ```

3. **API Integration:**
   - Enable with `CITATION_VERIFICATION_ENABLED=true`
   - Response includes new fields:
     - `verified_citations` - Citations that passed verification
     - `flagged_citations` - Citations flagged as suspicious or hallucinated
     - `verification_status` - Overall verification result

4. **Benefits:**
   - Catches hallucinated citations before returning to user
   - Flags citation drift (when answer doesn't match sources)
   - Improves trust in RAG system
   - Perfect for high-stakes use cases (legal, medical, compliance)

---

## Next Steps

→ [Multi-turn Chat](04-multi-turn-chat.md) - Ask follow-up questions
→ [Evaluation](07-evaluation.md) - Measure and improve quality
