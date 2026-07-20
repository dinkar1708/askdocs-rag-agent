# Evaluation Plan

How to measure if askdocs-rag-agent works well.

---

## Overview

**Goal:** Measure retrieval quality and answer accuracy before going to production.

**Approach:** Create labeled test set → Run evaluation → Measure metrics → Iterate

---

## What We're Measuring

### 1. Retrieval Hit-Rate
**Question:** Does the correct chunk appear in top-k results?

**Metric:** `(# questions where correct chunk in top-k) / (total questions)`

**Target:** >80% @ k=5

**Why it matters:** If retrieval fails, answer will be wrong no matter how good the LLM is.

---

### 2. Answer Groundedness
**Question:** Does the answer only use information from retrieved chunks?

**Metric:** `(# grounded answers) / (total answered questions)`

**Target:** >95%

**Why it matters:** Hallucinations erode trust. "Not found" is better than wrong answer.

---

### 3. Correct Refusals
**Question:** Does it return "not_found" for off-topic questions?

**Metric:** `(# correctly refused) / (total off-topic questions)`

**Target:** 100%

**Why it matters:** Shows the system knows its limits.

---

## Test Dataset Structure

### File: `eval/questions.json`

```json
[
  {
    "id": 1,
    "question": "What is the vacation policy?",
    "category": "answerable",
    "expected_document": "handbook.pdf",
    "expected_page": 7,
    "expected_answer_contains": ["15 days", "paid vacation"]
  },
  {
    "id": 2,
    "question": "What's the weather today?",
    "category": "off_topic",
    "expected_answer": "not_found"
  },
  {
    "id": 3,
    "question": "Leave",
    "category": "ambiguous",
    "expected_answer": "clarify"
  }
]
```

### Categories

1. **answerable** (70% of dataset)
   - Questions that should be answered from docs
   - Include expected doc + page for hit-rate measurement

2. **off_topic** (20% of dataset)
   - Questions unrelated to docs
   - Should all return "not_found"

3. **ambiguous** (10% of dataset)
   - Vague questions
   - Should request clarification

---

## Creating the Test Dataset

### Step 1: Upload Sample Documents

Create or use:
- `samples/handbook.pdf` - Employee handbook (fictional)
- `samples/terms.pdf` - Terms & conditions (fictional)

### Step 2: Generate Questions

**Answerable questions (14-16 questions):**

From handbook:
1. "What is the vacation policy?"
2. "How many sick days do employees get?"
3. "How do I request parental leave?"
4. "What is the remote work policy?"
5. "What benefits are offered?"

From terms:
6. "What is the refund policy?"
7. "How long does shipping take?"
8. "Can I return damaged items?"
9. "What payment methods are accepted?"
10. "What is the return window?"

Edge cases:
11. "What are vacation and sick leave policies?" (multi-topic)
12. "Do new employees get the same benefits?" (requires inference)

**Off-topic questions (4-5 questions):**
1. "What's the weather today?"
2. "Who won the election?"
3. "What's the stock price?"
4. "Write me a Python script"
5. "What's 2+2?"

**Ambiguous questions (2-3 questions):**
1. "Policy" (too vague)
2. "Leave" (which type?)
3. "What about that?" (pronoun without context)

---

## Running Evaluation

### Command

```bash
docker compose exec api python -m eval.run
```

### What It Does

1. Loads `eval/questions.json`
2. For each question:
   - Runs retrieval
   - Generates answer
   - Compares to expected results
3. Generates `eval/report.md`

---

## Evaluation Report Format

### `eval/report.md`

```markdown
# Evaluation Report

**Date:** 2026-07-20
**Questions:** 20
**Configuration:**
- CHUNK_SIZE: 512
- RETRIEVAL_TOP_K: 5
- CONFIDENCE_THRESHOLD: 0.7

## Summary

| Metric | Score |
|---|---|
| Retrieval Hit-Rate @ k=5 | 85% (17/20) |
| Answer Groundedness | 94% (16/17) |
| Correct Refusals | 100% (5/5) |

## Failed Cases

### Question 3: "How do I request parental leave?"
- **Expected:** handbook.pdf, page 23
- **Retrieved:** handbook.pdf, pages [12, 15, 19, 22, 24]
- **Issue:** Correct chunk (page 23) not in top-5
- **Fix:** Increase top_k to 7 OR improve chunking

### Question 12: "What are the benefits?"
- **Expected:** Grounded answer
- **Actual:** Used general knowledge about common benefits
- **Issue:** Hallucination
- **Fix:** Strengthen prompt grounding instructions
```

---

## Iteration Process

### 1. Run Baseline
```bash
python -m eval.run
# Results: 75% hit-rate, 88% groundedness
```

### 2. Identify Issues
- Low hit-rate → Chunking problem? Embedding problem?
- Low groundedness → Prompt problem? Confidence threshold too low?

### 3. Make Changes
Example: Increase chunk size
```bash
# Edit .env
CHUNK_SIZE=768  # was 512

# Re-run
python -m eval.run
# Results: 85% hit-rate ↑, 92% groundedness ↑
```

### 4. Track Progress

| Config | Hit-Rate | Groundedness | Refusals |
|---|---|---|---|
| Baseline (chunk=512, k=5) | 75% | 88% | 100% |
| Larger chunks (768) | 85% | 92% | 100% |
| More results (k=7) | 90% | 91% | 100% |
| **Final** | **90%** | **94%** | **100%** |

---

## Manual Testing Checklist

Before considering "done":

- [ ] Upload a real document
- [ ] Ask 5 questions you know the answer to
- [ ] Ask 2 questions not in the document
- [ ] Check all citations are correct
- [ ] Verify "not_found" for off-topic

---

## Acceptance Criteria

**Minimum to deploy:**
- ✅ Retrieval hit-rate >80%
- ✅ Groundedness >90%
- ✅ Refusals = 100%

**Good quality:**
- ✅ Retrieval hit-rate >85%
- ✅ Groundedness >95%
- ✅ Refusals = 100%

**Excellent quality:**
- ✅ Retrieval hit-rate >90%
- ✅ Groundedness >98%
- ✅ Refusals = 100%

---

## Ongoing Evaluation

### In Production

**Monthly:**
- Run eval suite on new documents
- Check metrics haven't degraded

**When making changes:**
- Run eval before + after
- Ensure no regression

**User feedback:**
- Track thumbs up/down on answers
- Review "not helpful" cases
- Add to eval dataset

---

## Advanced Metrics (Future)

Once basic eval works:

1. **Answer Quality Score** (1-5 scale, human-rated)
2. **Latency** (p50, p95, p99 response times)
3. **Citation Precision** (% of citations that are relevant)
4. **Coverage** (% of document topics that can be answered)

---

## Next Steps

**Before coding:**
1. Create `eval/questions.json` with 20 questions
2. Upload 2 sample documents to `samples/`

**During development:**
3. Implement `eval/run.py` script
4. Run eval after each major change
5. Track results in `eval/report.md`

**This document will be updated** with actual evaluation results after implementation.
