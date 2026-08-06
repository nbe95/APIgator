FROM python:3.11-alpine
RUN apk add --no-cache jq
RUN pip install fastapi uvicorn httpx pyyaml

ARG VERSION=unknown
ENV APIGATOR_VERSION=${VERSION}

COPY apigator.py /app/apigator.py
WORKDIR /app
CMD ["python", "apigator.py"]
