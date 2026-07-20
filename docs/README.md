# Documentation

Complete documentation for askdocs-rag-agent.

---

## Structure

```
docs/
├── README.md                    # This file
│
├── core/                        # Shared technical docs
│   ├── architecture/            # System design
│   ├── security/                # Security guidelines
│   ├── deployment/              # Cloud deployment
│   └── configuration/           # Environment config
│
├── interfaces/                  # How to use (each interface)
│   ├── web-ui/                  # Web interface
│   ├── api/                     # REST API integration
│   ├── slack-bot/               # Slack integration
│   └── mcp/                     # Claude Desktop
│
├── features/                    # What it does
├── development/                 # For developers
├── business/                    # For sales
├── project/                     # Planning
├── testing/                     # Testing
└── getting-started/             # Quick start
```

---

## Quick Navigation

### Getting Started

**New user?** Start here:
1. [getting-started/WHY.md](getting-started/WHY.md) - Why use this?
2. [getting-started/LOCAL_DEVELOPMENT.md](getting-started/LOCAL_DEVELOPMENT.md) - Run locally
3. [Choose interface](#interfaces) - Pick how to use it

---

### Core (Reusable Docs)

**Architecture & Design:**
- [core/architecture/ARCHITECTURE.md](core/architecture/ARCHITECTURE.md) - System design
- [core/architecture/DATABASE_SCHEMA.md](core/architecture/DATABASE_SCHEMA.md) - Database design
- [core/architecture/API.md](core/architecture/API.md) - API technical spec

**Security:**
- [core/security/README.md](core/security/README.md) - Security overview
- [core/security/AUTHENTICATION.md](core/security/API_SECURITY.md) - API keys, auth
- [core/security/SECRETS_MANAGEMENT.md](core/security/SECRETS_MANAGEMENT.md) - Secrets handling

**Deployment:**
- [core/deployment/DEPLOYMENT.md](core/deployment/DEPLOYMENT.md) - Overview
- [core/deployment/GCP.md](core/deployment/GCP.md) - Google Cloud Run
- [core/deployment/AZURE.md](core/deployment/AZURE.md) - Azure Container Apps

**Configuration:**
- [core/configuration/CONFIGURATION.md](core/configuration/CONFIGURATION.md) - All env vars

---

### Interfaces (How to Use)

Pick how you want to use AskDocs:

**[Web UI](interfaces/web-ui/)** - Browser interface
- For: End users, demos
- Setup: 5 minutes
- Use: Upload PDF, ask questions in browser

**[REST API](interfaces/api/)** - Programmatic integration
- For: Developers integrating into apps
- Setup: 10 minutes
- Use: HTTP requests from your code

**[Slack Bot](interfaces/slack-bot/)** - Ask in Slack
- For: Teams using Slack
- Setup: 15 minutes
- Use: @askdocs your question

**[MCP/Claude Desktop](interfaces/mcp/)** - AI assistant integration
- For: Claude Desktop users
- Setup: 10 minutes
- Use: Ask Claude to search your docs

---

### Features

What the product does:
- [Document Ingestion](features/01-document-ingestion.md)
- [Grounded Q&A](features/02-grounded-qa.md)
- [Document Management](features/03-document-management.md)
- [Multi-turn Chat](features/04-multi-turn-chat.md)
- [Query Routing](features/05-query-routing.md)
- [MCP Integration](features/06-mcp-integration.md)
- [Evaluation](features/07-evaluation.md)

---

### Development

For developers building features:
- [development/DEVELOPMENT.md](development/DEVELOPMENT.md) - Dev workflow
- [development/PROMPTS.md](development/PROMPTS.md) - LLM prompts
- [development/EVALUATION_PLAN.md](development/EVALUATION_PLAN.md) - Quality metrics

---

### Business

For sales and marketing:
- [business/ONE_PAGER.md](business/ONE_PAGER.md) - Product pitch
- [business/PRICING.md](business/PRICING.md) - Plans and pricing
- [business/CASE_STUDIES.md](business/CASE_STUDIES.md) - Customer examples
- [business/ROI_CALCULATOR.md](business/ROI_CALCULATOR.md) - Financial justification

---

### Project

Planning and research:
- [project/PRE_CODE_CHECKLIST.md](project/PRE_CODE_CHECKLIST.md) - Implementation roadmap
- [project/MARKET_RESEARCH.md](project/MARKET_RESEARCH.md) - Market analysis

---

### Testing

Quality assurance:
- [testing/TESTING.md](testing/TESTING.md) - How to test

---

## By Role

### End User
1. Pick interface: [Web UI](interfaces/web-ui/) or [Slack](interfaces/slack-bot/)
2. Upload documents
3. Ask questions

### Developer
1. [getting-started/LOCAL_DEVELOPMENT.md](getting-started/LOCAL_DEVELOPMENT.md) - Setup
2. [interfaces/api/](interfaces/api/) - Integration guide
3. [development/DEVELOPMENT.md](development/DEVELOPMENT.md) - Dev workflow

### DevOps
1. [core/deployment/](core/deployment/) - Deployment guides
2. [core/security/](core/security/) - Security setup
3. [core/configuration/](core/configuration/) - Configuration

### Business
1. [business/ONE_PAGER.md](business/ONE_PAGER.md) - Product overview
2. [business/PRICING.md](business/PRICING.md) - Pricing
3. [business/CASE_STUDIES.md](business/CASE_STUDIES.md) - Examples

---

## File Count

| Category | Count | Location |
|---|---|---|
| Core (shared) | 10 | `/docs/core/**/*.md` |
| Interfaces | 4 | `/docs/interfaces/**/*.md` |
| Features | 7 | `/docs/features/*.md` |
| Development | 3 | `/docs/development/*.md` |
| Business | 5 | `/docs/business/*.md` |
| Project | 2 | `/docs/project/*.md` |
| Testing | 1 | `/docs/testing/*.md` |
| Getting Started | 2 | `/docs/getting-started/*.md` |
| **Total** | **34 files** | All organized |

---

## Key Concept: Core vs Interfaces

**Core docs** are reusable across ALL interfaces:
- Security → used by web-ui, API, Slack, MCP
- Deployment → used by all interfaces
- Configuration → used by all interfaces

**Interface docs** are specific to each way of using:
- Web UI → browser setup, customization
- API → integration code examples
- Slack → bot setup, commands
- MCP → Claude Desktop config

**This avoids duplication.** Each interface references core docs.

---

## Contributing

Found an issue or want to improve docs?
1. Open GitHub issue with label `documentation`
2. Or submit a PR

**Questions?** See [main README](../README.md)
