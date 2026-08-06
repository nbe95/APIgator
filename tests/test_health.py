from datetime import datetime
import pytest
from fastapi.testclient import TestClient

from apigator.main import app


@pytest.fixture
def client():
    """Fixture to provide a test client for the FastAPI app."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test suite for the /health endpoint."""

    def test_health_returns_200(self, client: TestClient):
        """Test that the health endpoint returns a 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client: TestClient):
        """Test that the health endpoint returns valid response structure."""
        response = client.get("/health")
        data = response.json()

        # Verify required fields exist and have correct types
        assert data["status"] == "success"
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["data"], dict)
        assert isinstance(data["error"], str)

        try:
            datetime.fromisoformat(data["timestamp"])
        except ValueError:
            pytest.fail(f"Invalid ISO 8601 timestamp: {data['timestamp']}")
