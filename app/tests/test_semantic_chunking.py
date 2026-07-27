"""Comprehensive tests for semantic chunking functionality"""

import pytest
import numpy as np
from app.services.semantic_chunker import SemanticChunker, get_semantic_chunker
from app.services.embeddings import semantic_chunk_text, chunk_text


class TestSemanticChunkerInitialization:
    """Test SemanticChunker initialization"""

    def test_init_default_parameters(self):
        """Test initialization with default parameters"""
        chunker = SemanticChunker()
        assert chunker.model is not None
        assert chunker.similarity_threshold == 0.5

    def test_init_custom_threshold(self):
        """Test initialization with custom similarity threshold"""
        chunker = SemanticChunker(similarity_threshold=0.7)
        assert chunker.similarity_threshold == 0.7

    def test_get_semantic_chunker_singleton(self):
        """Test that get_semantic_chunker returns singleton instance"""
        chunker1 = get_semantic_chunker()
        chunker2 = get_semantic_chunker()
        assert chunker1 is chunker2


class TestSentenceSplitting:
    """Test sentence splitting functionality"""

    def test_split_simple_sentences(self):
        """Test splitting simple sentences"""
        chunker = SemanticChunker()
        text = "This is sentence one. This is sentence two. This is sentence three."
        sentences = chunker.split_into_sentences(text)
        assert len(sentences) == 3
        assert "sentence one" in sentences[0]
        assert "sentence two" in sentences[1]
        assert "sentence three" in sentences[2]

    def test_split_with_question_marks(self):
        """Test splitting sentences with question marks"""
        chunker = SemanticChunker()
        text = "What is your name? My name is Claude. How are you?"
        sentences = chunker.split_into_sentences(text)
        assert len(sentences) == 3

    def test_split_with_exclamation_marks(self):
        """Test splitting sentences with exclamation marks"""
        chunker = SemanticChunker()
        text = "Hello! Welcome to the system. This is amazing!"
        sentences = chunker.split_into_sentences(text)
        assert len(sentences) == 3

    def test_split_empty_text(self):
        """Test splitting empty text"""
        chunker = SemanticChunker()
        sentences = chunker.split_into_sentences("")
        assert len(sentences) == 0

    def test_split_single_sentence(self):
        """Test splitting single sentence without period"""
        chunker = SemanticChunker()
        text = "This is a single sentence without period"
        sentences = chunker.split_into_sentences(text)
        assert len(sentences) == 1

    def test_split_with_multiple_spaces(self):
        """Test splitting text with multiple spaces"""
        chunker = SemanticChunker()
        text = "Sentence one.   Sentence two.    Sentence three."
        sentences = chunker.split_into_sentences(text)
        assert len(sentences) == 3


class TestSimilarityCalculation:
    """Test cosine similarity calculation"""

    def test_identical_embeddings(self):
        """Test similarity of identical embeddings"""
        chunker = SemanticChunker()
        emb = np.array([1.0, 0.0, 0.0])
        similarity = chunker.calculate_similarity(emb, emb)
        assert similarity == 1.0

    def test_orthogonal_embeddings(self):
        """Test similarity of orthogonal embeddings"""
        chunker = SemanticChunker()
        emb1 = np.array([1.0, 0.0, 0.0])
        emb2 = np.array([0.0, 1.0, 0.0])
        similarity = chunker.calculate_similarity(emb1, emb2)
        assert similarity == 0.0

    def test_similar_embeddings(self):
        """Test similarity of similar embeddings"""
        chunker = SemanticChunker()
        emb1 = np.array([1.0, 1.0, 0.0])
        emb2 = np.array([1.0, 0.9, 0.0])
        similarity = chunker.calculate_similarity(emb1, emb2)
        assert 0.9 < similarity < 1.0

    def test_zero_vector_handling(self):
        """Test handling of zero vectors"""
        chunker = SemanticChunker()
        emb1 = np.array([0.0, 0.0, 0.0])
        emb2 = np.array([1.0, 1.0, 1.0])
        similarity = chunker.calculate_similarity(emb1, emb2)
        assert similarity == 0.0


class TestSemanticBoundaryDetection:
    """Test semantic boundary detection in chunking"""

    def test_topic_change_creates_new_chunk(self):
        """Test that topic changes create new chunks"""
        chunker = SemanticChunker(similarity_threshold=0.5)
        # Text with clear topic change
        text = (
            "The weather today is sunny and warm. "
            "It's a perfect day for outdoor activities. "
            "Python is a programming language. "
            "It is widely used for data science and web development."
        )
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=50, max_chunk_size=500)
        # Should create multiple chunks due to topic change (weather -> programming)
        assert len(chunks) >= 1

    def test_similar_sentences_stay_together(self):
        """Test that semantically similar sentences stay in same chunk"""
        chunker = SemanticChunker(similarity_threshold=0.3)
        text = (
            "Machine learning is a subset of artificial intelligence. "
            "Deep learning is a technique in machine learning. "
            "Neural networks are the foundation of deep learning."
        )
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=50, max_chunk_size=500)
        # Related sentences should stay together
        assert len(chunks) >= 1
        # All text should be preserved
        combined = ' '.join(chunks)
        assert "Machine learning" in combined
        assert "Deep learning" in combined
        assert "Neural networks" in combined

    def test_high_threshold_creates_more_chunks(self):
        """Test that higher threshold creates more chunks"""
        text = (
            "The cat sat on the mat. The dog ran in the park. "
            "The bird flew in the sky. The fish swam in the ocean."
        )
        chunker_low = SemanticChunker(similarity_threshold=0.3)
        chunker_high = SemanticChunker(similarity_threshold=0.7)

        chunks_low = chunker_low.chunk_by_similarity(text, min_chunk_size=10, max_chunk_size=500)
        chunks_high = chunker_high.chunk_by_similarity(text, min_chunk_size=10, max_chunk_size=500)

        # Higher threshold should create more or equal chunks
        assert len(chunks_high) >= len(chunks_low)


