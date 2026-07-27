"""Tests for reranking service"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.reranker import Reranker, create_reranker


class TestReranker:
    """Test suite for Reranker class"""

    @pytest.fixture
    def mock_cross_encoder(self):
        """Mock CrossEncoder model"""
        with patch('app.services.reranker.CrossEncoder') as mock_ce:
            mock_model = Mock()
            mock_ce.return_value = mock_model
            yield mock_model

    @pytest.fixture
    def reranker(self, mock_cross_encoder):
        """Create a Reranker instance with mocked model"""
        return Reranker(model_name='test-model')

    @pytest.fixture
    def sample_chunks(self):
        """Sample chunks for testing"""
        return [
            {
                "chunk_id": 1,
                "text": "Vacation days can be carried over up to 5 days per year.",
                "filename": "policy.pdf",
                "page_number": 1,
                "similarity_score": 0.70
            },
            {
                "chunk_id": 2,
                "text": "Sick leave policy allows 10 days annually.",
                "filename": "policy.pdf",
                "page_number": 2,
                "similarity_score": 0.75
            },
            {
                "chunk_id": 3,
                "text": "Holiday schedule for next year is available.",
                "filename": "policy.pdf",
                "page_number": 3,
                "similarity_score": 0.68
            }
        ]

    def test_reranker_initialization(self):
        """Test that reranker initializes with default model"""
        reranker = Reranker()
        assert reranker.model_name == 'BAAI/bge-reranker-v2-m3'
        assert reranker._model is None  # Lazy loading

    def test_reranker_custom_model(self):
        """Test reranker with custom model name"""
        reranker = Reranker(model_name='custom-model')
        assert reranker.model_name == 'custom-model'

    def test_lazy_model_loading(self, mock_cross_encoder):
        """Test that model is loaded lazily on first access"""
        reranker = Reranker(model_name='test-model')
        assert reranker._model is None

        # Access model property to trigger loading
        model = reranker.model
        assert model is not None
        assert model == mock_cross_encoder

    def test_rerank_improves_ranking(self, reranker, mock_cross_encoder, sample_chunks):
        """Test that reranking reorders chunks based on relevance"""
        query = "vacation carryover policy"

        # Mock scores: vacation chunk gets highest score despite lower initial similarity
        mock_scores = [0.95, 0.60, 0.40]  # Vacation, sick leave, holiday
        mock_cross_encoder.predict.return_value = mock_scores

        result = reranker.rerank(query, sample_chunks, top_k=3)

        # Verify CrossEncoder was called correctly
        mock_cross_encoder.predict.assert_called_once()
        call_args = mock_cross_encoder.predict.call_args[0][0]
        assert len(call_args) == 3
        assert call_args[0] == (query, sample_chunks[0]['text'])

        # Check results
        assert len(result) == 3

        # Vacation chunk should be first (highest reranking score)
        assert result[0]['chunk_id'] == 1
        assert result[0]['reranking_score'] == 0.95
        assert result[0]['original_similarity'] == 0.70

        # Sick leave should be second
        assert result[1]['chunk_id'] == 2
        assert result[1]['reranking_score'] == 0.60

        # Holiday should be third
        assert result[2]['chunk_id'] == 3
        assert result[2]['reranking_score'] == 0.40

    def test_rerank_top_k_limits_results(self, reranker, mock_cross_encoder, sample_chunks):
        """Test that top_k parameter limits number of results"""
        query = "vacation policy"
        mock_scores = [0.9, 0.8, 0.7]
        mock_cross_encoder.predict.return_value = mock_scores

        result = reranker.rerank(query, sample_chunks, top_k=2)

        assert len(result) == 2
        assert result[0]['reranking_score'] == 0.9
        assert result[1]['reranking_score'] == 0.8

    def test_rerank_empty_chunks(self, reranker):
        """Test reranking with empty chunks list"""
        query = "any question"
        result = reranker.rerank(query, [], top_k=5)

        assert result == []

    def test_rerank_empty_query_raises_error(self, reranker, sample_chunks):
        """Test that empty query raises ValueError"""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            reranker.rerank("", sample_chunks, top_k=5)

        with pytest.raises(ValueError, match="Query cannot be empty"):
            reranker.rerank("   ", sample_chunks, top_k=5)

    def test_rerank_preserves_original_similarity(self, reranker, mock_cross_encoder, sample_chunks):
        """Test that original similarity scores are preserved"""
        query = "test query"
        mock_scores = [0.9, 0.8, 0.7]
        mock_cross_encoder.predict.return_value = mock_scores

        result = reranker.rerank(query, sample_chunks, top_k=3)

        # Original similarity should be preserved
        assert result[0]['original_similarity'] == 0.70
        assert result[1]['original_similarity'] == 0.75
        assert result[2]['original_similarity'] == 0.68

        # Similarity score should still exist
        assert 'similarity_score' in result[0]

    def test_rerank_handles_model_errors_gracefully(self, reranker, mock_cross_encoder, sample_chunks):
        """Test that reranking falls back to original order if model fails"""
        query = "test query"
        mock_cross_encoder.predict.side_effect = Exception("Model error")

        # Should return original chunks (up to top_k) without raising
        result = reranker.rerank(query, sample_chunks, top_k=2)

        assert len(result) == 2
        # Should return first top_k chunks in original order
        assert result[0]['chunk_id'] == 1
        assert result[1]['chunk_id'] == 2

    def test_rerank_single_chunk(self, reranker, mock_cross_encoder):
        """Test reranking with single chunk"""
        query = "test query"
        chunks = [{
            "chunk_id": 1,
            "text": "Single chunk",
            "similarity_score": 0.8
        }]
        mock_cross_encoder.predict.return_value = [0.95]

        result = reranker.rerank(query, chunks, top_k=1)

        assert len(result) == 1
        assert result[0]['reranking_score'] == 0.95

    def test_rerank_top_k_larger_than_chunks(self, reranker, mock_cross_encoder, sample_chunks):
        """Test when top_k is larger than available chunks"""
        query = "test query"
        mock_scores = [0.9, 0.8, 0.7]
        mock_cross_encoder.predict.return_value = mock_scores

        result = reranker.rerank(query, sample_chunks, top_k=10)

        # Should return all available chunks
        assert len(result) == 3

    def test_model_loading_import_error(self):
        """Test handling of missing sentence-transformers package"""
        with patch('app.services.reranker.CrossEncoder', side_effect=ImportError("No module")):
            reranker = Reranker()

            with pytest.raises(ImportError, match="sentence-transformers is required"):
                _ = reranker.model

    def test_model_loading_runtime_error(self):
        """Test handling of model loading failures"""
        with patch('app.services.reranker.CrossEncoder', side_effect=RuntimeError("Model download failed")):
            reranker = Reranker()

            with pytest.raises(RuntimeError, match="Failed to load reranker model"):
                _ = reranker.model

    def test_create_reranker_factory(self):
        """Test create_reranker factory function"""
        with patch('app.services.reranker.Reranker') as mock_reranker_class:
            with patch('app.services.reranker.settings') as mock_settings:
                mock_settings.RERANKING_MODEL = 'test-model'

                create_reranker()

                mock_reranker_class.assert_called_once_with(model_name='test-model')

    def test_create_reranker_with_override(self):
        """Test create_reranker with model name override"""
        with patch('app.services.reranker.Reranker') as mock_reranker_class:
            create_reranker(model_name='override-model')

            mock_reranker_class.assert_called_once_with(model_name='override-model')


class TestRerankingScores:
    """Test suite for reranking score calculations"""

    @pytest.fixture
    def reranker_with_real_scores(self):
        """Create reranker with realistic score behavior"""
        with patch('app.services.reranker.CrossEncoder') as mock_ce:
            mock_model = Mock()
            # Simulate realistic cross-encoder scores
            def predict_func(pairs):
                # Return different scores based on text relevance
                scores = []
                for query, text in pairs:
                    if "vacation" in text.lower() and "vacation" in query.lower():
                        scores.append(0.92)
                    elif "sick" in text.lower():
                        scores.append(0.65)
                    else:
                        scores.append(0.45)
                return scores

            mock_model.predict.side_effect = predict_func
            mock_ce.return_value = mock_model

            return Reranker(model_name='test-model')

    def test_reranking_improves_relevance_order(self, reranker_with_real_scores):
        """Integration test: verify reranking puts most relevant chunk first"""
        query = "What is the vacation carryover policy?"

        chunks = [
            {
                "chunk_id": 1,
                "text": "Sick leave accrues at 1 day per month.",
                "similarity_score": 0.78
            },
            {
                "chunk_id": 2,
                "text": "Vacation days can be carried over up to 5 days.",
                "similarity_score": 0.72  # Lower initial score
            },
            {
                "chunk_id": 3,
                "text": "Holiday calendar is published annually.",
                "similarity_score": 0.70
            }
        ]

        result = reranker_with_real_scores.rerank(query, chunks, top_k=3)

        # Vacation chunk should be ranked first despite lower initial similarity
        assert result[0]['chunk_id'] == 2
        assert result[0]['text'] == "Vacation days can be carried over up to 5 days."
        assert result[0]['reranking_score'] > result[0]['original_similarity']

        # Verify order is by reranking score
        assert result[0]['reranking_score'] > result[1]['reranking_score']
        assert result[1]['reranking_score'] > result[2]['reranking_score']
