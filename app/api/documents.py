"""Document upload and management endpoints"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import json

from app.db.database import get_db
from app.db.models import Document, Chunk
from app.services.pdf_processor import process_pdf
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentMetadataUpdate

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
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

    # Parse metadata if provided
    doc_metadata = {}
    if metadata:
        try:
            doc_metadata = json.loads(metadata)
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid metadata JSON format"
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
        page_count=doc_data["page_count"],
        doc_metadata=doc_metadata
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
            embedding=chunk_data["embedding"],
            chunk_type=chunk_data.get("chunk_type", "text"),
            chunk_metadata=chunk_data.get("metadata", {})
        )
        db.add(chunk)

    db.commit()

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        page_count=document.page_count,
        uploaded_at=document.uploaded_at,
        chunk_count=len(doc_data["chunks"]),
        doc_metadata=document.doc_metadata
    )


@router.get("/", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 10,
    metadata_filters: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all uploaded documents

    Supports pagination with skip/limit parameters and optional metadata filtering.

    Args:
        skip: Number of documents to skip (for pagination)
        limit: Maximum number of documents to return
        metadata_filters: JSON string of metadata filters (e.g., '{"department": "HR", "grade": "9-12"}')

    Example:
        GET /documents?metadata_filters={"department":"HR"}
    """
    # Build base query
    query = db.query(Document)

    # Apply metadata filters if provided
    if metadata_filters:
        try:
            filters = json.loads(metadata_filters)
            from sqlalchemy import func, text as sql_text
            for key, value in filters.items():
                if isinstance(value, list):
                    # For array values, check if any element matches
                    conditions = []
                    for v in value:
                        conditions.append(
                            func.json_extract_path_text(Document.doc_metadata, key) == str(v)
                        )
                    from sqlalchemy import or_
                    query = query.filter(or_(*conditions))
                else:
                    # For scalar values, do equality check
                    query = query.filter(
                        func.json_extract_path_text(Document.doc_metadata, key) == str(value)
                    )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400,
                detail="Invalid metadata_filters JSON format"
            )

    # Get total count before pagination
    total = query.count()

    # Apply pagination
    documents = query.offset(skip).limit(limit).all()

    return DocumentListResponse(
        documents=[
            DocumentResponse(
                id=doc.id,
                filename=doc.filename,
                page_count=doc.page_count,
                uploaded_at=doc.uploaded_at,
                chunk_count=len(doc.chunks),
                doc_metadata=doc.doc_metadata
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
        chunk_count=len(document.chunks),
        doc_metadata=document.doc_metadata
    )


@router.patch("/{document_id}", response_model=DocumentResponse)
def update_document_metadata(
    document_id: int,
    metadata_update: DocumentMetadataUpdate,
    db: Session = Depends(get_db)
):
    """Update document metadata

    Merges provided metadata fields with existing metadata.
    """
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Merge new metadata with existing
    updated_metadata = {**document.doc_metadata, **metadata_update.doc_metadata}
    document.doc_metadata = updated_metadata

    db.commit()
    db.refresh(document)

    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        page_count=document.page_count,
        uploaded_at=document.uploaded_at,
        chunk_count=len(document.chunks),
        doc_metadata=document.doc_metadata
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
