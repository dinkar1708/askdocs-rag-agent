"""CLI script to run evaluation harness

Usage:
    python -m eval.run [--dataset path/to/questions.json] [--top-k 5]
"""

import asyncio
import argparse
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.services.evaluator import get_evaluator
from app.schemas.evaluation import EvaluationRequest


async def main():
    parser = argparse.ArgumentParser(description="Run AskDocs RAG Evaluation Harness")
    parser.add_argument("--dataset", type=str, default=None, help="Path to questions.json dataset")
    parser.add_argument("--top-k", type=int, default=5, help="Retrieval top-k chunks")
    parser.add_argument("--threshold", type=float, default=0.7, help="Similarity threshold")
    parser.add_argument("--no-save", action="store_true", help="Do not save markdown report")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        evaluator = get_evaluator(db=db)
        request = EvaluationRequest(
            dataset_path=args.dataset,
            top_k=args.top_k,
            confidence_threshold=args.threshold,
            save_report=not args.no_save
        )

        print(f"Running evaluation with top-k={request.top_k}...")
        response = await evaluator.run_evaluation(request)

        m = response.metrics
        print("\nEvaluation Completed:")
        print(f"Total Evaluated: {response.total_evaluated}")
        print(f"Retrieval Hit-Rate @ k={request.top_k}: {m.retrieval_hit_rate * 100:.1f}%")
        print(f"Mean Reciprocal Rank (MRR): {m.mrr:.3f}")
        print(f"Retrieval Precision @ k: {m.precision_at_k * 100:.1f}%")
        print(f"Answer Groundedness: {m.answer_groundedness * 100:.1f}%")
        print(f"Correct Refusals: {m.refusal_accuracy * 100:.1f}%")

        if response.report_path:
            print(f"\nReport saved to: {response.report_path}")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
