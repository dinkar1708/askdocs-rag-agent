"""Tests for table extraction functionality"""

import io
import pytest
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import pdfplumber

from app.services.table_processor import (
    extract_tables_from_page,
    clean_table_data,
    extract_headers,
    table_to_markdown,
    is_table_region,
    get_table_bboxes,
    is_point_in_table
)
from app.services.pdf_processor import process_pdf, extract_text_excluding_tables


class TestTableProcessor:
    """Test table processing functions"""

    def test_clean_table_data_basic(self):
        """Test cleaning table data with None values"""
        raw_data = [
            ["Header1", "Header2", "Header3"],
            ["Value1", None, "Value3"],
            [None, None, None],  # Should be removed
            ["Value4", "Value5", "Value6"]
        ]

        cleaned = clean_table_data(raw_data)

        assert len(cleaned) == 3  # Empty row removed
        assert cleaned[0] == ["Header1", "Header2", "Header3"]
        assert cleaned[1] == ["Value1", "", "Value3"]
        assert cleaned[2] == ["Value4", "Value5", "Value6"]

    def test_clean_table_data_empty_table(self):
        """Test cleaning empty table"""
        raw_data = []
        cleaned = clean_table_data(raw_data)
        assert cleaned == []

    def test_extract_headers_with_text_headers(self):
        """Test header extraction with text headers"""
        table_data = [
            ["Name", "Age", "City"],
            ["John", "30", "NYC"],
            ["Jane", "25", "LA"]
        ]

        headers = extract_headers(table_data)
        assert headers == ["Name", "Age", "City"]

    def test_extract_headers_with_numeric_first_row(self):
        """Test header extraction when first row is numeric"""
        table_data = [
            ["100", "200", "300"],
            ["400", "500", "600"]
        ]

        headers = extract_headers(table_data)
        # Should return empty list for all-numeric first row (not headers)
        assert len(headers) == 0

    def test_extract_headers_empty_table(self):
        """Test header extraction with empty table"""
        headers = extract_headers([])
        assert headers == []

    def test_table_to_markdown_with_headers(self):
        """Test markdown conversion with headers"""
        table_data = [
            ["Product", "Price", "Quantity"],
            ["Apple", "1.50", "100"],
            ["Banana", "0.75", "200"]
        ]

        markdown = table_to_markdown(table_data)

        assert "Product" in markdown
        assert "Price" in markdown
        assert "Apple" in markdown
        assert ("1.50" in markdown or "1.5" in markdown)  # tabulate may format decimals
        # GitHub markdown format uses pipes
        assert "|" in markdown

    def test_table_to_markdown_without_headers(self):
        """Test markdown conversion without clear headers"""
        table_data = [
            ["100", "200", "300"],
            ["400", "500", "600"]
        ]

        markdown = table_to_markdown(table_data)
        assert "|" in markdown
        assert "100" in markdown

    def test_table_to_markdown_empty(self):
        """Test markdown conversion with empty table"""
        markdown = table_to_markdown([])
        assert markdown == ""

    def test_is_table_region(self):
        """Test table region overlap detection"""
        bbox = (100, 100, 200, 200)
        text_regions = [
            (150, 150, 250, 250),  # Overlaps
            (300, 300, 400, 400)   # Does not overlap
        ]

        assert is_table_region(bbox, text_regions) is True

    def test_is_table_region_no_overlap(self):
        """Test table region with no overlap"""
        bbox = (100, 100, 200, 200)
        text_regions = [
            (300, 300, 400, 400),
            (500, 500, 600, 600)
        ]

        assert is_table_region(bbox, text_regions) is False

    def test_is_point_in_table(self):
        """Test point in table detection"""
        table_bboxes = [
            (100, 100, 200, 200),
            (300, 300, 400, 400)
        ]

        assert is_point_in_table(150, 150, table_bboxes) is True
        assert is_point_in_table(350, 350, table_bboxes) is True
        assert is_point_in_table(250, 250, table_bboxes) is False


