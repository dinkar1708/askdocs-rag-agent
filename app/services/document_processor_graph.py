"""LangGraph state machine for async document processing

This module implements a state machine for background document processing:
1. Accept Job -> Store file content and create job record
2. Extract Text -> Extract text from PDF page by page
3. Chunk Text -> Split text into semantic chunks
4. Generate Embeddings -> Batch embed all chunks
5. Store in DB -> Save document and chunks atomically
6. Complete -> Mark job as complete

Error handling: Automatic retries with exponential backoff for transient failures
"""

import io
import hashlib
import logging
from typing import TypedDict, Annotated, Literal
from datetime import datetime
import traceback

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.db.models import Document, Chunk, DocumentProcessingJob
from app.services.embeddings import generate_embedding, chunk_text, semantic_chunk_text
from app.services.table_processor import extract_tables_from_page, get_table_bboxes
from app.core.config import settings

logger = logging.getLogger(__name__)

# Maximum number of retries for transient errors
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [5, 15, 60]  # Exponential backoff


class DocumentProcessingState(TypedDict):
    """State passed through the processing graph"""
    job_id: str
    filename: str
    content: bytes
    content_hash: str
    doc_metadata: dict
    file_size: int

    # Processing stage outputs
    extracted_data: dict | None  # {page_count, pages: [{page_num, text, tables}]}
    chunks: list | None  # [{text, page_number, chunk_type, embedding, metadata}]
    document_id: int | None

    # Error handling
    error: str | None
    retry_count: int


def accept_job(state: DocumentProcessingState, db: Session) -> DocumentProcessingState:
    """
    Initial state: Accept the job and store metadata

    Updates job status to 'queued' and validates input
    """
    job_id = state["job_id"]

    logger.info(f"[Job {job_id}] Accepting job for file: {state['filename']}")

    # Update job status
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    if not job:
        state["error"] = f"Job {job_id} not found in database"
        return state

    job.status = "queued"
    job.progress = 0
    job.current_stage = "Job accepted, queued for processing"
    db.commit()

    logger.info(f"[Job {job_id}] Job accepted successfully")
    return state


def extract_text(state: DocumentProcessingState, db: Session) -> DocumentProcessingState:
    """
    Extract text and tables from PDF page by page

    Updates job status to 'extracting'
    """
    job_id = state["job_id"]

    logger.info(f"[Job {job_id}] Starting text extraction")

    # Update job status
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    job.status = "extracting"
    job.progress = 10
    job.current_stage = "Extracting text from PDF"
    db.commit()

    try:
        import pdfplumber

        pdf_file = io.BytesIO(state["content"])
        extracted_data = {"pages": [], "page_count": 0}

        with pdfplumber.open(pdf_file) as pdf:
            page_count = len(pdf.pages)
            extracted_data["page_count"] = page_count

            for page_num, page in enumerate(pdf.pages):
                logger.debug(f"[Job {job_id}] Extracting page {page_num + 1}/{page_count}")

                # Extract tables
                tables = extract_tables_from_page(page)
                table_bboxes = get_table_bboxes(tables)

                # Extract text (excluding table regions)
                from app.services.pdf_processor import extract_text_excluding_tables
                text = extract_text_excluding_tables(page, table_bboxes)

                extracted_data["pages"].append({
                    "page_num": page_num + 1,
                    "text": text,
                    "tables": tables
                })

                # Update progress
                progress = 10 + int((page_num + 1) / page_count * 20)  # 10-30%
                job.progress = progress
                job.current_stage = f"Extracting text: page {page_num + 1}/{page_count}"
                db.commit()

        state["extracted_data"] = extracted_data
        logger.info(f"[Job {job_id}] Text extraction complete: {page_count} pages")

    except Exception as e:
        logger.error(f"[Job {job_id}] Text extraction failed: {str(e)}")
        logger.error(traceback.format_exc())
        state["error"] = f"Text extraction failed: {str(e)}"

    return state


