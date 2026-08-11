"""Unit tests for the jq filter execution module."""

import pytest

from apigator.jq import run_jq_filter


class TestRunJqFilter:
    """Test suite for the run_jq_filter function."""

    def test_run_jq_filter_simple_extraction(self):
        """Test running a simple jq filter to extract a field."""
        data = {"name": "John", "age": 30}
        result = run_jq_filter(data, ".name")

        assert result == "John"

    def test_run_jq_filter_nested_extraction(self):
        """Test running jq filter on nested data."""
        data = {"user": {"name": "John", "email": "john@example.com"}}
        result = run_jq_filter(data, ".user.name")

        assert result == "John"

    def test_run_jq_filter_array_extraction(self):
        """Test running jq filter on arrays."""
        data = {"items": [1, 2, 3, 4, 5]}
        result = run_jq_filter(data, ".items | length")

        assert result == 5

    def test_run_jq_filter_invalid_filter_raises_error(self):
        """Test that invalid jq filter raises ValueError."""
        data = {"name": "John"}
        with pytest.raises(ValueError, match="jq filter failed"):
            run_jq_filter(data, ".invalid.[")

    def test_run_jq_filter_missing_path_returns_null(self):
        """Test that accessing missing path returns null."""
        data = {"name": "John"}
        result = run_jq_filter(data, ".missing")

        assert result is None

    def test_run_jq_filter_complex_transformation(self):
        """Test running jq filter with transformation logic."""
        data = {"items": [{"id": 1, "value": 10}, {"id": 2, "value": 20}]}
        result = run_jq_filter(data, ".items | map(.value) | add")

        assert result == 30
