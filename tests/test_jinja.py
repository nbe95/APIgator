"""Comprehensive unit tests for the Jinja Handler."""

from collections.abc import Callable
from datetime import datetime, timedelta
from unittest.mock import patch

from apigator.jinja import JinjaHandler


class TestJinjaHandlerInitialization:
    """Test suite for JinjaHandler initialization."""

    def test_jinja_handler_creates_environment(self):
        """Test that JinjaHandler correctly initializes Jinja2 environment."""
        handler = JinjaHandler()
        assert handler.env is not None
        assert hasattr(handler.env, "from_string")

    def test_jinja_handler_sets_basic_globals(self):
        """Test that basic date/time globals are set (today, tomorrow, yesterday)."""
        with patch("apigator.jinja.datetime") as mock_datetime:
            mock_now = datetime(2024, 1, 15, 10, 30, 45)
            mock_datetime.now.return_value = mock_now
            mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

            handler = JinjaHandler()

            assert "today" in handler.env.globals
            assert "tomorrow" in handler.env.globals
            assert "yesterday" in handler.env.globals

    def test_jinja_handler_sets_week_globals(self):
        """Test that week-related globals are set."""
        handler = JinjaHandler()

        assert "this_week_start" in handler.env.globals
        assert "this_week_end" in handler.env.globals
        assert "last_week_start" in handler.env.globals
        assert "last_week_end" in handler.env.globals
        assert "next_week_start" in handler.env.globals
        assert "next_week_end" in handler.env.globals

    def test_jinja_handler_sets_month_globals(self):
        """Test that month-related globals are set."""
        handler = JinjaHandler()

        assert "this_month_start" in handler.env.globals
        assert "this_month_end" in handler.env.globals
        assert "last_month_start" in handler.env.globals
        assert "last_month_end" in handler.env.globals
        assert "next_month_start" in handler.env.globals
        assert "next_month_end" in handler.env.globals

    def test_jinja_handler_sets_year_globals(self):
        """Test that year-related globals are set."""
        handler = JinjaHandler()

        assert "this_year_start" in handler.env.globals
        assert "this_year_end" in handler.env.globals
        assert "last_year_start" in handler.env.globals
        assert "last_year_end" in handler.env.globals
        assert "next_year_start" in handler.env.globals
        assert "next_year_end" in handler.env.globals

    def test_jinja_handler_registers_strftime_filter(self):
        """Test that the custom strftime filter is registered."""
        handler = JinjaHandler()
        assert "strftime" in handler.env.filters


class TestSimpleVariableRendering:
    """Test suite for simple template rendering with variables."""

    def test_render_empty_string(self):
        """Test rendering an empty string."""
        handler = JinjaHandler()
        result = handler.render("")
        assert result == ""

    def test_render_plain_text(self):
        """Test rendering plain text without any template syntax."""
        handler = JinjaHandler()
        result = handler.render("Hello, World!")
        assert result == "Hello, World!"

    def test_render_simple_variable(self):
        """Test rendering a simple variable from globals."""
        handler = JinjaHandler()
        # Use today as a global variable
        result = handler.render("{{ today }}")
        # Result should be a string representation of today's date
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_custom_context_today(self):
        """Test that 'today' global is correctly used."""
        handler = JinjaHandler()
        template_str = "{{ today.year }}"
        result = handler.render(template_str)
        current_year = str(datetime.now().year)
        assert current_year in result

    def test_render_with_tomorrow_global(self):
        """Test rendering with tomorrow global."""
        handler = JinjaHandler()
        template_str = "{{ tomorrow }}"
        result = handler.render(template_str)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_render_with_yesterday_global(self):
        """Test rendering with yesterday global."""
        handler = JinjaHandler()
        template_str = "{{ yesterday }}"
        result = handler.render(template_str)
        assert isinstance(result, str)
        assert len(result) > 0


class TestLoopRendering:
    """Test suite for template rendering with loops."""

    def test_render_list_simple_loop(self):
        """Test rendering a list through the render method."""
        handler = JinjaHandler()
        data_list = ["apple", "banana", "cherry"]
        result = handler.render(data_list)
        assert result == data_list

    def test_render_for_loop_in_string(self):
        """Test rendering a for loop in a template string."""
        handler = JinjaHandler()
        template_str = (
            """{% for item in items %}{{ item }}{% if not loop.last %}, {% endif %}{% endfor %}"""
        )
        # Since items is not in globals, this will try to render with undefined
        # The behavior depends on Jinja2's undefined handling
        result = handler.render(template_str)
        assert isinstance(result, str)

    def test_render_list_with_nested_templates(self):
        """Test rendering a list where each element contains template syntax."""
        handler = JinjaHandler()
        data_list = ["Item 1: {{ today }}", "Item 2: {{ tomorrow }}", "Item 3: {{ yesterday }}"]
        result = handler.render(data_list)
        assert isinstance(result, list)
        assert len(result) == 3
        # Each element should be rendered
        assert all(isinstance(item, str) for item in result)


