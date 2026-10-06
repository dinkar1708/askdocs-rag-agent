"""Document Summarization Service

Generates executive summaries, detailed summaries, key points with page references,
and section breakdowns from full documents using LLMs.
"""

import json
import logging
import inspect
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.db.models import Document, Chunk
from app.llm.factory import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.schemas.summary import (
    SummaryRequest,
    SummaryResponse,
    KeyPoint,
    SectionSummary,
    SummaryType,
    BatchSummaryRequest,
    BatchSummaryResponse
)

logger = logging.getLogger(__name__)


class DocumentSummarizer:
    """Service for auto-generating and caching document summaries"""

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    async def summarize_document(
        self,
        db: Session,
        document_id: int,
        request: SummaryRequest
    ) -> SummaryResponse:
        """
        Generate a summary for a specific document with caching.

        Args:
            db: Database session
            document_id: ID of document to summarize
            request: Summary configuration request

        Returns:
            SummaryResponse containing summary text, key points, and metadata
        """
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        # 1. Check cache in doc_metadata if not forcing regeneration
        doc_metadata = dict(document.doc_metadata or {})
        cached_summaries = doc_metadata.get("summaries", {})
        cache_key = f"{request.summary_type}_{request.max_length}_{','.join(request.focus_areas or [])}"

        if not request.force_regenerate and cache_key in cached_summaries:
            cached_data = cached_summaries[cache_key]
            logger.info(f"Serving cached summary for document {document_id} (key: {cache_key})")
            return SummaryResponse(
                document_id=document.id,
                filename=document.filename,
                summary=cached_data.get("summary", ""),
                summary_type=request.summary_type,
                word_count=cached_data.get("word_count", 0),
                key_points=[KeyPoint(**kp) for kp in cached_data.get("key_points", [])],
                sections=[SectionSummary(**sec) for sec in cached_data.get("sections", [])] if cached_data.get("sections") else None,
                cached=True,
                generated_at=datetime.fromisoformat(cached_data["generated_at"]) if "generated_at" in cached_data else datetime.utcnow()
            )

        # 2. Retrieve all chunks ordered by page and index
        chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == document_id)
            .order_by(Chunk.page_number.asc(), Chunk.chunk_index.asc())
            .all()
        )

        if not chunks:
            empty_summary = "This document contains no readable text content."
            return SummaryResponse(
                document_id=document.id,
                filename=document.filename,
                summary=empty_summary,
                summary_type=request.summary_type,
                word_count=len(empty_summary.split()),
                key_points=[],
                sections=None,
                cached=False,
                generated_at=datetime.utcnow()
            )

        # 3. Format document text with page markers
        formatted_pages: List[str] = []
        page_chunks: Dict[int, List[str]] = {}
        for chunk in chunks:
            page_chunks.setdefault(chunk.page_number, []).append(chunk.text)

        for page_num, texts in page_chunks.items():
            formatted_pages.append(f"--- [Page {page_num}] ---\n" + "\n".join(texts))

        full_document_text = "\n\n".join(formatted_pages)

        if len(full_document_text) > 25000:
            full_document_text = full_document_text[:25000] + "\n\n[Content truncated for length...]"

        # 4. Generate summary using LLM
        summary_result = await self._generate_summary_with_llm(
            filename=document.filename,
            document_text=full_document_text,
            summary_type=request.summary_type,
            max_length=request.max_length or 200,
            focus_areas=request.focus_areas,
            available_pages=list(page_chunks.keys())
        )

        now = datetime.utcnow()
        summary_text = summary_result["summary"]
        key_points = summary_result["key_points"]
        sections = summary_result["sections"]
        word_count = len(summary_text.split())

        # 5. Cache result in doc_metadata
        if "summaries" not in doc_metadata:
            doc_metadata["summaries"] = {}

        doc_metadata["summaries"][cache_key] = {
            "summary": summary_text,
            "summary_type": request.summary_type,
            "word_count": word_count,
            "key_points": [kp.model_dump() for kp in key_points],
            "sections": [sec.model_dump() for sec in sections] if sections else None,
            "generated_at": now.isoformat()
        }
        document.doc_metadata = doc_metadata
        flag_modified(document, "doc_metadata")
        db.commit()

        return SummaryResponse(
            document_id=document.id,
            filename=document.filename,
            summary=summary_text,
            summary_type=request.summary_type,
            word_count=word_count,
            key_points=key_points,
            sections=sections,
            cached=False,
            generated_at=now
        )

    async def _generate_summary_with_llm(
        self,
        filename: str,
        document_text: str,
        summary_type: str,
        max_length: int,
        focus_areas: Optional[List[str]],
        available_pages: List[int]
    ) -> Dict[str, Any]:
        """Call LLM provider to construct structured summary"""
        focus_str = f"Focus particularly on: {', '.join(focus_areas)}." if focus_areas else ""

        type_instructions = {
            SummaryType.EXECUTIVE: f"Provide an executive overview in {max_length} words or less capturing key objectives, scope, and conclusions.",
            SummaryType.DETAILED: f"Provide a comprehensive, detailed summary in {max_length} words structured with subheadings.",
            SummaryType.KEY_POINTS: "Focus primarily on extracting critical takeaway points and action items.",
            SummaryType.SECTION_SUMMARIES: "Break down the document section by section with distinct topic summaries."
        }.get(summary_type, f"Summarize the document in {max_length} words.")

        system_prompt = (
            "You are an expert document summarization AI. Analyze the document text provided with [Page X] markers.\n"
            "Respond ONLY with a valid JSON object following this exact schema:\n"
            "{\n"
            '  "summary": "The main summary text here...",\n'
            '  "key_points": [\n'
            '    {"point": "Key takeaway point statement", "page": 1},\n'
            '    {"point": "Another important point", "page": 2}\n'
            "  ],\n"
            '  "sections": [\n'
            '    {"section": "Section name", "summary": "Section summary", "pages": [1, 2]}\n'
            "  ]\n"
            "}\n"
            "Do NOT include markdown backticks (```json), only output raw JSON."
        )

        user_prompt = (
            f"Document Filename: {filename}\n"
            f"Summary Type: {summary_type}\n"
            f"Target Length: ~{max_length} words\n"
            f"{focus_str}\n\n"
            f"Instructions: {type_instructions}\n\n"
            f"Document Text:\n{document_text}"
        )

        try:
            # Handle both async and sync generate signatures safely
            gen_func = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            if inspect.iscoroutine(gen_func):
                raw_response = await gen_func
            else:
                raw_response = gen_func

            # Clean JSON markdown fences if present
            cleaned = raw_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)
            summary_text = parsed.get("summary", "")
            key_points = [
                KeyPoint(
                    point=item.get("point", ""),
                    page=item.get("page") if item.get("page") in available_pages else (available_pages[0] if available_pages else 1)
                )
                for item in parsed.get("key_points", [])
                if item.get("point")
            ]
            sections = None
            if summary_type == SummaryType.SECTION_SUMMARIES or parsed.get("sections"):
                sections = [
                    SectionSummary(
                        section=s.get("section", "General"),
                        summary=s.get("summary", ""),
                        pages=s.get("pages", [1])
                    )
                    for s in parsed.get("sections", [])
                    if s.get("section")
                ]

            if not summary_text:
                summary_text = f"Summary of {filename} ({len(document_text.split())} words processed)."

            return {
                "summary": summary_text,
                "key_points": key_points,
                "sections": sections
            }

        except Exception as e:
            logger.warning(f"LLM json summarization parsing failed ({e}), using fallback extractor")
            first_page = available_pages[0] if available_pages else 1
            summary_text = (
                f"Summary of {filename}: The document covers {len(available_pages)} page(s) "
                f"discussing key topics and specifications."
            )
            key_points = [
                KeyPoint(point=f"Document contains {len(available_pages)} page(s) of content", page=first_page),
                KeyPoint(point=f"Processed filename: {filename}", page=first_page)
            ]
            return {
                "summary": summary_text,
                "key_points": key_points,
                "sections": None
            }

    async def summarize_batch(
        self,
        db: Session,
        request: BatchSummaryRequest
    ) -> BatchSummaryResponse:
        """Summarize multiple documents in batch"""
        summaries: List[SummaryResponse] = []
        failed_ids: List[int] = []

        single_req = SummaryRequest(
            summary_type=request.summary_type,
            max_length=request.max_length,
            focus_areas=request.focus_areas,
            force_regenerate=request.force_regenerate
        )

        for doc_id in request.document_ids:
            try:
                resp = await self.summarize_document(db=db, document_id=doc_id, request=single_req)
                summaries.append(resp)
            except Exception as e:
                logger.error(f"Failed to summarize document {doc_id}: {e}")
                failed_ids.append(doc_id)

        return BatchSummaryResponse(
            summaries=summaries,
            total_processed=len(summaries),
            failed_document_ids=failed_ids
        )


def get_document_summarizer(llm_provider: Optional[BaseLLMProvider] = None) -> DocumentSummarizer:
    """Factory function for DocumentSummarizer"""
    return DocumentSummarizer(llm_provider=llm_provider)
