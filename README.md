# :crocodile: APIgator

A lightweight HTTP **API Aggregator** with jq filtering. Combine multiple API responses into a
single endpoint with field extraction and transformation.

## Features

- 🔗 Aggregate multiple APIs in one query
- 🎯 Extract specific fields from responses
- 🔄 Transform data with jq filters
- 🐳 Self-hosted Docker container
- ⚡ Fast, async request handling

## Quick Start

```sh
docker run -d \
  -p 8080:8080 \
  -v $(pwd)/config.yaml:/config/config.yaml \
  nbe95/apigator:latest
```

## Configuration

Create a `config.yaml`:

```yaml
port: 8080                                  # server configuration
host: "0.0.0.0"

queries:
  sysinfo:                                  # query named "sysinfo"
    - url: http://monitoring/api/system     # first upstream API
      method: GET
      headers:
        Authorization: "Bearer ${API_TOKEN}"
      fields:
        - cpu_usage: "stats.cpu.usage"      # option 1: simple path
        - temp:
            path: "stats.temperature"
            filter: "round"                 # option 2: with jq filter

    - url: http://api/memory                # seconds upstream API
      method: GET
      fields:
        - memory_used: "data.used"
        - memory_percent:
            path: "data.percent"
            filter: "round"

  ...                                       # further queries
```

## Usage

A GET request with the specified query name  returns
aggregated data at once:

```sh
curl http://localhost:8080/query/sysinfo
```

```json
{
  "status": "success",
  "timestamp": "2024-01-15T10:30:45.123456",
  "data": {
    "cpu_usage": 45.2,
    "temp": 65,
    "memory_used": 8192,
    "memory_percent": 50
  },
  "error": "",
  "message": "",
  "version": "x.y.z"
}
```

## Environment Variables

Always store sensitive values and credentials in an environment file. Reference it with
`${SECRET_STUFF}`, for example:

```yaml
headers:
  Authorization: Bearer ${SOME_API_TOKEN}
```

## Docker Compose

```yaml
services:
  apigator:
    image: nbe95/apigator:latest
    ports:
      - 8080:8080
    volumes:
      - ./config.yaml:/config/config.yaml
    environment:
      - SOME_API_TOKEN=...
```

## API Endpoints

| Endpoint      | Method    | Description                               |
|---------------|-----------|-------------------------------------------|
| /query/{name} | GET       | Execute query and return aggregated data  |
| /health       | GET       | Health check                              |

## ⚠️ Security Considerations

APIgator is intended for internal use only:

1. **Config is sensitive** – Never commit `config.yaml`. It contains API credentials and internal URLs.
1. **SSRF attacks** – Only trusted admins should modify the config.
1. **No HTTPS** – Add TLS via reverse proxy (Traefik, Caddy, ...).
1. **No built-in auth** – Use a reverse proxy with authentication.
1. **Timeouts** – Configure appropriately for slow upstream APIs.

When running APIgator in production, use a reverse proxy with authentication, HTTPS, rate limiting
and network isolation.
