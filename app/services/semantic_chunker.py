"""Semantic chunking service - chunks text by topic/meaning instead of character count"""

from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import re


class SemanticChunker:
    """Chunk text based on semantic similarity between sentences"""

    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        similarity_threshold: float = 0.5
    ):
        """Initialize with sentence transformer model

        Args:
            model_name: Name of the sentence transformer model to use
            similarity_threshold: Threshold below which to create new chunk (0-1)
        """
        self.model = SentenceTransformer(model_name)
        self.similarity_threshold = similarity_threshold

    def chunk_by_similarity(
        self,
        text: str,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1000
    ) -> List[str]:
        """
        Split text at points where sentence similarity drops below threshold.

        Algorithm:
        1. Split text into sentences
        2. Embed each sentence
        3. Calculate similarity between consecutive sentences
        4. When similarity drops below threshold, start new chunk
        5. Respect min/max chunk size constraints

        Args:
            text: Text to chunk
            min_chunk_size: Minimum characters per chunk
            max_chunk_size: Maximum characters per chunk

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        # Split into sentences
        sentences = self.split_into_sentences(text)

        if len(sentences) == 0:
            return []

        if len(sentences) == 1:
            return [text.strip()]

        # Embed all sentences
        embeddings = self.model.encode(sentences, convert_to_numpy=True)

        # Build chunks based on similarity
        chunks = []
        current_chunk_sentences = [sentences[0]]
        current_chunk_length = len(sentences[0])

        for i in range(1, len(sentences)):
            sentence = sentences[i]
            sentence_length = len(sentence)

            # Calculate similarity between consecutive sentences
            similarity = self.calculate_similarity(
                embeddings[i-1],
                embeddings[i]
            )

            # Check if we should start a new chunk
            should_split = False

            # Split if similarity drops below threshold (topic change)
            if similarity < self.similarity_threshold:
                # But only split if current chunk meets minimum size
                if current_chunk_length >= min_chunk_size:
                    should_split = True

            # Force split if we exceed max chunk size
            if current_chunk_length + sentence_length > max_chunk_size:
                should_split = True

            if should_split and current_chunk_sentences:
                # Save current chunk
                chunk_text = ' '.join(current_chunk_sentences)
                chunks.append(chunk_text.strip())

                # Start new chunk
                current_chunk_sentences = [sentence]
                current_chunk_length = sentence_length
            else:
                # Add to current chunk
                current_chunk_sentences.append(sentence)
                current_chunk_length += sentence_length

        # Add final chunk
        if current_chunk_sentences:
            chunk_text = ' '.join(current_chunk_sentences)
            chunks.append(chunk_text.strip())

        return chunks

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex patterns

        This is a simple implementation that works well for most text.
        For more complex sentence boundary detection, consider using
        NLTK or spaCy.

        Args:
            text: Text to split

        Returns:
            List of sentences
        """
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Split on sentence boundaries
        # Matches: . ! ? followed by space and capital letter or end of string
        sentence_endings = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
        sentences = re.split(sentence_endings, text)

        # Filter out empty sentences and clean up
        sentences = [s.strip() for s in sentences if s.strip()]

        return sentences

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """Calculate cosine similarity between embeddings

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Cosine similarity: dot product of normalized vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)

        # Clip to [0, 1] range (cosine similarity can be [-1, 1])
        # We use max(0, sim) to treat negative similarity as 0
        return float(max(0.0, min(1.0, similarity)))

    def create_hierarchical_chunks(
        self,
        text: str,
        section_headers: Optional[List[str]] = None,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1000
    ) -> Dict[str, any]:
        """
        Create parent-child chunk relationships:
        - Parent = full section or entire text
        - Children = semantic sub-chunks within section

        Args:
            text: Text to chunk
            section_headers: Optional list of detected section headers
            min_chunk_size: Minimum characters per child chunk
            max_chunk_size: Maximum characters per child chunk

        Returns:
            Dict with structure:
            {
                "parent": {"text": "...", "type": "parent"},
                "children": [
                    {"text": "...", "type": "child", "parent_ref": 0},
                    ...
                ]
            }
        """
        if not text or not text.strip():
            return {"parent": None, "children": []}

        # Create parent chunk (entire text or section)
        parent = {
            "text": text.strip(),
            "type": "parent"
        }

        # Create children chunks using semantic chunking
        child_chunks = self.chunk_by_similarity(
            text,
            min_chunk_size=min_chunk_size,
            max_chunk_size=max_chunk_size
        )

        children = []
        for idx, chunk_text in enumerate(child_chunks):
            children.append({
                "text": chunk_text,
                "type": "child",
                "parent_ref": 0,  # Reference to parent (could be parent ID in DB)
                "child_index": idx
            })

        return {
            "parent": parent,
            "children": children
        }

    def extract_sections(self, text: str) -> List[Dict[str, str]]:
        """Extract sections from text based on common header patterns

        This looks for common section markers like:
        - All caps headers: SECTION 1
        - Numbered headers: 1. Introduction
        - Markdown headers: ## Section

        Args:
            text: Text to analyze

        Returns:
            List of sections with title and content
        """
        sections = []

        # Pattern for section headers (simplified)
        # Matches: numbered sections, all caps, or markdown headers
        header_pattern = r'^(?:(?:\d+\.?\s+[A-Z].*)|(?:[A-Z\s]{3,})|(?:#{1,6}\s+.+))$'

        lines = text.split('\n')
        current_section = {"title": "Introduction", "content": []}

        for line in lines:
            line_stripped = line.strip()
            if re.match(header_pattern, line_stripped):
                # Save previous section if it has content
                if current_section["content"]:
                    current_section["content"] = '\n'.join(current_section["content"])
                    sections.append(current_section)

                # Start new section
                current_section = {
                    "title": line_stripped,
                    "content": []
                }
            else:
                if line_stripped:  # Skip empty lines
                    current_section["content"].append(line_stripped)

        # Add final section
        if current_section["content"]:
            current_section["content"] = '\n'.join(current_section["content"])
            sections.append(current_section)

        return sections if sections else [{"title": "Content", "content": text}]


# Singleton instance for reuse
_semantic_chunker_instance = None


def get_semantic_chunker(
    similarity_threshold: float = 0.5
) -> SemanticChunker:
    """Get or create semantic chunker instance (singleton pattern)

    Args:
        similarity_threshold: Threshold for semantic similarity

    Returns:
        SemanticChunker instance
    """
    global _semantic_chunker_instance
    if _semantic_chunker_instance is None:
        _semantic_chunker_instance = SemanticChunker(
            similarity_threshold=similarity_threshold
        )
    return _semantic_chunker_instance
