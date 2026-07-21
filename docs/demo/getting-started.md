# Quick Start - 5 Minute Demo

Get the system running and ask your first question in 5 minutes.

---

## Step 1: Start Backend (1 min)

```bash
cd askdocs-rag-agent
docker compose -f app/docker-compose.yml up -d

# Wait 10 seconds for database initialization
sleep 10

# Verify backend is running
curl http://localhost:8000/health
```

**Expected:** `{"status":"healthy","service":"askdocs-rag-agent",...}`

---

## Step 2: Start Frontend (1 min)

```bash
cd web-ui
npm install  # First time only
npm run dev
```

**Open:** http://localhost:3000

---

## Step 3: Upload Sample Document (1 min)

```bash
# Upload the sample company policy PDF
curl -X POST http://localhost:8000/documents/ \
  -F "file=@app/samples/company_policy.pdf"
```

**Expected:** `{"id":1,"filename":"company_policy.pdf","page_count":4,"chunk_count":9}`

---

## Step 4: Ask Your First Question (1 min)

**Via API:**
```bash
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How many vacation days do employees get?"}'
```

**Via Web UI:**
1. Go to http://localhost:3000
2. Type: "How many vacation days do employees get?"
3. Press Enter

**Expected Answer:**
> According to the employee handbook [company_policy.pdf - Page 1], full-time employees accrue 15 days of paid vacation per year...

---

## Step 5: Try More Questions (1 min)

Copy-paste these into the web UI:

```
What is the remote work policy?
```

```
What health insurance options are available?
```

```
What are the standard work hours?
```

```
What is the weather today?
```

The last question should return "not_found" because it's not in the documents!

---

## 🎉 That's It!

You now have a working RAG system with:
- ✅ Document upload and chunking
- ✅ Vector similarity search
- ✅ Grounded Q&A with citations
- ✅ Honest "not_found" for unanswerable questions

---

## Next Steps

**For better answers:**
- See [docs/demo/ollama-local-llm-demo.md](ollama-local-llm-demo.md) for 100% offline local LLM
- See [Gemini setup](../core/configuration/CONFIGURATION.md) for cloud LLM (best quality)

**For more demo questions:**
- See [mock-mode-demo.md](mock-mode-demo.md) for copy-paste questions

**To understand how it works:**
- See [Architecture](../core/architecture/ARCHITECTURE.md)
- See [Local Development](../development/LOCAL_DEVELOPMENT.md)
