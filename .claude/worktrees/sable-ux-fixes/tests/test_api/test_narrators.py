"""Tests for narrator endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

SAMPLE_NARRATOR = {
    "id": "nar-001",
    "name_ar": "أبو هريرة",
    "name_en": "Abu Hurayra",
    "generation": "companion",
    "gender": "male",
    "sect_affiliation": "sunni",
    "trustworthiness_consensus": "thiqah",
}


def test_list_narrators_empty(client: TestClient) -> None:
    """GET /api/v1/narrators returns empty paginated response when no data."""
    resp = client.get("/api/v1/narrators")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1
    assert body["limit"] == 20


def test_list_narrators_with_data(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/narrators returns narrators from Neo4j."""
    mock_neo4j.execute_read.side_effect = [
        [{"total": 1}],
        [{"props": SAMPLE_NARRATOR}],
    ]
    resp = client.get("/api/v1/narrators")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "nar-001"
    assert body["items"][0]["name_en"] == "Abu Hurayra"


def test_list_narrators_pagination(client: TestClient, mock_neo4j: MagicMock) -> None:
    """Pagination params are forwarded correctly."""
    mock_neo4j.execute_read.side_effect = [
        [{"total": 50}],
        [{"props": SAMPLE_NARRATOR}],
    ]
    resp = client.get("/api/v1/narrators?page=3&limit=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["page"] == 3
    assert body["limit"] == 10


def test_get_narrator_found(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/narrators/{id} returns narrator when found."""
    mock_neo4j.execute_read.return_value = [{"props": SAMPLE_NARRATOR}]
    resp = client.get("/api/v1/narrators/nar-001")
    assert resp.status_code == 200
    assert resp.json()["id"] == "nar-001"


def test_get_narrator_not_found(client: TestClient) -> None:
    """GET /api/v1/narrators/{id} returns 404 when not found."""
    resp = client.get("/api/v1/narrators/nonexistent")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
