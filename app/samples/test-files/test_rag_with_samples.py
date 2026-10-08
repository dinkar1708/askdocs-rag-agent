#!/usr/bin/env python3
"""
Test script to verify RAG system functionality with sample test files.

This script:
1. Loads the ground truth test queries
2. Tests the RAG system with each query via POST /ask
3. Compares results with expected answers
4. Reports accuracy and retrieval quality

Usage:
    python test_rag_with_samples.py --api-url http://localhost:8000
"""

import json
import os
import sys
import re
import urllib.request
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))


def load_ground_truth():
    """Load ground truth test queries and expected answers."""
    script_dir = Path(__file__).parent
    ground_truth_file = script_dir / "ground_truth.json"

    with open(ground_truth_file, 'r') as f:
        return json.load(f)


def calculate_similarity(expected: str, actual: str) -> float:
    """
    Calculate token overlap Jaccard similarity between expected and actual answers.
    """
    expected_tokens = set(re.findall(r"\w+", expected.lower()))
    actual_tokens = set(re.findall(r"\w+", actual.lower()))
    if not expected_tokens:
        return 0.0
    intersection = expected_tokens.intersection(actual_tokens)
    union = expected_tokens.union(actual_tokens)
    return len(intersection) / len(union) if union else 0.0


def test_query(query, expected_answer, document_name, api_url="http://localhost:8000"):
    """
    Test a single query against the RAG system via POST /ask.

    Args:
        query: The question to ask
        expected_answer: The expected answer
        document_name: The source document name
        api_url: Base URL of the RAG API

    Returns:
        dict: Test results including success status and scores
    """
    api_key = os.getenv("API_KEY", "test-api-key-not-for-production")
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key,
    }
    payload = json.dumps({
        "question": query,
        "top_k": 3,
        "include_sources": True
    }).encode("utf-8")

    try:
        req = urllib.request.Request(f"{api_url}/ask/", data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            actual_answer = res_data.get("answer", "")
            sources = res_data.get("sources", [])
            similarity = calculate_similarity(expected_answer, actual_answer)

            return {
                "query": query,
                "expected": expected_answer,
                "actual": actual_answer,
                "document": document_name,
                "similarity_score": round(similarity, 3),
                "passed": similarity >= 0.25,
                "sources_count": len(sources),
                "status": "COMPLETED",
            }
    except Exception as e:
        return {
            "query": query,
            "expected": expected_answer,
            "document": document_name,
            "status": "ERROR",
            "message": str(e)
        }


def run_tests(api_url="http://localhost:8000", verbose=True):
    """
    Run all tests from ground truth file.

    Args:
        api_url: Base URL of the RAG API
        verbose: Print detailed output

    Returns:
        dict: Test results summary
    """
    ground_truth = load_ground_truth()
    results = {
        "total_queries": 0,
        "passed_queries": 0,
        "by_document": {},
        "by_category": {},
        "failed_queries": []
    }

    print("=" * 80)
    print("RAG SYSTEM TEST SUITE")
    print("=" * 80)

    for document_name, queries in ground_truth.items():
        if verbose:
            print(f"\n\nTesting document: {document_name}")
            print("-" * 80)

        doc_results = {
            "total": len(queries),
            "passed": 0,
            "failed": 0,
            "queries": []
        }

        for query_data in queries:
            results["total_queries"] += 1

            test_result = test_query(
                query_data["query"],
                query_data["expected_answer"],
                document_name,
                api_url
            )

            if test_result.get("passed"):
                doc_results["passed"] += 1
                results["passed_queries"] += 1
            else:
                doc_results["failed"] += 1
                results["failed_queries"].append(test_result)

            doc_results["queries"].append(test_result)

            # Track by category
            category = query_data["category"]
            if category not in results["by_category"]:
                results["by_category"][category] = {"total": 0, "passed": 0}
            results["by_category"][category]["total"] += 1
            if test_result.get("passed"):
                results["by_category"][category]["passed"] += 1

        results["by_document"][document_name] = doc_results

    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total queries tested: {results['total_queries']}")
    print(f"Passed queries: {results['passed_queries']}")

    return results


def main():
    """Main entry point for test script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test RAG system with sample documents"
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="Base URL of the RAG API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )
    parser.add_argument(
        "--save-results",
        action="store_true",
        help="Save test results to a JSON file"
    )

    args = parser.parse_args()

    # Check if ground truth file exists
    script_dir = Path(__file__).parent
    ground_truth_file = script_dir / "ground_truth.json"

    if not ground_truth_file.exists():
        print(f"Error: Ground truth file not found at {ground_truth_file}")
        sys.exit(1)

    # Run tests
    results = run_tests(api_url=args.api_url, verbose=args.verbose)

    if args.save_results:
        results_file = script_dir / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()
