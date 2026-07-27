"""Table extraction service for PDF processing"""

from typing import List, Dict, Any, Tuple
from tabulate import tabulate


def extract_tables_from_page(page) -> List[Dict]:
    """Extract tables from a pdfplumber page

    Args:
        page: pdfplumber page object

    Returns:
        List of dicts with: table_data, bbox, markdown_text, headers
    """
    tables = []

    # Extract tables using pdfplumber
    extracted_tables = page.extract_tables()

    if not extracted_tables:
        return tables

    # Get table bounding boxes for later exclusion from text
    table_settings = {
        "vertical_strategy": "lines",
        "horizontal_strategy": "lines",
    }

    found_tables = page.find_tables(table_settings=table_settings)

    for idx, table_data in enumerate(extracted_tables):
        if not table_data or len(table_data) == 0:
            continue

        # Clean the table data (remove None values)
        cleaned_table = clean_table_data(table_data)

        if not cleaned_table or len(cleaned_table) == 0:
            continue

        # Get bounding box if available
        bbox = None
        if idx < len(found_tables):
            bbox = found_tables[idx].bbox

        # Extract headers (first row if it looks like headers)
        headers = extract_headers(cleaned_table)

        # Convert to markdown
        markdown_text = table_to_markdown(cleaned_table)

        tables.append({
            "table_data": cleaned_table,
            "bbox": bbox,
            "markdown": markdown_text,
            "headers": headers
        })

    return tables


def clean_table_data(table_data: List[List[Any]]) -> List[List[str]]:
    """Clean table data by handling None values and empty rows

    Args:
        table_data: Raw table data from pdfplumber

    Returns:
        Cleaned table data with strings
    """
    cleaned = []

    for row in table_data:
        if not row:
            continue

        # Replace None with empty string and convert to string
        cleaned_row = [str(cell).strip() if cell is not None else "" for cell in row]

        # Skip completely empty rows
        if all(cell == "" for cell in cleaned_row):
            continue

        cleaned.append(cleaned_row)

    return cleaned


def extract_headers(table_data: List[List[str]]) -> List[str]:
    """Extract headers from table data

    Assumes first row contains headers. Returns empty list if no clear headers.

    Args:
        table_data: Cleaned table data

    Returns:
        List of header names
    """
    if not table_data or len(table_data) == 0:
        return []

    # First row is typically headers
    headers = table_data[0]

    # Check if it looks like headers (not all empty, not all numbers)
    if all(h == "" for h in headers):
        return []

    # If most cells in first row are text (not numbers), treat as headers
    numeric_count = sum(1 for h in headers if h.replace('.', '').replace(',', '').replace('-', '').isdigit())

    if numeric_count < len(headers) * 0.7:  # Less than 70% numeric
        return headers

    return []


def table_to_markdown(table_data: List[List[str]]) -> str:
    """Convert table data to markdown format

    Args:
        table_data: Cleaned table data

    Returns:
        Markdown formatted table string
    """
    if not table_data or len(table_data) == 0:
        return ""

    # Check if first row should be headers
    headers = extract_headers(table_data)

    if headers:
        # First row is headers, rest is data
        markdown = tabulate(
            table_data[1:],
            headers=table_data[0],
            tablefmt="github",
            numalign="right",
            stralign="left"
        )
    else:
        # No headers, just format the table
        markdown = tabulate(
            table_data,
            tablefmt="github",
            numalign="right",
            stralign="left"
        )

    return markdown


def is_table_region(bbox: Tuple[float, float, float, float],
                    text_regions: List[Tuple[float, float, float, float]]) -> bool:
    """Check if bbox overlaps with any text regions

    Args:
        bbox: Bounding box (x0, y0, x1, y1)
        text_regions: List of bounding boxes to check against

    Returns:
        True if there's overlap, False otherwise
    """
    if not bbox:
        return False

    x0, y0, x1, y1 = bbox

    for region in text_regions:
        rx0, ry0, rx1, ry1 = region

        # Check for overlap
        if not (x1 < rx0 or x0 > rx1 or y1 < ry0 or y0 > ry1):
            return True

    return False


def get_table_bboxes(tables: List[Dict]) -> List[Tuple[float, float, float, float]]:
    """Extract bounding boxes from table list

    Args:
        tables: List of table dicts from extract_tables_from_page

    Returns:
        List of bounding boxes
    """
    bboxes = []
    for table in tables:
        if table.get("bbox"):
            bboxes.append(table["bbox"])
    return bboxes


def is_point_in_table(x: float, y: float,
                      table_bboxes: List[Tuple[float, float, float, float]]) -> bool:
    """Check if a point (x, y) is inside any table bounding box

    Args:
        x: X coordinate
        y: Y coordinate
        table_bboxes: List of table bounding boxes

    Returns:
        True if point is inside a table, False otherwise
    """
    for bbox in table_bboxes:
        x0, y0, x1, y1 = bbox
        if x0 <= x <= x1 and y0 <= y <= y1:
            return True
    return False
