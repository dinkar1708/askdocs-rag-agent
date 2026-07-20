# Feature: Evaluation Harness

**What:** Automated testing framework that measures retrieval quality and answer groundedness.

**Why it matters:** Objectively track how well the system performs, find regressions, and optimize configuration.

---

## User Story

```
As a system engineer,
I want to measure retrieval hit-rate and answer groundedness automatically,
So I can optimize chunking, embeddings, and thresholds based on data, not guesswork.
```

---

## What It Measures

### 1. Retrieval Hit-Rate @ k

**Question:** Do the top-k retrieved chunks include the correct answer?

**Formula:**
```
Hit-Rate = (# questions where correct chunk in top-k) / (total questions)
```

**Example:**
```
20 test questions
17 questions: correct chunk in top-5
Hit-rate @ k=5: 17/20 = 85%
```

**What "good" looks like:**
- <70%: Poor (need better chunking or embeddings)
- 70-85%: Acceptable
- >85%: Excellent

---

### 2. Answer Groundedness

**Question:** Does the generated answer only use information from retrieved chunks?

**Formula:**
```
Groundedness = (# answers using only retrieved chunks) / (total answered questions)
```

**Example:**
```
20 questions
17 answered (3 were "not_found")
16 answers grounded (1 hallucinated)
Groundedness: 16/17 = 94%
```

**What "good" looks like:**
- <90%: Concerning (hallucination risk)
- 90-95%: Good
- >95%: Excellent

---

### 3. Correct Refusals

**Question:** Does the system correctly return "not_found" for off-topic questions?

**Formula:**
```
Refusal Accuracy = (# correctly refused) / (total off-topic questions)
```

**Example:**
```
5 off-topic questions ("weather", "stock price", etc.)
5 correctly refused
Refusal accuracy: 5/5 = 100%
```

**What "good" looks like:**
- <80%: Poor (too many hallucinations on off-topic)
- >95%: Good

---

## Test Dataset Format

**File:** `eval/questions.json`

```json
[
  {
    "question": "What is the vacation policy?",
    "expected_document": "handbook.pdf",
    "expected_page": 7,
    "expected_answer_contains": ["15 days", "paid vacation"],
    "category": "answerable"
  },
  {
    "question": "What's the weather today?",
    "expected_answer": "not_found",
    "category": "off_topic"
  },
  {
    "question": "Policy",
    "expected_answer": "clarify",
    "category": "ambiguous"
  }
]
```

---

## Running Evaluation

### Quick Run

```bash
docker compose exec api python -m eval.run
```

**Output:**
```
Running evaluation on 20 test questions...

Retrieval Hit-Rate @ k=5: 85% (17/20)
Answer Groundedness: 94% (16/17)
Correct Refusals: 100% (5/5)

Report saved to: eval/report.md
```

---

### Detailed Report

**File:** `eval/report.md`

```markdown
# Evaluation Report

**Date:** 2026-07-20
**Configuration:**
- CHUNK_SIZE: 512
- CHUNK_OVERLAP: 128
- RETRIEVAL_TOP_K: 5
- CONFIDENCE_THRESHOLD: 0.7

## Summary

| Metric | Score |
|---|---|
| Retrieval Hit-Rate @ k=5 | 85% (17/20) |
| Answer Groundedness | 94% (16/17) |
| Correct Refusals | 100% (5/5) |

## Failed Cases

### Question: "How do I request parental leave?"
- **Expected chunk:** handbook.pdf, page 23
- **Retrieved chunks:** handbook.pdf pages [12, 15, 19, 22, 24]
- **Issue:** Correct chunk (page 23) not in top-5
- **Recommendation:** Increase top_k to 7 or retune chunking

### Question: "What are the benefits?"
- **Expected:** Clarify (too vague)
- **Actual:** Answered (hallucinated generic benefits)
- **Issue:** Classification failed
- **Recommendation:** Improve classify_query logic
```

---

## Tuning Workflow

### 1. Baseline Measurement

```bash
# Current config
CHUNK_SIZE=512
CHUNK_OVERLAP=128
CONFIDENCE_THRESHOLD=0.7

# Run eval
python -m eval.run
# Hit-rate: 85%, Groundedness: 94%
```

---

### 2. Experiment: Increase top_k

```bash
# Edit .env
RETRIEVAL_TOP_K=7  # was 5

# Re-run
python -m eval.run
# Hit-rate: 90% ↑, Groundedness: 93% ↓ (slight decrease due to more noise)
```

