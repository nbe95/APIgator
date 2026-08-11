"""Query execution engine for API aggregation and jq-based filtering."""

import json
import subprocess
from typing import Any

import httpx

from .config import config
from .constants import INSTANCE_ID


class QueryError(Exception):
    """Exception raised when an error occurs during query execution."""

    def __init__(self, msg):
        self.msg: str = msg


async def execute_query(query_def) -> dict[str, Any]:
    """Execute a query definition by fetching and aggregating data from multiple endpoints."""
    fields: dict[str, Any] = {}
    default_timeout = config.get("default_timeout", 10)

    async with httpx.AsyncClient() as client:
        for endpoint in query_def:
            timeout = endpoint.get("timeout", default_timeout)
            try:
                headers = (endpoint.get("headers") or {}).copy()
                headers["X-APIgator-Instance-ID"] = INSTANCE_ID

                response = await client.request(
                    method=endpoint.get("method", "GET"),
                    url=endpoint["url"],
                    headers=headers,
                    params=endpoint.get("params"),
                    content=json.dumps(endpoint.get("body")),
                    timeout=timeout,
                )
                data = response.json()

                # Apply jq filters to extract specific fields from the API response
                fields = _parse_fields(endpoint.get("fields"))
                for key, jq_filter in fields.items():
                    try:
                        fields[key] = _apply_jq_filter(data, jq_filter)
                    except Exception as e:
                        raise QueryError(f"Error processing field '{key}': {e!s}")

            except httpx.ConnectError:
                raise QueryError(f"Connection failed for '{endpoint['url']}'")
            except httpx.TimeoutException:
                raise QueryError(f"Request timeout for '{endpoint['url']}'")
            except json.JSONDecodeError:
                raise QueryError(f"Invalid JSON response from '{endpoint['url']}'")
            except Exception as e:
                raise QueryError(f"Error processing endpoint '{endpoint['url']}': {e!s}")

    return fields


def _apply_jq_filter(data: Any, jq_filter: str) -> str:
    """Run jq filters on specified data."""
    result = subprocess.run(
        ("jq", jq_filter), input=json.dumps(data), capture_output=True, text=True
    )
    if result.returncode == 0:
        value = json.loads(result.stdout)
    else:
        raise QueryError(f"jq filter failed for '{jq_filter}': {result.stderr}")
    return value


def _parse_fields(field_definition: list[str] | dict[str, str] | None) -> dict[str, str]:
    """Parse different possible types of an API field definition."""
    # Handle empty definition
    if field_definition is None:
        return {}

    # Handle list format (top-level only)
    if isinstance(field_definition, list):
        return {str(field): f".{field}" for field in field_definition}

    # Handle dict format
    if isinstance(field_definition, dict):
        return dict(field_definition)

    raise TypeError("Invalid field definition.")
