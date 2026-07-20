# Feature: Structured Data Extraction

**What:** Extract key-value pairs from documents (job requirements, salary, skills, etc.) into structured JSON.

**Why it matters:** Auto-parse documents to extract specific fields without manual reading. Perfect for job descriptions, invoices, contracts, and forms.

---

## User Story

```
As an HR manager,
I want to automatically extract job requirements (title, skills, experience, salary) from job description PDFs,
So I can populate our job database without manual data entry.
```

---

## How It Works

### Extract with Custom Schema

**Request:**
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_123",
    "schema": {
      "title": "string",
      "experience_years": "number",
      "required_skills": "array",
      "location": "string",
      "salary_range": "string"
    }
  }'
```

**Response:**
```json
{
  "document_id": "doc_123",
  "extracted_data": {
    "title": "Senior AI Engineer (GG11)",
    "experience_years": 8,
    "required_skills": [
      "Python",
      "Machine Learning",
      "TensorFlow",
      "AWS",
      "Docker"
    ],
    "location": "Remote / New York",
    "salary_range": "$150,000 - $180,000"
  },
  "confidence": 0.92,
  "sources": [
    {"page": 1, "field": "title"},
    {"page": 1, "field": "experience_years"},
    {"page": 2, "field": "required_skills"}
  ]
}
```

---

### Batch Extraction

**Request:**
```bash
curl -X POST http://localhost:8000/extract/batch \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": ["doc_123", "doc_456", "doc_789"],
    "schema": {
      "title": "string",
      "experience_years": "number",
      "required_skills": "array"
    }
  }'
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc_123",
      "filename": "job_gg11.pdf",
      "extracted_data": {
        "title": "Senior AI Engineer (GG11)",
        "experience_years": 8,
        "required_skills": ["Python", "ML", "AWS"]
      }
    },
    {
      "document_id": "doc_456",
      "filename": "job_gg10.pdf",
      "extracted_data": {
        "title": "AI Developer (GG10)",
        "experience_years": 5,
        "required_skills": ["Python", "ML"]
      }
    }
  ],
  "total": 2,
  "export_url": "/extract/batch/export/batch_abc123.csv"
}
```

---

## Behind the Scenes

### Extraction Pipeline

```
Document ID
    ↓
1. Retrieve document chunks from vector DB
    ↓
2. Build extraction prompt with schema
   "Extract these fields from the document:
    - title (string)
    - experience_years (number)
    - required_skills (array)

    Document text: [chunks]"
    ↓
3. LLM extracts structured data
    ↓
4. Validate against schema (type checking)
    ↓
5. Track source pages for each field
    ↓
