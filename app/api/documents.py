"""Document upload and management endpoints"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os

from app.db.database import get_db
from app.db.models import Document, Chunk
from app.services.pdf_processor import process_pdf
from app.schemas.document import DocumentResponse, DocumentListResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a PDF document

    The document will be:
    1. Validated (must be PDF)
    2. Text extracted page by page
    3. Split into chunks
    4. Embeddings generated for each chunk
    5. Stored in database with vector search enabled

    Returns document metadata including ID and page count.
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # Read file content
    content = await file.read()

    # Process PDF (extract text, chunk, embed)
    try:
        doc_data = await process_pdf(content, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to process PDF: {str(e)}"
        )

    # Create document record
    document = Document(
        filename=file.filename,
        page_count=doc_data["page_count"]
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Create chunk records with embeddings
    for chunk_data in doc_data["chunks"]:
        chunk = Chunk(
            document_id=document.id,
            text=chunk_data["text"],
            page_number=chunk_data["page_number"],
            embedding=chunk_data["embedding"]
        )
        db.add(chunk)

    db.commit()

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        page_count=document.page_count,
        uploaded_at=document.uploaded_at,
        chunk_count=len(doc_data["chunks"])
    )


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all uploaded documents

    Supports pagination with skip/limit parameters.
    """
    documents = db.query(Document).offset(skip).limit(limit).all()
    total = db.query(Document).count()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                page_count=doc.page_count,
                uploaded_at=doc.uploaded_at,
                chunk_count=len(doc.chunks)
            )
            for doc in documents
        ],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific document by ID"""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        page_count=document.page_count,
        uploaded_at=document.uploaded_at,
        chunk_count=len(document.chunks)
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document and all its chunks"""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(document)
    db.commit()

    return None
