"""
Unit tests for Infinite Loop Detection based on Instance ID Header.

Tests the loop detection mechanism that prevents self-referencing requests
by checking the X-APIgator-Instance-ID header.
"""

import pytest
from fastapi.testclient import TestClient

from apigator.__main__ import INSTANCE_ID, app


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app."""
    return TestClient(app)


class TestLoopDetection:
    """Test suite for the loop detection functionality."""

    def test_query_wihtout_instance_id(self, client: TestClient):
        """Test that a request without instance ID is processed."""
        response = client.get("/query/test_query")

        assert response.status_code != 400

    def test_query_with_other_instance_id(self, client: TestClient):
        """Test that a request with another instance ID is processed."""
        headers = {"X-APIgator-Instance-ID": "foo"}
        response = client.get("/query/test_query", headers=headers)

        assert response.status_code != 400

    def test_query_with_same_instance_id(self, client: TestClient):
        """Test that a request with the same instance ID is detected and blocked."""
        headers = {"X-APIgator-Instance-ID": INSTANCE_ID}
        response = client.get("/query/test_query", headers=headers)

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
