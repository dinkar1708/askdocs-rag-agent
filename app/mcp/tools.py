"""MCP Tool Implementations

Implements search_documents, ask_question, list_documents, and summarize_document
tools exposed via the Model Context Protocol.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import Document, Chunk
from app.services.retriever import retrieve_relevant_chunks, format_context_for_llm
from app.graph.query_routing_graph import route_query
from app.llm.factory import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.services.document_summarizer import get_document_summarizer
from app.schemas.summary import SummaryRequest

logger = logging.getLogger(__name__)


def tool_search_documents(db: Session, query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search for relevant document chunks using vector similarity.

    Args:
        db: Database session
        query: Search query string
        top_k: Number of chunks to retrieve

    Returns:
        Dict with query, count, and chunk details
    """
    chunks = retrieve_relevant_chunks(query=query, db=db, top_k=top_k)

    formatted_chunks = []
    for c in chunks:
        formatted_chunks.append({
            "chunk_id": c.get("chunk_id"),
            "filename": c.get("filename"),
            "page_number": c.get("page_number"),
            "similarity_score": c.get("similarity_score"),
            "text": c.get("text")
        })

    return {
        "query": query,
        "total_results": len(formatted_chunks),
        "chunks": formatted_chunks
    }


async def tool_ask_question(
    db: Session,
    question: str,
    top_k: int = 5,
    llm_provider: Optional[BaseLLMProvider] = None
) -> Dict[str, Any]:
    """
    Ask a grounded question and get an answer with source citations.

    Args:
        db: Database session
        question: User query question
        top_k: Number of sources to retrieve
        llm_provider: Optional LLM provider override

    Returns:
        Dict with answer, sources, and metadata
    """
    provider = llm_provider or get_llm_provider()
    chunks = retrieve_relevant_chunks(query=question, db=db, top_k=top_k)

    if not chunks:
        return {
            "question": question,
            "answer": "NOT_FOUND: No relevant information found in the uploaded documents.",
            "sources": [],
            "confidence": 0.0,
            "intent": "refuse"
        }

    # Route query
    route_result = await route_query(
        question=question,
        chunks=chunks,
        llm_provider=provider,
        use_llm_classification=True
    )
    intent = route_result.get("intent", "answer")
    confidence = route_result.get("confidence", 0.8)

    if intent == "refuse":
        return {
            "question": question,
            "answer": "This question appears to be outside the scope of the available documents.",
            "sources": [],
            "confidence": confidence,
            "intent": "refuse"
        }
    elif intent == "clarify":
        return {
            "question": question,
            "answer": f"Could you please clarify your question? Found related documents but query is ambiguous.",
            "sources": [],
            "confidence": confidence,
            "intent": "clarify"
        }

    # Generate answer with citations
    context = format_context_for_llm(chunks)
    sources = []
    for c in chunks:
        sources.append({
            "filename": c.get("filename"),
            "page": c.get("page_number"),
            "chunk_id": c.get("chunk_id"),
            "similarity_score": c.get("similarity_score")
        })

    if hasattr(provider, "generate_with_context"):
        resp = provider.generate_with_context(question=question, context=context)
        answer = resp.get("answer", "")
    else:
        answer = await provider.generate(
            system_prompt=(
                "You are AskDocs, an expert Q&A system. Answer the question truthfully using ONLY "
                "the provided context. Cite sources with [filename - Page X]."
            ),
            user_prompt=f"Context:\n{context}\n\nQuestion: {question}"
        )

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
        "intent": "answer"
    }


def tool_list_documents(db: Session, limit: int = 20) -> List[Dict[str, Any]]:
    """
    List uploaded documents in AskDocs knowledge base.

    Args:
        db: Database session
        limit: Max documents to list

    Returns:
        List of document summary dictionaries
    """
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).limit(limit).all()
    return [
        {
            "id": doc.id,
            "filename": doc.filename,
            "page_count": doc.page_count,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "metadata": doc.doc_metadata or {}
        }
        for doc in docs
    ]


async def tool_summarize_document(
    db: Session,
    document_id: int,
    summary_type: str = "executive",
    llm_provider: Optional[BaseLLMProvider] = None
) -> Dict[str, Any]:
    """
    Generate an executive summary or breakdown for a document.

    Args:
        db: Database session
        document_id: ID of the document to summarize
        summary_type: Type of summary (executive, detailed, key_points)
        llm_provider: Optional LLM provider override

    Returns:
        Dict with summary, key points, and metadata
    """
    summarizer = get_document_summarizer(llm_provider=llm_provider)
    resp = await summarizer.summarize_document(
        db=db,
        document_id=document_id,
        request=SummaryRequest(summary_type=summary_type)
    )
    return {
        "document_id": resp.document_id,
        "filename": resp.filename,
        "summary": resp.summary,
        "summary_type": resp.summary_type,
        "word_count": resp.word_count,
        "key_points": [kp.model_dump() for kp in resp.key_points],
        "cached": resp.cached
    }
