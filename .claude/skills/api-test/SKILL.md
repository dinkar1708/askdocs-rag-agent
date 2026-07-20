---
description: Test API endpoints with real requests
---

Perform integration testing of the API endpoints.

Steps:
1. Check if server is running on port 8000
2. If not running, ask if user wants to start it
3. Test health endpoint: `curl http://localhost:8000/ask/health`
4. Test root endpoint: `curl http://localhost:8000/`
5. If user wants, test document upload with sample PDF
6. If user wants, test question-answering endpoint
7. Report response status, times, and any errors
8. Save test results to docs/testing/api-results/ if requested

Best practices:
- Verify all status codes are as expected
- Check response schemas match OpenAPI spec
- Test error cases (404, 422, etc.)
- Measure response times for performance
