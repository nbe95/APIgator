"""Unit tests for the query execution engine module."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from apigator.query import QueryError, execute_query


class TestExecuteQuery:
    """Test suite for the execute_query function."""

    @pytest.mark.asyncio
    async def test_execute_query_simple_endpoint(self):
        """Test executing a query with a single endpoint."""
        query_def = [
            {
                "url": "https://api.example.com/user",
                "method": "GET",
                "fields": ["name", "email"],
            }
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "John", "email": "john@example.com"}

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await execute_query(query_def)

            assert result["name"] == "John"
            assert result["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_execute_query_with_jq_filter(self):
        """Test executing a query with jq filter field."""
        query_def = [
            {
                "url": "https://api.example.com/data",
                "method": "GET",
                "fields": {"status": ".response.status"},
            }
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {"response": {"status": "ok"}}

        with (
            patch("apigator.query.httpx.AsyncClient") as mock_client,
            patch("apigator.query.run_jq_filter", return_value="ok") as mock_jq,
        ):
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await execute_query(query_def)

            assert result["status"] == "ok"
            mock_jq.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_query_connection_error(self):
        """Test that connection errors are caught and converted to QueryError."""
        query_def = [{"url": "https://api.example.com/data", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.ConnectError("Connection failed")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Connection failed"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_timeout_error(self):
        """Test that timeout errors are caught and converted to QueryError."""
        query_def = [{"url": "https://api.example.com/data", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.TimeoutException("Request timeout")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Request timeout"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_invalid_json_response(self):
        """Test that invalid JSON response raises QueryError."""
        query_def = [{"url": "https://api.example.com/data", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Invalid JSON response"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_multiple_endpoints(self):
        """Test executing a query with multiple endpoints."""
        query_def = [
            {
                "url": "https://api.example.com/user",
                "method": "GET",
                "fields": ["name"],
            },
            {
                "url": "https://api.example.com/stats",
                "method": "GET",
                "fields": ["count"],
            },
        ]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()

            responses = [
                MagicMock(json=MagicMock(return_value={"name": "John"})),
                MagicMock(json=MagicMock(return_value={"count": 42})),
            ]
            mock_instance.request.side_effect = responses
            mock_client.return_value.__aenter__.return_value = mock_instance

            result = await execute_query(query_def)

            assert result["name"] == "John"
            assert result["count"] == 42

    @pytest.mark.asyncio
    async def test_execute_query_with_custom_timeout(self):
        """Test that custom timeout is passed to request."""
        query_def = [
            {
                "url": "https://api.example.com/data",
                "method": "GET",
                "timeout": 30,
                "fields": [],
            }
        ]

        mock_response = MagicMock()
        mock_response.json.return_value = {}

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            await execute_query(query_def)

            # Verify timeout was passed to request
            mock_instance.request.assert_called_once()
            call_kwargs = mock_instance.request.call_args[1]
            assert call_kwargs["timeout"] == 30
