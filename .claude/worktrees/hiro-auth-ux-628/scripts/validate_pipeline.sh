#!/usr/bin/env bash
# Run the full pipeline against real data and validate results.
# Prerequisites: Docker services running (make infra), API keys configured (.env)
set -euo pipefail

echo "=== Pipeline Validation ==="

echo "Step 1: Checking infrastructure..."
docker compose ps --services --filter status=running

echo "Step 2: Running acquisition (subset)..."
uv run isnad acquire

echo "Step 3: Running parsing..."
uv run isnad parse

echo "Step 4: Validating staging data..."
uv run isnad validate-staging

echo "Step 5: Running entity resolution..."
uv run isnad resolve

echo "Step 6: Loading graph..."
uv run isnad load

echo "Step 7: Running enrichment..."
uv run isnad enrich

echo "Step 8: Running validation queries..."
uv run isnad validate

echo "=== Pipeline Validation Complete ==="
