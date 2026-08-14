"""Shared pytest fixtures for all tests."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_httpx_client_context():
    """Fixture that patches httpx.AsyncClient as a context manager.

    Returns the mock AsyncClient instance used within the context manager.
    """
    with patch("apigator.query.httpx.AsyncClient") as mock_client_class:
        mock_instance = MagicMock()
        mock_client_class.return_value.__aenter__.return_value = mock_instance
        mock_client_class.return_value.__aexit__.return_value = None

        async def send_wrapper(request_obj):
            return mock_instance.request()

        mock_instance.request = MagicMock()
        mock_instance.send = send_wrapper

        yield mock_instance
