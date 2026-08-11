"""Unit tests for the field definitions module."""

import pytest

from apigator.field import Field


class TestField:
    """Test suite for the Field class."""

    def test_parse_field_def_with_none(self):
        """Test parsing None field definition returns empty list."""
        result = Field.parse_field_def(None)
        assert result == []

    def test_parse_field_def_with_list(self):
        """Test parsing list format field definition."""
        definition = ["name", "email", "age"]
        result = Field.parse_field_def(definition)

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
        result = Field.parse_field_def(definition)

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
            Field.parse_field_def(definition)

    def test_parse_field_def_invalid_type_raises_error(self):
        """Test that invalid definition types raise TypeError."""
        with pytest.raises(TypeError, match="Invalid field definition"):
            Field.parse_field_def("invalid")  # type: ignore

    def test_parse_field_def_empty_list(self):
        """Test parsing empty list returns empty field list."""
        result = Field.parse_field_def([])
        assert result == []

    def test_parse_field_def_empty_dict(self):
        """Test parsing empty dict returns empty field list."""
        result = Field.parse_field_def({})
        assert result == []
