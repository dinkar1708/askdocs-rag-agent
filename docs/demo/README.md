# Demo Guides

Choose your demo scenario based on your needs.

---

## 🚀 [Getting Started](getting-started.md)

**Best for:** First-time users, live demos, quick testing

Get the system running and ask your first question in 5 minutes.

- ✅ No configuration needed
- ✅ Works with default mock LLM
- ✅ Copy-paste commands
- ✅ Instant results

**Start here if:** You want to see the system working immediately.

---

## 📋 [Sample Questions](sample-questions.md)

**Best for:** Testing, CI/CD, offline demos, no API costs

Pre-configured demo questions with expected answers using mock LLM provider (hard-coded patterns).

- ✅ Zero setup (no API keys)
- ✅ Instant responses
- ✅ Unique answers per question type
- ✅ Perfect for automated testing

**Use this when:** You need reliable, fast demos without external dependencies.

---

## 🖥️ [Ollama Local LLM Demo](ollama-local-llm-demo.md)

**Best for:** Privacy-sensitive deployments, offline production, zero API costs

Real LLM inference running 100% on your machine with actual test results.

- ✅ 100% offline (no internet required)
- ✅ Zero API costs (unlimited queries)
- ✅ Full data privacy (documents never leave your machine)
- ✅ Decent quality (llama3.2 2GB model)
- ⚠️ Requires ~4GB RAM
- ⚠️ First query: 10-15s (model loading)

**Use this when:** You need production-quality answers without cloud dependencies.

---

## 📊 Comparison

| Feature | Sample Questions (Mock) | Ollama Local | Gemini Cloud |
|---------|-----------|--------------|--------------|
| **Setup Time** | 0 min | 5 min | 2 min |
| **API Key** | ❌ Not needed | ❌ Not needed | ✅ Required |
| **Cost** | $0 | $0 | ~$0.001/query |
| **Internet** | ❌ Not needed | ❌ Not needed | ✅ Required |
| **Answer Quality** | Demo-quality | Good | Excellent |
| **Response Time** | <100ms | 1-15s | 1-3s |
| **Privacy** | ✅ 100% local | ✅ 100% local | ⚠️ Cloud |
| **Production Ready** | ❌ Testing only | ✅ Yes | ✅ Yes |

---

## 🎯 Which Demo Should I Use?

**For a quick live demo:**
→ Start with [Getting Started](getting-started.md)

**For automated testing:**
→ Use [Sample Questions](sample-questions.md) (mock mode)

**For privacy-sensitive production:**
→ Deploy with [Ollama](ollama-local-llm-demo.md)

**For best answer quality:**
→ Configure [Gemini](../core/configuration/CONFIGURATION.md) (requires API key)

---

## 📁 Sample Data

All demos use: `app/samples/company_policy.pdf`

**Contents:**
- Vacation policy (15 days PTO)
- Remote work policy (2 days/week)
- Health insurance (PPO/HMO/HDHP)
- Standard work hours (9-5 M-F)

**Chunk count:** 9 chunks across 4 pages

---

## 🔗 Related Docs

- [Architecture](../core/architecture/ARCHITECTURE.md) - How RAG works
- [Configuration](../core/configuration/CONFIGURATION.md) - LLM provider setup
- [Local Development](../development/LOCAL_DEVELOPMENT.md) - Full dev environment
- [API Reference](../interfaces/api/) - REST API documentation

---

## 🆘 Troubleshooting

**Backend won't start:**
```bash
docker logs app-api-1
# Check for port conflicts: lsof -i :8000
```

**Frontend won't start:**
```bash
cd web-ui && rm -rf node_modules && npm install
# Check for port conflicts: lsof -i :3000
```

**Ollama not responding:**
```bash
brew services restart ollama
ollama list  # Verify llama3.2 is downloaded
```

**Questions returning "not_found":**
- Verify document is uploaded: `curl http://localhost:8000/documents/`
- Check if chunks were created (should see `chunk_count: 9`)
- Try exact questions from demo guides
