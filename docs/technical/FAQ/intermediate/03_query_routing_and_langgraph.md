# Intermediate Level: Query Routing & LangGraph State Machine

---

## 1. LangGraph State Machine Code

### Q1: How is the LangGraph query router built in code?
**Answer:**
In [`app/graph/query_routing_graph.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/graph/query_routing_graph.py), AskDocs builds a compiled `StateGraph` for query routing:

```python
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END

class QueryRoutingState(TypedDict):
    question: str
    chunks: List[Dict[str, Any]]
    intent: str               # 'answer' | 'clarify' | 'refuse'
    confidence: float          # Best similarity/rerank score
    reason: str                # Human-readable explanation
    classification_method: str # 'threshold' | 'llm'

def classify_query_threshold(state: QueryRoutingState) -> QueryRoutingState:
    """Classify user question into answer, clarify, or refuse based on confidence"""
    question = state["question"].strip()
    chunks = state["chunks"]

    # 1. Empty question check
    if not question:
        state["intent"] = "clarify"
        state["confidence"] = 0.0
        state["reason"] = "Question is empty"
        return state

    # 2. Missing documents check
    if not chunks:
        state["intent"] = "refuse"
        state["confidence"] = 0.0
        state["reason"] = "No relevant documents found"
        return state

    # 3. Score evaluation
    best_score = max(c.get("reranking_score", c.get("similarity_score", 0.0)) for c in chunks)
    
    if best_score >= 0.5:
        state["intent"] = "answer"
        state["reason"] = f"High confidence match ({best_score:.3f})"
    elif best_score >= 0.3:
        # Check for ambiguous pronouns or short 1-word inputs
        if len(question.split()) <= 2 or "that" in question.lower():
            state["intent"] = "clarify"
            state["reason"] = f"Ambiguous question with medium confidence ({best_score:.3f})"
        else:
            state["intent"] = "answer"
            state["reason"] = f"Clear question with medium confidence ({best_score:.3f})"
    else:
        state["intent"] = "refuse"
        state["reason"] = f"Confidence too low ({best_score:.3f} < 0.3)"

    state["confidence"] = best_score
    state["classification_method"] = "threshold"
    return state

def build_query_routing_graph() -> StateGraph:
    """Construct and compile the LangGraph workflow"""
    workflow = StateGraph(QueryRoutingState)
    workflow.add_node("classify", classify_query_threshold)
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", END)
    return workflow.compile()
```

---

## 2. Invoking the Graph in FastAPI Endpoint

### Q2: How does the `/ask` route invoke the compiled LangGraph?
**Answer:**
```python
@router.post("/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest, db: Session = Depends(get_db)):
    # 1. Retrieve candidates
    chunks = retrieve_with_reranking(request.question, db, top_k=request.top_k)
    
    # 2. Invoke LangGraph Router
    graph = build_query_routing_graph()
    initial_state = {
        "question": request.question,
        "chunks": chunks,
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": ""
    }
    result = graph.invoke(initial_state)
    
    # 3. Branch execution based on state intent
    if result["intent"] == "refuse":
        return AnswerResponse(answer="not_found - Cannot answer from documents.", sources=[])
    elif result["intent"] == "clarify":
        return AnswerResponse(answer="Could you please provide more context or be more specific?", sources=[])
    else:
        # Generate grounded answer using LLM
        answer = generate_grounded_answer(request.question, chunks)
        return AnswerResponse(answer=answer, sources=format_sources(chunks))
```
