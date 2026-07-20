---
description: Initialize or reset the database
---

Set up or reset the SQLite database for the RAG system.

Steps:
1. Check if `askdocs.db` exists
2. If exists, ask user if they want to backup or delete
3. Remove old database: `rm -f askdocs.db` (if confirmed)
4. Initialize new database by starting the app briefly (creates tables automatically)
5. Verify database file exists and has correct schema
6. Report database location and tables created

Best practices:
- Always backup before resetting production data
- Verify database schema matches models
- Check database file permissions
