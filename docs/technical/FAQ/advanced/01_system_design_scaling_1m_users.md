# Advanced Level: System Design & Scaling to 1 Million Users

---

## 1. Multi-Tier Scaling Architecture

### Q1: How would AskDocs scale to 1 million daily users and 10M queries/day?
**Answer:**

```
                    Users & Client Applications
                                │
                                ▼
                     GCP Cloud Load Balancer
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
       Cloud Run Instance 1            Cloud Run Instance N
       (Stateless FastAPI)             (Stateless FastAPI)
                │                               │
                ├───────────────┬───────────────┤
                ▼               ▼               ▼
          Redis Cluster     PgBouncer     Vector Model Cache
         (Response Cache) (Conn Pooling) (Singleton Memory)
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
       PostgreSQL Primary               PostgreSQL Read Replica
        (Writes & Ingest)                (Read-heavy Vector Q&A)
```

1. **Stateless API Auto-Scaling**:
   - Google Cloud Run or AWS ECS scales container instances from 0 to hundreds horizontally within seconds based on HTTP concurrency.
2. **Connection Pooling with PgBouncer**:
   - Manages thousands of simultaneous client connections efficiently without overwhelming PostgreSQL backend workers.
3. **Database Read Replicas**:
   - 95% of traffic is read-only Q&A retrieval. Routing `SELECT` vector queries to read replicas frees the primary instance for document uploads and ingestion.
4. **Caching Layer (Redis)**:
   - Caching frequent queries (e.g. standard HR questions) with 1-hour TTL saves over 70% of database vector scans and LLM inference calls.
