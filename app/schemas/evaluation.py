"""Evaluation schemas for testing retrieval quality and answer groundedness"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class EvaluationRequest(BaseModel):
    """Request schema for executing an evaluation run"""
    dataset_path: Optional[str] = Field(
        default=None,
        description="Path to questions.json dataset file (defaults to eval/questions.json)"
    )
    top_k: int = Field(default=5, ge=1, le=20, description="Top-k retrieval parameter")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence threshold for retrieval")
    save_report: bool = Field(default=True, description="Whether to write report markdown to disk")


class QuestionEvaluationDetail(BaseModel):
    """Evaluation result for an individual test question"""
    id: int = Field(..., description="Question identifier")
    question: str = Field(..., description="Query text")
    category: str = Field(..., description="Question category: answerable, off_topic, ambiguous")
    passed: bool = Field(..., description="Whether the question met all expected criteria")
    retrieval_success: bool = Field(..., description="Whether the target document was retrieved in top-k")
    retrieved_documents: List[str] = Field(default_factory=list, description="Filenames of retrieved chunks")
    retrieved_pages: List[int] = Field(default_factory=list, description="Page numbers of retrieved chunks")
    answer_grounded: bool = Field(default=True, description="Whether the answer contains grounded information")
    correct_refusal: Optional[bool] = Field(default=None, description="Whether off-topic question was properly refused")
    actual_intent: Optional[str] = Field(default=None, description="Routed intent (answer, refuse, clarify)")
    answer: Optional[str] = Field(default=None, description="Generated answer text")
    failure_reason: Optional[str] = Field(default=None, description="Explanation of failure if passed is False")


class EvaluationMetrics(BaseModel):
    """Aggregate metrics across evaluated test set"""
    total_questions: int = Field(..., description="Total questions evaluated")
    answerable_count: int = Field(..., description="Count of answerable questions")
    off_topic_count: int = Field(..., description="Count of off-topic questions")
    ambiguous_count: int = Field(..., description="Count of ambiguous questions")
    retrieval_hit_rate: float = Field(..., description="Hit rate @ top-k for answerable questions (0.0 - 1.0)")
    recall_at_k: float = Field(..., description="Recall @ top-k")
    precision_at_k: float = Field(..., description="Precision @ top-k")
    mrr: float = Field(..., description="Mean Reciprocal Rank of target document")
    answer_groundedness: float = Field(..., description="Percentage of answers grounded in documents (0.0 - 1.0)")
    refusal_accuracy: float = Field(..., description="Accuracy of refusing off-topic queries (0.0 - 1.0)")


class EvaluationResponse(BaseModel):
    """Response schema returned by the evaluation pipeline"""
    metrics: EvaluationMetrics = Field(..., description="Summary evaluation metrics")
    total_evaluated: int = Field(..., description="Number of test items processed")
    passed_count: int = Field(..., description="Number of passing test items")
    failed_count: int = Field(..., description="Number of failing test items")
    failed_cases: List[QuestionEvaluationDetail] = Field(
        default_factory=list,
        description="Detailed diagnostics for failed test cases"
    )
    report_markdown: str = Field(..., description="Full evaluation report in Markdown format")
    report_path: Optional[str] = Field(None, description="Path where report was saved if save_report=True")
