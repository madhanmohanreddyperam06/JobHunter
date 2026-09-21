"""
Utility and helper functions.
"""
from typing import Any, Dict


def sanitize_string(value: str) -> str:
    """Strip extraneous whitespace and control characters from input string."""
    if not value:
        return ""
    return value.strip()
