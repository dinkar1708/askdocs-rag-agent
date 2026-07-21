# Local Development Setup

**description**: Set up local development environment with seed data

You are helping set up the AskDocs RAG Agent for local development.

## Steps

### 1. Start Backend

```bash
cd app
docker compose up -d
sleep 3
curl http://localhost:8000/health
```

### 2. Start Frontend

```bash
cd web-ui
npm install  # First time only
npm run dev &
```

### 3. Load Sample Data

```bash
curl -X POST http://localhost:8000/documents/ \
  -F "file=@app/samples/company_policy.pdf"
```

### 4. Test

```bash
curl -X POST http://localhost:8000/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "How many vacation days do employees get?"}'
```

Expected: Answer with "15 days" and citations

## Quick Checklist

- [ ] Backend: http://localhost:8000/health responds
- [ ] Frontend: http://localhost:3000 loads
- [ ] Document uploaded successfully
- [ ] Question answering works
- [ ] Web UI shows answers with sources

## Troubleshooting

**"GEMINI_API_KEY required":**
- Ensure `app/.env` has `LLM_PROVIDER=mock`
- Restart: `docker compose -f app/docker-compose.yml restart`

**Port in use:**
- Check: `lsof -i :8000` or `lsof -i :3000`

**Database not ready:**
- Wait and check: `docker logs app-db-1`

**Frontend can't connect:**
- Verify: `curl http://localhost:8000/health`
- Check browser console (F12)

## Test Questions

- "How many vacation days do employees get?"
- "What health insurance options are available?"
- "What is the remote work policy?"

## Reference

See [LOCAL_DEVELOPMENT.md](../../../docs/development/LOCAL_DEVELOPMENT.md) for details
