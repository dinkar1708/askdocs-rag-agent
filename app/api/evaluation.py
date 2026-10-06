"""Evaluation API endpoints"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_db
from app.core.auth import verify_api_key
from app.schemas.evaluation import EvaluationRequest, EvaluationResponse
from app.services.evaluator import get_evaluator

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/evaluate",
    tags=["evaluation"],
    dependencies=[Depends(verify_api_key)]
)


@router.post("", response_model=EvaluationResponse)
@router.post("/", response_model=EvaluationResponse, include_in_schema=False)
async def run_evaluation(
    request: Optional[EvaluationRequest] = None,
    db: Session = Depends(get_db)
):
    """
    Run automated RAG evaluation harness against benchmark questions.

    Calculates:
    - Retrieval Hit-Rate @ k
    - Mean Reciprocal Rank (MRR)
    - Retrieval Precision & Recall
    - Answer Groundedness
    - Refusal Accuracy on Off-Topic Queries
    """
    eval_req = request or EvaluationRequest()
    evaluator = get_evaluator(db=db)
    try:
        return await evaluator.run_evaluation(request=eval_req)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")
