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

First, create a configuration file:

```yaml
# config.yaml
host: 0.0.0.0                                 # server address to listen on
port: 8080                                    # server port
default_timeout: 10                           # default timeout in seconds for all endpoints

queries:                                      # predefined queries

  # Basic example with two upstream queries
  sysinfo:                                    # query named "sysinfo"
    - url: http://my.api/status/system        # list of upstream APIs to fetch
      fields:
        cpu_usage: .stats.cpu.usage           # fields names and values to gather in our response
        temp: .stats.temperature

    - url: http://another.api/memory
      fields:
        memory_used: .cores[0].used
        memory_percent: .cores[0].percent | round   # jq filter for rounded value

    - url: http://yet.another.api/all
      fields:
        result: .                             # Fetch entire reponse as data

  # Example with optional properties and complex jq filters
  full-example:                               # query named "full-example"
    - url: http://complex.example/memory
      method: GET                             # optional HTTP method, defaults to GET
      timeout: 15                             # optional timeout for this endpoint
      headers:                                # optional headers
        Authorization: Bearer ${API_TOKEN}
      params:                                 # optional extra params
        param1: some value
      body:                                   # optional message body
        foo: bar
      fields:
        rounded_2decimals: (. * 100 | round) / 100    # rounds a single float value to two decimals
        sum_of_foos: map(.foo) | add                  # gives the sum of each "foo" item in an array
        len_of_array: .somearray | length             # gets the length of a given array
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