class TestConditionalRendering:
    """Test suite for template rendering with conditionals."""

    def test_render_if_statement_true(self):
        """Test rendering if statement that evaluates to true."""
        handler = JinjaHandler()
        # Using a simple condition that should be true
        template_str = "{% if true %}Success{% endif %}"
        result = handler.render(template_str)
        assert "Success" in result

    def test_render_if_statement_false(self):
        """Test rendering if statement that evaluates to false."""
        handler = JinjaHandler()
        template_str = "{% if false %}Should not appear{% endif %}"
        result = handler.render(template_str)
        assert "Should not appear" not in result

    def test_render_if_else_statement(self):
        """Test rendering if-else statement."""
        handler = JinjaHandler()
        template_str = "{% if false %}False{% else %}True{% endif %}"
        result = handler.render(template_str)
        assert "True" in result
        assert "False" not in result

    def test_render_comparison_operators(self):
        """Test rendering with comparison operators in conditionals."""
        handler = JinjaHandler()
        template_str = "{% if 5 > 3 %}Greater{% else %}Not greater{% endif %}"
        result = handler.render(template_str)
        assert "Greater" in result


class TestFilterRendering:
    """Test suite for template rendering with filters."""

    def test_render_with_strftime_filter(self):
        """Test rendering with the custom strftime filter."""
        handler = JinjaHandler()
        template_str = "{{ today|strftime('%Y-%m-%d') }}"
        result = handler.render(template_str)
        # Result should be in YYYY-MM-DD format
        assert isinstance(result, str)
        assert len(result) > 0
        # Check if it matches the expected date format
        parts = result.split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # Year
        assert len(parts[1]) == 2  # Month
        assert len(parts[2]) == 2  # Day

    def test_render_strftime_filter_custom_format(self):
        """Test strftime filter with custom format."""
        handler = JinjaHandler()
        template_str = "{{ today|strftime('%d/%m/%Y') }}"
        result = handler.render(template_str)
        assert isinstance(result, str)
        # Check if it matches DD/MM/YYYY format
        parts = result.split("/")
        assert len(parts) == 3

    def test_render_with_builtin_filters(self):
        """Test rendering with built-in Jinja2 filters."""
        handler = JinjaHandler()
        template_str = "{{ 'hello world'|upper }}"
        result = handler.render(template_str)
        assert "HELLO WORLD" in result

    def test_render_with_length_filter(self):
        """Test rendering with length filter."""
        handler = JinjaHandler()
        template_str = "{{ 'test'|length }}"
        result = handler.render(template_str)
        assert "4" in result


class TestErrorHandling:
    """Test suite for error handling."""

    def test_render_invalid_template_syntax(self):
        """Test rendering with invalid Jinja2 syntax."""
        handler = JinjaHandler()
        # Invalid syntax: unclosed if statement
        template_str = "{% if true %}This is missing endif"
        result = handler.render(template_str)
        # Should return original data on error
        assert result == template_str

    def test_render_undefined_variable_handling(self):
        """Test rendering with undefined variables."""
        handler = JinjaHandler()
        # Jinja2 by default renders undefined variables as empty strings
        template_str = "{{ undefined_variable }}"
        result = handler.render(template_str)
        # Should not raise error, should render as empty string
        assert isinstance(result, str)

    def test_render_malformed_filter_syntax(self):
        """Test rendering with malformed filter syntax."""
        handler = JinjaHandler()
        template_str = "{{ today|unknown_filter }}"
        result = handler.render(template_str)
        # Should handle filter error gracefully
        assert isinstance(result, str)

    def test_render_dict_with_invalid_template(self):
        """Test rendering a dict where value has invalid template."""
        handler = JinjaHandler()
        data_dict = {"valid": "Hello", "invalid": "{% if true %}missing endif"}
        result = handler.render(data_dict)
        assert isinstance(result, dict)
        # Valid key should be rendered
        assert result["valid"] == "Hello"
        # Invalid key should return original value
        assert result["invalid"] == "{% if true %}missing endif"


