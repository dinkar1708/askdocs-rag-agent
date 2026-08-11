"""Extraction API endpoints"""

import csv
import json
import io
import uuid
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.extractor import ExtractionService
from app.schemas.extraction import (
    ExtractionRequest,
    ExtractionResponse,
    BatchExtractionRequest,
    BatchExtractionResponse,
    BatchExtractionResult
)
from app.core.auth import verify_api_key

router = APIRouter(
    prefix="/extract",
    tags=["extraction"],
    dependencies=[Depends(verify_api_key)]
)

# In-memory storage for batch results (in production, use Redis or database)
_batch_results: Dict[str, Dict] = {}


@router.post("/", response_model=ExtractionResponse)
async def extract_structured_data(
    request: ExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Extract structured data from a single document based on provided schema.

    Example:
        POST /extract
        {
            "document_id": 1,
            "schema": {
                "title": "string",
                "experience_years": "number",
                "required_skills": "array",
                "location": "string"
            }
        }
    """
    try:
        extractor = ExtractionService(db)
        extracted_data, confidence, sources, warnings = await extractor.extract_from_document(
            request.document_id,
            request.schema
        )

        return ExtractionResponse(
            document_id=request.document_id,
            extracted_data=extracted_data,
            confidence=confidence,
            sources=sources,
            warnings=warnings
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")


@router.post("/batch", response_model=BatchExtractionResponse)
async def batch_extract(
    request: BatchExtractionRequest,
    db: Session = Depends(get_db)
):
    """
    Extract structured data from multiple documents.

    Example:
        POST /extract/batch
        {
            "document_ids": [1, 2, 3],
            "schema": {
                "title": "string",
                "experience_years": "number",
                "required_skills": "array"
            },
            "export_format": "csv"
        }
    """
    try:
        extractor = ExtractionService(db)
        results = await extractor.batch_extract(
            request.document_ids,
            request.schema
        )

        # Generate batch ID
        batch_id = f"batch_{uuid.uuid4().hex[:12]}"

        # Convert to response format
        batch_results = [
            BatchExtractionResult(**result)
            for result in results
        ]

        # Store results for export
        _batch_results[batch_id] = {
            "results": results,
            "schema": request.schema,
            "format": request.export_format
        }

        # Generate export URL if format specified
        export_url = None
        if request.export_format:
            export_url = f"/extract/batch/export/{batch_id}.{request.export_format}"

        return BatchExtractionResponse(
            batch_id=batch_id,
            results=batch_results,
            total=len(batch_results),
            export_url=export_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch extraction failed: {str(e)}")


@router.get("/batch/export/{batch_id}.{format}")
async def export_batch_results(batch_id: str, format: str):
    """
    Export batch extraction results in specified format.

    Supported formats: csv, json
    """
    # Remove file extension if it's in the batch_id
    if '.' in batch_id:
        batch_id = batch_id.split('.')[0]

    if batch_id not in _batch_results:
        raise HTTPException(status_code=404, detail="Batch results not found")

    batch_data = _batch_results[batch_id]
    results = batch_data["results"]
    schema = batch_data["schema"]

    if format == "csv":
        return _export_as_csv(results, schema, batch_id)
    elif format == "json":
        return _export_as_json(results, batch_id)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported export format: {format}")


def _export_as_csv(results: list, schema: Dict[str, str], batch_id: str) -> StreamingResponse:
    """Export results as CSV"""
    output = io.StringIO()

    # Define CSV columns: document_id, filename, + schema fields
    fieldnames = ["document_id", "filename"] + list(schema.keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()

    for result in results:
        row = {
            "document_id": result["document_id"],
            "filename": result["filename"]
        }

        # Add extracted fields
        for field in schema.keys():
            value = result["extracted_data"].get(field)

            # Convert arrays to comma-separated strings
            if isinstance(value, list):
                row[field] = ", ".join(str(v) for v in value)
            elif value is None:
                row[field] = ""
            else:
                row[field] = value

        writer.writerow(row)

    # Reset stream position
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={batch_id}.csv"
        }
    )


def _export_as_json(results: list, batch_id: str) -> StreamingResponse:
    """Export results as JSON"""
    json_data = json.dumps(results, indent=2)

    return StreamingResponse(
        iter([json_data]),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename={batch_id}.json"
        }
    )
