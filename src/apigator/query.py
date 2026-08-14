"""Query execution engine for API aggregation and jq-based filtering."""

import json
from typing import Any

import httpx

from .config import config
from .constants import DEBUG, INSTANCE_ID
from .field import parse_field_def
from .jinja import JinjaHandler


class QueryError(Exception):
    """Exception raised when an error occurs during query execution."""

    def __init__(self, msg):
        self.msg: str = msg


async def execute_query(query_def) -> dict[str, Any]:
    """Execute a query definition by fetching and aggregating data from multiple endpoints."""
    result: dict[str, Any] = {}
    default_timeout = config.get("default_timeout", 10)
    jinja = JinjaHandler()

    async with httpx.AsyncClient() as client:
        for endpoint in query_def:
            timeout = endpoint.get("timeout", default_timeout)
            try:
                headers = (endpoint.get("headers") or {}).copy()
                headers["X-APIgator-Instance-ID"] = INSTANCE_ID

                # Prepare upstream query with parsed data from Jinja2 templates...
                body = endpoint.get("body")
                request = client.build_request(
                    method=endpoint.get("method", "GET"),
                    url=endpoint["url"],
                    headers=jinja.render(headers),
                    params=jinja.render(endpoint.get("params")),
                    content=json.dumps(jinja.render(body)) if body else None,
                    timeout=timeout,
                )

                if DEBUG:
                    print("-" * 50 + " UPSTREAM REQUEST START")
                    print(vars(request))
                    print("-" * 50 + " UPSTREAM REQUEST END")

                # ...and shoot!
                response = await client.send(request)

                if DEBUG:
                    print("-" * 50 + " UPSTREAM RESPONSE START")
                    print(vars(response))
                    print("-" * 50 + " UPSTREAM RESPONSE END")

                if response.is_error:
                    raise QueryError(
                        "Upstream API threw an error:"
                        f" {response.status_code} {response.reason_phrase}"
                    )

                # Parse field definition and extract desired values from API response
                data: Any = response.json()
                fields = parse_field_def(endpoint.get("fields"))
                for field in fields:
                    try:
                        parsed_field = field.parse(data)
                        result.update(parsed_field)
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
