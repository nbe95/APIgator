"""Module for customized Jinja handling."""

from datetime import datetime, timedelta
from typing import Any

from jinja2 import Environment


class JinjaHandler:
    """Jinja handler for custom APIgator globals and filters

    Because of date/time dependency, an individual handler needs to be created each time a query is
    performed."""

    def __init__(self):
        self._create_environment()

    def render(self, data: Any) -> Any:
        """Render Jinja2 templates in strings, lists or dicts

        Any other type is returned without modification.
        """

        if isinstance(data, str):
            try:
                template = self.env.from_string(data)
                return template.render()
            except Exception as e:
                print(f"Jinja2 render error: {e}")
                return data

        if isinstance(data, dict):
            return {key: self.render(value) for key, value in data.items()}

        if isinstance(data, list):
            return [self.render(value) for value in data]

        return data

    def _create_environment(self) -> None:
        """Create a Jinja2 environment with custom filters and globals."""
        self.env = Environment()

        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)

        self.env.globals.update(
            {
                # Basics
                "today": today,
                "tomorrow": today + timedelta(days=1),
                "yesterday": today - timedelta(days=1),
                # This time period
                "this_week_start": today - timedelta(days=today.weekday()),
                "this_week_end": today + timedelta(days=6 - today.weekday()),
                "this_month_start": today.replace(day=1),
                "this_month_end": (today.replace(day=1) + timedelta(days=32)).replace(day=1)
                - timedelta(days=1),
                "this_year_start": today.replace(month=1, day=1),
                "this_year_end": today.replace(month=12, day=31),
                # Last time period
                "last_week_start": today - timedelta(days=today.weekday() + 7),
                "last_week_end": today - timedelta(days=today.weekday() + 1),
                "last_month_start": (today.replace(day=1) - timedelta(days=1)).replace(day=1),
                "last_month_end": today.replace(day=1) - timedelta(days=1),
                "last_year_start": today.replace(year=today.year - 1, month=1, day=1),
                "last_year_end": today.replace(year=today.year - 1, month=12, day=31),
                # Next time period
                "next_week_start": today + timedelta(days=7 - today.weekday()),
                "next_week_end": today + timedelta(days=13 - today.weekday()),
                "next_month_start": (today.replace(day=1) + timedelta(days=32)).replace(day=1),
                "next_month_end": (today.replace(day=1) + timedelta(days=64)).replace(day=1)
                - timedelta(days=1),
                "next_year_start": today.replace(year=today.year + 1, month=1, day=1),
                "next_year_end": today.replace(year=today.year + 1, month=12, day=31),
            }
        )

        def strftime_filter(dt, fmt="%Y-%m-%d"):
            """Format datetime object with strftime"""
            if isinstance(dt, datetime):
                return dt.strftime(fmt)
            return str(dt)

        self.env.filters.update({"strftime": strftime_filter})
