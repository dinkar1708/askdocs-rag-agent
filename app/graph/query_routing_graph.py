"""
LangGraph Query Routing State Machine

Implements intelligent query routing with three paths:
1. ANSWER: High confidence, relevant question → generate answer
2. CLARIFY: Ambiguous or vague question → ask for clarification
3. REFUSE: Off-topic or low confidence → refuse to answer

Architecture:
    START
      ↓
   classify_query (LLM-based classification)
      ↓
   ┌──┴──┐
   ↓     ↓     ↓
ANSWER CLARIFY REFUSE
   ↓     ↓     ↓
   └──┬──┘
      ↓
     END
"""

from typing import TypedDict, List, Dict, Literal, Any
from langgraph.graph import StateGraph, END
from app.llm.base import BaseLLMProvider
import logging
import json

logger = logging.getLogger(__name__)


class QueryRoutingState(TypedDict):
    """State passed through the query routing graph"""
    question: str  # User's question
    chunks: List[Dict[str, Any]]  # Retrieved chunks with scores
    intent: str  # Classified intent: answer/clarify/refuse
    confidence: float  # Retrieval confidence score
    reason: str  # Why this intent was chosen
    classification_method: str  # "llm" or "threshold"
    llm_reasoning: str  # LLM's reasoning for classification (if using LLM)


def classify_query_llm(state: QueryRoutingState, llm_provider: BaseLLMProvider) -> QueryRoutingState:
    """
    Classify query intent using LLM (most accurate, but slower)

    Uses the LLM to intelligently determine if a question is:
    - answerable: Clear question that can be answered from documents
    - ambiguous: Vague question needing clarification
    - off_topic: Not related to uploaded documents
    """
    question = state["question"]
    chunks = state["chunks"]

    # Get best retrieval score
    best_score = 0.0
    if chunks:
        best_score = max(
            chunk.get("reranking_score", chunk.get("similarity_score", 0.0))
            for chunk in chunks
        )

    # Prepare context preview for LLM
    context_preview = ""
    if chunks:
        # Show top 2 chunks as context
        for i, chunk in enumerate(chunks[:2]):
            text = chunk.get("text", "")[:150]
            context_preview += f"Chunk {i+1}: {text}...\n"

    # LLM classification prompt
    system_prompt = """You are a query classifier for a document Q&A system.

Your job is to classify user questions into one of three categories:

1. **answerable**: The question is clear, specific, and can be answered from documents about policies, procedures, or facts.
   Examples:
   - "What is the vacation policy?"
   - "How many sick days do employees get?"
   - "What's the return policy for damaged items?"

2. **ambiguous**: The question is too vague, uses pronouns without context, or lacks specificity.
   Examples:
   - "Tell me about it"
   - "What about that?"
   - "How?"
   - "Policy" (single word, no context)

3. **off_topic**: The question is not related to documents/policies, or asks for things outside the system's scope.
   Examples:
   - "What's the weather today?"
   - "Write me a Python script"
   - "What's the latest news?"
   - "Tell me a joke"

IMPORTANT:
- Do NOT refuse legitimate business questions just because they use common words
- "What's the score on the compliance audit?" → answerable (not off-topic)
- "What time does the office open?" → answerable (legitimate policy question)
- "What's the news about the product launch?" → answerable (if documents exist)

Respond with ONLY a JSON object:
{
  "classification": "answerable" | "ambiguous" | "off_topic",
  "reasoning": "brief explanation of why"
}"""

    user_prompt = f"""Question: "{question}"

Retrieved context preview:
{context_preview if context_preview else "(No relevant chunks found)"}

Retrieval confidence score: {best_score:.3f}

Classify this question. Return JSON only."""

    try:
        # Call LLM for classification
        import asyncio

        # Check if generate returns a coroutine
        result = llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # If it's a coroutine, run it in event loop
        if asyncio.iscoroutine(result):
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # We're in an async context but called from sync code
                    # Create a new event loop in a thread pool
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, result)
                        response = future.result(timeout=30)
                else:
                    response = loop.run_until_complete(result)
            except RuntimeError:
                # No event loop, create one
                response = asyncio.run(result)
        else:
            response = result

        # Extract JSON from response
        response_text = response.strip()

        # Try to find JSON in response
        if "{" in response_text:
            json_start = response_text.index("{")
            json_end = response_text.rindex("}") + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
        else:
            # Fallback: couldn't parse, use threshold-based
            logger.warning(f"Could not parse LLM classification response: {response_text}")
            return classify_query_threshold(state)

        classification = result.get("classification", "").lower()
        reasoning = result.get("reasoning", "")

        # Map LLM classification to intent
        if classification == "answerable":
            # Still check confidence threshold
            if best_score >= 0.5:
                intent = "answer"
                reason = f"LLM classified as answerable. {reasoning}"
            elif best_score >= 0.3:
                # Medium confidence - check if ambiguous
                if "ambiguous" in reasoning.lower() or len(question.split()) <= 2:
                    intent = "clarify"
                    reason = f"Medium confidence with potential ambiguity. {reasoning}"
                else:
                    intent = "answer"
                    reason = f"Medium confidence but clear question. {reasoning}"
            else:
                # Low confidence - refuse
                intent = "refuse"
                reason = f"Retrieval confidence too low ({best_score:.3f}). {reasoning}"

        elif classification == "ambiguous":
            intent = "clarify"
            reason = f"LLM classified as ambiguous. {reasoning}"

        elif classification == "off_topic":
            intent = "refuse"
            reason = f"LLM classified as off-topic. {reasoning}"

        else:
            # Unknown classification, fallback to threshold
            logger.warning(f"Unknown LLM classification: {classification}")
            return classify_query_threshold(state)

        state["intent"] = intent
        state["confidence"] = best_score
        state["reason"] = reason
        state["classification_method"] = "llm"
        state["llm_reasoning"] = reasoning

        return state

    except Exception as e:
        # If LLM classification fails, fall back to threshold-based
        logger.error(f"LLM classification error: {e}. Falling back to threshold-based routing.")
        return classify_query_threshold(state)


