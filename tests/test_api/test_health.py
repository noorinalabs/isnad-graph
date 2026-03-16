"""Tests for the health check endpoint."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_health_check_ok(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET / returns 200 with status and neo4j_connected when Neo4j is reachable."""
    mock_neo4j.execute_read.return_value = [{"ok": 1}]
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["neo4j_connected"] is True


def test_health_check_neo4j_down(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET / reports neo4j_connected=False when Neo4j raises."""
    mock_neo4j.execute_read.side_effect = RuntimeError("connection refused")
    resp = client.get("/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["neo4j_connected"] is False
