# API Integration Guide

How to integrate AskDocs into your application.

---

## Overview

Use the REST API to add document Q&A to your app.

**Base URL:** http://localhost:8000 (local) or https://your-domain.com

**API Spec:** See [core/architecture/API.md](../../core/architecture/API.md)

---

## Quick Start

### 1. Get API Key

See [core/security/AUTHENTICATION.md](../../core/security/AUTHENTICATION.md)

```bash
# Set in environment
export ASKDOCS_API_KEY="your-key-here"
```

### 2. Upload Document

```bash
curl -X POST http://localhost:8000/documents \
  -H "X-API-Key: $ASKDOCS_API_KEY" \
  -F "file=@handbook.pdf"
```

Response:
```json
{
  "id": "doc-123",
  "filename": "handbook.pdf",
  "pages": 42,
  "chunks": 156
}
```

### 3. Ask Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: $ASKDOCS_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the vacation policy?"}'
```

Response:
```json
{
  "answer": "Employees receive 15 days of paid vacation per year.",
  "sources": [
    {"document": "handbook.pdf", "page": 7}
  ],
  "confidence": 0.92
}
```

---

## Integration Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-key"

def ask_question(question):
    response = requests.post(
        f"{API_URL}/ask",
        headers={"X-API-Key": API_KEY},
        json={"question": question}
    )
    return response.json()

# Use it
result = ask_question("What is the vacation policy?")
print(result["answer"])
print("Sources:", result["sources"])
```

### JavaScript/Node.js

```javascript
const API_URL = "http://localhost:8000";
const API_KEY = "your-key";

async function askQuestion(question) {
  const response = await fetch(`${API_URL}/ask`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({question})
  });

  return await response.json();
}

// Use it
const result = await askQuestion("What is the vacation policy?");
console.log(result.answer);
console.log("Sources:", result.sources);
```

### cURL

```bash
# Upload
curl -X POST http://localhost:8000/documents \
  -H "X-API-Key: your-key" \
  -F "file=@doc.pdf"

# Ask
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Your question?"}'

# List documents
curl http://localhost:8000/documents \
  -H "X-API-Key: your-key"
```

---

## Common Use Cases

### Use Case 1: Customer Support Widget

Embed in your support portal:

```javascript
// Widget on your website
<script>
const widget = new AskDocsWidget({
  apiUrl: 'https://api.askdocs.ai',
  apiKey: 'your-public-key',
  placeholder: 'Ask about our policies...'
});

widget.mount('#support-widget');
</script>
```

### Use Case 2: Internal Knowledge Base

Employee intranet search:

```python
# Internal search tool
def search_handbook(query):
    result = ask_question(query)
    if result.get("answer") == "not_found":
        return "No answer found. Contact HR."
    return f"{result['answer']}\n\nSource: {result['sources'][0]}"
```

### Use Case 3: Mobile App Integration

```swift
// iOS Swift
func askQuestion(question: String) async throws -> Answer {
    let url = URL(string: "https://api.askdocs.ai/ask")!
    var request = URLRequest(url: url)
    request.setValue(apiKey, forHTTPHeaderField: "X-API-Key")
    request.httpMethod = "POST"
    request.httpBody = try JSONEncoder().encode(["question": question])

    let (data, _) = try await URLSession.shared.data(for: request)
    return try JSONDecoder().decode(Answer.self, from: data)
}
```

---

## Security

**API Keys:**
See [core/security/AUTHENTICATION.md](../../core/security/AUTHENTICATION.md)

**Rate Limiting:**
See [core/security/API_SECURITY.md](../../core/security/API_SECURITY.md)

**HTTPS:**
Always use HTTPS in production.

---

## Error Handling

```javascript
async function askQuestionSafely(question) {
  try {
    const result = await askQuestion(question);

    if (result.answer === "not_found") {
      return "Sorry, I couldn't find that in our documents.";
    }

    return result.answer;
  } catch (error) {
    console.error("API error:", error);
    return "Sorry, something went wrong. Please try again.";
  }
}
```

---

## Testing

```bash
# Health check
curl http://localhost:8000/health

# Test upload
curl -X POST http://localhost:8000/documents \
  -H "X-API-Key: test-key" \
  -F "file=@samples/test.pdf"

# Test question
curl -X POST http://localhost:8000/ask \
  -H "X-API-Key: test-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}'
```

---

## Deployment

See [core/deployment/](../../core/deployment/)

**Production checklist:**
- Use HTTPS
- Secure API keys (env vars)
- Set rate limits
- Enable CORS properly
- Monitor usage

---

## Next Steps

1. Get API key from admin
2. Test with sample documents
3. Integrate into your app
4. Monitor usage

**Full API reference:** [core/architecture/API.md](../../core/architecture/API.md)

**Support:** api-support@askdocs.ai
