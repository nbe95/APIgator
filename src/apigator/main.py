import json
import os
import subprocess
from datetime import datetime
from enum import Enum

import httpx
import uvicorn
import yaml
from fastapi import FastAPI, HTTPException

CONFIG_FILE = "/config/config.yaml"
VERSION = os.getenv("APIGATOR_VERSION", "(unknown)")
config = {}
app = FastAPI(title="APIgator")


class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"


def load_config():
    global config
    with open(CONFIG_FILE) as f:
        config_raw = f.read()
        for key, value in os.environ.items():
            config_raw = config_raw.replace(f"${{{key}}}", str(value))
            config_raw = config_raw.replace(f"${key}", str(value))
        config = yaml.safe_load(config_raw)


def create_response(
    status: ResponseStatus, data: dict | None = None, error: str = "", message: str = ""
):
    """Standard response format of consistent structure"""
    return {
        "version": VERSION,
        "status": status.value,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data if data is not None else {},
        "error": error,
        "message": message,
    }


def extract_field(data: dict, path: str):
    """Extracts a value from a (nested) object via path, e.g. 'status.cpu.usage'"""
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


async def execute_query(query_def):
    results = {}
    async with httpx.AsyncClient(timeout=10) as client:
        for endpoint in query_def:
            try:
                response = await client.request(
                    method=endpoint.get("method", "GET"),
                    url=endpoint["url"],
                    headers=endpoint.get("headers"),
                    params=endpoint.get("params"),
                    content=json.dumps(endpoint.get("body")) if endpoint.get("body") else None,
                )
                api_data = response.json()

                fields = endpoint.get("fields", [])

                if not fields:
                    results[endpoint.get("key", endpoint["url"])] = api_data
                else:
                    for field_def in fields:
                        for output_key, field_config in field_def.items():
                            try:
                                if isinstance(field_config, str):
                                    path = field_config
                                    jq_filter = None
                                elif isinstance(field_config, dict):
                                    path = field_config.get("path", "")
                                    jq_filter = field_config.get("filter")
                                else:
                                    return None, f"Invalid field config for '{output_key}'"

                                value = extract_field(api_data, path)

                                if jq_filter and value is not None:
                                    result = subprocess.run(
                                        ["jq", jq_filter],
                                        input=json.dumps(value),
                                        capture_output=True,
                                        text=True,
                                    )
                                    if result.returncode == 0:
                                        value = json.loads(result.stdout)
                                    else:
                                        return (
                                            None,
                                            f"jq filter failed for '{output_key}': {result.stderr}",
                                        )

                                results[output_key] = value
                            except Exception as e:
                                return None, f"Error processing field '{output_key}': {e!s}"

            except httpx.ConnectError:
                return None, f"Connection failed for '{endpoint['url']}'"
            except httpx.TimeoutException:
                return None, f"Request timeout for '{endpoint['url']}'"
            except json.JSONDecodeError:
                return None, f"Invalid JSON response from '{endpoint['url']}'"
            except Exception as e:
                return None, f"Error processing endpoint '{endpoint['url']}': {e!s}"

    return results, None


@app.get("/health")
async def health():
    return create_response(status=ResponseStatus.SUCCESS, message="APIgator is running")


@app.get("/query/{query_name}")
async def get_query(query_name: str):
    queries = config.get("queries", {})

    if query_name not in queries:
        raise HTTPException(
            status_code=404,
            detail=create_response(
                status=ResponseStatus.ERROR,
                error="query_not_found",
                message=f"Query '{query_name}' not found",
            ),
        )

    try:
        results, error = await execute_query(queries[query_name])

        if error:
            raise HTTPException(
                status_code=502,
                detail=create_response(
                    status=ResponseStatus.ERROR, error="upstream_error", message=error
                ),
            )

        return create_response(status=ResponseStatus.SUCCESS, data=results)

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=create_response(
                status=ResponseStatus.ERROR, error="internal_error", message="Internal server error"
            ),
        )


if __name__ == "__main__":
    load_config()
    print(f"APIgator v{VERSION} running")

    port = config.get("port", 8080)
    host = config.get("host", "0.0.0.0")

    uvicorn.run(app, host=host, port=port)
