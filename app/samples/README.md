# Sample PDFs for Testing

This folder contains sample PDF files for testing the document upload feature.

## Files

- `sample_document.pdf` - Simple test PDF (13KB, 1 page) - Basic functionality test
- `company_policy.pdf` - **Generated employee handbook** (6KB, 4 pages) - **Recommended for testing**
  - **Copyright-free** content created specifically for this project
  - Contains realistic company policies (vacation, benefits, code of conduct)
  - Multi-page PDF with real text content
  - Tests full pipeline: extraction → chunking → embeddings
  - Generates 9 chunks with embeddings
  - Source: Generated using `create_sample_pdf.py`

## Usage

Test the PDF upload endpoint:

```bash
# Upload a sample PDF
curl -X POST http://localhost:8000/documents/ \
  -F "file=@samples/sample_document.pdf"

# List uploaded documents
curl http://localhost:8000/documents/

# Get specific document
curl http://localhost:8000/documents/1
```

## Adding Your Own Test PDFs

Place any PDF files in this folder to use them for testing. The API will:
1. Extract text from each page
2. Split text into chunks (500 chars, 50 overlap)
3. Generate embeddings for each chunk
4. Store in PostgreSQL with pgvector

## Best Practices

- Keep test PDFs small (< 10MB)
- Use PDFs with actual text content (not scanned images)
- Test with various PDF formats and structures
