# Intermediate Level: Retrieval & Cross-Encoder Reranking Pipeline

---

## 1. Two-Stage Retrieval Architecture

### Q1: Why is a two-stage retrieval pipeline necessary in production RAG?
**Answer:**
Single-stage vector search relies on **Bi-Encoders** where queries and document chunks are converted into vectors completely independently. While bi-encoders are fast (milliseconds), they miss nuanced query-document interactions.

**Two-Stage Pipeline:**
1. **Stage 1: Fast Candidate Search (Bi-Encoder)**
   - Retrieves `initial_k=30` candidates using cosine distance in pgvector.
   - High recall, low compute cost (<10ms).
2. **Stage 2: Cross-Encoder Reranking**
   - Feeds `(Query, Chunk Text)` pairs together into a Cross-Encoder transformer model (`BAAI/bge-reranker-v2-m3`).
   - Uses full cross-attention across all tokens in both query and passage.
   - Rescores the 30 candidates and selects the top `final_k=5` highest-quality chunks.

```
Query ──► [Bi-Encoder: Top 30 Candidates] ──► [Cross-Encoder Reranker] ──► Top 5 Chunks
```

---

## 2. Implementation & Code Reference

### Q2: How is reranking implemented in AskDocs?
**Answer:**
In [`app/services/reranker.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/reranker.py) and [`app/services/retriever.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/retriever.py):

```python
def retrieve_with_reranking(
    query: str,
    db: Session,
    initial_k: int = 30,
    final_k: int = 5,
    similarity_threshold: float = 0.2,
    metadata_filters: Optional[Dict] = None
) -> List[Dict]:
    """Two-stage retrieval with cross-encoder reranking"""
    
    # 1. Retrieve candidates
    candidates = retrieve_relevant_chunks(
        query=query,
        db=db,
        top_k=initial_k,
        similarity_threshold=similarity_threshold,
        metadata_filters=metadata_filters
    )
    if not candidates:
        return []
        
    # 2. Rescore candidates with cross-encoder
    reranker = create_reranker()
    final_chunks = reranker.rerank(query, candidates, top_k=final_k)
    return final_chunks
```

**Quality Gain:** Cross-encoder reranking increases overall passage retrieval accuracy and Mean Reciprocal Rank (MRR) by 15–30% without adding latency to the entire corpus.
