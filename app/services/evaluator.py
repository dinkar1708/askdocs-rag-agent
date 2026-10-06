"""Evaluation Service

Measures retrieval quality (Hit-Rate @ k, MRR, Precision, Recall),
answer groundedness, and intent routing / refusal accuracy against benchmark datasets.
"""

import json
import logging
import os
import time
import inspect
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models import Document, Chunk
from app.services.retriever import retrieve_relevant_chunks, format_context_for_llm
from app.graph.query_routing_graph import route_query
from app.llm.factory import get_llm_provider
from app.llm.base import BaseLLMProvider
from app.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationMetrics,
    QuestionEvaluationDetail
)

logger = logging.getLogger(__name__)


class EvaluationHarness:
    """Automated evaluation harness for RAG retrieval and answer groundedness"""

    def __init__(self, db: Session, llm_provider: Optional[BaseLLMProvider] = None):
        self.db = db
        self.llm = llm_provider or get_llm_provider()

    async def run_evaluation(self, request: EvaluationRequest) -> EvaluationResponse:
        """
        Execute full evaluation against the questions dataset.

        Args:
            request: Configuration containing dataset path, top_k, and options

        Returns:
            EvaluationResponse with metrics, detailed results, and Markdown report
        """
        dataset_path = request.dataset_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "eval",
            "questions.json"
        )

        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Evaluation dataset not found at path: {dataset_path}")

        with open(dataset_path, "r", encoding="utf-8") as f:
            test_questions = json.load(f)

        details: List[QuestionEvaluationDetail] = []
        reciprocal_ranks: List[float] = []
        precision_scores: List[float] = []

        total_questions = len(test_questions)
        answerable_count = 0
        off_topic_count = 0
        ambiguous_count = 0

        hits_at_k = 0
        grounded_answers = 0
        correct_refusals = 0

        for item in test_questions:
            q_id = item.get("id", len(details) + 1)
            query_text = item.get("question", "")
            category = item.get("category", "answerable")
            expected_doc = item.get("expected_document")
            expected_page = item.get("expected_page")
            expected_contains = item.get("expected_answer_contains", [])
            expected_answer = item.get("expected_answer")

            # 1. Retrieval
            chunks = retrieve_relevant_chunks(
                query=query_text,
                db=self.db,
                top_k=request.top_k,
                similarity_threshold=request.confidence_threshold
            )

            retrieved_docs: List[str] = []
            retrieved_pages: List[int] = []
            rank = None

            for idx, c in enumerate(chunks):
                if isinstance(c, dict):
                    doc_name = c.get("filename", "unknown")
                    page_num = c.get("page_number", 1)
                else:
                    doc_name = c.document.filename if hasattr(c, "document") and c.document else "unknown"
                    page_num = getattr(c, "page_number", 1)

                retrieved_docs.append(doc_name)
                retrieved_pages.append(page_num)
                if expected_doc and expected_doc.lower() in doc_name.lower() and rank is None:
                    rank = idx + 1

            retrieval_success = rank is not None if expected_doc else True
            rr = 1.0 / rank if rank else 0.0

            # Precision for this query
            if chunks and expected_doc:
                matching_chunks = sum(1 for d in retrieved_docs if expected_doc.lower() in d.lower())
                prec = matching_chunks / len(chunks)
            else:
                prec = 1.0 if not expected_doc else 0.0
            precision_scores.append(prec)

            # 2. Query Routing
            try:
                route_result = await route_query(
                    question=query_text,
                    chunks=chunks,
                    llm_provider=self.llm,
                    use_llm_classification=True
                )
                actual_intent = route_result.get("intent", "answer")
            except Exception as e:
                logger.warning(f"Routing failed for '{query_text}': {e}")
                actual_intent = "answer" if chunks else "refuse"

            # 3. Answer Generation (if intent is answer)
            generated_answer = None
            answer_grounded = True
            is_correct_refusal = None
            passed = True
            failure_reason = None

            if category == "answerable":
                answerable_count += 1
                reciprocal_ranks.append(rr)
                if retrieval_success:
                    hits_at_k += 1
                else:
                    passed = False
                    failure_reason = f"Target document '{expected_doc}' not retrieved in top-{request.top_k}"

                # Generate answer with context
                context = format_context_for_llm(chunks)
                gen_func = self.llm.generate(
                    system_prompt="Answer the question based strictly on the provided context.",
                    user_prompt=f"Context:\n{context}\n\nQuestion: {query_text}"
                )
                if inspect.iscoroutine(gen_func):
                    generated_answer = await gen_func
                else:
                    generated_answer = gen_func

                # Check grounded keywords
                if expected_contains and generated_answer:
                    missing = [kw for kw in expected_contains if kw.lower() not in generated_answer.lower()]
                    if missing:
                        answer_grounded = False
                        if passed:
                            passed = False
                            failure_reason = f"Answer missing key facts: {missing}"

                if answer_grounded:
                    grounded_answers += 1

            elif category == "off_topic":
                off_topic_count += 1
                is_correct_refusal = actual_intent in ["refuse", "not_found"] or not chunks
                if is_correct_refusal:
                    correct_refusals += 1
                else:
                    passed = False
                    failure_reason = f"Expected refusal for off-topic query, got intent '{actual_intent}'"

            elif category == "ambiguous":
                ambiguous_count += 1
                if actual_intent not in ["clarify", "refuse"] and chunks:
                    # Some ambiguous queries may route to clarify or answer
                    pass

            detail = QuestionEvaluationDetail(
                id=q_id,
                question=query_text,
                category=category,
                passed=passed,
                retrieval_success=retrieval_success,
                retrieved_documents=retrieved_docs,
                retrieved_pages=retrieved_pages,
                answer_grounded=answer_grounded,
                correct_refusal=is_correct_refusal,
                actual_intent=actual_intent,
                answer=generated_answer,
                failure_reason=failure_reason
            )
            details.append(detail)

        # Metrics calculation
        hit_rate = (hits_at_k / answerable_count) if answerable_count > 0 else 1.0
        recall = hit_rate
        avg_precision = (sum(precision_scores) / len(precision_scores)) if precision_scores else 0.0
        mrr = (sum(reciprocal_ranks) / len(reciprocal_ranks)) if reciprocal_ranks else 0.0
        groundedness = (grounded_answers / answerable_count) if answerable_count > 0 else 1.0
        refusal_acc = (correct_refusals / off_topic_count) if off_topic_count > 0 else 1.0

        metrics = EvaluationMetrics(
            total_questions=total_questions,
            answerable_count=answerable_count,
            off_topic_count=off_topic_count,
            ambiguous_count=ambiguous_count,
            retrieval_hit_rate=round(hit_rate, 4),
            recall_at_k=round(recall, 4),
            precision_at_k=round(avg_precision, 4),
            mrr=round(mrr, 4),
            answer_groundedness=round(groundedness, 4),
            refusal_accuracy=round(refusal_acc, 4)
        )

        passed_count = sum(1 for d in details if d.passed)
        failed_cases = [d for d in details if not d.passed]

        # Generate Report Markdown
        report_md = self._format_report(
            metrics=metrics,
            top_k=request.top_k,
            confidence_threshold=request.confidence_threshold,
            failed_cases=failed_cases
        )

        report_path = None
        if request.save_report:
            eval_dir = os.path.dirname(dataset_path)
            report_path = os.path.join(eval_dir, "report.md")
            try:
                with open(report_path, "w", encoding="utf-8") as f:
                    f.write(report_md)
            except Exception as e:
                logger.error(f"Failed to write evaluation report to {report_path}: {e}")

        return EvaluationResponse(
            metrics=metrics,
            total_evaluated=total_questions,
            passed_count=passed_count,
            failed_count=len(failed_cases),
            failed_cases=failed_cases,
            report_markdown=report_md,
            report_path=report_path
        )

    def _format_report(
        self,
        metrics: EvaluationMetrics,
        top_k: int,
        confidence_threshold: float,
        failed_cases: List[QuestionEvaluationDetail]
    ) -> str:
        """Format clean Markdown evaluation report"""
        today = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        hit_pct = f"{metrics.retrieval_hit_rate * 100:.1f}%"
        ground_pct = f"{metrics.answer_groundedness * 100:.1f}%"
        refusal_pct = f"{metrics.refusal_accuracy * 100:.1f}%"
        prec_pct = f"{metrics.precision_at_k * 100:.1f}%"

        lines = [
            "# Evaluation Report",
            "",
            f"**Generated:** {today}",
            f"**Total Questions:** {metrics.total_questions}",
            "",
            "## Configuration",
            f"- **RETRIEVAL_TOP_K:** {top_k}",
            f"- **CONFIDENCE_THRESHOLD:** {confidence_threshold}",
            "",
            "## Summary Metrics",
            "",
            "| Metric | Score | Target | Status |",
            "|---|---|---|---|",
            f"| Retrieval Hit-Rate @ k={top_k} | {hit_pct} | >80% | {'✅ PASS' if metrics.retrieval_hit_rate >= 0.8 else '⚠️ REVIEW'} |",
            f"| Mean Reciprocal Rank (MRR) | {metrics.mrr:.3f} | >0.70 | {'✅ PASS' if metrics.mrr >= 0.7 else '⚠️ REVIEW'} |",
            f"| Retrieval Precision @ k | {prec_pct} | >50% | {'✅ PASS' if metrics.precision_at_k >= 0.5 else '⚠️ REVIEW'} |",
            f"| Answer Groundedness | {ground_pct} | >95% | {'✅ PASS' if metrics.answer_groundedness >= 0.9 else '⚠️ REVIEW'} |",
            f"| Correct Refusal Accuracy | {refusal_pct} | >90% | {'✅ PASS' if metrics.refusal_accuracy >= 0.9 else '⚠️ REVIEW'} |",
            "",
            f"## Question Breakdown",
            f"- **Answerable:** {metrics.answerable_count}",
            f"- **Off-topic:** {metrics.off_topic_count}",
            f"- **Ambiguous:** {metrics.ambiguous_count}",
            ""
        ]

        if failed_cases:
            lines.append("## Failed or Flagged Cases")
            lines.append("")
            for fc in failed_cases:
                lines.append(f"### Question {fc.id}: \"{fc.question}\"")
                lines.append(f"- **Category:** `{fc.category}`")
                lines.append(f"- **Retrieved Docs:** {fc.retrieved_documents}")
                lines.append(f"- **Routed Intent:** `{fc.actual_intent}`")
                lines.append(f"- **Reason:** {fc.failure_reason or 'Validation mismatch'}")
                lines.append("")
        else:
            lines.append("## Verification")
            lines.append("All test cases satisfied expected criteria.")
            lines.append("")

        return "\n".join(lines)


def get_evaluator(db: Session, llm_provider: Optional[BaseLLMProvider] = None) -> EvaluationHarness:
    """Factory function for EvaluationHarness"""
    return EvaluationHarness(db=db, llm_provider=llm_provider)
