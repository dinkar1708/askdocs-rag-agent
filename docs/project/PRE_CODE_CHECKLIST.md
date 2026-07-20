# Pre-Code Checklist

Essential items to complete before writing code.

---

## Documentation Complete

### Architecture & Design
- [x] System architecture documented ([ARCHITECTURE.md](ARCHITECTURE.md))
- [x] Database schema designed ([DATABASE_SCHEMA.md](DATABASE_SCHEMA.md))
- [x] API endpoints defined ([API.md](API.md))
- [x] Configuration documented ([CONFIGURATION.md](CONFIGURATION.md))

### Security
- [x] Security checklist created ([security/SECURITY_CHECKLIST.md](security/SECURITY_CHECKLIST.md))
- [x] Secrets management guide ([security/SECRETS_MANAGEMENT.md](security/SECRETS_MANAGEMENT.md))
- [x] API security guidelines ([security/API_SECURITY.md](security/API_SECURITY.md))

### Features
- [x] All 7 features documented ([features/](features/))
- [x] User-facing documentation complete
- [x] MCP integration planned ([MCP.md](MCP.md))

### Quality & Testing
- [x] Prompts defined ([PROMPTS.md](PROMPTS.md))
- [x] Evaluation plan created ([EVALUATION_PLAN.md](EVALUATION_PLAN.md))
- [x] Testing strategy documented ([testing/TESTING.md](testing/TESTING.md))

### Deployment
- [x] GCP deployment guide ([deployment/GCP.md](deployment/GCP.md))
- [x] Azure deployment guide ([deployment/AZURE.md](deployment/AZURE.md))
- [x] Local development setup ([LOCAL_DEVELOPMENT.md](LOCAL_DEVELOPMENT.md))

### Market Research
- [x] Market analysis complete ([MARKET_RESEARCH.md](MARKET_RESEARCH.md))
- [x] Competitive landscape understood
- [x] Pricing strategy identified

---

## Ready to Start Coding

You now have:

27 comprehensive documentation files covering:
- ✅ What to build (features, architecture)
- ✅ How to build it (API design, database schema, prompts)
- ✅ How to secure it (security guidelines)
- ✅ How to test it (evaluation plan)
- ✅ How to deploy it (GCP, Azure)
- ✅ Why build it (market research, positioning)

---

## Implementation Order

### Phase 1: Foundation
1. Create project skeleton
   - `docker-compose.yml`
   - `requirements.txt`
   - `.env.example`
   - Directory structure

2. Set up database
   - SQLAlchemy models (based on DATABASE_SCHEMA.md)
   - Alembic migrations
   - pgvector extension

3. Create evaluation dataset
   - `eval/questions.json` (20 questions)
   - Sample PDFs in `samples/`

### Phase 2: Core RAG
4. Ingestion pipeline
   - PDF text extraction
   - Chunking (per PROMPTS.md strategy)
   - Embeddings (sentence-transformers)
   - Storage in PostgreSQL

5. Retrieval
   - Vector similarity search
   - Top-k retrieval
   - Confidence scoring

6. Answer generation
   - LLM integration (Gemini/Ollama/Azure)
   - Prompt templates (from PROMPTS.md)
   - Citation extraction

### Phase 3: API & Features
7. FastAPI application
   - `/documents` (upload, list, delete)
   - `/ask` (single question)
   - `/chat` (multi-turn)
   - `/search` (raw retrieval)

8. Security
   - API key authentication
   - Rate limiting
   - Input validation
   - (Follow security/SECURITY_CHECKLIST.md)

9. LangGraph router
   - Query classification
   - Answer/clarify/refuse paths

### Phase 4: Testing & Deployment
10. Testing
    - Unit tests
    - Integration tests
    - Evaluation harness (eval/run.py)

11. Deployment
    - Docker container
    - GCP Cloud Run
    - CI/CD pipeline

---

## Documentation Updates During Coding

These docs will be updated **after** implementation:

### Will Add During Coding
- Actual SQLAlchemy model code (to DATABASE_SCHEMA.md)
- Final prompt templates with tested examples (to PROMPTS.md)
- Real evaluation results (to EVALUATION_PLAN.md)
- Actual API request/response examples (to API.md)
- Troubleshooting based on real issues (to LOCAL_DEVELOPMENT.md)

### Will Not Change
- Architecture decisions
- Security requirements
- Feature specifications
- Market research
- Deployment strategy

---

## Progress Tracking

Use GitHub Projects or this checklist:

**Foundation:**
- [ ] Project skeleton created
- [ ] Database models written
- [ ] Migrations set up
- [ ] Eval dataset created

**Core RAG:**
- [ ] PDF ingestion works
- [ ] Chunking works
- [ ] Embeddings work
- [ ] Vector search works
- [ ] Answer generation works

**API:**
- [ ] All endpoints implemented
- [ ] Authentication works
- [ ] Rate limiting works
- [ ] Tests written

**Deployment:**
- [ ] Docker container builds
- [ ] Deploys to Cloud Run
- [ ] CI/CD pipeline works

---

## Ready to Build

**Total documentation:** 34 files

**Next step:** Create project skeleton and start Phase 1

**When to update docs:**
- After major features work → Update with code examples
- After deployment works → Update with actual commands
- After evaluation runs → Update with real metrics

**Document updates will be iterative** as you implement and learn what works.

---

## Tips for Success

1. **Refer to docs often** - They're your spec
2. **Update docs when design changes** - Keep them accurate
3. **Add troubleshooting sections** - Document problems you solve
4. **Track decisions** - Add "Design Decisions" sections when you make choices
5. **Keep eval running** - Run `eval.run` after each major change

---

Ready to build? Start with docker-compose.yml and requirements.txt.
