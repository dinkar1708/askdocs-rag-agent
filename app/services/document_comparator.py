"""Comparative Analysis Service

Enables side-by-side comparison of multiple documents, structured Markdown table generation,
and fine-grained version diffs across specific aspects.
"""

import json
import logging
import inspect
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.db.models import Document, Chunk
from app.llm.factory import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.schemas.comparison import (
    ComparisonRequest,
    ComparisonResponse,
    ComparisonData,
    DocumentAspectData,
    TableComparisonRequest,
    TableComparisonResponse,
    DiffRequest,
    DiffResponse,
    DiffFieldChange,
    DocumentSnippet
)

logger = logging.getLogger(__name__)


class DocumentComparator:
    """Service for comparing documents across multiple aspects"""

    def __init__(self, db: Session, llm_provider: Optional[BaseLLMProvider] = None):
        self.db = db
        self.llm = llm_provider or get_llm_provider()

    async def compare_documents(self, request: ComparisonRequest) -> ComparisonResponse:
        """
        Compare multiple documents across specified aspects.

        Args:
            request: Comparison configuration containing document_ids and aspects

        Returns:
            ComparisonResponse containing structured data, differences, and synthesis summary
        """
        if len(request.document_ids) < 2:
            raise ValueError("At least 2 documents are required for comparison")
        if len(request.document_ids) > 5:
            raise ValueError("Maximum 5 documents can be compared at once")

        documents = self._fetch_documents(request.document_ids)
        doc_contexts = self._build_document_contexts(documents)

        # Call LLM to extract aspect data and analyze differences
        comparison_result = await self._generate_comparison_with_llm(
            documents=documents,
            doc_contexts=doc_contexts,
            aspects=request.aspects,
            question=request.question
        )

        doc_data_list: List[DocumentAspectData] = []
        for doc in documents:
            data_dict = comparison_result.get("documents", {}).get(doc.id, {})
            # Ensure every requested aspect exists in data_dict
            for aspect in request.aspects:
                if aspect not in data_dict:
                    data_dict[aspect] = f"Not specified in {doc.filename}"
            doc_data_list.append(
                DocumentAspectData(
                    document_id=doc.id,
                    filename=doc.filename,
                    data=data_dict
                )
            )

        return ComparisonResponse(
            comparison=ComparisonData(
                aspects=request.aspects,
                documents=doc_data_list
            ),
            differences=comparison_result.get("differences", {}),
            summary=comparison_result.get("summary", "Comparison generated based on available document text.")
        )

    async def compare_table(self, request: TableComparisonRequest) -> TableComparisonResponse:
        """
        Generate a Markdown table comparing documents side-by-side.

        Args:
            request: Table comparison configuration

        Returns:
            TableComparisonResponse containing Markdown table and underlying data
        """
        comp_req = ComparisonRequest(
            document_ids=request.document_ids,
            aspects=request.aspects
        )
        comp_resp = await self.compare_documents(comp_req)

        markdown_table = self._build_markdown_table(
            aspects=request.aspects,
            documents=comp_resp.comparison.documents
        )

        return TableComparisonResponse(
            markdown_table=markdown_table,
            aspects=request.aspects,
            documents=comp_resp.comparison.documents
        )

    async def compare_diff(self, request: DiffRequest) -> DiffResponse:
        """
        Compare two documents on a specific aspect to identify exact differences and changes.

        Args:
            request: Diff configuration with exactly two document IDs and one aspect

        Returns:
            DiffResponse with text snippets, field-level differences, and summary
        """
        if len(request.document_ids) != 2:
            raise ValueError("Diff comparison requires exactly two document IDs")

        doc1_id, doc2_id = request.document_ids[0], request.document_ids[1]
        documents = self._fetch_documents([doc1_id, doc2_id])
        doc1 = next(d for d in documents if d.id == doc1_id)
        doc2 = next(d for d in documents if d.id == doc2_id)

        doc1_text = self._extract_aspect_snippet(doc1, request.aspect)
        doc2_text = self._extract_aspect_snippet(doc2, request.aspect)

        diff_result = await self._generate_diff_with_llm(
            doc1=doc1,
            doc1_text=doc1_text,
            doc2=doc2,
            doc2_text=doc2_text,
            aspect=request.aspect
        )

        return DiffResponse(
            document_1=DocumentSnippet(
                document_id=doc1.id,
                filename=doc1.filename,
                text=diff_result.get("doc_1_text", doc1_text)
            ),
            document_2=DocumentSnippet(
                document_id=doc2.id,
                filename=doc2.filename,
                text=diff_result.get("doc_2_text", doc2_text)
            ),
            differences=diff_result.get("differences", []),
            summary=diff_result.get("summary")
        )

    def _fetch_documents(self, document_ids: List[int]) -> List[Document]:
        """Fetch documents by ID and validate existence"""
        docs = self.db.query(Document).filter(Document.id.in_(document_ids)).all()
        found_ids = {d.id for d in docs}
        for doc_id in document_ids:
            if doc_id not in found_ids:
                raise ValueError(f"Document with ID {doc_id} not found")
        # Keep original request ordering
        docs_by_id = {d.id: d for d in docs}
        return [docs_by_id[doc_id] for doc_id in document_ids]

    def _build_document_contexts(self, documents: List[Document]) -> Dict[int, str]:
        """Retrieve and format chunks for each document"""
        contexts: Dict[int, str] = {}
        for doc in documents:
            chunks = (
                self.db.query(Chunk)
                .filter(Chunk.document_id == doc.id)
                .order_by(Chunk.page_number.asc(), Chunk.chunk_index.asc())
                .all()
            )
            if not chunks:
                contexts[doc.id] = f"No text content available in {doc.filename}."
                continue

            lines: List[str] = []
            for chunk in chunks:
                lines.append(f"[Page {chunk.page_number}]: {chunk.text}")
            combined = "\n".join(lines)
            if len(combined) > 12000:
                combined = combined[:12000] + "\n[Content truncated for length...]"
            contexts[doc.id] = combined
        return contexts

    def _extract_aspect_snippet(self, document: Document, aspect: str) -> str:
        """Extract a relevant snippet for an aspect from document chunks"""
        chunks = (
            self.db.query(Chunk)
            .filter(Chunk.document_id == document.id)
            .order_by(Chunk.page_number.asc(), Chunk.chunk_index.asc())
            .all()
        )
        if not chunks:
            return f"No text content found for {document.filename}."

        aspect_lower = aspect.lower()
        matching = [c.text for c in chunks if aspect_lower in c.text.lower()]
        if matching:
            return "\n".join(matching[:3])
        return "\n".join([c.text for c in chunks[:2]])

    def _build_markdown_table(
        self,
        aspects: List[str],
        documents: List[DocumentAspectData]
    ) -> str:
        """Build Markdown comparison table from aspect data"""
        headers = ["Aspect"] + [f"{doc.filename} (ID: {doc.document_id})" for doc in documents]
        sep = ["---"] * len(headers)

        rows: List[str] = []
        rows.append("| " + " | ".join(headers) + " |")
        rows.append("| " + " | ".join(sep) + " |")

        for aspect in aspects:
            row_cells = [aspect.title().replace("_", " ")]
            for doc in documents:
                val = doc.data.get(aspect, "-")
                if isinstance(val, list):
                    val_str = ", ".join(str(item) for item in val)
                elif isinstance(val, dict):
                    val_str = json.dumps(val)
                else:
                    val_str = str(val).replace("\n", " ").strip()
                row_cells.append(val_str)
            rows.append("| " + " | ".join(row_cells) + " |")

        return "\n".join(rows)

    async def _generate_comparison_with_llm(
        self,
        documents: List[Document],
        doc_contexts: Dict[int, str],
        aspects: List[str],
        question: Optional[str]
    ) -> Dict[str, Any]:
        """Invoke LLM to produce structured comparison and synthesis"""
        aspects_str = ", ".join(aspects)
        question_str = f"Focus on this user question: '{question}'." if question else ""

        system_prompt = (
            "You are an expert document comparative analysis AI. Compare the provided documents across specific aspects.\n"
            "Respond ONLY with a valid JSON object matching this exact schema:\n"
            "{\n"
            '  "documents": {\n'
            '    "<document_id>": {\n'
            '      "<aspect_name>": "Extracted value or list of values"\n'
            "    }\n"
            "  },\n"
            '  "differences": {\n'
            '    "<aspect_name>": {\n'
            '      "trend": "Description of trend or change across documents",\n'
            '      "common": ["Shared points"],\n'
            '      "unique": ["Distinct or unique points"]\n'
            "    }\n"
            "  },\n"
            '  "summary": "Cohesive narrative summarizing key comparisons and contrasts."\n'
            "}\n"
            "Do NOT include markdown backticks (```json), output raw JSON."
        )

        user_prompt_lines = [
            f"Aspects to compare: {aspects_str}",
            question_str,
            "\nDocuments to compare:"
        ]
        for doc in documents:
            user_prompt_lines.append(f"\n--- Document ID {doc.id} ({doc.filename}) ---")
            user_prompt_lines.append(doc_contexts.get(doc.id, ""))

        user_prompt = "\n".join(user_prompt_lines)

        try:
            gen_func = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            if inspect.iscoroutine(gen_func):
                raw = await gen_func
            else:
                raw = gen_func

            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)

            # Re-key documents by integer ID
            formatted_docs: Dict[int, Dict[str, Any]] = {}
            for k, v in parsed.get("documents", {}).items():
                try:
                    formatted_docs[int(k)] = v
                except ValueError:
                    continue

            return {
                "documents": formatted_docs,
                "differences": parsed.get("differences", {}),
                "summary": parsed.get("summary", f"Comparison completed across {len(documents)} documents.")
            }

        except Exception as e:
            logger.warning(f"LLM comparison generation/parsing failed ({e}), using fallback extractor")
            return self._fallback_comparison(documents, doc_contexts, aspects, question)

    def _fallback_comparison(
        self,
        documents: List[Document],
        doc_contexts: Dict[int, str],
        aspects: List[str],
        question: Optional[str]
    ) -> Dict[str, Any]:
        """Deterministic fallback when LLM output is not structured JSON"""
        docs_data: Dict[int, Dict[str, Any]] = {}
        differences: Dict[str, Any] = {}

        for doc in documents:
            context = doc_contexts.get(doc.id, "")
            doc_aspects: Dict[str, Any] = {}
            for aspect in aspects:
                aspect_lower = aspect.lower()
                matched_line = None
                for line in context.splitlines():
                    if aspect_lower in line.lower():
                        matched_line = line.strip()
                        break
                doc_aspects[aspect] = matched_line or f"Relevant {aspect} information from {doc.filename}"
            docs_data[doc.id] = doc_aspects

        for aspect in aspects:
            differences[aspect] = {
                "comparison": f"Values vary across {len(documents)} documents for {aspect}.",
                "documents_count": len(documents)
            }

        summary = (
            f"Compared {len(documents)} documents ({', '.join(d.filename for d in documents)}) "
            f"across aspects: {', '.join(aspects)}."
        )
        if question:
            summary += f" Addressing query: '{question}'."

        return {
            "documents": docs_data,
            "differences": differences,
            "summary": summary
        }

    async def _generate_diff_with_llm(
        self,
        doc1: Document,
        doc1_text: str,
        doc2: Document,
        doc2_text: str,
        aspect: str
    ) -> Dict[str, Any]:
        """Invoke LLM to detect fine-grained diffs between two document snippets"""
        system_prompt = (
            "You are a document difference analysis AI. Compare two document snippets on a specific aspect.\n"
            "Respond ONLY with a valid JSON object matching this schema:\n"
            "{\n"
            '  "doc_1_text": "Cleaned snippet from Doc 1",\n'
            '  "doc_2_text": "Cleaned snippet from Doc 2",\n'
            '  "differences": [\n'
            '    {\n'
            '      "field": "Field or clause name",\n'
            '      "doc_1_value": "Value in doc 1",\n'
            '      "doc_2_value": "Value in doc 2",\n'
            '      "change": "Description of the change (e.g. +3 days, 20% increase)"\n'
            "    }\n"
            "  ],\n"
            '  "summary": "Summary of changes"\n'
            "}\n"
            "Do NOT include markdown backticks (```json), output raw JSON."
        )

        user_prompt = (
            f"Aspect: {aspect}\n\n"
            f"--- Document 1: {doc1.filename} (ID: {doc1.id}) ---\n{doc1_text}\n\n"
            f"--- Document 2: {doc2.filename} (ID: {doc2.id}) ---\n{doc2_text}\n"
        )

        try:
            gen_func = self.llm.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2
            )
            if inspect.iscoroutine(gen_func):
                raw = await gen_func
            else:
                raw = gen_func

            cleaned = raw.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            parsed = json.loads(cleaned)
            diffs = [
                DiffFieldChange(
                    field=d.get("field", aspect),
                    doc_1_value=d.get("doc_1_value", "Doc 1 value"),
                    doc_2_value=d.get("doc_2_value", "Doc 2 value"),
                    change=d.get("change")
                )
                for d in parsed.get("differences", [])
            ]

            return {
                "doc_1_text": parsed.get("doc_1_text", doc1_text),
                "doc_2_text": parsed.get("doc_2_text", doc2_text),
                "differences": diffs,
                "summary": parsed.get("summary", f"Diff analysis on {aspect} between {doc1.filename} and {doc2.filename}.")
            }

        except Exception as e:
            logger.warning(f"LLM diff generation/parsing failed ({e}), using fallback diff extractor")
            return {
                "doc_1_text": doc1_text,
                "doc_2_text": doc2_text,
                "differences": [
                    DiffFieldChange(
                        field=aspect,
                        doc_1_value=doc1_text[:60] + "..." if len(doc1_text) > 60 else doc1_text,
                        doc_2_value=doc2_text[:60] + "..." if len(doc2_text) > 60 else doc2_text,
                        change="Content updated"
                    )
                ],
                "summary": f"Diff between {doc1.filename} and {doc2.filename} regarding {aspect}."
            }


def get_document_comparator(db: Session, llm_provider: Optional[BaseLLMProvider] = None) -> DocumentComparator:
    """Factory function for DocumentComparator"""
    return DocumentComparator(db=db, llm_provider=llm_provider)
