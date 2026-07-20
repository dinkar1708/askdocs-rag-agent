"""Utility to automatically document API requests/responses during testing"""
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict


# Output directory for API test results - in docs/testing folder
API_EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "docs" / "testing" / "api-results"
API_EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)


def document_api_call(
    filename: str,
    method: str,
    endpoint: str,
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    status_code: int
):
    """
    Save API request/response to JSON file for documentation

    Args:
        filename: Output filename (e.g., "health.json")
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        request_data: Request body/params
        response_data: Response body
        status_code: HTTP status code
    """
    # Simple format: API name, request, response
    example = {
        "api": f"{method} {endpoint}",
        "request": request_data,
        "response": response_data
    }

    filepath = API_EXAMPLES_DIR / filename
    with open(filepath, 'w') as f:
        json.dump(example, f, indent=2)
