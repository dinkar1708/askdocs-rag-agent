"""Background worker for processing document jobs using LangGraph

This worker continuously polls the database for queued jobs and processes them
using the LangGraph state machine.

Run this as a separate process:
    python -m app.services.job_worker
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.db.models import DocumentProcessingJob
from app.services.document_processor_graph import create_document_processing_graph, DocumentProcessingState

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_flag = False


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    global shutdown_flag
    logger.info("Shutdown signal received, finishing current job...")
    shutdown_flag = True


def process_job(job: DocumentProcessingJob, db: Session) -> None:
    """
    Process a single job using the LangGraph state machine

    Args:
        job: DocumentProcessingJob to process
        db: Database session
    """
    logger.info(f"Processing job {job.job_id}: {job.filename}")

    try:
        # Load file content from temporary storage
        # In production, this would load from S3, Redis, or filesystem
        # For now, we'll handle this in the API endpoint

        # Create initial state
        initial_state: DocumentProcessingState = {
            "job_id": job.job_id,
            "filename": job.filename,
            "content": b"",  # Will be populated by API
            "content_hash": job.content_hash or "",
            "doc_metadata": job.doc_metadata,
            "file_size": job.file_size,
            "extracted_data": None,
            "chunks": None,
            "document_id": None,
            "error": None,
            "retry_count": job.retry_count
        }

        # Create and run the graph
        graph = create_document_processing_graph(db)

        # Execute the graph
        final_state = graph.invoke(initial_state)

        if final_state.get("error"):
            logger.error(f"Job {job.job_id} failed: {final_state['error']}")
        else:
            logger.info(f"Job {job.job_id} completed successfully: Document {final_state['document_id']}")

    except Exception as e:
        logger.error(f"Error processing job {job.job_id}: {str(e)}", exc_info=True)

        # Mark job as failed
        job.status = "failed"
        job.error_message = f"Worker error: {str(e)}"
        db.commit()


def run_worker(poll_interval: int = 5):
    """
    Main worker loop - polls for queued jobs and processes them

    Args:
        poll_interval: Seconds to wait between polling for new jobs
    """
    logger.info("Starting document processing worker...")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    while not shutdown_flag:
        db = SessionLocal()

        try:
            # Get next queued job (FIFO order)
            job = db.query(DocumentProcessingJob).filter(
                DocumentProcessingJob.status == "queued"
            ).order_by(
                DocumentProcessingJob.created_at
            ).first()

            if job:
                # Process the job
                process_job(job, db)
            else:
                # No jobs, wait before polling again
                logger.debug(f"No queued jobs, waiting {poll_interval}s...")
                asyncio.sleep(poll_interval)

        except Exception as e:
            logger.error(f"Worker error: {str(e)}", exc_info=True)
            asyncio.sleep(poll_interval)

        finally:
            db.close()

    logger.info("Worker shutdown complete")


if __name__ == "__main__":
    # For production, use a proper job queue like Celery, RQ, or Dramatiq
    # This simple polling worker is for development/demo purposes
    run_worker(poll_interval=5)
