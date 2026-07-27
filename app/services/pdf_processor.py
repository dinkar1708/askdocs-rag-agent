"""PDF processing service"""

import io
from typing import Dict, List
import pdfplumber

from app.services.embeddings import generate_embedding, chunk_text, semantic_chunk_text
from app.services.table_processor import (
    extract_tables_from_page,
    get_table_bboxes
)
from app.core.config import settings


async def process_pdf(content: bytes, filename: str) -> Dict:
    """Process PDF file: extract text and tables, chunk, and generate embeddings

    Args:
        content: PDF file bytes
        filename: Original filename

    Returns:
        Dict with page_count and chunks list
    """
    # Read PDF using pdfplumber for better table detection
    pdf_file = io.BytesIO(content)

    all_chunks = []
    page_count = 0

    with pdfplumber.open(pdf_file) as pdf:
        page_count = len(pdf.pages)

        # Extract text and tables from each page
        for page_num, page in enumerate(pdf.pages):
            # Extract tables first
            tables = extract_tables_from_page(page)
            table_bboxes = get_table_bboxes(tables)

            # Add table chunks
            for table in tables:
                embedding = generate_embedding(table["markdown"])
                all_chunks.append({
                    "text": table["markdown"],
                    "chunk_type": "table",
                    "page_number": page_num + 1,
                    "metadata": {
                        "headers": table["headers"],
                        "bbox": table["bbox"]
                    },
                    "embedding": embedding
                })

            # Extract text (excluding table regions)
            text = extract_text_excluding_tables(page, table_bboxes)

            if not text.strip():
                continue

            # Chunk the text from this page (semantic or character-based)
            if settings.SEMANTIC_CHUNKING_ENABLED:
                chunks = semantic_chunk_text(
                    text,
                    page_number=page_num + 1,
                    use_semantic=True,
                    similarity_threshold=settings.SEMANTIC_SIMILARITY_THRESHOLD,
                    min_chunk_size=settings.MIN_CHUNK_SIZE,
                    max_chunk_size=settings.MAX_CHUNK_SIZE
                )
            else:
                chunks = chunk_text(text, page_number=page_num + 1)

            # Generate embeddings for each text chunk
            for chunk in chunks:
                embedding = generate_embedding(chunk["text"])
                chunk["embedding"] = embedding
                chunk["chunk_type"] = "text"
                chunk["metadata"] = {}
                all_chunks.append(chunk)

    return {
        "page_count": page_count,
        "chunks": all_chunks
    }


def extract_text_excluding_tables(page, table_bboxes: List) -> str:
    """Extract text from page, excluding table regions

    Args:
        page: pdfplumber page object
        table_bboxes: List of table bounding boxes to exclude

    Returns:
        Extracted text with tables excluded
    """
    if not table_bboxes:
        # No tables, extract all text
        return page.extract_text() or ""

    # Get page dimensions
    page_height = page.height

    # Extract text by filtering out table regions
    # Strategy: Use extract_words and filter out words in table regions
    words = page.extract_words()

    filtered_words = []
    for word in words:
        # Check if word is in any table bbox
        word_in_table = False
        for bbox in table_bboxes:
            x0, top, x1, bottom = bbox

            # Check if word center is in table bbox
            word_x = (word['x0'] + word['x1']) / 2
            word_y = (word['top'] + word['bottom']) / 2

            if x0 <= word_x <= x1 and top <= word_y <= bottom:
                word_in_table = True
                break

        if not word_in_table:
            filtered_words.append(word)

    # Reconstruct text from filtered words
    # Sort by position (top to bottom, left to right)
    filtered_words.sort(key=lambda w: (w['top'], w['x0']))

    # Build text with basic spacing
    text_lines = []
    current_line = []
    current_top = None

    for word in filtered_words:
        # Check if we're on a new line (tolerance for slight variations)
        if current_top is None or abs(word['top'] - current_top) > 3:
            if current_line:
                text_lines.append(' '.join(current_line))
            current_line = [word['text']]
            current_top = word['top']
        else:
            current_line.append(word['text'])

    # Add last line
    if current_line:
        text_lines.append(' '.join(current_line))

    return '\n'.join(text_lines)
