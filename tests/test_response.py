"""Unit tests for the response formatting module."""

from datetime import datetime

import pytest

from apigator.response import RspStatus, create_response


class TestCreateResponse:
    """Test suite for the create_response function."""

    def test_create_response_success(self):
        """Test creating a success response."""
        data = {"key": "value"}
        response = create_response(RspStatus.SUCCESS, data=data)

        assert response["status"] == "success"
        assert response["data"] == {"key": "value"}
        assert response["message"] is None
        assert isinstance(response["timestamp"], str)

    def test_create_response_error(self):
        """Test creating an error response."""
        response = create_response(RspStatus.ERROR, message="Something went wrong")

        assert response["status"] == "error"
        assert response["data"] == {}
        assert response["message"] == "Something went wrong"
        assert isinstance(response["timestamp"], str)

    def test_create_response_default_values(self):
        """Test creating response with default values."""
        response = create_response(RspStatus.SUCCESS)

        assert response["status"] == "success"
        assert response["data"] == {}
        assert response["message"] is None

    def test_create_response_timestamp_is_iso8601(self):
        """Test that response timestamp is valid ISO 8601 format."""
        response = create_response(RspStatus.SUCCESS)

        try:
            datetime.fromisoformat(response["timestamp"])
        except ValueError:
            pytest.fail(f"Invalid ISO 8601 timestamp: {response['timestamp']}")

    def test_create_response_with_both_data_and_error(self):
        """Test response with both data and error populated."""
        data = {"partial": "result"}
        response = create_response(RspStatus.ERROR, data=data, message="Partial failure")

        assert response["status"] == "error"
        assert response["data"] == {"partial": "result"}
        assert response["message"] == "Partial failure"
