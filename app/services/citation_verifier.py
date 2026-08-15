"""LangGraph-based Citation Verification

This module implements a multi-step verification workflow to validate that
LLM-generated citations actually exist in retrieved chunks and semantically
support the claims made in answers.

Prevents "citation hallucination" where the model cites sources that don't
support the answer or don't exist in the context.
"""

from typing import TypedDict, List, Dict, Literal, Any
from langgraph.graph import StateGraph, END
import logging
import re

logger = logging.getLogger(__name__)


class CitationVerificationState(TypedDict):
    """State passed through the citation verification graph"""
    question: str
    context_chunks: List[Dict[str, Any]]  # Retrieved chunks with metadata
    generated_answer: str
    claimed_citations: List[Dict[str, Any]]  # Citations extracted from answer
    verified_citations: List[Dict[str, Any]]  # Citations that passed verification
    flagged_citations: List[Dict[str, Any]]  # Suspicious or hallucinated citations
    verification_status: str  # "verified", "partially_verified", "failed"


def extract_claimed_citations(state: CitationVerificationState) -> CitationVerificationState:
    """
    Extract citation claims from the generated answer

    Looks for patterns like:
    - [doc.pdf, p.5]
    - (source: handbook.pdf, page 23)
    - handbook.pdf, page 7
    """
    answer = state["generated_answer"]

    # Pattern to match various citation formats
    patterns = [
        r'\[([^,]+),\s*(?:p\.?|page)\s*(\d+)\]',  # [doc.pdf, p.5]
        r'\(source:\s*([^,]+),\s*(?:page|p\.?)\s*(\d+)\)',  # (source: doc.pdf, page 5)
        r'([a-zA-Z0-9_\-\.]+\.pdf),\s*(?:page|p\.?)\s*(\d+)',  # doc.pdf, page 5
    ]

    claimed_citations = []

    for pattern in patterns:
        matches = re.findall(pattern, answer, re.IGNORECASE)
        for match in matches:
            claimed_citations.append({
                "document": match[0].strip(),
                "page": int(match[1]),
                "found_in_context": False,  # Will be verified in next step
                "semantically_supports": None  # Will be verified later
            })

    state["claimed_citations"] = claimed_citations
    logger.info(f"Extracted {len(claimed_citations)} claimed citations from answer")

    return state


def verify_citation_existence(state: CitationVerificationState) -> CitationVerificationState:
    """
    Verify that claimed citations actually exist in the retrieved context

    Checks if the cited document and page number appear in the context chunks.
    """
    claimed_citations = state["claimed_citations"]
    context_chunks = state["context_chunks"]

    for citation in claimed_citations:
        # Check if this citation exists in the retrieved chunks
        for chunk in context_chunks:
            # Extract filename from chunk metadata
            chunk_filename = chunk.get("filename", "")
            chunk_page = chunk.get("page_number", 0)

            if (citation["document"] in chunk_filename or chunk_filename in citation["document"]) and \
               citation["page"] == chunk_page:
                citation["found_in_context"] = True
                citation["chunk_id"] = chunk.get("chunk_id")
                citation["chunk_text"] = chunk.get("text", "")
                break

    # Separate verified from flagged
    verified = [c for c in claimed_citations if c["found_in_context"]]
    flagged = [c for c in claimed_citations if not c["found_in_context"]]

    logger.info(f"Citation existence check: {len(verified)} found, {len(flagged)} not found")

    state["verified_citations"] = verified
    state["flagged_citations"] = flagged

    return state


