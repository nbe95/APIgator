"""Query execution engine for API aggregation and jq-based filtering."""

import json
from typing import Any

import httpx

from .config import config
from .constants import INSTANCE_ID
from .field import Field
from .jq import run_jq_filter


class QueryError(Exception):
    """Exception raised when an error occurs during query execution."""

    def __init__(self, msg):
        self.msg: str = msg


async def execute_query(query_def) -> dict[str, Any]:
    """Execute a query definition by fetching and aggregating data from multiple endpoints."""
    result: dict[str, Any] = {}
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

                # Parse field definition and extract desired values from API response
                fields = Field.parse_field_def(endpoint.get("fields"))
                for field in fields:
                    try:
                        if field.is_jq_filter:
                            result[field.key] = run_jq_filter(data, field.path)
                        else:
                            result[field.key] = dict(data).get(field.path)
                    except Exception as e:
                        raise QueryError(f"Error processing field '{field.key}': {e!s}")

            except httpx.ConnectError:
                raise QueryError(f"Connection failed for '{endpoint['url']}'")
            except httpx.TimeoutException:
                raise QueryError(f"Request timeout for '{endpoint['url']}'")
            except json.JSONDecodeError:
                raise QueryError(f"Invalid JSON response from '{endpoint['url']}'")
            except Exception as e:
                raise QueryError(f"Error processing endpoint '{endpoint['url']}': {e!s}")

    return result
