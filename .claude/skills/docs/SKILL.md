---
description: Generate or update project documentation
---

Create or update documentation for the askdocs RAG project.

Steps:
1. Identify what needs documentation:
   - New features or endpoints
   - API changes
   - Architecture decisions
   - Setup/deployment instructions
2. Check existing docs in docs/ directory
3. Generate appropriate documentation:
   - API examples in docs/interfaces/api/examples/
   - Architecture docs in docs/architecture/
   - Testing guides in docs/testing/
4. Update README.md if needed
5. Ensure code has docstrings for public functions
6. Generate API documentation if OpenAPI spec changed

Best practices:
- Keep docs in sync with code
- Include examples for all endpoints
- Document environment variables
- Explain architectural decisions
- Provide troubleshooting guides
