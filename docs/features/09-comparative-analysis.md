# Feature: Comparative Analysis

**What:** Compare multiple documents side-by-side to identify similarities and differences.

**Why it matters:** Quickly understand how policies differ across versions, compare job requirements, or analyze contract variations without manual reading.

---

## User Story

```
As an HR analyst,
I want to compare job requirements across GG9, GG10, and GG11 AI Engineer roles,
So I can understand career progression requirements without reading all three documents.
```

---

## How It Works

### Compare Multiple Documents

**Request:**
```bash
curl -X POST http://localhost:8000/compare \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare the experience requirements",
    "document_ids": [1, 2, 3],
    "aspects": ["qualifications", "experience", "skills"]
  }'
```

**Response:**
```json
{
  "comparison": {
    "aspects": ["qualifications", "experience", "skills"],
    "documents": [
      {
        "document_id": 1,
        "filename": "job_gg9.pdf",
        "data": {
          "qualifications": "Bachelor's degree in Computer Science or related field",
          "experience": "3-5 years in software development",
          "skills": ["Python", "SQL", "Basic ML"]
        }
      },
      {
        "document_id": 2,
        "filename": "job_gg10.pdf",
        "data": {
          "qualifications": "Bachelor's or Master's degree in CS/AI",
          "experience": "5-7 years with 2+ years in ML/AI",
          "skills": ["Python", "TensorFlow", "AWS", "MLOps"]
        }
      },
      {
        "document_id": 3,
        "filename": "job_gg11.pdf",
        "data": {
          "qualifications": "Master's or PhD preferred",
          "experience": "8+ years with 4+ years in AI/ML leadership",
          "skills": ["Python", "TensorFlow", "PyTorch", "AWS", "Team Leadership"]
        }
      }
    ]
  },
  "differences": {
    "experience": {
      "trend": "increasing",
      "range": "3-5 years (GG9) → 8+ years (GG11)"
    },
    "skills": {
      "common": ["Python"],
      "unique_to_gg11": ["PyTorch", "Team Leadership"]
    }
  },
  "summary": "Career progression requires increasing experience (3→8+ years) and expanding from basic ML to leadership and advanced frameworks."
}
```

---

### Compare as Table

**Request:**
```bash
curl -X POST http://localhost:8000/compare/table \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2, 3],
    "aspects": ["experience", "education", "salary"]
  }'
```

**Response (Markdown Table):**
```markdown
| Aspect | GG9 (job_gg9.pdf) | GG10 (job_gg10.pdf) | GG11 (job_gg11.pdf) |
|--------|-------------------|---------------------|---------------------|
| Experience | 3-5 years | 5-7 years (2+ ML/AI) | 8+ years (4+ AI leadership) |
| Education | Bachelor's in CS | Bachelor's/Master's in CS/AI | Master's/PhD preferred |
| Salary | $90k-$120k | $120k-$150k | $150k-$180k |
```

---

### Highlight Differences

**Request:**
```bash
curl -X POST http://localhost:8000/compare/diff \
  -H "Content-Type: application/json" \
  -d '{
    "document_ids": [1, 2],
    "aspect": "benefits"
  }'
```

**Response:**
```json
{
  "document_1": {
    "filename": "handbook_2025.pdf",
    "text": "Employees receive 15 days of paid vacation per year."
  },
  "document_2": {
    "filename": "handbook_2026.pdf",
    "text": "Employees receive 18 days of paid vacation per year."
  },
  "differences": [
    {
      "field": "vacation_days",
      "doc_1_value": "15 days",
      "doc_2_value": "18 days",
      "change": "+3 days (20% increase)"
    }
  ]
}
```

---

## Behind the Scenes

### Comparison Pipeline

```
Multiple Document IDs + Comparison Question
    ↓
1. For each document:
   - Retrieve relevant chunks for each aspect
   - Extract specific information
    ↓
2. Align extracted data across documents
   - Match fields (e.g., "experience" in all docs)
   - Identify common values
   - Find unique values
    ↓
3. Generate comparison:
   - Side-by-side table
   - Difference summary
   - Trend analysis
    ↓
4. LLM synthesizes summary
   "The main difference is experience requirements increase from 3-5 years to 8+ years..."
    ↓
Return structured comparison
```

---

## Use Cases

### Use Case 1: Policy Version Comparison

**Scenario:** Company updates employee handbook annually.

**Question:** "What changed between 2025 and 2026 handbooks?"

**Request:**
```bash
curl -X POST http://localhost:8000/compare \
  -d '{
    "question": "What changed in the vacation and sick leave policies?",
    "document_ids": ["handbook_2025", "handbook_2026"],
    "aspects": ["vacation", "sick_leave", "remote_work"]
  }'
```

**Result:**
```
Changes:
- Vacation: 15 → 18 days (+3 days)
- Sick leave: 10 → 12 days (+2 days)
- Remote work: New policy added (up to 2 days/week)

Sources:
- handbook_2025.pdf, pages 7-8
- handbook_2026.pdf, pages 7-9
```

---

### Use Case 2: Job Grade Comparison

**Scenario:** Employee wants to understand promotion requirements.

**Question:** "What's the difference between GG10 and GG11 roles?"

**Request:**
```bash
curl -X POST http://localhost:8000/compare/table \
  -d '{
    "document_ids": ["job_gg10", "job_gg11"],
    "aspects": ["experience", "skills", "responsibilities", "salary"]
  }'
```

**Result:**
| Aspect | GG10 | GG11 |
|--------|------|------|
| Experience | 5-7 years | 8+ years |
| Skills | Python, TensorFlow, AWS | + PyTorch, Team Leadership |
| Responsibilities | Individual contributor | Technical leadership |
| Salary | $120k-$150k | $150k-$180k |

