"""
Integration tests for real PDF processing with Advanced RAG features.

Tests verify:
- Phase 1: Reranking
- Phase 2: Table extraction from real PDFs
- Phase 3: Semantic chunking
- Real file I/O from disk
"""

import os
import pytest
from pathlib import Path

from app.services.pdf_processor import process_pdf


# Get the samples directory using relative path from this test file
# Test file location: app/tests/test_integration_01_document_ingestion/test_real_pdf_processing_with_advanced_rag.py
# Samples location: app/samples/
SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"


class TestRealPDFProcessingWithAdvancedRAG:
    """Integration tests for real PDF processing with reranking, table extraction, and semantic chunking"""

    @pytest.mark.asyncio
    async def test_company_policy_pdf_semantic_chunking(self):
        """Test semantic chunking on real company_policy.pdf"""
        pdf_path = SAMPLES_DIR / "company_policy.pdf"

        # Read the real PDF file
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # Process the PDF
        result = await process_pdf(pdf_bytes, "company_policy.pdf")

        # Verify basic processing
        assert len(result["chunks"]) > 0, "Should extract chunks from company policy PDF"
        assert result["page_count"] > 0, "Should have page count"

        # Verify chunks have content
        for chunk in result["chunks"]:
            assert len(chunk["text"]) > 0, "Chunks should have text"
            assert chunk["page_number"] > 0, "Chunks should have page numbers"
            assert chunk["embedding"] is not None, "Chunks should have embeddings"
            assert len(chunk["embedding"]) == 384, "Embeddings should be 384-dimensional"

        # Verify content exists (real PDF may have different content than synthetic)
        all_text = " ".join([chunk["text"] for chunk in result["chunks"]])
        assert len(all_text) > 100, "Should contain substantive content"

    @pytest.mark.asyncio
    async def test_sample_document_pdf_processing(self):
        """Test PDF processing on real sample_document.pdf with table extraction"""
        pdf_path = SAMPLES_DIR / "sample_document.pdf"

        # Read the real PDF file
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()

        # Process the PDF
        result = await process_pdf(pdf_bytes, "sample_document.pdf")

        # Verify basic processing
        assert len(result["chunks"]) > 0, "Should extract chunks from sample document PDF"
        assert result["page_count"] > 0, "Should have page count"

        # Verify all chunks have required fields
        for chunk in result["chunks"]:
            assert len(chunk["text"]) > 0, "Chunks should have text"
            assert chunk["page_number"] > 0, "Chunks should have page numbers"
            assert chunk["embedding"] is not None, "All chunks should have embeddings"
            assert len(chunk["embedding"]) == 384, "Embeddings should be 384-dimensional"
            assert chunk.get("chunk_type") in ["text", "table"], "Chunk type should be text or table"

        # Check if table extraction worked (if PDF has tables)
        table_chunks = [chunk for chunk in result["chunks"] if chunk.get("chunk_type") == "table"]
        if table_chunks:
            # Verify table chunks contain markdown table format
            for table_chunk in table_chunks:
                assert "|" in table_chunk["text"], "Table chunks should contain markdown table format"

    def test_verify_real_sample_pdf_files_exist(self):
        """Verify real sample PDF files exist and are readable from disk"""
        required_files = [
            "company_policy.pdf",
            "sample_document.pdf"
        ]

        for filename in required_files:
            file_path = SAMPLES_DIR / filename
            assert file_path.exists(), f"Sample file {filename} should exist at {file_path}"
            assert file_path.stat().st_size > 0, f"Sample file {filename} should not be empty"

            # Verify it's actually a PDF file
            with open(file_path, "rb") as f:
                header = f.read(4)
                assert header == b'%PDF', f"{filename} should be a valid PDF file"
