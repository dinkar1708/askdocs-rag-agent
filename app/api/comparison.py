"""Comparative Analysis API endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import verify_api_key
from app.schemas.comparison import (
    ComparisonRequest,
    ComparisonResponse,
    TableComparisonRequest,
    TableComparisonResponse,
    DiffRequest,
    DiffResponse
)
from app.services.document_comparator import get_document_comparator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/compare",
    tags=["comparison"],
    dependencies=[Depends(verify_api_key)]
)


@router.post("", response_model=ComparisonResponse)
@router.post("/", response_model=ComparisonResponse, include_in_schema=False)
async def compare_documents(
    request: ComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Compare multiple documents side-by-side across specified aspects.

    Returns structured comparison data per document, detected differences/trends,
    and a synthesized executive narrative summary.
    """
    comparator = get_document_comparator(db=db)
    try:
        return await comparator.compare_documents(request=request)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logger.error(f"Failed to compare documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to compare documents: {str(e)}")


@router.post("/table", response_model=TableComparisonResponse)
async def compare_documents_table(
    request: TableComparisonRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a Markdown table comparing documents side-by-side.

    Ideal for rendering in dashboards, wikis, and markdown viewers.
    """
    comparator = get_document_comparator(db=db)
    try:
        return await comparator.compare_table(request=request)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logger.error(f"Failed to generate comparison table: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate comparison table: {str(e)}")


@router.post("/diff", response_model=DiffResponse)
async def compare_documents_diff(
    request: DiffRequest,
    db: Session = Depends(get_db)
):
    """
    Perform a fine-grained version diff between two documents on a specific aspect.

    Identifies exact field changes, delta descriptions, and context snippets.
    """
    comparator = get_document_comparator(db=db)
    try:
        return await comparator.compare_diff(request=request)
    except ValueError as e:
        msg = str(e)
        if "not found" in msg.lower():
            raise HTTPException(status_code=404, detail=msg)
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logger.error(f"Failed to generate document diff: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate document diff: {str(e)}")
