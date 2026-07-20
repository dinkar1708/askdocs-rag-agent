# Why Not Just Use ChatGPT / Gemini / Claude?

A fair question — consumer AI chat apps can already answer questions about uploaded PDFs. Why build this?

---

## The Short Answer

**Consumer chat apps are assistants for a person.**

**This project is infrastructure for a business to offer that experience to its customers.**

---

## Detailed Comparison

| Capability | ChatGPT / Gemini / Claude | askdocs-rag-agent |
|---|---|---|
| **Who can ask?** | The account owner only | Your customers/users via API, web app, Slack, etc. — no accounts needed |
| **Document lifetime** | Per-conversation (gone after chat ends) | Persistent knowledge base — ingest once, query forever |
| **Answer scope** | May blend general model knowledge with document | **Grounded-or-refuse** — answers only from uploaded docs with citations, or explicit "not found" |
| **Integration** | Closed UI (ChatGPT app) | REST API + MCP tools → plug into WhatsApp, web widgets, internal tools, AI assistants |
| **Multi-user** | One account, one context | Multi-tenant ready — isolated document sets per tenant, usage caps, per-tenant config |
| **Model choice** | Fixed by vendor (OpenAI, Google, Anthropic) | **Swappable adapter** — Gemini, Ollama, Azure OpenAI; switch by config, not code |
| **Data location** | Vendor-managed servers | Documents + embeddings in **your own PostgreSQL** |
| **Cost model** | $20-30/month per seat | Pennies per query via API + scale-to-zero hosting — viable for high-volume customer Q&A |
| **Customization** | Limited (system prompts, some tuning) | Full control — chunking, retrieval threshold, routing logic, evaluation metrics |
| **Auditability** | Chat history in app | Database logs of every query, retrieval, and answer — queryable for compliance |

---

## Real-World Use Cases This Enables

### 1. Customer Support Bot

**Scenario:** E-commerce site with 50-page return policy.

**Problem with ChatGPT:**
- Customers don't have ChatGPT Plus accounts
- Policy changes monthly → need to re-upload every time
- Can't embed into website (closed app)

**With askdocs-rag-agent:**
- Upload policy once → `/ask` endpoint on website widget
- Update policy → re-upload → all future answers reflect it
- Customers ask "refund for damaged items?" → get cited answer from policy
- Track which questions get "not_found" → improve policy docs

---

### 2. Employee HR Handbook

**Scenario:** 200-employee company, 80-page handbook (vacation, benefits, codes of conduct).

**Problem with Gemini:**
- Employees without Gemini accounts can't access
- HR team can't track what questions are being asked
- Answers may improvise policies not in handbook

**With askdocs-rag-agent:**
- Upload handbook → Slack bot powered by `/chat` endpoint
- Employees ask "can I take 3 weeks vacation?" → bot answers with handbook citation
- HR sees analytics: "top 10 unanswered questions" → add to next handbook revision
- Confidence threshold ensures no hallucinated policies

---

### 3. Legal Contract Q&A

**Scenario:** Law firm with 1000s of precedent contracts.

**Problem with Claude:**
- Cannot ingest 1000s of documents (context window limits)
- Answers may cite general legal principles, not firm's contracts
- No audit trail for compliance

**With askdocs-rag-agent:**
- Ingest entire contract library (pgvector scales to millions of chunks)
- Lawyer asks "boilerplate for NDA termination clauses" → retrieves from firm's actual contracts
- Every query logged with retrieval sources → compliance audit trail
- Multi-tenant: each client's contracts isolated

---

## What Consumer Apps Do Better

To be fair, ChatGPT/Gemini/Claude excel at:

- **Conversational UX** - Polished chat interface, voice input, mobile apps
- **General knowledge** - Answering questions beyond uploaded documents
- **Zero setup** - No deployment, no database, no code
- **Multimodal** - Images, PDFs, videos, code all in one chat

**When to just use ChatGPT:**
- Personal use (research, learning)
- One-off document analysis
- No need for persistent knowledge base

**When to build askdocs-rag-agent:**
- Business offering document Q&A to customers/employees
- Need persistent, updateable knowledge base
- Require grounded answers with citations
- Want full control (chunking, models, hosting)

---

## How Enterprises Actually Deploy LLMs

From experience deploying AI in enterprises, here's what they need:

| Requirement | Consumer Apps | This Project |
|---|---|---|
| **SSO integration** | ❌ | ✅ (add OAuth middleware) |
| **Data residency** (e.g., EU-only) | ❌ | ✅ (deploy in EU region) |
| **Custom retention policy** | ❌ | ✅ (delete chunks after N days) |
| **Usage caps per tenant** | ❌ | ✅ (add rate limiting by tenant_id) |
| **Audit logs** | ❌ | ✅ (log every query to database) |
| **Air-gapped deployment** | ❌ | ✅ (Ollama provider, no internet) |
| **Model fine-tuning** | ❌ | ✅ (swap in fine-tuned model) |

Enterprises don't point users at ChatGPT — they build controlled RAG services with ingestion, isolation, grounding rules, evaluation, and observability.

**This project is that architecture.**

---

## The Technical Moat (What ChatGPT Can't Do)

Even if OpenAI adds "persistent document Q&A" tomorrow, this project differentiates on:

1. **Grounded-or-refuse threshold** - Explicit "not_found" when confidence <0.7 (no guessing)
2. **Citation tracking** - Every answer includes `[doc, page]` sources
3. **LLM provider portability** - Not locked into OpenAI pricing or API limits
4. **Query routing** - LangGraph classifies: answer / clarify / refuse (not just "best effort")
5. **Evaluation harness** - Measure retrieval hit-rate and groundedness over labeled test set
6. **Multi-tenant isolation** - One deployment serves 100s of customers with isolated docs

These are **business requirements**, not features consumer apps optimize for.

---

## Is This a Product or a Portfolio Project?

**Both.**

**As a portfolio/demonstration project:**
- Demonstrates production engineering: CI/CD, testing, migrations, cloud deployment
- Shows RAG understanding: chunking, embeddings, retrieval, grounding
- Proves system design: adapter pattern, stateless services, scalability
- Highlights cloud skills: GCP Cloud Run, Azure Container Apps, Kubernetes

**As a commercial product:**
- **Too generic as-is** - competes with everything
- **Needs vertical focus** - HR bots, legal Q&A, customer support, etc.
- **Needs proprietary layer** - conflict detection, proactive alerts, version control
- **Realistic path:** Lifestyle SaaS ($10-50k MRR) with niche focus and sales effort

See main README for detailed market analysis.

---

## Summary

**Consumer chat apps:** Great for individuals, closed ecosystems.

**askdocs-rag-agent:** Infrastructure for businesses to offer trusted document Q&A to their users, under their brand, with their rules.

**The gap this fills:** ChatGPT is an assistant. This is the layer that makes it a customer-facing service.

---

**Next:** See [Architecture](ARCHITECTURE.md) for how it works, or [Local Development](LOCAL_DEVELOPMENT.md) to run it.
