# API Test Results

This folder contains API request/response examples automatically generated from test runs.

## How It Works

When you run pytest tests, the `document_api_call()` utility automatically saves API examples here.

## Format

Each JSON file contains:
- `api`: API endpoint (method + path)
- `request`: Request body/params
- `response`: Response data

## Example

```json
{
  "api": "GET /health",
  "request": {},
  "response": {
    "status": "healthy",
    "service": "askdocs-rag-agent",
    "version": "0.1.0"
  }
}
```

## Regenerating

Run tests to regenerate:
```bash
docker compose exec api pytest tests/test_api.py -v
```

Files are automatically created/updated with each test run.