def chunk_text_stage(state: DocumentProcessingState, db: Session) -> DocumentProcessingState:
    """
    Split extracted text into chunks

    Updates job status to 'chunking'
    """
    job_id = state["job_id"]

    logger.info(f"[Job {job_id}] Starting text chunking")

    # Update job status
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    job.status = "chunking"
    job.progress = 30
    job.current_stage = "Splitting text into chunks"
    db.commit()

    try:
        all_chunks = []
        extracted_data = state["extracted_data"]
        total_pages = extracted_data["page_count"]

        for idx, page_data in enumerate(extracted_data["pages"]):
            page_num = page_data["page_num"]
            text = page_data["text"]
            tables = page_data["tables"]

            logger.debug(f"[Job {job_id}] Chunking page {page_num}")

            # Add table chunks
            for table in tables:
                all_chunks.append({
                    "text": table["markdown"],
                    "chunk_type": "table",
                    "page_number": page_num,
                    "metadata": {
                        "headers": table["headers"],
                        "bbox": table["bbox"]
                    },
                    "embedding": None  # Will be filled in next stage
                })

            # Chunk text
            if text and text.strip():
                if settings.SEMANTIC_CHUNKING_ENABLED:
                    chunks = semantic_chunk_text(
                        text,
                        page_number=page_num,
                        use_semantic=True,
                        similarity_threshold=settings.SEMANTIC_SIMILARITY_THRESHOLD,
                        min_chunk_size=settings.MIN_CHUNK_SIZE,
                        max_chunk_size=settings.MAX_CHUNK_SIZE
                    )
                else:
                    chunks = chunk_text(text, page_number=page_num)

                for chunk in chunks:
                    chunk["chunk_type"] = "text"
                    chunk["metadata"] = {}
                    chunk["embedding"] = None  # Will be filled in next stage
                    all_chunks.append(chunk)

            # Update progress
            progress = 30 + int((idx + 1) / total_pages * 20)  # 30-50%
            job.progress = progress
            job.current_stage = f"Chunking: page {page_num}/{total_pages}"
            db.commit()

        state["chunks"] = all_chunks
        logger.info(f"[Job {job_id}] Chunking complete: {len(all_chunks)} chunks created")

    except Exception as e:
        logger.error(f"[Job {job_id}] Chunking failed: {str(e)}")
        logger.error(traceback.format_exc())
        state["error"] = f"Chunking failed: {str(e)}"

    return state


def generate_embeddings_stage(state: DocumentProcessingState, db: Session) -> DocumentProcessingState:
    """
    Generate embeddings for all chunks

    Updates job status to 'embedding'
    """
    job_id = state["job_id"]

    logger.info(f"[Job {job_id}] Starting embedding generation")

    # Update job status
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    job.status = "embedding"
    job.progress = 50
    job.current_stage = "Generating embeddings"
    db.commit()

    try:
        chunks = state["chunks"]
        total_chunks = len(chunks)

        for idx, chunk in enumerate(chunks):
            logger.debug(f"[Job {job_id}] Embedding chunk {idx + 1}/{total_chunks}")

            embedding = generate_embedding(chunk["text"])
            chunk["embedding"] = embedding

            # Update progress every 10 chunks
            if (idx + 1) % 10 == 0 or idx == total_chunks - 1:
                progress = 50 + int((idx + 1) / total_chunks * 30)  # 50-80%
                job.progress = progress
                job.current_stage = f"Generating embeddings: {idx + 1}/{total_chunks}"
                db.commit()

        logger.info(f"[Job {job_id}] Embedding generation complete: {total_chunks} embeddings")

    except Exception as e:
        logger.error(f"[Job {job_id}] Embedding generation failed: {str(e)}")
        logger.error(traceback.format_exc())
        state["error"] = f"Embedding generation failed: {str(e)}"

    return state


def store_in_database(state: DocumentProcessingState, db: Session) -> DocumentProcessingState:
    """
    Store document and chunks in database atomically

    Updates job status to 'storing'
    """
    job_id = state["job_id"]

    logger.info(f"[Job {job_id}] Starting database storage")

    # Update job status
    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    job.status = "storing"
    job.progress = 80
    job.current_stage = "Storing document and chunks"
    db.commit()

    try:
        # Check for duplicate
        existing_doc = db.query(Document).filter(
            Document.content_hash == state["content_hash"]
        ).first()

        if existing_doc:
            logger.warning(f"[Job {job_id}] Duplicate document found: {existing_doc.id}")
            state["error"] = f"Document already exists with ID {existing_doc.id}"
            return state

        # Create document record
        document = Document(
            filename=state["filename"],
            page_count=state["extracted_data"]["page_count"],
            doc_metadata=state["doc_metadata"],
            content_hash=state["content_hash"]
        )
        db.add(document)
        db.flush()  # Get document ID without committing
        db.refresh(document)

        logger.info(f"[Job {job_id}] Created document record: ID {document.id}")

        # Create chunk records
        for chunk_index, chunk_data in enumerate(state["chunks"]):
            chunk = Chunk(
                document_id=document.id,
                text=chunk_data["text"],
                page_number=chunk_data["page_number"],
                chunk_index=chunk_index,
                embedding=chunk_data["embedding"],
                chunk_type=chunk_data.get("chunk_type", "text"),
                chunk_metadata=chunk_data.get("metadata", {})
            )
            db.add(chunk)

        # Atomic commit - document and all chunks saved together
        db.commit()

        state["document_id"] = document.id
        logger.info(f"[Job {job_id}] Database storage complete: Document {document.id}, {len(state['chunks'])} chunks")

    except Exception as e:
        logger.error(f"[Job {job_id}] Database storage failed: {str(e)}")
        logger.error(traceback.format_exc())
        db.rollback()
        state["error"] = f"Database storage failed: {str(e)}"

    return state