def semantic_verification(state: CitationVerificationState, llm_provider) -> CitationVerificationState:
    """
    Verify that cited chunks semantically support the claims in the answer

    Uses LLM to check if the cited text actually supports the claim.
    """
    verified_citations = state["verified_citations"]
    answer = state["generated_answer"]

    # For each verified citation, check semantic support
    for citation in verified_citations:
        chunk_text = citation.get("chunk_text", "")

        if not chunk_text:
            citation["semantically_supports"] = False
            continue

        # Build verification prompt
        prompt = f"""
You are a fact-checker. Determine if the cited text supports the claim in the answer.

ANSWER CLAIM: {answer}

CITED TEXT FROM [{citation['document']}, page {citation['page']}]:
{chunk_text}

Does the cited text support the claim in the answer?
Respond with ONLY "YES" or "NO".
"""

        try:
            # Use LLM to verify semantic support
            response = llm_provider.complete(prompt).strip().upper()

            if "YES" in response:
                citation["semantically_supports"] = True
            else:
                citation["semantically_supports"] = False
                # Move to flagged if it doesn't support the claim
                state["flagged_citations"].append({
                    **citation,
                    "reason": "Citation exists but doesn't semantically support the claim"
                })
        except Exception as e:
            logger.error(f"Semantic verification failed: {e}")
            citation["semantically_supports"] = None  # Unknown

    # Update verified citations (only those that passed semantic check)
    state["verified_citations"] = [
        c for c in verified_citations
        if c.get("semantically_supports") is True
    ]

    logger.info(f"Semantic verification: {len(state['verified_citations'])} support claims")

    return state


def determine_verification_status(state: CitationVerificationState) -> CitationVerificationState:
    """
    Determine overall verification status based on results
    """
    verified_count = len(state["verified_citations"])
    flagged_count = len(state["flagged_citations"])
    total_count = verified_count + flagged_count

    if total_count == 0:
        # No citations claimed (valid for some answers)
        state["verification_status"] = "no_citations"
    elif flagged_count == 0:
        # All citations verified
        state["verification_status"] = "verified"
    elif verified_count == 0:
        # All citations flagged
        state["verification_status"] = "failed"
    else:
        # Some verified, some flagged
        state["verification_status"] = "partially_verified"

    logger.info(f"Final verification status: {state['verification_status']}")

    return state


def create_citation_verification_graph(llm_provider) -> StateGraph:
    """
    Create the LangGraph state machine for citation verification

    Graph structure:
        extract_claimed_citations
            ↓
        verify_citation_existence
            ↓
        semantic_verification
            ↓
        determine_verification_status
            ↓
        END

    Args:
        llm_provider: LLM provider instance for semantic verification

    Returns:
        Compiled StateGraph
    """
    # Create graph
    workflow = StateGraph(CitationVerificationState)

    # Add nodes
    workflow.add_node("extract_claimed_citations", extract_claimed_citations)
    workflow.add_node("verify_citation_existence", verify_citation_existence)
    workflow.add_node("semantic_verification", lambda state: semantic_verification(state, llm_provider))
    workflow.add_node("determine_verification_status", determine_verification_status)

    # Set entry point
    workflow.set_entry_point("extract_claimed_citations")

    # Add edges (linear flow)
    workflow.add_edge("extract_claimed_citations", "verify_citation_existence")
    workflow.add_edge("verify_citation_existence", "semantic_verification")
    workflow.add_edge("semantic_verification", "determine_verification_status")
    workflow.add_edge("determine_verification_status", END)

    return workflow.compile()


def verify_citations(
    question: str,
    answer: str,
    context_chunks: List[Dict[str, Any]],
    llm_provider
) -> Dict[str, Any]:
    """
    Verify citations in a generated answer

    Args:
        question: Original question
        answer: Generated answer with citations
        context_chunks: Retrieved chunks used to generate answer
        llm_provider: LLM provider for semantic verification

    Returns:
        Dictionary with verification results:
        - verified_citations: List of verified citations
        - flagged_citations: List of suspicious/hallucinated citations
        - verification_status: Overall status
    """
    # Create initial state
    initial_state: CitationVerificationState = {
        "question": question,
        "context_chunks": context_chunks,
        "generated_answer": answer,
        "claimed_citations": [],
        "verified_citations": [],
        "flagged_citations": [],
        "verification_status": "unknown"
    }

    # Create and run the graph
    graph = create_citation_verification_graph(llm_provider)
    final_state = graph.invoke(initial_state)

    return {
        "verified_citations": final_state["verified_citations"],
        "flagged_citations": final_state["flagged_citations"],
        "verification_status": final_state["verification_status"],
        "total_claimed": len(final_state["claimed_citations"])
    }
