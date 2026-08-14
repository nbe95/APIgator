# :crocodile: APIgator

A lightweight HTTP **API Aggregator** with jq filtering. Combine multiple API responses into a
single endpoint with field extraction and transformation.

## Features

- 🔗 Aggregate multiple predefined APIs calls in one query
- 🎯 Extract specific fields from responses
- 🔄 Transform data with jq filters
- 📅 Jinja2 templates with predefined time variables and filters
- 🐳 Self-hosted Docker container
- ⚡ Fast, async request handling

## Use Cases

- **Simplify cascaded requests** – Combine multiple dependent API calls into a single GET request
- **Externalize credentials** – Keep sensitive credentials isolated from client applications for better security and trust
- **Aggregate multi-endpoint data** – Fetch and merge data from multiple endpoints in one query (useful for dashboards when the framework doesn't support this natively)

## Usage

### Quick Start

Spin up a Docker container and edit your configuration as described below.

```sh
docker run -d \
  -p 8080:8080 \
  -v ./config:/app/config \
  nbe95/apigator:latest
```

Use `latest` for the most recent version with automatic updates, or pin to specific versions with
SemVer tags (`1.2.3`, `1.2`, `1`) for stability.

### Configuration

Create a configuration file named `config.yaml` and mount it into the container:

```yaml
# Server configuration
host: 0.0.0.0
port: 8080
default_timeout: 10

queries:

  # Basic query definition "my-posts" with multiple upstream queries
  my-posts:
    - url: https://jsonplaceholder.typicode.com/posts/1   # upstream APIs to fetch
      fields:
        - title                               # fields to aggregate (short syntax, top-level only)
        - body

    - url: https://jsonplaceholder.typicode.com/posts/2
      fields:
        remapped-title: .title                # explicit syntax (enables remapping of fields)
        remapped-body: .body
        nested: .some.nested.object           # nested objects, arrays, ...
        array: .some.indexed[42].item
        everything: .                         # fetch entire response at once

    - url: https://jsonplaceholder.typicode.com/posts
      fields:
        total_posts: . | length               # some complex jq filters
        sum_of_ids: map(.id) | add
        rounded: .[42].userId | round
        rounded_2decimals: (.[42].userId * 100 | round) / 100


  # Full example with optional properties
  full-example:
    - url: http://my.api/endpoint?foo=bar
      method: POST                            # optional HTTP method, defaults to GET
      timeout: 20                             # optional timeout in seconds for this endpoint
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
Note that after each change, you will need to restart the container for the new config to take
effect.

The arguments `headers`, `params` and `body` all accept Jinja2 based templates with predefined time
constants and filters evaluated at runtime. This means that you can define dynamic, time dependant
parameters in your upstream queries, like so:

```yaml
params:
  start_date: "{{ today | strftime }}"
  end_date: "{{ tomorrow | strftime }}"
  this_week: "{{ this_week_start | strftime }}"
  months:
    last:
      - "{{ last_month_start | strftime }}"
      - "{{ last_month_end | strftime }}"
  us_date_format: "{{ yesterday | strftime('%m/%d/%Y') }}"
  weird_date_format: "{{ next_year_start | strftime('%Y%m%d') }}"
  ...
...
```

The `strftime` filter formats any datetime object as `YYYY-MM-DD`, but will take any custom format
argument if provided. Take a look [here](src/apigator/jinja.py) to see what's supported.

### Running APIgator

A simple GET request with a specified query name returns all aggregated data at once.

Using the config example from above:

```sh
curl http://localhost:8080/query/my-posts
```

```json
{
    "status": "success",
    "timestamp": "2024-01-15T10:30:45.123456",
    "data": {
        "title": "sunt aut facere ...",
        "body": "quia et suscipit ...",
        "remapped-title": "qui est esse",
        "remapped-body": "est rerum tempore ...",
        "nested": null,
        "array": null,
        "everything": {
            "userId": 1,
            "id": 1,
            "title": "qui est esse",
            "body": "est rerum tempore ...",
        },
        "total_posts": 100,
        "sum_of_ids": 5050,
        "rounded": 5,
        "rounded_2decimals": 5.00
    },
    "error": ""
}
```

> [!NOTE]
> Any values not found in the upstream responses will be set to `null` (e.g. "nested" and "array").

> [!IMPORTANT]
> Always store sensitive values and credentials in an environment file. Reference them with
> `${SECRET_STUFF}` in your configuration.

### Docker Compose

```yaml
services:
  apigator:
    image: nbe95/apigator:latest
    restart: unless-stopped
    ports:
      - 8080:8080
    volumes:
      - ./config:/app/config
    environment:
      - SOME_API_TOKEN=...
```

## API Endpoints

| Endpoint      | Method    | Description                               |
|---------------|-----------|-------------------------------------------|
| /query/{name} | GET       | Execute query and return aggregated data  |
| /health       | GET       | General health check                      |

> [!NOTE]
> Only JSON responses are supported for any upstream queries.

## :warning:️ Security Considerations

APIgator is intended for internal use only:

1. **Config is sensitive** – Never commit `config.yaml`. It may contain API credentials and internal
   URLs.
1. **SSRF attacks** – Only trusted admins should modify the config.
1. **No HTTPS** – Add TLS via reverse proxy (Traefik, Caddy, ...).
1. **No built-in auth** – Use a reverse proxy with authentication.
1. **Timeouts** – To prevent freezing, use `default_timeout` and per-endpoint timeouts appropriately
   for your upstream APIs.

> [!WARNING]
> When running APIgator in production, use a reverse proxy with authentication, HTTPS, rate limiting
> and network isolation.