def classify_query_threshold(state: QueryRoutingState) -> QueryRoutingState:
    """
    Classify query intent using simple threshold-based rules (fast, deterministic)

    Fallback when LLM classification fails or is disabled.
    """
    question = state["question"]
    chunks = state["chunks"]

    # Check for empty question
    if not question or not question.strip():
        state["intent"] = "clarify"
        state["confidence"] = 0.0
        state["reason"] = "Question is empty or contains only whitespace"
        state["classification_method"] = "threshold"
        return state

    # Check if we have chunks
    if not chunks:
        state["intent"] = "refuse"
        state["confidence"] = 0.0
        state["reason"] = "No relevant documents found"
        state["classification_method"] = "threshold"
        return state

    # Get best score
    best_score = max(
        chunk.get("reranking_score", chunk.get("similarity_score", 0.0))
        for chunk in chunks
    )

    # Threshold-based routing
    HIGH_THRESHOLD = 0.5
    LOW_THRESHOLD = 0.3

    # High confidence: answer
    if best_score >= HIGH_THRESHOLD:
        state["intent"] = "answer"
        state["confidence"] = best_score
        state["reason"] = f"High confidence match (score: {best_score:.3f})"
        state["classification_method"] = "threshold"

    # Medium confidence: check for ambiguity
    elif best_score >= LOW_THRESHOLD:
        question_lower = question.lower().strip()

        # Check for ambiguous patterns
        is_ambiguous = (
            len(question_lower.split()) <= 2 or
            any(pattern in question_lower for pattern in [
                "tell me about it", "what about that", "what about the thing",
                "how does it work", "what is it", "where is it"
            ])
        )

        if is_ambiguous:
            state["intent"] = "clarify"
            state["confidence"] = best_score
            state["reason"] = f"Medium confidence ({best_score:.3f}), question appears ambiguous"
            state["classification_method"] = "threshold"
        else:
            state["intent"] = "answer"
            state["confidence"] = best_score
            state["reason"] = f"Medium confidence ({best_score:.3f}), proceeding with answer"
            state["classification_method"] = "threshold"

    # Low confidence: refuse
    else:
        state["intent"] = "refuse"
        state["confidence"] = best_score
        state["reason"] = f"Confidence too low (score: {best_score:.3f}, threshold: {LOW_THRESHOLD})"
        state["classification_method"] = "threshold"

    return state


def build_query_routing_graph(
    llm_provider: BaseLLMProvider = None,
    use_llm_classification: bool = True
) -> StateGraph:
    """
    Build the LangGraph query routing state machine

    Args:
        llm_provider: LLM provider for classification (required if use_llm_classification=True)
        use_llm_classification: Use LLM for classification (True) or threshold-based (False)

    Returns:
        Compiled StateGraph for query routing
    """
    # Create the graph
    workflow = StateGraph(QueryRoutingState)

    # Choose classification method
    if use_llm_classification and llm_provider:
        # Use LLM-based classification (more accurate)
        def classify_node(state):
            return classify_query_llm(state, llm_provider)
    else:
        # Use threshold-based classification (faster, deterministic)
        def classify_node(state):
            return classify_query_threshold(state)

    # Add classification node
    workflow.add_node("classify", classify_node)

    # Set entry point
    workflow.set_entry_point("classify")

    # Add edge from classify to END (classification is the only step)
    workflow.add_edge("classify", END)

    # Compile the graph
    return workflow.compile()


async def route_query(
    question: str,
    chunks: List[Dict[str, Any]],
    llm_provider: BaseLLMProvider = None,
    use_llm_classification: bool = True
) -> Dict[str, Any]:
    """
    Route a query through the LangGraph state machine

    Args:
        question: User's question
        chunks: Retrieved document chunks
        llm_provider: LLM provider for classification
        use_llm_classification: Whether to use LLM classification

    Returns:
        Dict with intent, confidence, reason, and metadata
    """
    # Build the graph
    graph = build_query_routing_graph(llm_provider, use_llm_classification)

    # Initial state
    initial_state: QueryRoutingState = {
        "question": question,
        "chunks": chunks,
        "intent": "",
        "confidence": 0.0,
        "reason": "",
        "classification_method": "",
        "llm_reasoning": ""
    }

    # Run the graph
    final_state = graph.invoke(initial_state)

    # Return routing result
    return {
        "intent": final_state["intent"],
        "confidence": final_state["confidence"],
        "reason": final_state["reason"],
        "classification_method": final_state["classification_method"],
        "llm_reasoning": final_state.get("llm_reasoning", "")
    }
