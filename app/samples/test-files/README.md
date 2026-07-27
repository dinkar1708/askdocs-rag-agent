# Test Files for RAG System

This directory contains sample documents for testing different ingestion and retrieval scenarios.

## File Inventory

### 1. Plain Text PDF
**File:** `plain-text.pdf` (6.8 KB)
**Purpose:** Baseline - simple text extraction
**Contents:** Employee handbook with comprehensive policies:
- Company overview (TechCorp Solutions)
- Working hours and attendance policies
- Leave policy (20 days PTO annually)
- Employee benefits (health insurance, 401k, professional development)
- Code of conduct
- Remote work policy (up to 3 days/week)
- Performance reviews and termination policies
- Contact information

**Expected behavior:** Should work perfectly with current implementation. Tests basic text extraction and retrieval.

### 2. PDF with Tables
**File:** `financial-report-with-tables.pdf` (6.8 KB)
**Purpose:** Test table structure preservation
**Contents:** TechCorp Solutions Q2 2024 Quarterly Financial Report with:
- Executive summary
- Consolidated Statement of Income (revenue, expenses, net income)
- Consolidated Balance Sheet (assets, liabilities, equity)
- Consolidated Statement of Cash Flows (operating, investing, financing activities)
- Year-over-year comparisons with Q2 2023

**Current limitation:** Table structure may be lost, numbers extracted as plain text
**After Phase 2:** Tables should be preserved as markdown/structured data

### 3. PDF with Diagrams
**File:** `technical-manual-with-diagrams.pdf` (6.0 KB)
**Purpose:** Test multimodal ingestion with diagrams
**Contents:** CloudServer Pro X500 Technical Manual with:
- System architecture diagram (load balancer, app servers, database)
- Hardware specifications (CPU, RAM, storage, network)
- Installation process (physical installation, BIOS config, OS installation)
- Network configuration diagram (internet, firewall, DMZ, internal network)
- Troubleshooting guide (boot issues, network problems, performance, database)

**Current limitation:** Diagrams may be ignored or not properly described
**After Phase 5:** Diagrams should have captions and be indexed for retrieval

### 4. Excel File
**File:** `product-catalog.xlsx` (8.2 KB)
**Purpose:** Test structured data ingestion
**Contents:** Product catalog with 30 products across multiple sheets:
- **Products Sheet:** Product Name, SKU, Price, Category, Stock Level
- **Category Summary Sheet:** Product counts and values by category
- **Inventory Status Sheet:** Products needing reorder (stock < 100)
- Categories: Electronics, Accessories, Office Supplies, Furniture, Storage

**Current limitation:** May not be supported or structure lost
**After Phase 6:** Should be queryable ("What products cost under $50?", "Show Electronics category")

### 5. Ground Truth Test Queries
**File:** `ground_truth.json` (4.5 KB)
**Purpose:** Test queries with expected answers for evaluation
**Contents:** 20 test queries across all document types:
- 5 queries for plain-text.pdf (benefits, policies)
- 5 queries for financial-report-with-tables.pdf (financial metrics, analysis)
- 5 queries for product-catalog.xlsx (product info, inventory)
- 5 queries for technical-manual-with-diagrams.pdf (specs, configuration, troubleshooting)

Each query includes:
- Question text
- Expected answer
- Category (benefits, policy, financial_metrics, etc.)

**Use this for:** Automated testing, RAG evaluation, measuring retrieval quality

## Creating Test Files

All test files have been generated using the `create_test_files.py` script in this directory.

To regenerate the files:
```bash
# Activate virtual environment
source venv/bin/activate

# Run the generation script
python app/samples/test-files/create_test_files.py
```

The script creates:
- PDF files using reportlab library
- Excel files using pandas and openpyxl
- JSON ground truth file with test queries and expected answers

All files are synthetic and contain no real or sensitive data.

## Testing Checklist

After implementing each phase, test with these files:

- [ ] Can upload file without errors?
- [ ] Text extracted correctly?
- [ ] Tables preserved (Phase 2+)?
- [ ] Images indexed (Phase 5+)?
- [ ] Can answer questions about content?
- [ ] Citations point to correct pages?
- [ ] Retrieval quality acceptable?

## Sample Queries

### For plain-text.pdf (Employee Handbook)
- "How many days of PTO do full-time employees get per year?"
- "What are the standard working hours?"
- "How much does the company match for 401(k)?"
- "How many days per week can employees work remotely?"
- "What is the professional development budget?"

### For financial-report-with-tables.pdf
- "What was the total revenue in Q2 2024?"
- "What was the net income for Q2 2024?"
- "How much did revenue increase year-over-year?"
- "What was the total cash at the end of Q2 2024?"
- "What were the operating expenses in Q2 2024?"

### For technical-manual-with-diagrams.pdf
- "What are the RAM specifications for CloudServer Pro X500?"
- "How many cores does the CPU have?"
- "What is the recommended DMZ subnet?"
- "What should I do if the server won't boot?"
- "What storage configuration does the server use?"

### For product-catalog.xlsx
- "What is the price of the Mechanical Keyboard?"
- "How many Wireless Mouse units are in stock?"
- "What products are in the Furniture category?"
- "What is the most expensive product?"
- "Which products have stock level below 100?"

## Ground Truth Dataset

The `ground_truth.json` file contains 20 test queries with expected answers for automated evaluation:

```json
{
  "document_name.pdf": [
    {
      "query": "Question text",
      "expected_answer": "Expected answer",
      "category": "category_name"
    }
  ]
}
```

Each entry includes:
- **query**: The question to ask the RAG system
- **expected_answer**: The correct answer based on document content
- **category**: Type of query (benefits, policy, financial_metrics, inventory, etc.)

Use this for:
- Automated testing and CI/CD integration
- RAG evaluation metrics (precision, recall, answer quality)
- Regression testing after system changes
- Comparing different retrieval strategies
