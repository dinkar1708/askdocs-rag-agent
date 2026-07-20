# Market Research - Document Q&A / RAG Market 2026

Research conducted: July 2026

---

## Market Size & Growth

**Current Market (2025):** $1.94B
**Projected (2030):** $9.86B
**CAGR:** 38.4%

**Verdict:** ✅ Rapidly growing market with strong demand

---

## Competitive Landscape

### Tier 1: Enterprise Platforms ($100K-500K+ annual)

| Company | Focus | Pricing | Strengths |
|---|---|---|
| **Glean** | Enterprise search + RAG | $100K+ | Leader in AI-powered search, strong security |
| **Writer** | Enterprise content AI | Custom | Content generation + RAG |
| **SphereIQ** | Compliance-focused | Custom | Strong compliance/security |
| **Hebbia** | Finance/Investment | Custom | #1 for finance professionals |
| **Cohere North** | Enterprise AI | Custom | Multi-language, strong API |

**Your Position:** ❌ Direct competition at this tier is extremely difficult

---

### Tier 2: Managed RAG Services ($50-100/user/month)

| Service | Provider | Pricing | Strengths |
|---|---|---|
| **Vectara** | Managed RAG | Pay-as-you-go | Purpose-built for RAG |
| **AWS Bedrock KB** | Amazon | Usage-based | AWS ecosystem integration |
| **Azure AI Search** | Microsoft | Usage-based | Azure ecosystem integration |
| **Vertex AI Search** | Google | Usage-based | Google ecosystem integration |

**Your Position:** ⚠️ Compete on flexibility, not enterprise features

---

### Tier 3: Developer-First RAG Services ($9-50/month)

| Service | Pricing | Target | Strengths |
|---|---|---|
| **Ragie** | $9/month start | Product teams | Fast implementation |
| **Nuclia** | Custom | Developers | Multi-format support |
| **LlamaCloud** | $0 + credits | Developers | LlamaIndex ecosystem |

**Your Position:** ✅ **THIS IS YOUR SWEET SPOT**
- Self-hosted option (lower cost)
- Open source (customizable)
- Simple deployment (Docker + Cloud Run)
- Clear documentation

---

### Tier 4: Open Source Frameworks (FREE)

| Framework | GitHub Stars | Focus | Strengths |
|---|---|---|
| **Dify** | 114,000 | Visual workflow | No-code RAG builder |
| **RAGFlow** | 70,000 | Document understanding | Smart chunking, knowledge graphs |
| **LlamaIndex** | 46,500 | Data-first RAG | Best for custom indexing |
| **Haystack** | 24,000 | Production pipelines | Robust, production-ready |
| **LangChain** | - | General LLM apps | Most popular, flexible |

**Your Position:** ✅ **BUILD ON THESE, DON'T COMPETE**
- You're using LangChain/LangGraph (good choice)
- Differentiate with production-ready deployment + docs

---

## Pricing Analysis

### What The Market Charges

| Tier | Pricing | What You Get |
|---|---|---|
| Enterprise | $15K-500K/year | Custom deployment, SSO, SLAs, dedicated support |
| Managed SaaS | $50-100/user/month | Hosted, integrations, basic support |
| Developer Tools | $9-50/month | API access, basic limits, community support |
| Open Source | FREE | Self-hosted, no support |

### Component Costs (Build vs Buy)

| Component | DIY Cost | Service Cost |
|---|---|---|
| Document parsing | $0.003/page (LlamaParse) | $0.015/page (enterprise) |
| Vector DB | $45/month (Weaviate Flex) | $400/month (Weaviate Premium) |
| LLM API | Gemini Free Tier | $0.50-2.00 per 1M tokens |

---

## Your Competitive Position

### ✅ Where You Win

1. **Self-Hosted Option**
   - No vendor lock-in
   - Full data control
   - Lower ongoing costs

2. **Production-Ready Documentation**
   - Most open-source projects have poor docs
   - You have comprehensive guides
   - Clear deployment paths (GCP + Azure)

3. **Grounded-or-Refuse Design**
   - Explicit "not_found" responses
   - Citation tracking
   - Trust over answer rate

4. **Developer Experience**
   - Docker Compose for local dev
   - Clear API documentation
   - Multiple LLM providers (Gemini/Ollama/Azure)

5. **Deployment Simplicity**
   - One-click Cloud Run deployment
   - Scale-to-zero pricing
   - $8-18/month for small deployments

### ⚠️ Where You're Vulnerable

1. **No Enterprise Features**
   - No SSO/SAML
   - No audit logging (yet)
   - No SLAs

2. **Generic Use Case**
   - Not specialized for any vertical
   - Competes with everyone

3. **No UI**
   - API-only (not a problem for developers, but limits reach)

4. **Single Model**
   - Most competitors support multiple embeddings models
   - You use sentence-transformers only

---

## Market Opportunities

### 🎯 Viable Niches for Your Project

1. **HR Policy Bots ($50-200/month per company)**
   - 50-500 employee companies
   - Upload handbook → Slack bot
   - Addressable market: 200K+ companies

2. **Legal Contract Q&A ($100-500/month per firm)**
   - Small law firms (5-20 lawyers)
   - Search precedent contracts
   - Addressable market: 50K+ firms

3. **Customer Support Docs ($50-300/month per company)**
   - SaaS companies with knowledge bases
   - Self-service support
   - Addressable market: 100K+ SaaS companies

4. **Developer Documentation Search (FREE → $50/month)**
   - Open source projects
   - Company developer portals
   - Freemium → paid for analytics

### 💰 Revenue Potential

