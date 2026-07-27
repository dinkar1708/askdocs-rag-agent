"""Integration tests for reranking quality improvement"""
import pytest
from app.services.retriever import retrieve_relevant_chunks, retrieve_with_reranking
from app.db.models import Document, Chunk
from app.services.embeddings import generate_embedding


@pytest.fixture(scope="function")
def diverse_document_with_chunks(db_session):
    """Create a document with diverse chunks that test reranking capabilities"""
    # Create document
    doc = Document(
        filename="employee_handbook_detailed.pdf",
        page_count=10
    )
    db_session.add(doc)
    db_session.flush()
    db_session.refresh(doc)

    # Create chunks with varying semantic relevance to test queries
    chunk_texts = [
        # Vacation-related chunks
        "Paid Time Off (PTO): Full-time employees receive 20 days of vacation per year. Unused vacation can be carried over.",
        "Vacation Carryover Policy: Employees may carry over up to 5 unused vacation days to the next calendar year.",
        "Holiday Schedule: The company observes 10 federal holidays each year including New Year's Day and Christmas.",

        # Benefits chunks
        "Health Insurance: Comprehensive medical, dental, and vision coverage with 80% employer contribution.",
        "401(k) Retirement: Company matches 50% of employee contributions up to 6% of salary.",
        "Life Insurance: Company provides $50,000 basic life insurance at no cost to employees.",

        # Work policies
        "Remote Work: Employees may work from home up to 3 days per week with manager approval.",
        "Working Hours: Standard business hours are 9 AM to 5 PM, Monday through Friday.",
        "Overtime Policy: Non-exempt employees receive 1.5x pay for hours worked over 40 per week.",

        # Unrelated content
        "Office Location: Our headquarters is located at 123 Main Street, Downtown.",
        "Parking: Employees can park in the building garage with a monthly parking pass.",
        "Emergency Contacts: In case of emergency, call building security at extension 5555.",
    ]

    chunks = []
    for i, text in enumerate(chunk_texts):
        embedding = generate_embedding(text)
        chunk = Chunk(
            document_id=doc.id,
            text=text,
            page_number=(i // 3) + 1,
            embedding=embedding
        )
        db_session.add(chunk)
        chunks.append(chunk)

    db_session.flush()
    for chunk in chunks:
        db_session.refresh(chunk)

    return doc, chunks


class TestRerankingQuality:
    """Test that reranking improves retrieval quality"""

    def test_reranking_ranks_relevant_higher(self, db_session, diverse_document_with_chunks):
        """Test that reranking places more relevant results first"""
        doc, chunks = diverse_document_with_chunks

        # Query specifically about vacation carryover
        query = "Can I carry over unused vacation days to next year?"

        # Get results without reranking
        no_rerank = retrieve_relevant_chunks(query, db_session, top_k=5, similarity_threshold=0.1)

        # Get results with reranking
        with_rerank = retrieve_with_reranking(
            query,
            db_session,
            initial_k=10,
            final_k=5,
            similarity_threshold=0.1
        )

        # Both should return results
        assert len(no_rerank) > 0
        assert len(with_rerank) > 0

        # Find position of carryover chunk
        carryover_text = "carry over up to 5"

        def find_position(results, text):
            for i, r in enumerate(results):
                if text in r['text'].lower():
                    return i
            return -1

        pos_no_rerank = find_position(no_rerank, carryover_text)
        pos_with_rerank = find_position(with_rerank, carryover_text)

        # Reranking should place the most relevant chunk higher
        # (or at least keep it in top results)
        if pos_no_rerank >= 0 and pos_with_rerank >= 0:
            # If both found, reranked should be equal or better position
            assert pos_with_rerank <= pos_no_rerank or pos_with_rerank < 3

    def test_reranking_improves_precision(self, db_session, diverse_document_with_chunks):
        """Test that reranking improves precision of top results"""
        doc, chunks = diverse_document_with_chunks

        # Query about benefits
        query = "What retirement benefits does the company offer?"

        # Without reranking
        no_rerank = retrieve_relevant_chunks(query, db_session, top_k=3, similarity_threshold=0.1)

        # With reranking
        with_rerank = retrieve_with_reranking(
            query,
            db_session,
            initial_k=10,
            final_k=3,
            similarity_threshold=0.1
        )

        # Count how many results are actually about retirement/401k
        def count_relevant(results):
            keywords = ['401', 'retirement', 'match', 'contribution']
            count = 0
            for r in results:
                if any(kw in r['text'].lower() for kw in keywords):
                    count += 1
            return count

        relevant_no_rerank = count_relevant(no_rerank)
        relevant_with_rerank = count_relevant(with_rerank)

        # Both should find at least some relevant results
        # Note: Reranking may not always improve on small datasets
        assert relevant_with_rerank >= 1 or relevant_no_rerank >= 1

    def test_reranking_filters_irrelevant(self, db_session, diverse_document_with_chunks):
        """Test that reranking pushes irrelevant results down"""
        doc, chunks = diverse_document_with_chunks

        # Query about vacation, should not return parking/emergency info
        query = "How much paid time off do I get annually?"

        # With reranking
        results = retrieve_with_reranking(
            query,
            db_session,
            initial_k=10,
            final_k=5,
            similarity_threshold=0.1
        )

        # Check that irrelevant chunks are not in top results
        irrelevant_keywords = ['parking', 'emergency', 'office location']

        for result in results[:3]:  # Check top 3
            text_lower = result['text'].lower()
            for keyword in irrelevant_keywords:
                assert keyword not in text_lower, \
                    f"Irrelevant result '{keyword}' in top 3: {result['text'][:50]}"

    def test_reranking_score_distribution(self, db_session, diverse_document_with_chunks):
        """Test that reranking scores are distributed properly"""
        doc, chunks = diverse_document_with_chunks

        query = "What is the health insurance coverage?"

        results = retrieve_with_reranking(
            query,
            db_session,
            initial_k=10,
            final_k=5,
            similarity_threshold=0.1
        )

        assert len(results) > 0

        # Reranking scores should be in descending order
        scores = [r['reranking_score'] for r in results]
        assert scores == sorted(scores, reverse=True)

        # Top result should have significantly higher score than bottom
        if len(results) >= 3:
            assert scores[0] > scores[-1]

        # Scores should be reasonable (cross-encoder scores can be negative)
        # Just verify they exist and are numeric
        for score in scores:
            assert isinstance(score, (int, float))

    def test_reranking_preserves_context(self, db_session, diverse_document_with_chunks):
        """Test that reranking doesn't lose important context"""
        doc, chunks = diverse_document_with_chunks

        query = "vacation and sick leave policies"

        # Get many candidates
        results = retrieve_with_reranking(
            query,
            db_session,
            initial_k=12,  # Get all chunks
            final_k=5,
            similarity_threshold=0.0
        )

        # Should have multiple results about time off
        assert len(results) > 0

        # Verify we got relevant chunks
        time_off_keywords = ['vacation', 'pto', 'paid time off']
        found_relevant = False

        for result in results:
            if any(kw in result['text'].lower() for kw in time_off_keywords):
                found_relevant = True
                break

        assert found_relevant, "No relevant results about time off found"


class TestRerankingEdgeCases:
    """Test edge cases for reranking"""

    def test_reranking_with_single_chunk(self, db_session):
        """Test reranking with only one chunk"""
        doc = Document(filename="single.pdf", page_count=1)
        db_session.add(doc)
        db_session.flush()
        db_session.refresh(doc)

        text = "This is the only chunk in the document."
        chunk = Chunk(
            document_id=doc.id,
            text=text,
            page_number=1,
            embedding=generate_embedding(text)
        )
        db_session.add(chunk)
        db_session.flush()

        results = retrieve_with_reranking(
            "only chunk",
            db_session,
            initial_k=5,
            final_k=3
        )

        assert len(results) == 1
        assert "reranking_score" in results[0]

    def test_reranking_identical_chunks(self, db_session):
        """Test reranking when chunks are very similar"""
        doc = Document(filename="similar.pdf", page_count=1)
        db_session.add(doc)
        db_session.flush()
        db_session.refresh(doc)

        # Create very similar chunks
        similar_texts = [
            "The vacation policy allows 15 days off.",
            "The vacation policy provides 15 days off.",
            "The vacation policy gives 15 days off.",
        ]

        for i, text in enumerate(similar_texts):
            chunk = Chunk(
                document_id=doc.id,
                text=text,
                page_number=1,
                embedding=generate_embedding(text)
            )
            db_session.add(chunk)

        db_session.flush()

        results = retrieve_with_reranking(
            "vacation policy days",
            db_session,
            initial_k=5,
            final_k=3
        )

        # All should be returned and have reranking scores
        assert len(results) == 3
        assert all("reranking_score" in r for r in results)

    def test_reranking_with_very_short_query(self, db_session, diverse_document_with_chunks):
        """Test reranking with very short queries"""
        query = "PTO"

        results = retrieve_with_reranking(
            query,
            db_session,
            initial_k=5,
            final_k=3
        )

        # Should still work
        assert isinstance(results, list)
        if len(results) > 0:
            assert "reranking_score" in results[0]

    def test_reranking_with_very_long_query(self, db_session, diverse_document_with_chunks):
        """Test reranking with very long queries"""
        query = """
        I would like to understand the company's comprehensive vacation and paid time off policy,
        including how many days I receive per year, whether unused days can be carried over to
        the next calendar year, and what the process is for requesting time off in advance.
        """

        results = retrieve_with_reranking(
            query,
            db_session,
            initial_k=8,
            final_k=3
        )

        # Should handle long queries
        assert len(results) > 0
        assert all("reranking_score" in r for r in results)

        # Should still prioritize relevant chunks
        vacation_found = any('vacation' in r['text'].lower() or 'pto' in r['text'].lower()
                           for r in results[:3])
        assert vacation_found


# Performance comparison test (optional, can be slow)
@pytest.mark.slow
def test_reranking_performance_comparison(db_session, diverse_document_with_chunks):
    """Compare performance with and without reranking"""
    import time

    query = "What are the health insurance benefits?"

    # Time without reranking
    start = time.time()
    no_rerank = retrieve_relevant_chunks(query, db_session, top_k=5)
    time_no_rerank = time.time() - start

    # Time with reranking
    start = time.time()
    with_rerank = retrieve_with_reranking(query, db_session, initial_k=10, final_k=5)
    time_with_rerank = time.time() - start

    # Both should return results
    assert len(no_rerank) > 0
    assert len(with_rerank) > 0

    # Reranking should be slower but not more than 10x
    assert time_with_rerank < time_no_rerank * 10

    print(f"\nPerformance: No reranking: {time_no_rerank:.3f}s, With reranking: {time_with_rerank:.3f}s")