class TestPDFWithTables:
    """Test PDF processing with tables"""

    @pytest.fixture
    def pdf_with_table(self):
        """Create a test PDF with a table"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        # Add some text before table
        styles = getSampleStyleSheet()
        story.append(Paragraph("Financial Report 2024", styles['Heading1']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("This report contains important financial data.", styles['Normal']))
        story.append(Spacer(1, 12))

        # Create a table
        table_data = [
            ["Quarter", "Revenue", "Profit", "Growth"],
            ["Q1", "$100,000", "$20,000", "10%"],
            ["Q2", "$120,000", "$25,000", "20%"],
            ["Q3", "$150,000", "$35,000", "25%"],
            ["Q4", "$180,000", "$45,000", "20%"]
        ]

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
        story.append(Spacer(1, 12))

        # Add some text after table
        story.append(Paragraph("The data shows consistent growth throughout the year.", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @pytest.fixture
    def pdf_without_table(self):
        """Create a test PDF without tables (plain text)"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        styles = getSampleStyleSheet()
        story.append(Paragraph("Simple Document", styles['Heading1']))
        story.append(Spacer(1, 12))
        story.append(Paragraph("This is a plain text document with no tables.", styles['Normal']))
        story.append(Paragraph("It should be processed as regular text chunks.", styles['Normal']))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_process_pdf_with_table(self, pdf_with_table):
        """Test processing PDF with table"""
        result = await process_pdf(pdf_with_table, "financial_report.pdf")

        assert result["page_count"] == 1
        assert len(result["chunks"]) > 0

        # Check for table chunks
        table_chunks = [c for c in result["chunks"] if c.get("chunk_type") == "table"]
        assert len(table_chunks) > 0

        # Verify table chunk has markdown format
        table_chunk = table_chunks[0]
        assert "Quarter" in table_chunk["text"]
        assert "Revenue" in table_chunk["text"]
        assert "|" in table_chunk["text"]  # Markdown table format

        # Verify metadata
        assert "metadata" in table_chunk
        assert "headers" in table_chunk["metadata"]

    @pytest.mark.asyncio
    async def test_process_pdf_without_table(self, pdf_without_table):
        """Test processing PDF without tables (backward compatibility)"""
        result = await process_pdf(pdf_without_table, "simple_doc.pdf")

        assert result["page_count"] == 1
        assert len(result["chunks"]) > 0

        # All chunks should be text type
        text_chunks = [c for c in result["chunks"] if c.get("chunk_type") == "text"]
        assert len(text_chunks) == len(result["chunks"])

    @pytest.mark.asyncio
    async def test_table_extraction_from_page(self, pdf_with_table):
        """Test table extraction from pdfplumber page"""
        with pdfplumber.open(io.BytesIO(pdf_with_table)) as pdf:
            page = pdf.pages[0]
            tables = extract_tables_from_page(page)

            assert len(tables) > 0
            table = tables[0]

            # Check structure
            assert "table_data" in table
            assert "bbox" in table
            assert "markdown" in table
            assert "headers" in table

            # Check content
            assert len(table["table_data"]) > 0
            assert "Quarter" in table["markdown"]

    @pytest.mark.asyncio
    async def test_text_excluding_tables(self, pdf_with_table):
        """Test text extraction excluding table regions"""
        with pdfplumber.open(io.BytesIO(pdf_with_table)) as pdf:
            page = pdf.pages[0]
            tables = extract_tables_from_page(page)
            table_bboxes = get_table_bboxes(tables)

            text = extract_text_excluding_tables(page, table_bboxes)

            # Should contain text before/after table
            assert "Financial Report" in text or "report" in text.lower()
            # Should NOT contain table data
            assert "Q1" not in text or "Quarter" not in text  # Table content should be excluded

    @pytest.mark.asyncio
    async def test_chunks_have_embeddings(self, pdf_with_table):
        """Test that all chunks have embeddings"""
        result = await process_pdf(pdf_with_table, "test.pdf")

        for chunk in result["chunks"]:
            assert "embedding" in chunk
            assert isinstance(chunk["embedding"], list)
            assert len(chunk["embedding"]) == 384  # all-MiniLM-L6-v2 dimension

    @pytest.fixture
    def pdf_with_empty_table(self):
        """Create a PDF with an empty/malformed table"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []

        styles = getSampleStyleSheet()
        story.append(Paragraph("Document with Empty Table", styles['Heading1']))

        # Create a table with empty cells
        table_data = [
            ["", "", ""],
            ["", "", ""]
        ]

        table = Table(table_data)
        table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        story.append(table)
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

    @pytest.mark.asyncio
    async def test_empty_table_handling(self, pdf_with_empty_table):
        """Test handling of empty tables"""
        result = await process_pdf(pdf_with_empty_table, "empty_table.pdf")

        # Should not crash, and might not detect empty table
        assert result["page_count"] == 1
        assert "chunks" in result


class TestTableExtractionEdgeCases:
    """Test edge cases in table extraction"""

    def test_single_cell_table(self):
        """Test table with single cell"""
        table_data = [["Single Cell"]]
        markdown = table_to_markdown(table_data)
        assert "Single Cell" in markdown

    def test_table_with_special_characters(self):
        """Test table with special characters"""
        table_data = [
            ["Name", "Symbol", "Value"],
            ["Pi", "π", "3.14"],
            ["Alpha", "α", "0.05"]
        ]

        markdown = table_to_markdown(table_data)
        assert "π" in markdown
        assert "α" in markdown

    def test_table_with_long_text(self):
        """Test table with long text in cells"""
        table_data = [
            ["Description", "Details"],
            ["Short", "This is a very long description that spans multiple lines in the original document"],
            ["Medium", "Another description with moderate length"]
        ]

        markdown = table_to_markdown(table_data)
        assert "very long description" in markdown
