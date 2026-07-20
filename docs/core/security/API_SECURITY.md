# API Security Guide

Security best practices for FastAPI endpoints in askdocs-rag-agent.

---

## Overview

Secure all API endpoints against common attacks: injection, DDoS, unauthorized access, and data leaks.

---

## Rate Limiting

### Why?

Prevents:
- Brute force attacks
- DDoS attacks
- API abuse
- Cost overruns (LLM API calls)

### Implementation

**Install slowapi:**
```bash
pip install slowapi
```

**Add to FastAPI:**
```python
# app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**Apply to endpoints:**
```python
# app/api/routes/ask.py
from slowapi import Limiter
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@app.post("/ask")
@limiter.limit("100/minute")  # 100 requests per minute per IP
async def ask_question(request: Request, question: str):
    # Your code here
    pass

@app.post("/documents")
@limiter.limit("10/hour")  # Stricter limit for uploads
async def upload_document(request: Request, file: UploadFile):
    # Your code here
    pass
```

**Recommended limits:**
| Endpoint | Limit | Reason |
|---|---|---|
| `/ask` | 100/minute | Moderate query load |
| `/chat` | 50/minute | More expensive (LLM + history) |
| `/documents` (upload) | 10/hour | Expensive (processing + storage) |
| `/documents` (list/get) | 200/minute | Cheap reads |
| `/search` | 200/minute | Cheap vector search |

---

## Input Validation

### File Upload Validation

```python
# app/api/routes/documents.py
from fastapi import UploadFile, HTTPException
import magic  # pip install python-magic

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = ["application/pdf"]

@app.post("/documents")
async def upload_document(file: UploadFile):
    # 1. Check file size
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(413, "File too large (max 10MB)")

    # 2. Validate MIME type
    mime_type = magic.from_buffer(file_content, mime=True)
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(400, "Only PDF files allowed")

    # 3. Validate file extension
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "File must have .pdf extension")

    # Process file...
```

### Question Input Sanitization

```python
# app/api/routes/ask.py
import re
from fastapi import HTTPException

MAX_QUESTION_LENGTH = 1000  # characters

def sanitize_question(question: str) -> str:
    """Sanitize user input before sending to LLM."""

    # 1. Length check
    if len(question) > MAX_QUESTION_LENGTH:
        raise HTTPException(400, f"Question too long (max {MAX_QUESTION_LENGTH} chars)")

    # 2. Remove control characters
    question = re.sub(r'[\x00-\x1F\x7F]', '', question)

    # 3. Remove excessive whitespace
    question = ' '.join(question.split())

    # 4. Check for empty input
    if not question.strip():
        raise HTTPException(400, "Question cannot be empty")

    return question

@app.post("/ask")
async def ask_question(question: str):
    question = sanitize_question(question)
    # Continue processing...
```

### SQL Injection Prevention

**✅ Use ORM (SQLAlchemy) - Already safe:**
```python
# ✅ SAFE - Parameterized via ORM
from app.db.models import Document

documents = db.query(Document).filter(Document.tenant_id == tenant_id).all()
```

**❌ Never use raw SQL with user input:**
```python
# ❌ VULNERABLE - Never do this
query = f"SELECT * FROM documents WHERE name = '{user_input}'"
db.execute(query)
```

**If raw SQL needed (rare), use parameters:**
```python
# ✅ SAFE - Parameterized query
from sqlalchemy import text

query = text("SELECT * FROM documents WHERE name = :name")
result = db.execute(query, {"name": user_input})
```

---

## Authentication

### API Key Authentication

**Implement middleware:**
```python
# app/api/middleware/auth.py
from fastapi import Header, HTTPException
import os

