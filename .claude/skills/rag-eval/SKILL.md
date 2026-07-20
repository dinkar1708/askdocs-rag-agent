---
description: "Evaluate RAG system quality (retrieval, grounding, citations)"
---

# RAG Evaluation Skill

Test and evaluate the quality of the RAG system's retrieval, answer generation, and citation accuracy.

## Steps

1. **Check prerequisites**:
   - Server running on port 8000
   - Documents uploaded to the system
   - Sample questions available

2. **Test retrieval quality**:
   ```bash
   # Check if relevant chunks are being retrieved
   curl -X POST http://localhost:8000/ask \
     -H "Content-Type: application/json" \
     -d '{"question": "test question", "include_sources": true, "top_k": 5}'
   ```
   - Verify top-k chunks are relevant
   - Check similarity scores are reasonable (>0.7 is good)
   - Confirm chunks contain answer-related content

3. **Test router intent classification**:
   - **ANSWER**: Ask factual questions about uploaded docs
   - **CLARIFY**: Ask ambiguous/vague questions
   - **REFUSE**: Ask off-topic questions unrelated to docs

   Check that `metadata.intent` matches expected behavior

4. **Test grounding (no hallucination)**:
   - Ask questions NOT answerable from documents
   - Verify system returns "not_found" instead of making up answers
   - Check confidence scores and refusal reasoning

5. **Test citation accuracy**:
   - For each answer, verify citations point to actual content
   - Check page numbers are correct
   - Confirm quoted text matches source documents
   - Validate chunk_ids exist in database

6. **Test multi-turn conversations**:
   - Create a session
   - Ask follow-up questions
   - Verify context is maintained
   - Check session history is tracked

7. **Performance metrics**:
   - Measure response time (should be <3s for most queries)
   - Check token usage for LLM calls
   - Monitor database query count

## Evaluation Criteria

### Retrieval Quality
- ✅ Top-k chunks contain answer
- ✅ Similarity scores >0.7 for good matches
- ✅ Diverse chunks (not all from same page)
- ❌ Irrelevant chunks in top results

### Answer Quality
- ✅ Grounded in retrieved chunks only
- ✅ Accurate citations with page numbers
- ✅ Concise and relevant
- ✅ Returns "not_found" when appropriate
- ❌ Hallucinated information
- ❌ Made-up citations

### Router Accuracy
- ✅ ANSWER: High confidence factual questions
- ✅ CLARIFY: Ambiguous or vague questions
- ✅ REFUSE: Off-topic or low confidence
- ❌ False positives (refusing good questions)
- ❌ False negatives (answering bad questions)

## Sample Test Questions

**Should ANSWER** (factual, in docs):
```json
{"question": "What is the refund policy?"}
{"question": "How do I reset my password?"}
{"question": "What are the system requirements?"}
```

**Should CLARIFY** (ambiguous):
```json
{"question": "How does it work?"}
{"question": "Tell me about that thing"}
{"question": "What about the other one?"}
```

**Should REFUSE** (off-topic):
```json
{"question": "What's the weather today?"}
{"question": "Who won the Super Bowl?"}
{"question": "Write me a poem"}
```

## Automated Evaluation

Check if `eval/` directory exists with evaluation scripts:
```bash
python -m eval.run
```

This should generate metrics on:
- Retrieval precision/recall
- Answer accuracy
- Citation correctness
- Response times

## Best Practices

- ✅ Test with real user questions
- ✅ Verify both positive and negative cases
- ✅ Check edge cases (very long questions, special characters)
- ✅ Measure against baseline metrics
- ✅ Document any regressions
- ❌ Don't only test happy path
- ❌ Don't assume retrieval is working without checking
