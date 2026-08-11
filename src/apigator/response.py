"""Response formatting utilities for API responses."""

from datetime import UTC, datetime
from enum import Enum


class RspStatus(Enum):
    """Enumeration of possible response statuses."""

    SUCCESS = "success"
    ERROR = "error"


def create_response(status: RspStatus, data: dict | None = None, error: str | None = None):
    """Create a standardized API response with consistent structure."""
    return {
        "status": status.value,
        "timestamp": datetime.now(UTC).isoformat(),
        "data": data or {},
        "error": error or "",
    }
