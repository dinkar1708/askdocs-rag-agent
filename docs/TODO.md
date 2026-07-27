
---

## 📄 DOCUMENTED (Ready to Implement)

- [ ] **Feature 09:** Comparative Analysis (docs done, ready to implement)
- [ ] **Feature 10:** Advanced Filters & Metadata (docs done, ready to implement)
- [ ] **Feature 11:** Document Summarization (docs done, ready to implement)

---

## ⏳ TODO (Not Started)

### Advanced RAG - Next Phases
- [ ] **Phase 4:** Hybrid Search (BM25 + Semantic)
  - Add keyword-based retrieval alongside vector search
  - Weighted fusion of BM25 and semantic scores
  - Better handling of exact matches and acronyms

- [ ] **Phase 5:** Multimodal Support
  - Extract and describe images/diagrams using vision models
  - OCR for image-based tables
  - Preserve visual context in answers

- [ ] **Phase 6:** Excel/CSV Ingestion
  - Parse spreadsheets with multiple sheets
  - Preserve formulas and relationships
  - Query numeric data with aggregations

### High Priority Features
- [ ] **Feature 12:** Multi-format Document Support (Word, PowerPoint, HTML, Markdown)
- [ ] **Feature 13:** Query Templates & Saved Queries
- [ ] **Feature 14:** Batch Q&A Processing

### Phase 2: Medium Priority
- [ ] **Feature 16:** Analytics Dashboard
- [ ] **Feature 17:** Answer Feedback & Quality Loop
- [ ] **Feature 18:** Role-Based Access Control (RBAC)
- [ ] **Feature 19:** Multi-Language Support
- [ ] **Feature 20:** Graph-Based Knowledge Extraction
- [ ] **Feature 21:** Real-time Document Monitoring

### Infrastructure & DevOps
- [ ] API Authentication & Rate Limiting
- [ ] Redis caching for embeddings
- [ ] Background job queue (Celery + Redis)
- [ ] Structured logging & monitoring
- [ ] Increase test coverage to 80%+

---

## 📌 Notes

**Documentation Location:** `docs/features/`
**Implementation Priority:** Features 08-11 (documented, ready to implement)

**To start a feature:**
1. Read `docs/features/XX-feature-name.md`
2. Create branch: `feature/XX-feature-name`
3. Implement with tests
4. Mark as DONE above

---