---

### Use Case 3: Contract Terms Analysis

**Scenario:** Legal team comparing NDA templates.

**Question:** "How do termination clauses differ across our NDA templates?"

**Request:**
```bash
curl -X POST http://localhost:8000/compare \
  -d '{
    "question": "Compare termination notice periods",
    "document_ids": ["nda_v1", "nda_v2", "nda_v3"],
    "aspects": ["termination_notice", "duration"]
  }'
```

**Result:**
```
Termination Notice Periods:
- NDA v1: 30 days written notice
- NDA v2: 60 days written notice
- NDA v3: 90 days written notice

Duration:
- All versions: 2 years from signing
```

---

## Configuration

### Comparison Model

```bash
# .env
COMPARISON_LLM_PROVIDER=gemini  # or ollama, azure_openai
COMPARISON_DETAIL_LEVEL=high    # low, medium, high
```

**Detail levels:**
- **Low:** Simple side-by-side values
- **Medium:** Values + brief differences
- **High:** Detailed analysis with trends and implications

---

### Max Documents to Compare

```bash
# .env
MAX_COMPARE_DOCUMENTS=5  # Limit to prevent overwhelming comparisons
```

---

## Advanced Features

### Trend Analysis

**For time-series documents (e.g., annual policies):**

```bash
curl -X POST http://localhost:8000/compare/trend \
  -d '{
    "document_ids": ["policy_2022", "policy_2023", "policy_2024", "policy_2025"],
    "aspect": "vacation_days"
  }'
```

**Response:**
```json
{
  "aspect": "vacation_days",
  "trend": {
    "2022": 12,
    "2023": 15,
    "2024": 15,
    "2025": 18
  },
  "analysis": "Vacation days increased 50% from 2022 to 2025, with major increase in 2023 (+3 days) and 2025 (+3 days).",
  "chart_url": "/compare/trend/chart_abc123.png"
}
```

---

### Gap Analysis

**Find what's in one document but not others:**

```bash
curl -X POST http://localhost:8000/compare/gap \
  -d '{
    "reference_document_id": "job_gg11",
    "compare_to_documents": ["job_gg9", "job_gg10"]
  }'
```

**Response:**
```json
{
  "unique_to_reference": [
    "Team leadership experience required",
    "PhD preferred",
    "Experience with PyTorch"
  ],
  "missing_from_reference": [],
  "summary": "GG11 role uniquely requires team leadership, advanced degree, and PyTorch expertise."
}
```

---

## Export Comparison

### Export as PDF Report

```bash
curl -X POST http://localhost:8000/compare/export \
  -d '{
    "comparison_id": "cmp_abc123",
    "format": "pdf"
  }'
```

**Generates:** Professional PDF report with:
- Side-by-side comparison table
- Highlighted differences
- Summary section
- Source citations

---

### Export as Spreadsheet

```bash
curl -X POST http://localhost:8000/compare/export \
  -d '{
    "comparison_id": "cmp_abc123",
    "format": "xlsx"
  }'
```

---

## Real-World Example: Career Path Analysis

**Company:** Tech company with 5 engineering grades (GG7-GG11)

**Use Case:** Employees want to understand career progression.

**Implementation:**
1. Upload all 5 job description PDFs
2. Create comparison:
   ```bash
   curl -X POST http://localhost:8000/compare/table \
     -d '{
       "document_ids": [7, 8, 9, 10, 11],
       "aspects": ["experience", "education", "salary", "skills", "responsibilities"]
     }'
   ```
3. Generate PDF report
4. Publish to internal wiki

**Result:**
- Employees clearly see promotion requirements
- HR answers fewer career path questions
- Hiring managers use for salary negotiations

---

## Comparison Algorithms

### Field Alignment

**Challenge:** Documents use different terminology.

**Example:**
- Doc 1: "Years of experience: 5-7"
- Doc 2: "Required experience: 5 to 7 years"
- Doc 3: "Experience needed: 5-7 yrs"

**Solution:** LLM normalizes to common format.

**Result:** All align to "5-7 years"

---

### Semantic Similarity

**Detect equivalent but differently worded content:**

**Doc 1:** "Employees receive 15 days of paid vacation"
**Doc 2:** "Staff get 3 weeks of annual leave"

**Analysis:** 15 days ≈ 3 weeks (semantically equivalent)

---

## Limitations & Future Plans

**Current limitations:**
- Max 5 documents per comparison (performance constraint)
- Text-only comparison (no image/chart comparison)
- English-optimized (multilingual works but less accurate)

**Future enhancements:**
- [ ] Visual diff (highlighting changes in PDF)
- [ ] Automatic version detection (identify 2025 vs 2026 automatically)
- [ ] Comparison templates (pre-built for common use cases)
- [ ] Multi-language comparison
- [ ] Chart/table comparison (understand data in images)
- [ ] Change tracking over time (Git-like diff for documents)

---

## API Reference

### POST /compare

**Request:**
```json
{
  "question": "string",
  "document_ids": [1, 2, 3],
  "aspects": ["string"]
}
```

**Response:**
```json
{
  "comparison": {},
  "differences": {},
  "summary": "string"
}
```

---

### POST /compare/table

**Request:**
```json
{
  "document_ids": [1, 2, 3],
  "aspects": ["string"]
}
```

**Response:** Markdown table

---

### POST /compare/diff

**Request:**
```json
{
  "document_ids": [1, 2],
  "aspect": "string"
}
```

**Response:**
```json
{
  "document_1": {},
  "document_2": {},
  "differences": []
}
```

---

## Next Steps

→ [Structured Extraction](08-structured-extraction.md) - Extract fields before comparing
→ [Advanced Filters](10-advanced-filters.md) - Filter documents by metadata before comparison
