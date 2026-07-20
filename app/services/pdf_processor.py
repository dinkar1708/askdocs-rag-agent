"""PDF processing service"""

import io
from typing import Dict, List
from PyPDF2 import PdfReader

from app.services.embeddings import generate_embedding, chunk_text


async def process_pdf(content: bytes, filename: str) -> Dict:
    """Process PDF file: extract text, chunk, and generate embeddings

    Args:
        content: PDF file bytes
        filename: Original filename

    Returns:
        Dict with page_count and chunks list
    """
    # Read PDF
    pdf_file = io.BytesIO(content)
    reader = PdfReader(pdf_file)

    page_count = len(reader.pages)
    all_chunks = []

    # Extract text from each page
    for page_num in range(page_count):
        page = reader.pages[page_num]
        text = page.extract_text()

        if not text.strip():
            continue

        # Chunk the text from this page
        chunks = chunk_text(text, page_number=page_num + 1)

        # Generate embeddings for each chunk
        for chunk in chunks:
            embedding = generate_embedding(chunk["text"])
            chunk["embedding"] = embedding
            all_chunks.append(chunk)

    return {
        "page_count": page_count,
        "chunks": all_chunks
    }
