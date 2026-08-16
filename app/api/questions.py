"""API endpoints for asking questions about documents"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.db.models import Session as SessionModel, Message
from app.schemas.query import QuestionRequest, AnswerResponse, SourceCitation
from app.services.retriever import retrieve_relevant_chunks, retrieve_with_reranking, format_context_for_llm
from app.services.hybrid_search import hybrid_search, hybrid_search_with_reranking
from app.llm.factory import get_llm_provider
from app.core.config import settings
# from app.graph.router import get_query_router, QueryIntent
# from app.graph.query_routing_graph import route_query  # TEMPORARILY DISABLED
from app.core.auth import verify_api_key

router = APIRouter(
    prefix="/ask",
    tags=["questions"],
    dependencies=[Depends(verify_api_key)]
)


@router.post("/", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about uploaded documents with intelligent routing

    Process:
    1. Retrieve relevant document chunks using:
       - Hybrid search (BM25 + Vector + RRF) if HYBRID_SEARCH_ENABLED
       - Vector similarity only if hybrid search disabled
       - Optional cross-encoder reranking if RERANKING_ENABLED
    2. Route query (answer/clarify/refuse) based on confidence
    3. Generate appropriate response based on intent
    4. Return answer with source citations or clarification/refusal message
    """
    # Step 1: Retrieve relevant chunks
    if settings.HYBRID_SEARCH_ENABLED:
        # Use hybrid search (BM25 + Vector + RRF)
        if settings.RERANKING_ENABLED:
            # Hybrid + Reranking (3-stage)
            chunks = hybrid_search_with_reranking(
                query=request.question,
                db=db,
                top_k=request.top_k,
                initial_k=settings.RETRIEVAL_INITIAL_K,
                metadata_filters=request.metadata_filters
            )
        else:
            # Hybrid only (2-stage)
            chunks = hybrid_search(
                query=request.question,
                db=db,
                top_k=request.top_k,
                initial_k=settings.RETRIEVAL_INITIAL_K,
                metadata_filters=request.metadata_filters
            )
    else:
        # Traditional vector-only search
        if settings.RERANKING_ENABLED:
            # Vector + Reranking (2-stage)
            chunks = retrieve_with_reranking(
                query=request.question,
                db=db,
                initial_k=settings.RETRIEVAL_INITIAL_K,
                final_k=request.top_k,
                metadata_filters=request.metadata_filters
            )
        else:
            # Vector only (1-stage)
            chunks = retrieve_relevant_chunks(
                query=request.question,
                db=db,
                top_k=request.top_k,
                metadata_filters=request.metadata_filters
            )

    # Step 1.5: Verify session exists (if provided)
    session_id = request.session_id
    if session_id:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

        # Update last accessed time
        session.last_accessed = datetime.utcnow()
        db.commit()

    # Step 2: Route the query using LangGraph
    # TEMPORARILY DISABLED - langgraph dependency issues
    # llm_provider = get_llm_provider() if settings.QUERY_ROUTING_USE_LLM else None
    # route_result = await route_query(
    #     question=request.question,
    #     chunks=chunks,
    #     llm_provider=llm_provider,
    #     use_llm_classification=settings.QUERY_ROUTING_USE_LLM
    # )
    # intent = route_result["intent"]
    # confidence = route_result["confidence"]
    # reason = route_result["reason"]

    # TEMPORARY FIX: Always answer (skip routing)
    intent = "answer"
    confidence = 1.0 if chunks else 0.0
    reason = "Query routing temporarily disabled"

    # Helper function to save messages
    def save_to_session(user_question: str, assistant_answer: str, sources_list: list):
        if session_id:
            # Save user message
            user_msg = Message(
                session_id=session_id,
                role="user",
                content=user_question,
                sources=None
            )
            db.add(user_msg)

            # Save assistant message
            assistant_msg = Message(
                session_id=session_id,
                role="assistant",
                content=assistant_answer,
                sources=[source.dict() for source in sources_list] if sources_list else None
            )
            db.add(assistant_msg)
            db.commit()

    # Step 3: Handle based on intent
    sources = []
    if request.include_sources and chunks:
        for chunk in chunks:
            sources.append(SourceCitation(
                chunk_id=chunk["chunk_id"],
                filename=chunk["filename"],
                page_number=chunk["page_number"],
                similarity_score=chunk["similarity_score"],
                text_excerpt=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"],
                reranking_score=chunk.get("reranking_score"),
                original_similarity=chunk.get("original_similarity")
            ))

    # REFUSE: Not enough confidence or off-topic
    if intent == "refuse":
        answer_text = "not_found - This question cannot be answered from the uploaded documents."
        save_to_session(request.question, answer_text, sources)

        return AnswerResponse(
            question=request.question,
            answer=answer_text,
            sources=sources,
            timestamp=datetime.utcnow(),
            model_used=settings.LLM_PROVIDER,
            session_id=session_id,
            metadata={
                "intent": intent,
                "confidence": confidence,
                "reason": reason
            }
        )

    # CLARIFY: Ambiguous question
    elif intent == "clarify":
        answer_text = "Could you please provide more context or be more specific? Your question seems ambiguous."
        save_to_session(request.question, answer_text, sources)

        return AnswerResponse(
            question=request.question,
            answer=answer_text,
            sources=sources,
            timestamp=datetime.utcnow(),
            model_used=settings.LLM_PROVIDER,
            session_id=session_id,
            metadata={
                "intent": intent,
                "confidence": confidence,
                "reason": reason
            }
        )

    # ANSWER: Generate response from LLM
    else:
        # Format context for LLM
        context = format_context_for_llm(chunks)

        # Generate answer using LLM
        llm_provider = get_llm_provider()

        system_prompt = """You are a helpful assistant that answers questions based on provided documents.

IMPORTANT RULES:
1. ONLY answer using information from the provided context
2. If the answer is not in the context, say "I don't have enough information to answer that"
3. Always cite which document and page number you're using
4. Be concise and direct
5. Do not make up or infer information not present in the context"""

        user_prompt = f"""Context from documents:

{context}

Question: {request.question}

Answer the question using ONLY the information provided above. Include citations like [filename - Page X]."""

        answer_text = await llm_provider.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        # Save to session
        save_to_session(request.question, answer_text, sources)

        return AnswerResponse(
            question=request.question,
            answer=answer_text,
            sources=sources,
            timestamp=datetime.utcnow(),
            model_used=settings.LLM_PROVIDER,
            session_id=session_id,
            metadata={
                "intent": intent,
                "confidence": confidence,
                "reason": reason
            }
        )


@router.get("/health")
async def health_check():
    """Check if question answering service is operational"""
    return {
        "status": "healthy",
        "service": "question-answering",
        "llm_provider": settings.LLM_PROVIDER
    }
