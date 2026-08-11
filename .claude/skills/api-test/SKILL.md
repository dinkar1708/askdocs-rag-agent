---
description: Test API endpoints with real requests
---

Perform integration testing of the API endpoints.

Steps:
1. Check if server is running on port 8000
2. If not running, ask if user wants to start it

3. **Test authentication**:
   - Test WITHOUT API key (should get 401/403):
     ```bash
     curl http://localhost:8000/ask -X POST -H "Content-Type: application/json" -d '{"question":"test"}'
     ```
   - Test WITH valid API key (should work):
     ```bash
     curl http://localhost:8000/ask -X POST \
       -H "Content-Type: application/json" \
       -H "X-API-Key: your-api-key" \
       -d '{"question":"test"}'
     ```
   - Test with invalid API key (should get 403):
     ```bash
     curl http://localhost:8000/ask -X POST \
       -H "Content-Type: application/json" \
       -H "X-API-Key: wrong-key" \
       -d '{"question":"test"}'
     ```

4. Test health endpoint: `curl http://localhost:8000/health` (should not require auth)
5. Test root endpoint: `curl http://localhost:8000/` (should not require auth)
6. If user wants, test document upload with sample PDF (with auth)
7. If user wants, test question-answering endpoint (with auth)
8. Report response status, times, and any errors
9. Save test results to docs/testing/api-results/ if requested

Best practices:
- **Always test authentication first** - protected endpoints should reject requests without API key
- Verify all status codes are as expected (401 for missing auth, 403 for invalid auth)
- Check response schemas match OpenAPI spec
- Test error cases (404, 422, etc.)
- Measure response times for performance
- Verify all protected endpoints (documents, ask, sessions, extract) require authentication
