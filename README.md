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

First, create a configuration file named `config.yaml`:

```yaml
# Basic server configuration
host: 0.0.0.0
port: 8080
default_timeout: 10

queries:

  # Basic query definition "my-posts" with multiple upstream queries
  my-posts:
    - url: https://jsonplaceholder.typicode.com/posts/1   # upstream APIs to fetch
      fields:
        - title                                           # fields to aggregate
        - body

    - url: https://jsonplaceholder.typicode.com/posts/2
      fields:
        another-title: .title                             # re-mapping of fields
        another-body: .body
        nested: .some.nested.object                       # nested objects, arrays, ...
        array: .some.indexed[42].item
        everything: .

    - url: https://jsonplaceholder.typicode.com/posts
      fields:
        total_posts: . | length                           # complex jq filters
        sum_of_ids: map(.id) | add
        rounded: .[42].userId | round
        rounded_2decimals: (.[42].userId * 100 | round) / 100

  # With this config, a GET on /query/my-posts returns:
  # "data": {
  #     "title": "sunt aut facere ...",
  #     "body": "quia et suscipit ...",
  #     "another-title": "qui est esse",
  #     "another-body": "est rerum tempore ...",
  #     "nested": null,
  #     "array": null,
  #     "everything": {
  #         "userId": 1,
  #         "id": 1,
  #         "title": "qui est esse",
  #         "body": "est rerum tempore ...",
  #     },
  #     "total_posts": 100,
  #     "sum_of_ids": 5050,
  #     "rounded": 5,
  #     "rounded_2decimals": 5.00
  # }


  # Full example with optional properties:
  full-example:
    - url: http://my.api/endpoint?foo=bar
      method: POST                            # optional HTTP method, defaults to GET
      timeout: 20                             # optional timeout for this endpoint
      headers:                                # optional headers
        Authorization: Bearer ${API_TOKEN}
        ...
      params:                                 # optional query params
        param1: some value
        ...
      body:                                   # optional message body
        foo: bar
      fields:
        ...

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
  "error": ""
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
1. **Timeouts** – To prevent freezing, use `default_timeout` and per-endpoint timeouts appropriately for your upstream APIs.

When running APIgator in production, use a reverse proxy with authentication, HTTPS, rate limiting
and network isolation.
