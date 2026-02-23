"""Tests for the routing and pipeline logic."""

import pytest

from src.utils.helpers import safe_json_parse, truncate_text
from src.tools.custom_tools import calculate_cost_comparison


class TestHelpers:
    def test_parse_valid_json(self):
        result = safe_json_parse('{"complexity": "SIMPLE", "confidence": 0.9}')
        assert result["complexity"] == "SIMPLE"
        assert result["confidence"] == 0.9

    def test_parse_json_in_code_block(self):
        text = '```json\n{"complexity": "COMPLEX"}\n```'
        result = safe_json_parse(text)
        assert result["complexity"] == "COMPLEX"

    def test_parse_invalid_json(self):
        result = safe_json_parse("not json at all")
        assert result is None

    def test_truncate_short_text(self):
        result = truncate_text("hello", max_length=100)
        assert result == "hello"

    def test_truncate_long_text(self):
        long_text = "a" * 600
        result = truncate_text(long_text, max_length=500)
        assert len(result) == 500
        assert result.endswith("...")


class TestCostComparison:
    def test_basic_savings(self):
        result = calculate_cost_comparison(
            small_tokens=8000,
            large_tokens=2000,
        )
        assert result["savings_pct"] > 0
        assert result["routed_cost_usd"] < result["naive_cost_usd"]

    def test_all_large_no_savings(self):
        result = calculate_cost_comparison(
            small_tokens=0,
            large_tokens=10000,
        )
        assert result["savings_pct"] == 0.0

    def test_all_small_max_savings(self):
        result = calculate_cost_comparison(
            small_tokens=10000,
            large_tokens=0,
        )
        assert result["savings_pct"] > 90  # Should be very high savings

    def test_realistic_70_30_split(self):
        """Simulate 70% queries routed to small model (typical production split)."""
        result = calculate_cost_comparison(
            small_tokens=7000,
            large_tokens=3000,
        )
        assert result["savings_pct"] > 60  # Demonstrates ~70% savings target
