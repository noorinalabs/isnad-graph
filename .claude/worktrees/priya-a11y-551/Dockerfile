# syntax=docker/dockerfile:1
# Multi-arch build (amd64 + arm64) — see docs/devops/ghcr-publish-design.md
FROM python:3.14-slim AS base

# Single RUN layer for OS deps + cleanup to minimize image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

FROM base AS builder
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen --no-dev

FROM base AS runtime
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY . .

ENV PATH="/app/.venv/bin:$PATH"

# No CMD here — docker-compose.prod.yml `command:` is the single source of truth
# for the uvicorn invocation (includes --workers and other prod-specific flags).
# To run standalone: docker run ... uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000