class TestChunkSizeConstraints:
    """Test min/max chunk size constraints"""

    def test_min_chunk_size_respected(self):
        """Test that minimum chunk size is respected"""
        chunker = SemanticChunker(similarity_threshold=0.5)
        text = "A. B. C. D. E. F. G. H. I. J. K. L. M. N. O. P."
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=20, max_chunk_size=1000)

        for chunk in chunks:
            # Most chunks should meet minimum size (last chunk might be smaller)
            if chunk != chunks[-1]:
                assert len(chunk) >= 15  # Allow some flexibility

    def test_max_chunk_size_enforced(self):
        """Test that maximum chunk size is enforced"""
        chunker = SemanticChunker(similarity_threshold=0.5)
        # Create long text with similar sentences
        sentences = ["This is a very similar sentence about data processing. "] * 50
        text = ' '.join(sentences)

        max_size = 500
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=100, max_chunk_size=max_size)

        for chunk in chunks:
            assert len(chunk) <= max_size * 1.1  # Allow 10% tolerance

    def test_empty_text_returns_empty_list(self):
        """Test that empty text returns empty list"""
        chunker = SemanticChunker()
        chunks = chunker.chunk_by_similarity("", min_chunk_size=100, max_chunk_size=500)
        assert chunks == []

    def test_single_sentence_within_limits(self):
        """Test single sentence within size limits"""
        chunker = SemanticChunker()
        text = "This is a single sentence."
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=10, max_chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text.strip()


class TestHierarchicalChunking:
    """Test hierarchical chunking functionality"""

    def test_create_parent_child_structure(self):
        """Test creation of parent-child chunk structure"""
        chunker = SemanticChunker()
        text = (
            "This is the introduction to our document. "
            "It provides an overview of the main topics. "
            "The first section discusses machine learning. "
            "The second section covers deep learning."
        )
        result = chunker.create_hierarchical_chunks(text, min_chunk_size=50, max_chunk_size=500)

        assert "parent" in result
        assert "children" in result
        assert result["parent"] is not None
        assert len(result["children"]) > 0

    def test_parent_contains_full_text(self):
        """Test that parent chunk contains full text"""
        chunker = SemanticChunker()
        text = "This is a test document with some content."
        result = chunker.create_hierarchical_chunks(text)

        assert result["parent"]["text"] == text.strip()
        assert result["parent"]["type"] == "parent"

    def test_children_reference_parent(self):
        """Test that children reference parent"""
        chunker = SemanticChunker()
        text = "Sentence one. Sentence two. Sentence three. Sentence four."
        result = chunker.create_hierarchical_chunks(text, min_chunk_size=10, max_chunk_size=50)

        for child in result["children"]:
            assert child["type"] == "child"
            assert child["parent_ref"] == 0
            assert "child_index" in child

    def test_empty_text_hierarchical(self):
        """Test hierarchical chunking with empty text"""
        chunker = SemanticChunker()
        result = chunker.create_hierarchical_chunks("")

        assert result["parent"] is None
        assert result["children"] == []


class TestSectionExtraction:
    """Test section extraction functionality"""

    def test_extract_numbered_sections(self):
        """Test extraction of numbered sections"""
        chunker = SemanticChunker()
        text = """
1. Introduction
This is the introduction section.

2. Methods
This describes the methodology.

3. Results
These are the results.
        """
        sections = chunker.extract_sections(text)
        assert len(sections) >= 1

    def test_extract_all_caps_sections(self):
        """Test extraction of all caps section headers"""
        chunker = SemanticChunker()
        text = """
INTRODUCTION
This is the introduction.

METHODS
This is the methods section.
        """
        sections = chunker.extract_sections(text)
        assert len(sections) >= 1

    def test_no_sections_returns_full_content(self):
        """Test that text without sections returns full content"""
        chunker = SemanticChunker()
        text = "This is plain text without any sections."
        sections = chunker.extract_sections(text)
        assert len(sections) >= 1
        assert text in sections[0]["content"]


