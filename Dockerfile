ARG PYTHON_BASE=3.14-slim


# Build stage for pdm modules
FROM python:$PYTHON_BASE AS builder

WORKDIR /app

RUN pip install -U pdm
ENV PDM_CHECK_UPDATE=false

COPY pyproject.toml pdm.lock README.md /app/
COPY src/ /app/src

RUN pdm install --check --prod --no-editable


# Run stage
FROM python:$PYTHON_BASE

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    jq \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv/ /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
COPY src /app/src
COPY entrypoint.sh /app
COPY config.default.yaml /app/config.default.yaml

RUN chmod +x /app/entrypoint.sh

EXPOSE 8080

ARG VERSION
ARG VERSION_SHA
ENV APIGATOR_VERSION="${VERSION}"
ENV APIGATOR_VERSION_SHA="${VERSION_SHA}"

ENTRYPOINT ["/app/entrypoint.sh"]
