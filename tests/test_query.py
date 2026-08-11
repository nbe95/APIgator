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
        mock_response.is_error = False
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
        mock_response.is_error = False
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
            mock_response.is_error = False
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
                MagicMock(is_error=False, json=MagicMock(return_value={"name": "John"})),
                MagicMock(is_error=False, json=MagicMock(return_value={"count": 42})),
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
        mock_response.is_error = False
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

    @pytest.mark.asyncio
    async def test_execute_query_upstream_http_500_error(self):
        """Test that upstream HTTP 500 error causes the entire query to fail."""
        query_def = [
            {
                "url": "https://api.example.com/data",
                "method": "GET",
                "fields": ["result"],
            }
        ]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.is_error = True
            mock_response.status_code = 500
            mock_response.reason_phrase = "Internal Server Error"
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(
                QueryError, match="Upstream API threw an error: 500 Internal Server Error"
            ):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_upstream_http_404_error(self):
        """Test that upstream HTTP 404 error causes the entire query to fail."""
        query_def = [
            {
                "url": "https://api.example.com/notfound",
                "method": "GET",
                "fields": ["data"],
            }
        ]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.is_error = True
            mock_response.status_code = 404
            mock_response.reason_phrase = "Not Found"
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Upstream API threw an error: 404 Not Found"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_upstream_http_403_error(self):
        """Test that upstream HTTP 403 error causes the entire query to fail."""
        query_def = [
            {
                "url": "https://api.example.com/forbidden",
                "method": "GET",
                "fields": ["data"],
            }
        ]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.is_error = True
            mock_response.status_code = 403
            mock_response.reason_phrase = "Forbidden"
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Upstream API threw an error: 403 Forbidden"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_upstream_http_502_error(self):
        """Test that upstream HTTP 502 error causes the entire query to fail."""
        query_def = [
            {
                "url": "https://api.example.com/gateway",
                "method": "GET",
                "fields": ["data"],
            }
        ]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.is_error = True
            mock_response.status_code = 502
            mock_response.reason_phrase = "Bad Gateway"
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Upstream API threw an error: 502 Bad Gateway"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_multiple_endpoints_second_fails_http_error(self):
        """Test that if second endpoint fails with HTTP error, entire query fails."""
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

            # First response succeeds, second fails
            response1 = MagicMock()
            response1.is_error = False
            response1.json.return_value = {"name": "John"}

            response2 = MagicMock()
            response2.is_error = True
            response2.status_code = 503
            response2.reason_phrase = "Service Unavailable"

            mock_instance.request.side_effect = [response1, response2]
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(
                QueryError, match="Upstream API threw an error: 503 Service Unavailable"
            ):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_connection_refused_error(self):
        """Test that connection refused error is caught and causes query to fail."""
        query_def = [{"url": "https://api.example.com/data", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.ConnectError("Connection refused")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Connection failed"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_network_unreachable_error(self):
        """Test that network unreachable error is caught and causes query to fail."""
        query_def = [{"url": "https://api.unreachable.com/data", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.ConnectError("Network unreachable")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Connection failed"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_read_timeout_error(self):
        """Test that read timeout error is caught and causes query to fail."""
        query_def = [{"url": "https://api.example.com/slow", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.ReadTimeout("Read timed out")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Request timeout"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_write_timeout_error(self):
        """Test that write timeout error is caught and causes query to fail."""
        query_def = [{"url": "https://api.example.com/upload", "method": "POST", "body": {}}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.request.side_effect = httpx.WriteTimeout("Write timed out")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Request timeout"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_multiple_endpoints_first_fails(self):
        """Test that if first endpoint fails with connection error, entire query fails."""
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
            # First request fails with connection error
            mock_instance.request.side_effect = httpx.ConnectError("Connection failed")
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Connection failed"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_malformed_json_response(self):
        """Test that malformed JSON in response causes query to fail."""
        query_def = [{"url": "https://api.example.com/data", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.is_error = False
            mock_response.json.side_effect = json.JSONDecodeError(
                "Expecting value", "invalid json", 0
            )
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Invalid JSON response"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_empty_malformed_response(self):
        """Test that empty/malformed response causes query to fail."""
        query_def = [{"url": "https://api.example.com/data", "method": "GET"}]

        with patch("apigator.query.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_response = MagicMock()
            mock_response.is_error = False
            mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "", 0)
            mock_instance.request.return_value = mock_response
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Invalid JSON response"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_multiple_endpoints_malformed_response_second(self):
        """Test that malformed JSON in second endpoint causes entire query to fail."""
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

            # First response succeeds, second has malformed JSON
            response1 = MagicMock()
            response1.is_error = False
            response1.json.return_value = {"name": "John"}

            response2 = MagicMock()
            response2.is_error = False
            response2.json.side_effect = json.JSONDecodeError("Invalid JSON", "{bad json}", 0)

            mock_instance.request.side_effect = [response1, response2]
            mock_client.return_value.__aenter__.return_value = mock_instance

            with pytest.raises(QueryError, match="Invalid JSON response"):
                await execute_query(query_def)

    @pytest.mark.asyncio
    async def test_execute_query_http_error_with_error_status(self):
        """Test that various error status codes (4xx, 5xx) are properly detected and fail the
        query."""
        error_codes = [400, 401, 429, 500, 501, 503, 504]

        for status_code in error_codes:
            query_def = [{"url": "https://api.example.com/data", "method": "GET"}]

            with patch("apigator.query.httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.is_error = True
                mock_response.status_code = status_code
                mock_response.reason_phrase = f"Error {status_code}"
                mock_instance.request.return_value = mock_response
                mock_client.return_value.__aenter__.return_value = mock_instance

                with pytest.raises(QueryError, match=f"Upstream API threw an error: {status_code}"):
                    await execute_query(query_def)
