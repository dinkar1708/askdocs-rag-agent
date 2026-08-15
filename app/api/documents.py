"""Document upload and management endpoints"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Union
import os
import json
import hashlib
import uuid
import tempfile

from app.db.database import get_db
from app.db.models import Document, Chunk, DocumentProcessingJob
from app.services.pdf_processor import process_pdf
from app.services.document_processor_graph import create_document_processing_graph, DocumentProcessingState
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentMetadataUpdate
from app.schemas.job import JobCreateResponse, JobResponse, JobListResponse
from app.core.auth import verify_api_key

# File size limit: 50MB
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(verify_api_key)]
)


def process_document_async(
    job_id: str,
    content: bytes,
    filename: str,
    content_hash: str,
    doc_metadata: dict,
    db_session_factory
):
    """
    Background task to process document asynchronously using LangGraph

    Args:
        job_id: UUID of the processing job
        content: PDF file content
        filename: Original filename
        content_hash: SHA-256 hash of content
        doc_metadata: Custom metadata
        db_session_factory: Factory function to create DB session
    """
    import logging
    logger = logging.getLogger(__name__)

    db = db_session_factory()
    try:
        # Create initial state
        initial_state: DocumentProcessingState = {
            "job_id": job_id,
            "filename": filename,
            "content": content,
            "content_hash": content_hash,
            "doc_metadata": doc_metadata,
            "file_size": len(content),
            "extracted_data": None,
            "chunks": None,
            "document_id": None,
            "error": None,
            "retry_count": 0
        }

        # Create and run the graph
        graph = create_document_processing_graph(db)

        # Execute the graph
        final_state = graph.invoke(initial_state)

        if final_state.get("error"):
            logger.error(f"Job {job_id} failed: {final_state['error']}")
        else:
            logger.info(f"Job {job_id} completed: Document {final_state['document_id']}")

    except Exception as e:
        logger.error(f"Background job {job_id} failed: {str(e)}", exc_info=True)

        # Mark job as failed
        job = db.query(DocumentProcessingJob).filter(
            DocumentProcessingJob.job_id == job_id
        ).first()
        if job:
            job.status = "failed"
            job.error_message = f"Background processing error: {str(e)}"
            db.commit()

    finally:
        db.close()


@router.post("/", response_model=JobCreateResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a PDF document (async processing with LangGraph)

    Returns a job_id immediately. Processing happens in background using LangGraph state machine.
    Use GET /documents/jobs/{job_id} to poll for progress (0-100%).

    Processing stages:
    1. Accept Job (0-10%) - Validate and queue
    2. Extract Text (10-30%) - Extract text and tables from PDF
    3. Chunk Text (30-50%) - Split into semantic chunks
    4. Generate Embeddings (50-80%) - Create 384-dim vectors
    5. Store in Database (80-100%) - Atomic save to PostgreSQL
    6. Complete - Document ready for search

    Args:
        file: PDF file to upload
        metadata: Optional JSON string with custom metadata (department, grade, type, etc.)

    Returns:
        JobCreateResponse with job_id for tracking progress
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

    # Validate file size
    file_size = len(content)
    if file_size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f}MB, got {file_size / 1024 / 1024:.1f}MB"
        )

    # Calculate content hash for duplicate detection
    content_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicate
    existing_doc = db.query(Document).filter(Document.content_hash == content_hash).first()
    if existing_doc:
        raise HTTPException(
            status_code=409,
            detail=f"Document already exists with ID {existing_doc.id}. Upload date: {existing_doc.uploaded_at}"
        )

    # Create job record
    job_id = str(uuid.uuid4())
    job = DocumentProcessingJob(
        job_id=job_id,
        filename=file.filename,
        file_size=file_size,
        content_hash=content_hash,
        status="queued",
        progress=0,
        current_stage="Queued for processing",
        doc_metadata=doc_metadata
    )
    db.add(job)
    db.commit()

    # Schedule background processing with LangGraph
    from app.db.database import SessionLocal
    background_tasks.add_task(
        process_document_async,
        job_id=job_id,
        content=content,
        filename=file.filename,
        content_hash=content_hash,
        doc_metadata=doc_metadata,
        db_session_factory=SessionLocal
    )

    return JobCreateResponse(
        job_id=job_id,
        filename=file.filename,
        status="queued",
        message=f"Document upload initiated. Use GET /documents/jobs/{job_id} to track progress."
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


# ============================================================================
# Job Tracking Endpoints (for async document processing)
# ============================================================================

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the status of a document processing job

    Poll this endpoint to track progress of async document uploads.

    Returns:
        - job_id: Unique job identifier
        - status: queued, extracting, chunking, embedding, storing, complete, failed
        - progress: 0-100%
        - current_stage: Human-readable description of current stage
        - result_document_id: Document ID (only when status=complete)
        - error_message: Error details (only when status=failed)
    """
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return JobResponse(
        job_id=job.job_id,
        filename=job.filename,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage,
        error_message=job.error_message,
        result_document_id=job.result_document_id,
        created_at=job.created_at,
        updated_at=job.updated_at,
        completed_at=job.completed_at
    )


@router.get("/jobs/", response_model=JobListResponse)
def list_jobs(
    status: Optional[str] = Query(None, description="Filter by status (queued, extracting, complete, failed, etc.)"),
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    List all document processing jobs

    Supports pagination and filtering by status.

    Args:
        status: Filter by job status
        skip: Number of jobs to skip (for pagination)
        limit: Maximum number of jobs to return
    """
    # Build query
    query = db.query(DocumentProcessingJob)

    # Apply status filter if provided
    if status:
        query = query.filter(DocumentProcessingJob.status == status)

    # Get total count
    total = query.count()

    # Apply pagination and order by most recent first
    jobs = query.order_by(
        DocumentProcessingJob.created_at.desc()
    ).offset(skip).limit(limit).all()

    return JobListResponse(
        jobs=[
            JobResponse(
                job_id=job.job_id,
                filename=job.filename,
                status=job.status,
                progress=job.progress,
                current_stage=job.current_stage,
                error_message=job.error_message,
                result_document_id=job.result_document_id,
                created_at=job.created_at,
                updated_at=job.updated_at,
                completed_at=job.completed_at
            )
            for job in jobs
        ],
        total=total
    )
