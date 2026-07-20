"""API endpoints for asking questions about documents"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.database import get_db
from app.schemas.query import QuestionRequest, AnswerResponse, SourceCitation
from app.services.retriever import retrieve_relevant_chunks, format_context_for_llm
from app.llm.factory import get_llm_provider
from app.core.config import settings

router = APIRouter(prefix="/ask", tags=["questions"])


@router.post("/", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db)
):
    """
    Ask a question about uploaded documents

    Process:
    1. Retrieve relevant document chunks using vector similarity
    2. Format chunks as context
    3. Send to LLM with grounding instructions
    4. Return answer with source citations
    """
    # Step 1: Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(
        query=request.question,
        db=db,
        top_k=request.top_k
    )

    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="No relevant information found. Please upload documents first."
        )

    # Step 2: Format context for LLM
    context = format_context_for_llm(chunks)

    # Step 3: Generate answer using LLM
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

    # Step 4: Build source citations
    sources = []
    if request.include_sources:
        for chunk in chunks:
            sources.append(SourceCitation(
                chunk_id=chunk["chunk_id"],
                filename=chunk["filename"],
                page_number=chunk["page_number"],
                similarity_score=chunk["similarity_score"],
                text_excerpt=chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
            ))

    return AnswerResponse(
        question=request.question,
        answer=answer_text,
        sources=sources,
        timestamp=datetime.utcnow(),
        model_used=settings.LLM_PROVIDER
    )


@router.get("/health")
async def health_check():
    """Check if question answering service is operational"""
    return {
        "status": "healthy",
        "service": "question-answering",
        "llm_provider": settings.LLM_PROVIDER
    }
