# Feature: Document Summarization

**What:** Auto-generate executive summaries of uploaded documents with key points and page references.

**Why it matters:** Quickly understand document content without reading the entire document. Perfect for job descriptions, contracts, policies, and reports.

---

## User Story

```
As a hiring manager,
I want a 1-paragraph summary of each job description,
So I can quickly understand the role without reading 3 pages of requirements.
```

---

## How It Works

### Generate Summary on Demand

**Request:**
```bash
curl -X POST http://localhost:8000/documents/doc_123/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "summary_type": "executive",
    "max_length": 200
  }'
```

**Response:**
```json
{
  "document_id": "doc_123",
  "filename": "job_gg11.pdf",
  "summary": "This role is for a Senior AI Engineer (GG11) requiring 8+ years of experience with 4+ years in AI/ML leadership. Key responsibilities include leading AI initiatives, mentoring junior engineers, and architecting scalable ML systems. Required skills: Python, TensorFlow, PyTorch, AWS. Salary range: $150k-$180k. Remote work eligible.",
  "summary_type": "executive",
  "word_count": 52,
  "key_points": [
    {
      "point": "8+ years experience required with 4+ in AI/ML leadership",
      "page": 1
    },
    {
      "point": "Lead AI initiatives and mentor junior engineers",
      "page": 2
    },
    {
      "point": "Required: Python, TensorFlow, PyTorch, AWS",
      "page": 1
    },
    {
      "point": "Salary: $150k-$180k, remote eligible",
      "page": 3
    }
  ],
  "generated_at": "2026-07-20T10:30:00Z"
}
```

---

### Get Cached Summary

**Request:**
```bash
curl http://localhost:8000/documents/doc_123/summary
```

**Response:**
```json
{
  "document_id": "doc_123",
  "summary": "...",
  "cached": true,
  "generated_at": "2026-07-20T10:30:00Z"
}
```

**Note:** Summaries are cached to avoid regenerating on every request.

---

## Summary Types

### Executive Summary (Brief)

**Max length:** 100-200 words
**Use case:** Quick overview for decision makers

**Example:**
```
This Senior AI Engineer role (GG11) requires 8+ years of experience
including 4+ years in AI/ML leadership. Responsibilities include
leading AI initiatives, mentoring teams, and architecting ML systems.
Requires Python, TensorFlow, PyTorch, AWS expertise. Salary: $150k-$180k.
```

---

### Detailed Summary

**Max length:** 300-500 words
**Use case:** Comprehensive overview without reading full document

**Example:**
```
Role Overview:
This position is for a Senior AI Engineer (GG11) responsible for
leading advanced AI/ML initiatives across the organization.

Requirements:
- 8+ years software engineering experience
- 4+ years in AI/ML with leadership responsibilities
- Master's or PhD preferred
- Expert in Python, TensorFlow, PyTorch
- Cloud platform experience (AWS, Azure, or GCP)
- Team leadership and mentoring experience

Responsibilities:
- Design and architect scalable ML systems
- Lead AI research and development initiatives
- Mentor junior and mid-level engineers
- Collaborate with product and business teams
- Stay current with AI/ML advancements

Compensation & Benefits:
- Salary range: $150,000 - $180,000
- Remote work eligible (up to 3 days/week)
- Comprehensive benefits package
- Professional development budget
```

---

### Key Points Only

**Format:** Bulleted list
**Use case:** Scannable highlights

**Example:**
```
• 8+ years experience (4+ in AI/ML leadership)
• Master's/PhD preferred
• Required: Python, TensorFlow, PyTorch, AWS
• Lead AI initiatives and mentor teams
• $150k-$180k salary
• Remote eligible
```

---

### Section Summaries

**Format:** Summary per section/topic
**Use case:** Structured documents with clear sections

**Example:**
```json
{
  "sections": [
    {
      "section": "Qualifications",
      "summary": "8+ years experience, Master's/PhD preferred, 4+ years AI/ML leadership",
      "pages": [1]
    },
    {
      "section": "Technical Skills",
      "summary": "Python, TensorFlow, PyTorch, AWS, MLOps, Docker, Kubernetes",
      "pages": [1, 2]
    },
    {
      "section": "Responsibilities",
      "summary": "Lead AI initiatives, architect ML systems, mentor engineers, collaborate cross-functionally",
      "pages": [2]
    },
    {
      "section": "Compensation",
      "summary": "$150k-$180k, remote eligible, comprehensive benefits",
      "pages": [3]
    }
  ]
}
```

