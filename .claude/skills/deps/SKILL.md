---
description: Install or update project dependencies
---

Manage Python dependencies for the askdocs RAG project.

Steps:
1. Check if virtual environment is activated (look for venv indicator)
2. If not activated, warn user and suggest activation
3. Install/update dependencies: `pip install -r requirements.txt`
4. If requirements.txt doesn't exist, check for pyproject.toml
5. Show installed packages: `pip list | grep -E "(fastapi|langchain|openai|sqlalchemy)"`
6. Check for outdated packages: `pip list --outdated`
7. Report any dependency conflicts or warnings

Best practices:
- Always use virtual environment
- Pin dependency versions in requirements.txt
- Review security advisories for outdated packages
- Test after updating dependencies
