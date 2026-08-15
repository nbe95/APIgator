"""Unit tests for the field definitions module."""

import pytest

from apigator.field import Field, parse_field_def


class TestField:
    """Test suite for the Field class."""

    def test_parse_field_def_with_none(self):
        """Test parsing None field definition returns empty list."""
        result = parse_field_def(None)
        assert result == []

    def test_parse_field_def_with_list(self):
        """Test parsing list format field definition."""
        definition = ["name", "email", "age"]
        result = parse_field_def(definition)

        assert len(result) == 3
        assert result[0].key == "name"
        assert result[0].path == "name"
        assert result[0].is_jq_filter is False
        assert result[1].key == "email"
        assert result[1].path == "email"
        assert result[1].is_jq_filter is False
        assert result[2].key == "age"
        assert result[2].path == "age"
        assert result[2].is_jq_filter is False

    def test_parse_field_def_with_dict(self):
        """Test parsing dict format field definition with jq filters."""
        definition = {"name": ".user.name", "email": ".contact.email"}
        result = parse_field_def(definition)

        assert len(result) == 2
        assert result[0].key == "name"
        assert result[0].path == ".user.name"
        assert result[0].is_jq_filter is True
        assert result[1].key == "email"
        assert result[1].path == ".contact.email"
        assert result[1].is_jq_filter is True

    def test_parse_field_def_duplicate_in_list_raises_error(self):
        """Test that duplicate keys in list format raise NameError."""
        definition = ["name", "email", "name"]
        with pytest.raises(NameError, match="Duplicate field definition"):
            parse_field_def(definition)

    def test_parse_field_def_invalid_type_raises_error(self):
        """Test that invalid definition types raise TypeError."""
        with pytest.raises(TypeError, match="Invalid field definition"):
            parse_field_def("invalid")  # type: ignore

    def test_parse_field_def_empty_list(self):
        """Test parsing empty list returns empty field list."""
        result = parse_field_def([])
        assert result == []

    def test_parse_field_def_empty_dict(self):
        """Test parsing empty dict returns empty field list."""
        result = parse_field_def({})
        assert result == []


class TestFieldJqFilter:
    """Test suite for the Field class jq filter evaluation."""

    def test_field_eval_jq_filter_simple_extraction(self):
        """Test running a simple jq filter to extract a field."""
        field = Field(key="name", path=".name", is_jq_filter=True)
        data = {"name": "John", "age": 30}
        result = field.parse(data)

        assert result == {"name": "John"}

    def test_field_eval_jq_filter_nested_extraction(self):
        """Test running jq filter on nested data."""
        field = Field(key="user_name", path=".user.name", is_jq_filter=True)
        data = {"user": {"name": "John", "email": "john@example.com"}}
        result = field.parse(data)

        assert result == {"user_name": "John"}

    def test_field_eval_jq_filter_array_extraction(self):
        """Test running jq filter on arrays."""
        field = Field(key="items_count", path=".items | length", is_jq_filter=True)
        data = {"items": [1, 2, 3, 4, 5]}
        result = field.parse(data)

        assert result == {"items_count": 5}

    def test_field_eval_jq_filter_invalid_filter_raises_error(self):
        """Test that invalid jq filter raises ValueError."""
        field = Field(key="invalid", path=".invalid.[", is_jq_filter=True)
        data = {"name": "John"}
        with pytest.raises(ValueError, match="jq filter failed"):
            field.parse(data)

    def test_field_eval_jq_filter_missing_path_returns_null(self):
        """Test that accessing missing path returns null."""
        field = Field(key="missing", path=".missing", is_jq_filter=True)
        data = {"name": "John"}
        result = field.parse(data)

        assert result == {"missing": None}

    def test_field_eval_jq_filter_complex_transformation(self):
        """Test running jq filter with transformation logic."""
        field = Field(key="total", path=".items | map(.value) | add", is_jq_filter=True)
        data = {"items": [{"id": 1, "value": 10}, {"id": 2, "value": 20}]}
        result = field.parse(data)

        assert result == {"total": 30}
