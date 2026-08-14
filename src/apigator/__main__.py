"""Main FastAPI application and HTTP endpoint definitions."""

import uvicorn
from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse

from .config import config
from .constants import CONFIG_FILE, INSTANCE_ID, VERSION
from .query import QueryError, execute_query
from .response import RspStatus, create_response

# FastAPI application instance
app = FastAPI(title="APIgator")


@app.get("/health")
async def health():
    """Health check endpoint that returns APIgator status and version information."""
    return create_response(
        RspStatus.SUCCESS,
        data={
            "info": "APIgator is up and running! :)",
            "version": VERSION,
            "instance_id": INSTANCE_ID,
        },
    )


@app.get("/query/{query_name}")
async def get_query(query_name: str, x_apigator_instance_id: str = Header(None)):
    """Execute a named query and return aggregated API results with filtering."""

    # Detect self-referencing requests to prevent infinite loops
    if x_apigator_instance_id == INSTANCE_ID:
        return JSONResponse(
            status_code=400,
            content=create_response(
                RspStatus.ERROR,
                message="Self-referencing request detected."
                " You didn't want to create an infinite loop, did you?",
            ),
        )

    # Retrieve queries from configuration
    queries = config.get("queries", {})

    # Return 404 if the requested query name doesn't exist in configuration
    if query_name not in queries:
        return JSONResponse(
            status_code=404,
            content=create_response(RspStatus.ERROR, message=f"Query '{query_name}' not found"),
        )

    # Execute the query and handle various error scenarios
    try:
        results = await execute_query(queries[query_name])
        return create_response(status=RspStatus.SUCCESS, data=results)
    except QueryError as e:
        # Return 502 for query-specific errors (connection, timeout, jq filter errors, etc.)
        return JSONResponse(
            status_code=502,
            content=create_response(status=RspStatus.ERROR, message=e.msg),
        )
    except Exception:
        # Return 500 for unexpected errors
        return JSONResponse(
            status_code=500,
            content=create_response(status=RspStatus.ERROR, message="Internal server error"),
        )


if __name__ == "__main__":
    print(f"APIgator v{VERSION} running.")

    # Load configuration
    config.load_from_file(CONFIG_FILE)
    port = config.get("port", 8080)
    host = config.get("host", "0.0.0.0")

    # Start the Uvicorn ASGI server
    uvicorn.run(app, host=host, port=port)