---

### 3. Experiment: Adjust Chunk Size

```bash
# Edit .env
CHUNK_SIZE=768  # was 512
CHUNK_OVERLAP=192  # was 128

# Re-run
python -m eval.run
# Hit-rate: 92% ↑ (larger chunks capture more context)
# Groundedness: 95% ↑
```

---

### 4. Experiment: Raise Confidence Threshold

```bash
# Edit .env
CONFIDENCE_THRESHOLD=0.8  # was 0.7

# Re-run
python -m eval.run
# Answer rate: 70% ↓ (more "not_found")
# Groundedness: 98% ↑ (only high-confidence answers)
```

---

### 5. Choose Optimal Config

**Trade-off analysis:**
| Config | Hit-Rate | Groundedness | Answer Rate |
|---|---|---|---|
| Baseline | 85% | 94% | 85% |
| top_k=7 | 90% | 93% | 85% |
| chunk=768 | 92% | 95% | 85% |
| threshold=0.8 | 90% | 98% | 70% |

**Winner:** chunk=768 (best balance of hit-rate and groundedness)

---

## Automated Regression Testing

**CI Pipeline:** Run evaluation on every PR.

`.github/workflows/eval.yml`:
```yaml
name: Evaluation

on: [pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose up -d
      - run: docker compose exec -T api python -m eval.run
      - name: Check metrics
        run: |
          # Fail if hit-rate < 80%
          if [ $HIT_RATE -lt 80 ]; then exit 1; fi
```

---

## Real-World Example: Optimizing for Legal Docs

**Domain:** Law firm contract Q&A

**Initial eval:**
```
Hit-rate: 72% (too low)
Groundedness: 91% (acceptable)
```

**Problem:** Legal language is dense, 512-token chunks too small.

**Experiment 1: Larger chunks**
```bash
CHUNK_SIZE=1024
CHUNK_OVERLAP=256
# Hit-rate: 88% ↑ (better context)
```

**Experiment 2: Specialized embeddings**
```bash
EMBEDDING_MODEL=legal-bert-base  # Fine-tuned on legal corpus
# Hit-rate: 94% ↑↑
```

**Result:** Deployed with chunk=1024 + legal-bert.

---

## Creating Your Test Set

### Step 1: Collect Real Questions

**Sources:**
- User support tickets
- FAQ page
- Slack questions from employees

**Example:**
```
Real question from support ticket:
"I ordered a product but it arrived damaged. Can I get a refund?"
```

---

### Step 2: Label Expected Answers

```json
{
  "question": "Can I get a refund for a damaged product?",
  "expected_document": "terms.pdf",
  "expected_page": 5,
  "expected_answer_contains": ["damaged", "refund", "30 days"],
  "category": "answerable"
}
```

---

### Step 3: Add Edge Cases

**Off-topic:**
```json
{
  "question": "What's the stock price?",
  "expected_answer": "not_found",
  "category": "off_topic"
}
```

**Ambiguous:**
```json
{
  "question": "Policy",
  "expected_answer": "clarify",
  "category": "ambiguous"
}
```

---

### Step 4: Aim for 20-50 Questions

**Coverage:**
- 70% answerable (from different docs/topics)
- 20% off-topic (test refusals)
- 10% ambiguous (test clarifications)

---

## Continuous Monitoring

**Production metrics to track:**

```python
# Log every query
{
  "question": "What is the vacation policy?",
  "retrieval_score": 0.89,
  "answer_status": "answered",
  "groundedness_check": "pass"
}

# Daily aggregation
{
  "date": "2026-07-20",
  "total_queries": 1542,
  "answer_rate": 82%,
  "avg_confidence": 0.84,
  "not_found_rate": 18%
}
```

**Alert triggers:**
- Answer rate drops below 70% (docs need update)
- Groundedness drops below 90% (model drift)
- Not-found rate spikes (new topic users are asking about)

---

## Limitations & Future Plans

**Current limitations:**
- Manual test set curation
- No answer quality scoring (only groundedness)
- No cost tracking (LLM API tokens)

**Future enhancements:**
- [ ] Auto-generate test questions from documents
- [ ] Human-rated answer quality (1-5 scale)
- [ ] Cost per query tracking
- [ ] A/B testing framework (compare configs)

---

## Next Steps

→ [Configuration](../docs/CONFIGURATION.md) - Tune parameters based on eval results
→ [Architecture](../docs/ARCHITECTURE.md) - Understand the RAG pipeline
