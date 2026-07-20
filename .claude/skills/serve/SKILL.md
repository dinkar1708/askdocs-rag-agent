---
description: "Start the FastAPI development server for the RAG API"
---

# Server Start Skill

Start the askdocs RAG API server in development mode.

## Steps

1. **Check environment**:
   - Verify `.env` file exists with required variables
   - Check if PostgreSQL is running (or will use SQLite fallback)
   - Verify LLM provider is configured (GEMINI_API_KEY or use mock)

2. **Check port availability**:
   ```bash
   lsof -ti:8000
   ```
   - If occupied, ask user if they want to kill the process
   - Kill if needed: `kill -9 $(lsof -ti:8000)`

3. **Start server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   - `--reload`: Auto-restart on code changes
   - `--host 0.0.0.0`: Accept external connections
   - `--port 8000`: Default port

4. **Verify startup**:
   - Watch logs for successful database connection
   - Confirm no import errors
   - Check for LLM provider initialization

5. **Provide access links**:
   - 🏠 API Root: http://localhost:8000/
   - 📚 Interactive API Docs (Swagger): http://localhost:8000/docs
   - 📖 Alternative Docs (ReDoc): http://localhost:8000/redoc
   - ❤️ Health Check: http://localhost:8000/ask/health

## Environment Variables

Required in `.env`:
```bash
# Database (optional - defaults to PostgreSQL)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/askdocs

# LLM Provider
LLM_PROVIDER=gemini  # or: mock, ollama, azure
GEMINI_API_KEY=your_key_here

# API Security
API_KEY=test-key

# Logging
DEBUG=True
LOG_LEVEL=INFO
```

## Best Practices

- ✅ Always check `.env` configuration first
- ✅ Use `--reload` for development (auto-restart on changes)
- ✅ Test health endpoint after startup
- ✅ Keep server running in a dedicated terminal
- ❌ Don't run in production with `--reload`
- ❌ Don't commit with DEBUG=True for production

## Troubleshooting

- **Port already in use**: Kill the process or change port
- **Database connection failed**: Ensure PostgreSQL is running or configure SQLite
- **Import errors**: Check virtual environment is activated
- **LLM errors**: Verify API keys or use `LLM_PROVIDER=mock` for testing
