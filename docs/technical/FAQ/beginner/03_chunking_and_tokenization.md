# Beginner Level: Chunking & Tokenization

---

## 1. Text Chunking Implementations

### Q1: How does character-based recursive chunking work?
**Answer:**
Using LangChain's `RecursiveCharacterTextSplitter`, text is split hierarchically by `["\n\n", "\n", " ", ""]` to preserve paragraph and sentence structure while respecting token limits:

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

text = """
1. Paid Time Off (PTO)
Full-time employees accrue 15 days of paid vacation per year, starting from their first day of employment. 
PTO must be approved by the department manager at least 2 weeks in advance.

2. Sick Leave
Employees receive 10 days of sick leave annually. Sick leave does not roll over to the subsequent calendar year.

3. Health Benefits
Comprehensive health insurance coverage including medical, dental, and vision is provided after 30 days.
"""

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,       # Max characters per chunk (default in tokens in prod)
    chunk_overlap=50,      # Overlap to prevent boundary information loss
    separators=["\n\n", "\n", " ", ""]
)

chunks = splitter.split_text(text)
for i, chunk in enumerate(chunks):
    print(f"--- Chunk {i+1} ({len(chunk)} chars) ---")
    print(chunk.strip())
```

---

## 2. Semantic Chunking Implementation

### Q2: How does AskDocs implement semantic boundary detection?
**Answer:**
In [`app/services/semantic_chunker.py`](file:///Users/dinakarmaurya/Documents/Personal/askdocs-rag-agent/app/services/semantic_chunker.py), text is split by semantic shifts rather than fixed character counts:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

embedder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

sentences = [
    "Employees are entitled to 15 days of paid annual leave.",
    "Unused vacation days can be carried over up to a maximum of 5 days.",
    "The engineering team uses Kotlin and Python for all backend microservices.",
    "All pull requests must pass automated linting and unit tests."
]

embeddings = embedder.encode(sentences)

# Compute similarity between adjacent sentences:
print("Similarity S1 -> S2 (Both about Vacation):")
sim_1_2 = np.dot(embeddings[0], embeddings[1]) / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
print(f"Score: {sim_1_2:.3f}")  # ~0.72 (High -> Same chunk)

print("\nSimilarity S2 -> S3 (Shift from Vacation to Tech Stack):")
sim_2_3 = np.dot(embeddings[1], embeddings[2]) / (np.linalg.norm(embeddings[1]) * np.linalg.norm(embeddings[2]))
print(f"Score: {sim_2_3:.3f}")  # ~0.15 (Low -> Boundary split triggered!)
```