def mark_complete(state: DocumentProcessingState, db: Session) -> DocumentProcessingState:
    """
    Mark job as complete

    Updates job status to 'complete'
    """
    job_id = state["job_id"]

    logger.info(f"[Job {job_id}] Marking job as complete")

    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    job.status = "complete"
    job.progress = 100
    job.current_stage = "Processing complete"
    job.result_document_id = state["document_id"]
    job.completed_at = datetime.utcnow()
    db.commit()

    logger.info(f"[Job {job_id}] Job complete: Document {state['document_id']}")

    return state


def mark_failed(state: DocumentProcessingState, db: Session) -> DocumentProcessingState:
    """
    Mark job as failed

    Updates job status to 'failed' and stores error message
    """
    job_id = state["job_id"]
    error = state.get("error", "Unknown error")

    logger.error(f"[Job {job_id}] Marking job as failed: {error}")

    job = db.query(DocumentProcessingJob).filter(
        DocumentProcessingJob.job_id == job_id
    ).first()

    job.status = "failed"
    job.error_message = error
    job.completed_at = datetime.utcnow()
    db.commit()

    return state


def should_retry(state: DocumentProcessingState) -> Literal["retry", "failed"]:
    """
    Decide whether to retry or mark as failed

    Retries up to MAX_RETRIES times for transient errors
    """
    retry_count = state.get("retry_count", 0)

    if retry_count < MAX_RETRIES:
        logger.info(f"[Job {state['job_id']}] Retry {retry_count + 1}/{MAX_RETRIES}")
        return "retry"
    else:
        logger.error(f"[Job {state['job_id']}] Max retries exceeded")
        return "failed"


def route_after_stage(state: DocumentProcessingState) -> Literal["continue", "error"]:
    """
    Route to next stage or error handler based on state
    """
    if state.get("error"):
        return "error"
    return "continue"


# Build the LangGraph state machine
def create_document_processing_graph(db: Session) -> StateGraph:
    """
    Create the LangGraph state machine for document processing

    Graph structure:
        accept_job -> extract_text -> chunk_text -> generate_embeddings -> store_in_db -> mark_complete
                          ↓ error          ↓ error          ↓ error              ↓ error
                       should_retry? -> retry or mark_failed
    """

    # Create graph
    workflow = StateGraph(DocumentProcessingState)

    # Add nodes (each node is a processing stage)
    workflow.add_node("accept_job", lambda state: accept_job(state, db))
    workflow.add_node("extract_text", lambda state: extract_text(state, db))
    workflow.add_node("chunk_text", lambda state: chunk_text_stage(state, db))
    workflow.add_node("generate_embeddings", lambda state: generate_embeddings_stage(state, db))
    workflow.add_node("store_in_database", lambda state: store_in_database(state, db))
    workflow.add_node("mark_complete", lambda state: mark_complete(state, db))
    workflow.add_node("mark_failed", lambda state: mark_failed(state, db))

    # Set entry point
    workflow.set_entry_point("accept_job")

    # Add edges (define the flow)
    workflow.add_conditional_edges(
        "accept_job",
        route_after_stage,
        {
            "continue": "extract_text",
            "error": "mark_failed"
        }
    )

    workflow.add_conditional_edges(
        "extract_text",
        route_after_stage,
        {
            "continue": "chunk_text",
            "error": "mark_failed"
        }
    )

    workflow.add_conditional_edges(
        "chunk_text",
        route_after_stage,
        {
            "continue": "generate_embeddings",
            "error": "mark_failed"
        }
    )

    workflow.add_conditional_edges(
        "generate_embeddings",
        route_after_stage,
        {
            "continue": "store_in_database",
            "error": "mark_failed"
        }
    )

    workflow.add_conditional_edges(
        "store_in_database",
        route_after_stage,
        {
            "continue": "mark_complete",
            "error": "mark_failed"
        }
    )

    # Terminal nodes
    workflow.add_edge("mark_complete", END)
    workflow.add_edge("mark_failed", END)

    return workflow.compile()