---

## Behind the Scenes

### Summarization Pipeline

```
Document ID
    ↓
1. Retrieve all chunks for document
    ↓
2. Extract document structure (identify sections, headings)
    ↓
3. Build summarization prompt:
   "Summarize this job description in 200 words or less.
    Focus on: qualifications, responsibilities, compensation.

    Document text: [all chunks]"
    ↓
4. LLM generates summary
    ↓
5. Extract key points with page references
    ↓
6. Cache summary in database
    ↓
Return summary + key points
```

---

## Use Cases

### Use Case 1: Job Description Database

**Scenario:** Recruiters need to quickly scan 50 job openings.

**Without summaries:**
- Open each PDF
- Read 2-3 pages per job
- Time: 5 minutes × 50 = 4+ hours

**With summaries:**
```bash
# Generate summaries for all jobs
for doc_id in {1..50}; do
  curl -X POST http://localhost:8000/documents/$doc_id/summarize \
    -d '{"summary_type": "executive", "max_length": 150}'
done

# View summaries
curl http://localhost:8000/documents?include_summary=true
```

**Result:** Scan 50 jobs in 15 minutes (read summaries, deep-dive on 5-10 matches).

---

### Use Case 2: Contract Review

**Scenario:** Legal team receives 20-page vendor contract.

**Request:**
```bash
curl -X POST http://localhost:8000/documents/contract_123/summarize \
  -d '{
    "summary_type": "sections",
    "sections": ["parties", "scope", "payment_terms", "termination", "liability"]
  }'
```

**Response:**
```json
{
  "sections": [
    {
      "section": "Parties",
      "summary": "Agreement between Acme Corp (Client) and TechVendor Inc (Provider)",
      "pages": [1]
    },
    {
      "section": "Payment Terms",
      "summary": "$50k/month, net-30 payment terms, annual increase capped at 5%",
      "pages": [5, 6]
    },
    {
      "section": "Termination",
      "summary": "Either party may terminate with 90 days written notice, early termination penalty: 3 months fees",
      "pages": [12]
    }
  ]
}
```

**Result:** Legal team reviews summary first, then deep-dives into specific sections.

---

### Use Case 3: Policy Updates

**Scenario:** HR updates employee handbook, needs to communicate changes.

**Request:**
```bash
# Summarize what changed
curl -X POST http://localhost:8000/documents/compare/summary \
  -d '{
    "document_ids": ["handbook_2025", "handbook_2026"],
    "focus": "changes"
  }'
```

**Response:**
```
Key Changes in 2026 Handbook:
• Vacation days increased from 15 to 18 days (+20%)
• Remote work policy added (up to 2 days/week)
• Parental leave extended from 12 to 16 weeks
• New professional development budget: $2,000/year
```

**Result:** HR sends summary to all employees highlighting updates.

---

## Summarization Options

### Control Length

```json
{
  "max_length": 200,  // Word count
  "min_length": 50
}
```

---

### Focus Areas

```json
{
  "focus": ["qualifications", "responsibilities", "compensation"]
}
```

**Effect:** Summary emphasizes specified topics.

---

### Tone

```json
{
  "tone": "formal"  // or "casual", "technical"
}
```

---

### Language

```json
{
  "language": "en"  // or "es", "fr", "de", "ja"
}
```

**Use case:** Generate summaries in different languages for global teams.

---

## Auto-Summarization on Upload

### Enable Auto-Summarization

```bash
# .env
AUTO_SUMMARIZE_ON_UPLOAD=true
SUMMARY_TYPE=executive
SUMMARY_MAX_LENGTH=200
```

**Effect:** Every uploaded document automatically gets a summary generated.

---

**Upload with auto-summary:**
```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@job.pdf"
```

**Response:**
```json
{
  "id": "doc_123",
  "filename": "job.pdf",
  "summary": "This role is for a Senior AI Engineer...",
  "key_points": [...]
}
```

---

## Batch Summarization

**Request:**
```bash
curl -X POST http://localhost:8000/documents/summarize/batch \
  -d '{
    "document_ids": [1, 2, 3, 4, 5],
    "summary_type": "executive",
    "max_length": 150
  }'
```

**Response:**
```json
{
  "batch_id": "batch_abc123",
  "status": "processing",
  "total": 5,
  "completed": 0,
  "results_url": "/documents/summarize/batch/batch_abc123"
}
```

