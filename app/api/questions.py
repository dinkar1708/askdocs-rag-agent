"""API endpoints for asking questions about documents"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.schemas.query import QuestionRequest, AnswerResponse, SourceCitation
from app.services.retriever import retrieve_relevant_chunks, format_context_for_llm
from app.llm.factory import get_llm_provider
from app.core.config import settings
from app.graph.router import get_query_router, QueryIntent

router = APIRouter(prefix="/ask", tags=["questions"])


@router.post("/", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about uploaded documents with intelligent routing

    Process:
    1. Retrieve relevant document chunks using vector similarity
    2. Route query (answer/clarify/refuse) based on confidence
    3. Generate appropriate response based on intent
    4. Return answer with source citations or clarification/refusal message
    """
    # Step 1: Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(
        query=request.question,
        db=db,
        top_k=request.top_k
    )

    # Step 2: Route the query
    router = get_query_router()
    route_result = router.route(
        question=request.question,
        chunks=chunks
    )

    intent = route_result["intent"]
    confidence = route_result["confidence"]
    reason = route_result["reason"]

    # Step 3: Handle based on intent
    sources = []
    if request.include_sources and chunks:
        for chunk in chunks:
            sources.append(SourceCitation(
                chunk_id=chunk["chunk_id"],
                filename=chunk["filename"],
                page_number=chunk["page_number"],
                similarity_score=chunk["similarity_score"],
                text_excerpt=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            ))

    # REFUSE: Not enough confidence or off-topic
    if intent == QueryIntent.REFUSE:
        return AnswerResponse(
            question=request.question,
            answer="not_found - This question cannot be answered from the uploaded documents.",
            sources=sources,
            timestamp=datetime.utcnow(),
            model_used=settings.LLM_PROVIDER,
            metadata={
                "intent": intent,
                "confidence": confidence,
                "reason": reason
            }
        )

    # CLARIFY: Ambiguous question
    elif intent == QueryIntent.CLARIFY:
        return AnswerResponse(
            question=request.question,
            answer="Could you please provide more context or be more specific? Your question seems ambiguous.",
            sources=sources,
            timestamp=datetime.utcnow(),
            model_used=settings.LLM_PROVIDER,
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

        return AnswerResponse(
            question=request.question,
            answer=answer_text,
            sources=sources,
            timestamp=datetime.utcnow(),
            model_used=settings.LLM_PROVIDER,
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
