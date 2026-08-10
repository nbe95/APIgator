import json
import os
import subprocess
from datetime import datetime
from enum import Enum
from typing import Any

import httpx
import uvicorn
import yaml
from fastapi import FastAPI
from fastapi.responses import JSONResponse

CONFIG_FILE = "/config/config.yaml"
VERSION = os.getenv("APIGATOR_VERSION") or "(unknown)"
config = {}
app = FastAPI(title="APIgator")


class RspStatus(Enum):
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


def create_response(status: RspStatus, data: dict | None = None, error: str | None = None):
    """Standard response format of consistent structure"""
    return {
        "status": status.value,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data or {},
        "error": error or "",
    }


class QueryError(Exception):
    def __init__(self, msg):
        self.msg: str = msg


async def execute_query(query_def):
    results: dict[str, Any] = {}
    default_timeout = config.get("default_timeout", 10)
    async with httpx.AsyncClient() as client:
        for endpoint in query_def:
            timeout = endpoint.get("timeout", default_timeout)
            try:
                response = await client.request(
                    method=endpoint.get("method", "GET"),
                    url=endpoint["url"],
                    headers=endpoint.get("headers"),
                    params=endpoint.get("params"),
                    content=json.dumps(endpoint.get("body")),
                    timeout=timeout,
                )
                api_data = response.json()

                fields = endpoint.get("fields", {})
                if isinstance(fields, list):
                    fields = {field: field for field in fields}

                for output_key, jq_filter in fields.items():
                    try:
                        result = subprocess.run(
                            ("jq", jq_filter),
                            input=json.dumps(api_data),
                            capture_output=True,
                            text=True,
                        )
                        if result.returncode == 0:
                            value = json.loads(result.stdout)
                        else:
                            raise QueryError(
                                f"jq filter failed for '{output_key}': {result.stderr}"
                            )
                        results[output_key] = value

                    except Exception as e:
                        raise QueryError(f"Error processing field '{output_key}': {e!s}")

            except httpx.ConnectError:
                raise QueryError(f"Connection failed for '{endpoint['url']}'")
            except httpx.TimeoutException:
                raise QueryError(f"Request timeout for '{endpoint['url']}'")
            except json.JSONDecodeError:
                raise QueryError(f"Invalid JSON response from '{endpoint['url']}'")
            except Exception as e:
                raise QueryError(f"Error processing endpoint '{endpoint['url']}': {e!s}")

    return results


@app.get("/health")
async def health():
    return create_response(
        RspStatus.SUCCESS, data={"info": "APIgator is up and running! :)", "version": VERSION}
    )


@app.get("/query/{query_name}")
async def get_query(query_name: str):
    queries = config.get("queries", {})

    if query_name not in queries:
        return JSONResponse(
            status_code=404,
            content=create_response(RspStatus.ERROR, error=f"Query '{query_name}' not found"),
        )

    try:
        results = await execute_query(queries[query_name])
        return create_response(status=RspStatus.SUCCESS, data=results)
    except QueryError as e:
        return JSONResponse(
            status_code=502,
            content=create_response(status=RspStatus.ERROR, error=e.msg),
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content=create_response(status=RspStatus.ERROR, error="Internal server error"),
        )


if __name__ == "__main__":
    load_config()
    print(f"APIgator v{VERSION} running")

    port = config.get("port", 8080)
    host = config.get("host", "0.0.0.0")

    uvicorn.run(app, host=host, port=port)