**Check progress:**
```bash
curl http://localhost:8000/documents/summarize/batch/batch_abc123
```

**Result:**
```json
{
  "batch_id": "batch_abc123",
  "status": "completed",
  "total": 5,
  "completed": 5,
  "results": [
    {"document_id": 1, "summary": "..."},
    {"document_id": 2, "summary": "..."},
    ...
  ]
}
```

---

## Export Summaries

### CSV Export

```bash
curl http://localhost:8000/documents/summaries/export.csv
```

**Output:**
```csv
document_id,filename,summary,word_count
doc_123,job_gg11.pdf,"This role is for a Senior AI Engineer...",52
doc_456,job_gg10.pdf,"This position is for an AI Developer...",48
```

---

### PDF Report

```bash
curl -X POST http://localhost:8000/documents/summaries/report \
  -d '{
    "document_ids": [1, 2, 3],
    "format": "pdf",
    "include_key_points": true
  }'
```

**Generates:** Professional PDF with summaries + key points for all documents.

---

## Configuration

### Summarization Model

```bash
# .env
SUMMARIZATION_LLM_PROVIDER=gemini  # or ollama, azure_openai
```

---

### Cache Settings

```bash
# .env
SUMMARY_CACHE_TTL=86400  # Cache for 24 hours
SUMMARY_CACHE_INVALIDATE_ON_UPDATE=true  # Regenerate if doc updated
```

---

## Quality Metrics

### Evaluate Summary Quality

```bash
curl -X POST http://localhost:8000/documents/doc_123/summary/evaluate
```

**Response:**
```json
{
  "factual_accuracy": 0.95,  // Does summary match document?
  "coverage": 0.88,  // Does it cover key points?
  "conciseness": 0.92,  // Is it concise without fluff?
  "readability_score": 68  // Flesch reading ease
}
```

---

## Real-World Example: Investment Research

**Company:** VC firm reviewing 100 startup pitch decks/month

**Problem:**
- Each deck is 15-20 pages
- Partners need to quickly identify promising companies
- Reading all decks takes 30+ hours

**Solution:**
1. Upload all pitch decks to askdocs
2. Auto-generate executive summaries (200 words)
3. Export summaries to spreadsheet
4. Partners review summaries (5 minutes per deck = 8 hours)
5. Request full deck review for 10-15 promising startups

**Result:**
- Time savings: 30 hours → 8 hours (73% reduction)
- Better focus on high-potential startups
- Faster decision making

---

## Limitations & Future Plans

**Current limitations:**
- Text-only summarization (no image/chart understanding)
- Single-document summaries (no cross-document synthesis)
- English-optimized (multilingual works but less accurate)

**Future enhancements:**
- [ ] Multi-document synthesis (summarize all job descriptions together)
- [ ] Image/chart understanding (summarize visual content)
- [ ] Custom summary templates (per document type)
- [ ] Extractive + abstractive summarization (highlight exact quotes + generated summary)
- [ ] Bullet point summaries with auto-formatting
- [ ] Timeline summaries (for documents with dates/events)
- [ ] Sentiment analysis in summaries (positive/negative/neutral tone)

---

## API Reference

### POST /documents/{id}/summarize

Generate summary for a document.

**Request:**
```json
{
  "summary_type": "executive|detailed|key_points|sections",
  "max_length": 200,
  "focus": ["topic1", "topic2"],
  "tone": "formal|casual|technical",
  "language": "en"
}
```

**Response:**
```json
{
  "document_id": "string",
  "summary": "string",
  "key_points": [],
  "word_count": 0,
  "generated_at": "timestamp"
}
```

---

### GET /documents/{id}/summary

Retrieve cached summary.

**Response:**
```json
{
  "summary": "string",
  "cached": true,
  "generated_at": "timestamp"
}
```

---

### POST /documents/summarize/batch

Batch summarize multiple documents.

**Request:**
```json
{
  "document_ids": [1, 2, 3],
  "summary_type": "executive",
  "max_length": 200
}
```

**Response:**
```json
{
  "batch_id": "string",
  "status": "processing|completed",
  "results_url": "string"
}
```

---

## Next Steps

→ [Structured Extraction](08-structured-extraction.md) - Extract specific fields from documents
→ [Comparative Analysis](09-comparative-analysis.md) - Compare multiple documents
→ [Grounded Q&A](02-grounded-qa.md) - Ask detailed questions about documents
