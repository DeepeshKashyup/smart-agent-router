"""Shared utility functions."""

import json
import time
from contextlib import contextmanager
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def timer(label: str):
    """Context manager to measure and log execution time."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    logger.info("timer", label=label, elapsed_seconds=round(elapsed, 3))


def safe_json_parse(text: str) -> dict[str, Any] | None:
    """Attempt to parse JSON from LLM output, handling common formatting issues."""
    text = text.strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code blocks
    if "```" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

    logger.warning("json_parse_failed", text_preview=text[:100])
    return None


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
