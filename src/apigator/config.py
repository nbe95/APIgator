"""Configuration management for the APIgator application."""

import os
from typing import Any

import yaml


class Config:
    """Manages application configuration loaded from config files."""

    def __init__(self):
        self._data: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a configuration value by key with a default fallback."""
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Retrieve a configuration value using dictionary-style access."""
        return self._data[key]

    def load_from_file(self, config_file: str) -> None:
        """Load configuration from a YAML file with environment variable substitution."""
        with open(config_file) as f:
            config_raw = f.read()

            # Substitute environment variables in both ${VAR} and $VAR formats
            for key, value in os.environ.items():
                config_raw = config_raw.replace(f"${{{key}}}", str(value))
                config_raw = config_raw.replace(f"${key}", str(value))
            self._data = yaml.safe_load(config_raw)


# Global configuration instance used throughout the application
config = Config()
