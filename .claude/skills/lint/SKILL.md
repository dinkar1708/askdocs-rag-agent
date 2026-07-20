---
description: Run code quality checks (linting, formatting, type checking)
---

Perform comprehensive code quality checks on the project.

Steps:
1. Check if ruff is installed: `python -m ruff --version` (if not, suggest: `pip install ruff`)
2. Run ruff linting: `python -m ruff check app/`
3. Check formatting: `python -m ruff format --check app/`
4. Run mypy type checking if available: `python -m mypy app/` (optional)
5. Report all issues with file paths and line numbers
6. Suggest auto-fixes where applicable

Best practices:
- Fix linting errors before committing
- Use `ruff check --fix` to auto-fix issues
- Maintain consistent code style across the project
