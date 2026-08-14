"""Shared pytest fixtures for all tests."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def mock_httpx_client_context():
    """Fixture that patches httpx.AsyncClient as a context manager.

    Returns the mock AsyncClient instance used within the context manager.
    """
    with patch("apigator.query.httpx.AsyncClient") as mock_client_class:
        mock_instance = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_instance
        mock_client_class.return_value.__aexit__.return_value = None
        yield mock_instance
