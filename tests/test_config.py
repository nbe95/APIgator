"""Unit tests for the configuration management module."""

import os
from tempfile import NamedTemporaryFile

from apigator.config import Config


class TestConfig:
    """Test suite for the Config class."""

    def test_config_get_returns_value(self):
        """Test that get() retrieves a configuration value."""
        config = Config()
        config._data = {"key": "value"}
        assert config.get("key") == "value"

    def test_config_get_returns_default_when_missing(self):
        """Test that get() returns default value for missing keys."""
        config = Config()
        config._data = {}
        assert config.get("missing", "default") == "default"

    def test_config_getitem_retrieves_value(self):
        """Test that dictionary-style access retrieves a value."""
        config = Config()
        config._data = {"key": "value"}
        assert config["key"] == "value"

    def test_config_load_from_file_yaml(self):
        """Test loading configuration from a YAML file."""
        with NamedTemporaryFile(mode="w", suffix=".yaml") as file:
            file.write("test_key: test_value\nnumber: 42\n")
            file.flush()

            config = Config(file.name)
            assert config.get("test_key") == "test_value"
            assert config.get("number") == 42

    def test_config_load_with_env_substitution(self):
        """Test that environment variables are substituted in config."""
        os.environ["TEST_VAR"] = "test_value"
        with NamedTemporaryFile(mode="w", suffix=".yaml") as file:
            file.write("key: ${TEST_VAR}\n")
            file.flush()

            config = Config(file.name)
            assert config.get("key") == "test_value"
        del os.environ["TEST_VAR"]

    def test_config_load_with_env_substitution_no_braces(self):
        """Test environment variable substitution without braces format."""
        os.environ["TEST_VAR"] = "test_value"
        with NamedTemporaryFile(mode="w", suffix=".yaml") as file:
            file.write("key: $TEST_VAR\n")
            file.flush()

            config = Config(file.name)
            assert config.get("key") == "test_value"

        del os.environ["TEST_VAR"]
