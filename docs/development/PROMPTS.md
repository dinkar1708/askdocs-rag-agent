# Prompt Engineering Guide

LLM prompt templates and strategies for askdocs-rag-agent.

---

## Overview

This document defines the prompts used to generate grounded answers from retrieved chunks.

**Core Principle:** Answers must be grounded in retrieved context only. No general knowledge.

---

## Main Answer Prompt

### Template

```
You are a helpful assistant that answers questions based ONLY on the provided context.

Context (from documents):
{retrieved_chunks}

Question: {user_question}

Instructions:
1. Answer using ONLY the context above
2. If the context doesn't contain the answer, respond with "not_found"
3. Do not use your general knowledge
4. Include citations: [document_name, page_number]

Answer:
```

### Variables

- `{retrieved_chunks}` - Top-k chunks from vector search, formatted as:
  ```
  [Document: handbook.pdf, Page: 7]
  "Employees receive 15 days of paid vacation per year..."

  [Document: handbook.pdf, Page: 8]
  "Unused vacation can be carried over up to 5 days..."
  ```

- `{user_question}` - User's original question

### Expected Output Format

**Success:**
```
Employees receive 15 days of paid vacation per year. Unused days can be
carried over up to 5 days.

Citations: [handbook.pdf, page 7], [handbook.pdf, page 8]
```

**Not Found:**
```
not_found
```

---

## Query Classification Prompt (LangGraph Router)

### Template

```
Classify the following question into one of these categories:

Categories:
- "answerable": Question can be answered from policy/handbook documents
- "ambiguous": Question is too vague or uses pronouns without context
- "off_topic": Question is not related to documents (weather, news, general knowledge)

Question: {user_question}

Classification:
```

### Examples

**answerable:**
- "What is the vacation policy?"
- "How do I request parental leave?"
- "What is the refund policy for damaged items?"

**ambiguous:**
- "What about that?" (pronoun without context)
- "Policy" (too vague)
- "Leave" (which type?)

**off_topic:**
- "What's the weather today?"
- "Who won the election?"
- "Write me a Python script"

---

## Clarification Prompt

When query is ambiguous, ask for clarification.

### Template

```
The question "{user_question}" is unclear or ambiguous.

Possible topics in the documents:
- Vacation policy
- Sick leave policy
- Parental leave policy
- Benefits overview

Please rephrase your question to be more specific. For example:
"What is the vacation policy?"
```

---

## Multi-turn Chat Context

For follow-up questions, include conversation history.

### Template

```
You are a helpful assistant answering questions based on documents.

Conversation history:
{chat_history}

Current context (from documents):
{retrieved_chunks}

Current question: {user_question}

Instructions:
1. Use conversation history to understand pronouns (e.g., "it", "that")
2. Answer using ONLY the provided context
3. If context doesn't contain answer, respond with "not_found"
4. Include citations

Answer:
```

### Chat History Format

```
User: What is the vacation policy?
Assistant: Employees receive 15 days of paid vacation per year.

User: Can I carry over unused days?
Assistant: Yes, up to 5 days can be carried over.

User: What about sick leave?
[Current question - to be answered]
```

---

## Citation Extraction Prompt

Extract citations from generated answer.

### Template

```
Given this answer and source chunks, extract the citations.

Answer: {generated_answer}

Source chunks:
{chunks_with_metadata}

Output format (JSON):
[
  {"document": "filename.pdf", "page": 7},
  {"document": "filename.pdf", "page": 8}
]

Citations:
```

---

## Prompt Tuning Guidelines

### For Better Grounding

✅ **DO:**
- Emphasize "ONLY use provided context"
- Request explicit "not_found" when uncertain
- Repeat instructions (works better for some models)

❌ **DON'T:**
- Allow "based on general knowledge"
- Accept vague "I don't have enough information" (be explicit: "not_found")

### For Better Citations

✅ **DO:**
- Include document name + page in context chunks
- Request structured citation format
- Validate citations match source chunks

❌ **DON'T:**
- Rely on model to "remember" source
- Accept citations without page numbers

### For Better Multi-turn

✅ **DO:**
- Include last 5-10 conversation turns
- Explicitly mention "use history to resolve pronouns"
- Keep history concise (summarize old turns if needed)

❌ **DON'T:**
- Include entire conversation (token limit)
- Expect model to infer from 1-2 turns

---

## Model-Specific Adjustments

### Gemini
- Works well with structured instructions
- Good at following "ONLY use context" directive
- Recommended temperature: 0.1-0.3 (low for factual answers)

### GPT-4 / Azure OpenAI
- Excellent at citation extraction
- May try to use general knowledge if not strongly prompted
- Recommended temperature: 0.0 (deterministic)

### Ollama (Local Models)
- May need simpler prompts
- Repeat instructions 2-3 times
- Test with llama2, mistral, or gemma

---

## Confidence Scoring

No explicit prompt needed - use retrieval similarity scores:

- **High confidence (>0.8):** Answer directly
- **Medium confidence (0.7-0.8):** Answer with caveat
- **Low confidence (<0.7):** Return "not_found"

---

## Testing Prompts

### Test Cases

Create `eval/questions.json` with these categories:

1. **Direct questions** (should answer)
   - "What is the vacation policy?"

2. **Multi-hop questions** (should answer if chunks contain info)
   - "How many vacation days do new employees get?"

3. **Off-topic questions** (should return "not_found")
   - "What's the weather?"

4. **Ambiguous questions** (should clarify)
   - "Leave policy" (which type?)

5. **Trick questions** (should return "not_found")
   - "What is the salary range?" (if not in docs)

---

## Prompt Versioning

Track prompt changes for reproducibility:

```
# prompts/v1_answer.txt
Original prompt (July 2026)

# prompts/v2_answer.txt
Improved grounding (August 2026)
- Added "Do not use general knowledge"
- Stronger emphasis on "ONLY"
```

---

## Evaluation Metrics

### Groundedness
- **Metric:** % of answers using only retrieved context
- **Target:** >95%
- **How to measure:** Human review of 20+ answers

### Citation Accuracy
- **Metric:** % of citations matching actual sources
- **Target:** 100%
- **How to measure:** Automated check against chunk metadata

### Refusal Rate
- **Metric:** % of off-topic questions refused
- **Target:** >95%
- **How to measure:** Test with known off-topic questions

---

## Next Steps

**During Implementation:**
1. Start with templates above
2. Test with real documents
3. Iterate based on answer quality
4. Track prompt versions

**This document will be updated** with actual prompt performance metrics after testing.