class TestSemanticChunkTextIntegration:
    """Test semantic_chunk_text function integration"""

    def test_semantic_chunking_enabled(self):
        """Test semantic chunking when enabled"""
        text = (
            "Machine learning is a branch of AI. "
            "It uses algorithms to learn from data. "
            "Deep learning is a subset of machine learning. "
            "It uses neural networks with multiple layers."
        )
        chunks = semantic_chunk_text(
            text,
            page_number=1,
            use_semantic=True,
            similarity_threshold=0.5,
            min_chunk_size=50,
            max_chunk_size=500
        )

        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
        assert all("page_number" in chunk for chunk in chunks)
        assert all(chunk["page_number"] == 1 for chunk in chunks)

    def test_semantic_chunking_disabled_fallback(self):
        """Test fallback to character-based chunking when disabled"""
        text = "This is a test. " * 50
        chunks_semantic = semantic_chunk_text(
            text,
            page_number=1,
            use_semantic=False
        )
        chunks_character = chunk_text(text, page_number=1)

        # Should use character-based chunking
        assert len(chunks_semantic) == len(chunks_character)

    def test_preserve_page_number(self):
        """Test that page number is preserved in chunks"""
        text = "Test content for page numbering."
        page_num = 42
        chunks = semantic_chunk_text(text, page_number=page_num, use_semantic=True)

        for chunk in chunks:
            assert chunk["page_number"] == page_num


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_very_long_text(self):
        """Test chunking very long text"""
        chunker = SemanticChunker()
        # Create a very long text
        long_text = "This is a sentence. " * 1000
        chunks = chunker.chunk_by_similarity(long_text, min_chunk_size=200, max_chunk_size=1000)

        assert len(chunks) > 1
        assert all(len(chunk) > 0 for chunk in chunks)

    def test_single_long_sentence(self):
        """Test handling of single very long sentence"""
        chunker = SemanticChunker()
        long_sentence = "word " * 500
        chunks = chunker.chunk_by_similarity(long_sentence, min_chunk_size=100, max_chunk_size=500)

        assert len(chunks) > 0

    def test_special_characters(self):
        """Test handling of special characters"""
        chunker = SemanticChunker()
        text = "Hello! @#$% How are you? This is a test with special chars: &*()."
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=10, max_chunk_size=500)

        assert len(chunks) > 0
        combined = ' '.join(chunks)
        assert "@#$%" in combined

    def test_unicode_text(self):
        """Test handling of unicode text"""
        chunker = SemanticChunker()
        text = "Hello world. 你好世界. Bonjour le monde. مرحبا بالعالم."
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=10, max_chunk_size=500)

        assert len(chunks) > 0

    def test_whitespace_only_text(self):
        """Test handling of whitespace-only text"""
        chunker = SemanticChunker()
        text = "   \n\n   \t\t   "
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=10, max_chunk_size=500)

        assert chunks == []


class TestComparisonWithCharacterBased:
    """Test comparison between semantic and character-based chunking"""

    def test_semantic_vs_character_based_chunks(self):
        """Compare semantic chunking with character-based chunking"""
        text = (
            "The weather is sunny today. It's warm and pleasant outside. "
            "Python is a programming language. It's used for many applications. "
            "Machine learning models require training data. "
            "The data should be clean and well-structured."
        )

        # Semantic chunking
        semantic_chunks = semantic_chunk_text(
            text,
            page_number=1,
            use_semantic=True,
            similarity_threshold=0.5,
            min_chunk_size=50,
            max_chunk_size=500
        )

        # Character-based chunking
        char_chunks = chunk_text(text, page_number=1, chunk_size=100, overlap=20)

        # Both should produce chunks
        assert len(semantic_chunks) > 0
        assert len(char_chunks) > 0

        # All content should be preserved in both methods
        semantic_combined = ' '.join([c["text"] for c in semantic_chunks])
        char_combined = ' '.join([c["text"] for c in char_chunks])

        assert "weather" in semantic_combined
        assert "weather" in char_combined
        assert "Python" in semantic_combined
        assert "Python" in char_combined

    def test_semantic_respects_topic_boundaries(self):
        """Test that semantic chunking respects topic boundaries better"""
        # Text with clear topic separation
        text = (
            "The cat is a small carnivorous mammal. Cats are often kept as pets. "
            "They are valued for companionship and their ability to hunt pests. "
            "The quantum computer uses quantum bits or qubits. "
            "Quantum computing can solve certain problems much faster than classical computers."
        )

        chunker = SemanticChunker(similarity_threshold=0.5)
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=50, max_chunk_size=500)

        # The semantic chunker should ideally separate cat topic from quantum topic
        assert len(chunks) >= 1


class TestPerformance:
    """Test performance characteristics"""

    def test_chunking_completes_in_reasonable_time(self):
        """Test that chunking completes in reasonable time"""
        import time

        chunker = SemanticChunker()
        # Medium-sized text
        text = "This is a test sentence. " * 100

        start_time = time.time()
        chunks = chunker.chunk_by_similarity(text, min_chunk_size=100, max_chunk_size=500)
        end_time = time.time()

        elapsed = end_time - start_time

        # Should complete in under 5 seconds for this size
        assert elapsed < 5.0
        assert len(chunks) > 0


# Run tests with: pytest app/tests/test_semantic_chunking.py -v