class TestNestedDataStructures:
    """Test suite for rendering with nested data structures."""

    def test_render_nested_dict(self):
        """Test rendering nested dictionaries."""
        handler = JinjaHandler()
        data_dict = {"level1": {"level2": {"value": "nested"}}}
        result = handler.render(data_dict)
        assert result == data_dict
        assert result["level1"]["level2"]["value"] == "nested"

    def test_render_nested_dict_with_templates(self):
        """Test rendering nested dictionaries with template strings."""
        handler = JinjaHandler()
        data_dict = {"user": {"name": "John", "date": "{{ today }}"}}
        result = handler.render(data_dict)
        assert isinstance(result, dict)
        assert result["user"]["name"] == "John"
        assert isinstance(result["user"]["date"], str)
        assert len(result["user"]["date"]) > 0

    def test_render_list_of_dicts(self):
        """Test rendering list of dictionaries."""
        handler = JinjaHandler()
        data_list = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        result = handler.render(data_list)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"

    def test_render_list_of_dicts_with_templates(self):
        """Test rendering list of dictionaries with template strings."""
        handler = JinjaHandler()
        data_list = [{"id": 1, "created": "{{ today }}"}, {"id": 2, "created": "{{ tomorrow }}"}]
        result = handler.render(data_list)
        assert isinstance(result, list)
        assert len(result) == 2
        assert isinstance(result[0]["created"], str)
        assert isinstance(result[1]["created"], str)

    def test_render_deeply_nested_structure(self):
        """Test rendering deeply nested data structure."""
        handler = JinjaHandler()
        data = {
            "level1": {
                "level2": {
                    "level3": {"items": [{"value": "{{ today }}"}, {"value": "{{ tomorrow }}"}]}
                }
            }
        }
        result = handler.render(data)
        assert isinstance(result, dict)
        items = result["level1"]["level2"]["level3"]["items"]
        assert len(items) == 2
        assert isinstance(items[0]["value"], str)


class TestDateTimeGlobals:
    """Test suite for date/time related globals."""

    def test_today_is_datetime_object(self):
        """Test that today global is a datetime object."""
        handler = JinjaHandler()
        today: datetime = handler.env.globals.get("today")  # type: ignore
        assert isinstance(today, datetime)
        # Check that time is midnight
        assert today.hour == 0
        assert today.minute == 0
        assert today.second == 0
        assert today.microsecond == 0

    def test_tomorrow_is_one_day_after_today(self):
        """Test that tomorrow is exactly one day after today."""
        handler = JinjaHandler()
        today: datetime = handler.env.globals.get("today")  # type: ignore
        tomorrow: datetime = handler.env.globals.get("tomorrow")  # type: ignore
        assert (tomorrow - today).days == 1

    def test_yesterday_is_one_day_before_today(self):
        """Test that yesterday is exactly one day before today."""
        handler = JinjaHandler()
        today: datetime = handler.env.globals.get("today")  # type: ignore
        yesterday: datetime = handler.env.globals.get("yesterday")  # type: ignore
        assert (today - yesterday).days == 1

    def test_this_week_dates(self):
        """Test that this week dates are correct."""
        handler = JinjaHandler()
        week_start: datetime = handler.env.globals.get("this_week_start")  # type: ignore
        week_end: datetime = handler.env.globals.get("this_week_end")  # type: ignore
        # Week end should be after week start
        assert week_end > week_start
        # Week should be 7 days
        assert (week_end - week_start).days == 6  # Inclusive, so 6 days difference

    def test_this_month_dates(self):
        """Test that this month dates are correct."""
        handler = JinjaHandler()
        month_start: datetime = handler.env.globals.get("this_month_start")  # type: ignore
        month_end: datetime = handler.env.globals.get("this_month_end")  # type: ignore
        # Month end should be after month start
        assert month_end > month_start
        # Check that month start is on day 1
        assert month_start.day == 1
        # Check that month end is on last day of month
        next_month_start = (month_end + timedelta(days=1)).replace(day=1)
        assert next_month_start.month != month_end.month or next_month_start.year != month_end.year

    def test_this_year_dates(self):
        """Test that this year dates are correct."""
        handler = JinjaHandler()
        year_start: datetime = handler.env.globals.get("this_year_start")  # type: ignore
        year_end: datetime = handler.env.globals.get("this_year_end")  # type: ignore
        # Year end should be after year start
        assert year_end > year_start
        # Check that year start is January 1st
        assert year_start.month == 1
        assert year_start.day == 1
        # Check that year end is December 31st
        assert year_end.month == 12
        assert year_end.day == 31


class TestRenderMethod:
    """Test suite for the render method with various data types."""

    def test_render_none_value(self):
        """Test rendering None value."""
        handler = JinjaHandler()
        result = handler.render(None)
        assert result is None

    def test_render_integer(self):
        """Test rendering integer value."""
        handler = JinjaHandler()
        result = handler.render(42)
        assert result == 42

    def test_render_float(self):
        """Test rendering float value."""
        handler = JinjaHandler()
        result = handler.render(3.14)
        assert result == 3.14

    def test_render_boolean(self):
        """Test rendering boolean value."""
        handler = JinjaHandler()
        result = handler.render(True)
        assert result is True

    def test_render_empty_dict(self):
        """Test rendering empty dictionary."""
        handler = JinjaHandler()
        result = handler.render({})
        assert result == {}

    def test_render_empty_list(self):
        """Test rendering empty list."""
        handler = JinjaHandler()
        result = handler.render([])
        assert result == []

    def test_render_multiple_variables_in_string(self):
        """Test rendering multiple variables in a single string."""
        handler = JinjaHandler()
        template_str = "Start: {{ today }}, End: {{ tomorrow }}"
        result = handler.render(template_str)
        assert isinstance(result, str)
        assert "Start:" in result
        assert "End:" in result