API_KEYS = os.getenv("API_KEYS", "").split(",")  # Comma-separated keys

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from X-API-Key header."""
    if x_api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
    return x_api_key
```

**Apply to protected routes:**
```python
# app/api/routes/documents.py
from app.api.middleware.auth import verify_api_key
from fastapi import Depends

@app.post("/documents", dependencies=[Depends(verify_api_key)])
async def upload_document(file: UploadFile):
    # Only accessible with valid API key
    pass
```

**Usage:**
```bash
curl -H "X-API-Key: your_api_key" \
  http://localhost:8000/documents
```

### Multi-tenant Authentication

```python
# app/api/middleware/auth.py
from fastapi import Header, HTTPException
from app.db import SessionLocal
from app.db.models import APIKey

async def get_tenant_id(x_api_key: str = Header(...)):
    """Get tenant ID from API key."""
    db = SessionLocal()
    try:
        api_key = db.query(APIKey).filter(APIKey.key == x_api_key).first()
        if not api_key:
            raise HTTPException(401, "Invalid API key")
        return api_key.tenant_id
    finally:
        db.close()

@app.post("/documents")
async def upload_document(
    file: UploadFile,
    tenant_id: str = Depends(get_tenant_id)
):
    # tenant_id injected - use to scope queries
    doc = Document(filename=file.filename, tenant_id=tenant_id)
    # ...
```

---

## Security Headers

### Add to FastAPI

```python
# app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# 1. HTTPS redirect (production only)
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# 2. Trusted host
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["askdocs.yourdomain.com", "localhost"]
)

# 3. Security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response
```

---

## CORS Configuration

### Development (Permissive)

```python
# app/main.py - development
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Production (Strict)

```python
# app/main.py - production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://app.yourdomain.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],  # Only needed methods
    allow_headers=["Content-Type", "X-API-Key"],  # Only needed headers
)
```

---

## Error Handling

### Never Expose Internals

```python
# ❌ WRONG - Exposes stack trace
@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    doc = db.query(Document).get(doc_id)  # Might raise exception
    return doc

# ✅ CORRECT - Safe error handling
@app.get("/documents/{doc_id}")
def get_document(doc_id: str):
    try:
        doc = db.query(Document).get(doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        return doc
    except Exception as e:
        logger.error(f"Error fetching document: {e}")  # Log details
        raise HTTPException(500, "Internal server error")  # Generic message
```

### Custom Exception Handler

```python
# app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

---

## Request/Response Validation

### Use Pydantic Models

```python
# app/schemas.py
from pydantic import BaseModel, Field, validator

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(5, ge=1, le=20)  # Between 1 and 20

    @validator('question')
    def question_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Question cannot be empty')
        return v.strip()

# app/api/routes/ask.py
@app.post("/ask")
async def ask_question(request: AskRequest):
    # request.question is already validated
    pass
```

---

## Logging Security

### What to Log

✅ **Log:**
- Authentication failures
- Rate limit violations
- Invalid input attempts
- Errors and exceptions
- Document uploads/deletions

❌ **Never log:**
- API keys
- Database passwords
- User passwords
- Full request bodies (may contain sensitive data)

### Implementation

```python
# app/core/logging.py
import logging

logger = logging.getLogger("askdocs")

# ✅ CORRECT
logger.info(f"User {user_id} uploaded document {doc_id}")
logger.warning(f"Rate limit exceeded for IP {ip}")
logger.error(f"Failed to process document {doc_id}: {error_type}")

# ❌ WRONG - Never log secrets
logger.info(f"API key used: {api_key}")  # NO!
logger.debug(f"Request: {request.body}")  # May contain secrets
```

### Mask Sensitive Data

```python
def mask_api_key(key: str) -> str:
    """Mask API key for logging."""
    if len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"

logger.info(f"Request from key: {mask_api_key(api_key)}")
```

---

## Security Testing

### Manual Tests

```bash
# 1. Test rate limiting
for i in {1..150}; do
  curl http://localhost:8000/ask -d '{"question":"test"}'
done
# Should see 429 after ~100 requests

# 2. Test authentication
curl http://localhost:8000/documents  # Should fail (401)
curl -H "X-API-Key: invalid" http://localhost:8000/documents  # Should fail
curl -H "X-API-Key: valid_key" http://localhost:8000/documents  # Should work

# 3. Test input validation
curl -X POST http://localhost:8000/ask \
  -d '{"question":"' $(python -c "print('A'*2000)") '"}'
# Should reject (400 - too long)

# 4. Test file upload
curl -X POST http://localhost:8000/documents \
  -F "file=@malicious.exe"
# Should reject (400 - not a PDF)
```

### Automated Security Tests

```python
# tests/security/test_api_security.py
def test_rate_limiting(client):
    """Test rate limit enforcement."""
    for _ in range(150):
        response = client.post("/ask", json={"question": "test"})

    assert response.status_code == 429  # Too Many Requests

def test_authentication(client):
    """Test API key required."""
    response = client.get("/documents")
    assert response.status_code == 401  # Unauthorized

def test_input_validation(client):
    """Test input sanitization."""
    # Test XSS attempt
    response = client.post("/ask", json={
        "question": "<script>alert(1)</script>"
    })
    assert response.status_code == 200
    # Ensure script tag not in response
    assert "<script>" not in response.text

def test_file_upload_validation(client):
    """Test file type validation."""
    # Non-PDF file
    response = client.post("/documents", files={
        "file": ("test.txt", b"not a pdf", "text/plain")
    })
    assert response.status_code == 400
```

---

## Production Deployment Checklist

- [ ] Rate limiting enabled
- [ ] API key authentication required
- [ ] Input validation on all endpoints
- [ ] CORS restricted to production domains
- [ ] Security headers added
- [ ] HTTPS enforced
- [ ] DEBUG mode disabled
- [ ] API docs disabled or protected
- [ ] Proper error handling (no stack traces exposed)
- [ ] Logging configured (no secrets logged)

---

## Next Steps

1. Implement rate limiting
2. Add API key authentication
3. Add input validation
4. Test security controls
5. Review [SECURITY_CHECKLIST.md](SECURITY_CHECKLIST.md)
