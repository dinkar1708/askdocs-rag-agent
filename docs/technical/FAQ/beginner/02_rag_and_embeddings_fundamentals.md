# Beginner Level: RAG & Embeddings Fundamentals

---

## 1. Vector Embeddings Explained

### Q1: What are vector embeddings and how are they generated?
**Answer:**
Vector embeddings represent text as arrays of floating-point numbers in a continuous vector space where semantically similar texts are placed close to each other.

```python
from sentence_transformers import SentenceTransformer
import numpy as np

# Load the 384-dimensional embedding model
embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

text_1 = "What is the annual paid vacation policy?"
text_2 = "How many PTO days do employees receive?"
text_3 = "The capital of France is Paris."

# Generate 384-dimensional dense vectors
v1 = embedder.encode(text_1)
v2 = embedder.encode(text_2)
v3 = embedder.encode(text_3)

print("Vector shape:", v1.shape)  # Output: (384,)

# Function to compute cosine similarity
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

print("Similarity (Vacation vs PTO):", cosine_sim(v1, v2))      # ~0.84 (High semantic similarity)
print("Similarity (Vacation vs Paris):", cosine_sim(v1, v3))    # ~0.08 (No semantic similarity)
```

---

## 2. Distance Metrics: Cosine vs Dot Product vs Euclidean

### Q2: Which distance metric is used and why?
**Answer:**

| Metric | Formula | Use Case in AskDocs |
| :--- | :--- | :--- |
| **Cosine Distance** | $1 - \frac{A \cdot B}{\|A\| \|B\|}$ | **Default in AskDocs (`<=>` operator in pgvector)**. Measures angle, independent of text length. |
| **Dot Product** | $-(A \cdot B)$ | Used when vectors are pre-normalized to unit length ($\|A\| = 1$). Fast. |
| **L2 / Euclidean** | $\sqrt{\sum (A_i - B_i)^2}$ | Measures straight-line geometric distance. Sensitive to length differences. |

### Concrete SQL Query with pgvector:
```sql
-- Find top 5 most similar chunks to a query vector
SELECT 
    id,
    document_id,
    page_number,
    text,
    1 - (embedding <=> '[0.0123, -0.0456, 0.0891, ...]'::vector) AS similarity_score
FROM chunks
ORDER BY embedding <=> '[0.0123, -0.0456, 0.0891, ...]'::vector ASC
LIMIT 5;
```