**Conservative (First Year):**
- 20 customers × $50/month = $12K/year

**Moderate (Year 2):**
- 100 customers × $75/month = $90K/year

**Optimistic (Year 3):**
- 500 customers × $100/month = $600K/year

---

## Technology Trends (2026)

### What's Hot

1. **Agentic RAG** - Multi-step reasoning, query decomposition
2. **Hybrid Search** - Vector + keyword search combined
3. **Multi-modal RAG** - Images, tables, charts (not just text)
4. **Knowledge Graphs** - Structured relationships between chunks
5. **Streaming Responses** - Real-time answer generation

### What You Should Add

| Feature | Priority | Impact |
|---|---|---|
| Hybrid search (vector + BM25) | HIGH | Better retrieval |
| Table extraction from PDFs | MEDIUM | Multi-format support |
| Streaming responses | MEDIUM | Better UX |
| Knowledge graph | LOW | Differentiation |
| Multi-modal (images) | LOW | Future-proofing |

---

## Before You Write Code: Critical Gaps

### ✅ You Have

- [x] Architecture documented
- [x] Security guidelines
- [x] Deployment paths (GCP + Azure)
- [x] API design
- [x] Feature specifications
- [x] Testing strategy
- [x] Market positioning

### ❌ You're Missing

#### 1. **Technical Specs** (HIGH PRIORITY)

Create these before coding:

- [ ] **Database Schema** - Exact table definitions
  - Document: `docs/DATABASE_SCHEMA.md`
  - Include: column types, indexes, constraints

- [ ] **API Contracts** - Request/response schemas
  - Already in `docs/API.md` but add Pydantic schemas
  - Example: `QuestionRequest`, `AnswerResponse`

- [ ] **LLM Prompts** - Exact prompt templates
  - Document: `docs/PROMPT_ENGINEERING.md`
  - Critical for reproducibility

- [ ] **Evaluation Dataset** - Test questions + expected answers
  - Create: `eval/questions.json` with 20+ examples
  - Needed to measure quality

#### 2. **Infrastructure Details** (MEDIUM PRIORITY)

- [ ] **docker-compose.yml** - Local dev stack
- [ ] **Dockerfile** - Production container
- [ ] **requirements.txt** - Python dependencies
- [ ] **.env.example** - Environment template
- [ ] **alembic.ini** - Database migrations config

#### 3. **Development Workflow** (MEDIUM PRIORITY)

- [ ] **Pre-commit hooks** - Lint, format, secrets scan
- [ ] **GitHub Actions** - CI/CD workflows
- [ ] **Makefile** - Common commands (test, lint, deploy)

#### 4. **Legal/Business** (LOW PRIORITY NOW)

- [ ] **LICENSE** - MIT License file
- [ ] **TERMS.md** - Terms of service (if monetizing)
- [ ] **PRIVACY.md** - Privacy policy (if collecting data)

---

## Recommended Next Steps

### Phase 1: Technical Foundation

1. **Create missing technical specs:**
   - Database schema document
   - Prompt engineering guide
   - Create eval dataset (20 questions)

2. **Set up project skeleton:**
   - `docker-compose.yml`
   - `requirements.txt`
   - `alembic/` migrations setup
   - `.env.example`

3. **Write database models:**
   - `app/db/models.py` (Document, Chunk, Session tables)
   - Create first migration

### Phase 2: Core RAG

1. **Ingestion pipeline:**
   - PDF extraction
   - Chunking
   - Embeddings
   - Storage

2. **Retrieval:**
   - Vector search
   - Confidence scoring

3. **Answer generation:**
   - LLM integration
   - Prompt templates
   - Citation extraction

### Phase 3: API & Testing

1. **FastAPI routes:**
   - `/documents`, `/ask`, `/chat`
   - Rate limiting
   - Authentication

2. **Testing:**
   - Unit tests
   - Integration tests
   - Evaluation harness

### Phase 4: Deployment

1. **Cloud deployment:**
   - GCP Cloud Run
   - Cloud SQL setup
   - CI/CD pipeline

2. **Documentation:**
   - Update deployment docs with real commands
   - Add troubleshooting guide

---

## Market Research Conclusions

### ✅ YES, Build This Project

**Reasons:**
1. Growing market (38% CAGR)
2. Clear gap: production-ready open-source RAG
3. Good learning project (demonstrates skills)
4. Monetization potential ($10-50K MRR viable)

### 🎯 Focus Areas

**To Compete:**
1. **Documentation** - Your strength, keep it excellent
2. **Deployment simplicity** - One-click Cloud Run > complex setup
3. **Grounded answers** - Trust > answer rate
4. **Developer experience** - Great local dev setup

**To Differentiate:**
1. Pick a vertical (HR, legal, support)
2. Add vertical-specific features
3. Build integrations (Slack, Teams, etc.)

### ⚠️ Avoid

1. Competing with enterprise platforms (Glean, Writer)
2. Building another LangChain (too generic)
3. Trying to do everything (focus!)

---

## Final Answer: Missing Anything?

### Critical (Do Before Coding)

1. ✅ Database schema spec
2. ✅ Prompt templates documented
3. ✅ Evaluation dataset created
4. ✅ Project skeleton (docker-compose, requirements.txt)

### Important (Do During Coding)

5. ✅ Pydantic schemas for API
6. ✅ Tests alongside features
7. ✅ Alembic migrations for schema changes

### Nice-to-Have (Do Later)

8. License file
9. Contributing guide
10. Changelog

---

**You're 90% ready to code.** Just create the technical specs above, then start building!

**Recommended approach:** Start with Phase 1 (technical foundation), then iterate.