class TestCustomFilters:
    """Test suite for custom filters."""

    def test_strftime_filter_with_datetime_object(self):
        """Test strftime filter applied to datetime object."""
        handler = JinjaHandler()
        # Access the filter directly
        strftime_filter: Callable[[datetime, str], str] = handler.env.filters.get("strftime")  # type: ignore
        test_date = datetime(2024, 1, 15, 10, 30, 45)
        result = strftime_filter(test_date, "%Y-%m-%d")
        assert result == "2024-01-15"

    def test_strftime_filter_with_string_input(self):
        """Test strftime filter with non-datetime input."""
        handler = JinjaHandler()
        strftime_filter: Callable[[str, str], str] = handler.env.filters.get("strftime")  # type: ignore
        result = strftime_filter("not a datetime", "%Y-%m-%d")
        # Should return string representation
        assert isinstance(result, str)

    def test_strftime_filter_default_format(self):
        """Test strftime filter with default format."""
        handler = JinjaHandler()
        strftime_filter: Callable[[datetime], str] = handler.env.filters.get("strftime")  # type: ignore
        test_date = datetime(2024, 1, 15, 10, 30, 45)
        result = strftime_filter(test_date)  # Use default format
        assert result == "2024-01-15"


class TestComplexTemplates:
    """Test suite for complex template scenarios."""

    def test_render_template_with_arithmetic(self):
        """Test rendering template with arithmetic operations."""
        handler = JinjaHandler()
        template_str = "{{ 2 + 3 }}"
        result = handler.render(template_str)
        assert "5" in result

    def test_render_template_with_string_concatenation(self):
        """Test rendering template with string concatenation."""
        handler = JinjaHandler()
        template_str = "{{ 'Hello' ~ ' ' ~ 'World' }}"
        result = handler.render(template_str)
        assert "Hello World" in result

    def test_render_template_with_comparison_chain(self):
        """Test rendering template with comparison chain."""
        handler = JinjaHandler()
        template_str = "{% if 1 < 2 < 3 %}True{% else %}False{% endif %}"
        result = handler.render(template_str)
        assert "True" in result

    def test_render_template_with_nested_loop_and_condition(self):
        """Test rendering template with nested loop and condition."""
        handler = JinjaHandler()
        # This will render without error but result depends on undefined vars
        template_str = "{% for i in range(3) %}{% if i > 0 %}{{ i }}{% endif %}{% endfor %}"
        result = handler.render(template_str)
        assert isinstance(result, str)

    def test_render_with_set_statement(self):
        """Test rendering with set statement to define variables."""
        handler = JinjaHandler()
        template_str = "{% set name = 'John' %}Hello {{ name }}"
        result = handler.render(template_str)
        assert "Hello John" in result


class TestEdgeCases:
    """Test suite for edge cases."""

    def test_render_string_with_double_braces_at_start(self):
        """Test rendering string starting with double braces."""
        handler = JinjaHandler()
        result = handler.render("{{ start")
        assert isinstance(result, str)

    def test_render_very_long_string(self):
        """Test rendering very long string."""
        handler = JinjaHandler()
        long_string = "a" * 10000
        result = handler.render(long_string)
        assert result == long_string

    def test_render_string_with_special_characters(self):
        """Test rendering string with special characters."""
        handler = JinjaHandler()
        special_string = "Test with special chars: !@#$%^&*()"
        result = handler.render(special_string)
        assert result == special_string

    def test_render_unicode_string(self):
        """Test rendering unicode string."""
        handler = JinjaHandler()
        unicode_string = "こんにちは世界 🌍 Привет мир"
        result = handler.render(unicode_string)
        assert result == unicode_string

    def test_render_mixed_type_list(self):
        """Test rendering list with mixed types."""
        handler = JinjaHandler()
        mixed_list = [1, "two", 3.0, None, True, {"key": "value"}]
        result = handler.render(mixed_list)
        assert result == mixed_list

    def test_render_dict_with_none_values(self):
        """Test rendering dict with None values."""
        handler = JinjaHandler()
        data_dict = {"key1": None, "key2": "value"}
        result = handler.render(data_dict)
        assert result["key1"] is None
        assert result["key2"] == "value"
