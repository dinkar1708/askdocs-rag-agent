"""Tests for Evaluation Harness (Feature 07)"""

import pytest
import tempfile
import json
import os
from datetime import datetime
from app.db.models import Document, Chunk
from app.schemas.evaluation import EvaluationRequest
from app.services.evaluator import EvaluationHarness
from app.llm.mock_provider import MockLLMProvider


@pytest.fixture
def temp_eval_dataset():
    """Create a temporary small dataset for deterministic testing"""
    data = [
        {
            "id": 1,
            "question": "What is the vacation policy?",
            "category": "answerable",
            "expected_document": "company_policy.pdf",
            "expected_page": 1,
            "expected_answer_contains": ["15 days", "vacation"]
        },
        {
            "id": 2,
            "question": "What's the weather today?",
            "category": "off_topic",
            "expected_answer": "not_found"
        },
        {
            "id": 3,
            "question": "Policy",
            "category": "ambiguous",
            "expected_answer": "clarify"
        }
    ]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(data, f)
        temp_path = f.name

    yield temp_path

    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.mark.asyncio
async def test_evaluation_runner(db_session, sample_document_with_chunks, temp_eval_dataset):
    """Test evaluation harness calculation of metrics and report formatting"""
    harness = EvaluationHarness(db=db_session, llm_provider=MockLLMProvider())
    req = EvaluationRequest(
        dataset_path=temp_eval_dataset,
        top_k=5,
        confidence_threshold=0.0,
        save_report=False
    )

    response = await harness.run_evaluation(req)

    assert response.total_evaluated == 3
    assert response.metrics.answerable_count == 1
    assert response.metrics.off_topic_count == 1
    assert response.metrics.ambiguous_count == 1
    assert response.metrics.retrieval_hit_rate == 1.0
    assert response.metrics.mrr == 1.0
    assert response.metrics.answer_groundedness == 1.0
    assert response.metrics.refusal_accuracy == 1.0
    assert "# Evaluation Report" in response.report_markdown
    assert "Retrieval Hit-Rate" in response.report_markdown


@pytest.mark.asyncio
async def test_evaluation_missing_dataset(db_session):
    """Test error handling when dataset file is missing"""
    harness = EvaluationHarness(db=db_session, llm_provider=MockLLMProvider())
    req = EvaluationRequest(dataset_path="/nonexistent/path/questions.json")

    with pytest.raises(FileNotFoundError):
        await harness.run_evaluation(req)


def test_api_evaluate_endpoint(client, sample_document_with_chunks, temp_eval_dataset, monkeypatch):
    """Test POST /evaluate endpoint"""
    import app.llm.factory
    monkeypatch.setattr("app.core.config.settings.LLM_PROVIDER", "mock")
    app.llm.factory._llm_provider_instance = MockLLMProvider()

    resp = client.post(
        "/evaluate",
        json={
            "dataset_path": temp_eval_dataset,
            "top_k": 5,
            "confidence_threshold": 0.0,
            "save_report": False
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "metrics" in data
    assert data["metrics"]["total_questions"] == 3
    assert "report_markdown" in data