Return structured JSON
```

---

## Use Cases

### Use Case 1: Job Description Database

**Problem:** HR team has 50 job description PDFs, needs to populate job board database.

**Solution:**
```bash
# Upload all PDFs
for file in job_descriptions/*.pdf; do
  curl -X POST http://localhost:8000/documents -F "file=@$file"
done

# Batch extract
curl -X POST http://localhost:8000/extract/batch \
  -d '{
    "document_ids": [1,2,3,...,50],
    "schema": {
      "title": "string",
      "department": "string",
      "experience_years": "number",
      "required_skills": "array",
      "education": "string",
      "location": "string",
      "salary_range": "string"
    }
  }'

# Export to CSV for database import
curl http://localhost:8000/extract/batch/export/batch_abc123.csv > jobs.csv
```

**Result:** 50 job descriptions processed in 2 minutes vs 4 hours manual entry.

---

### Use Case 2: Contract Metadata Extraction

**Schema:**
```json
{
  "contract_type": "string",
  "parties": "array",
  "effective_date": "string",
  "expiry_date": "string",
  "termination_notice_days": "number",
  "governing_law": "string"
}
```

**Application:** Build searchable contract database with structured metadata.

---

### Use Case 3: Invoice Processing

**Schema:**
```json
{
  "invoice_number": "string",
  "invoice_date": "string",
  "vendor_name": "string",
  "total_amount": "number",
  "due_date": "string",
  "line_items": "array"
}
```

**Application:** Automate accounts payable data entry.

---

## Supported Field Types

### string
```json
{
  "title": "string"
}
// Extracts: "Senior AI Engineer"
```

### number
```json
{
  "experience_years": "number"
}
// Extracts: 8
```

### array
```json
{
  "required_skills": "array"
}
// Extracts: ["Python", "TensorFlow", "AWS"]
```

### boolean
```json
{
  "remote_eligible": "boolean"
}
// Extracts: true
```

### object (nested)
```json
{
  "salary": {
    "min": "number",
    "max": "number",
    "currency": "string"
  }
}
// Extracts: {"min": 150000, "max": 180000, "currency": "USD"}
```

---

## Configuration

### Extraction Confidence Threshold

```bash
# .env
EXTRACTION_CONFIDENCE_THRESHOLD=0.8
```

**Effect:**
- If extraction confidence < 0.8, return null for that field
- Prevents low-quality extractions

---

### Extraction Model

```bash
# .env
EXTRACTION_LLM_PROVIDER=gemini  # or ollama, azure_openai
```

**Trade-off:**
- **Gemini:** Fast, cheap, good quality
- **GPT-4:** Higher quality, more expensive
- **Ollama:** Free, slower, variable quality

---

## Validation & Error Handling

### Type Validation

**Schema:**
```json
{
  "experience_years": "number"
}
```

**Document says:** "8+ years of experience"

**Extraction:** `8`

**Validation:** ✅ Pass (valid number)

---

**Document says:** "Several years of experience"

**Extraction:** `null`

**Validation:** ⚠️ Warning (couldn't extract number)

**Response:**
```json
{
  "experience_years": null,
  "warnings": ["Could not extract number from 'Several years of experience'"]
}
```

---

### Handling Missing Fields

**If field not in document:**
```json
{
  "salary_range": null,
  "sources": []
}
```

---

## Export Formats

### CSV Export

```bash
curl http://localhost:8000/extract/batch/export/batch_abc123.csv
```

**Output:**
```csv
document_id,filename,title,experience_years,required_skills
doc_123,job_gg11.pdf,Senior AI Engineer,8,"Python,ML,AWS"
doc_456,job_gg10.pdf,AI Developer,5,"Python,ML"
```

---

### Excel Export

```bash
curl http://localhost:8000/extract/batch/export/batch_abc123.xlsx
```

---

### JSON Export

```bash
curl http://localhost:8000/extract/batch/export/batch_abc123.json
```

---

## Real-World Example: Job Board Automation

**Company:** Tech recruitment agency

**Challenge:**
- Receive 100+ job descriptions/week from clients
- Need to post to job board with structured data
- Manual data entry takes 5 minutes per job

**Solution:**
1. Clients email PDFs to jobs@company.com
2. Auto-upload to askdocs via email integration
3. Batch extraction with job schema
4. Auto-populate job board database
5. Human review edge cases only

**Result:**
- Time per job: 5 minutes → 30 seconds
- Accuracy: 95%+ (with human review for low confidence)
- Cost: $0.002 per extraction (Gemini API)

---

## Limitations & Future Plans

**Current limitations:**
- Single document extraction (no cross-document aggregation)
- Schema must be predefined (no auto-discovery)
- English-optimized (multilingual works but less accurate)

**Future enhancements:**
- [ ] Auto-generate schema from document analysis
- [ ] Cross-document field aggregation (e.g., "Compare salaries across all job docs")
- [ ] Multi-language optimization
- [ ] Custom extraction rules (regex, patterns)
- [ ] Confidence explanation (why field couldn't be extracted)

---

## API Reference

### POST /extract

Extract structured data from a single document.

**Request:**
```json
{
  "document_id": "string",
  "schema": {
    "field_name": "type"
  }
}
```

**Response:**
```json
{
  "document_id": "string",
  "extracted_data": {},
  "confidence": 0.0-1.0,
  "sources": [],
  "warnings": []
}
```

---

### POST /extract/batch

Extract structured data from multiple documents.

**Request:**
```json
{
  "document_ids": ["string"],
  "schema": {},
  "export_format": "csv|xlsx|json"
}
```

**Response:**
```json
{
  "batch_id": "string",
  "results": [],
  "total": 0,
  "export_url": "string"
}
```

---

## Next Steps

→ [Comparative Analysis](09-comparative-analysis.md) - Compare fields across documents
→ [Advanced Filters](10-advanced-filters.md) - Filter by extracted metadata
