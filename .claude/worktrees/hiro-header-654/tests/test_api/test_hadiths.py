"""Tests for hadith endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

SAMPLE_HADITH = {
    "id": "had-001",
    "matn_ar": "إنما الأعمال بالنيات",
    "matn_en": "Actions are by intentions",
    "source_corpus": "bukhari",
}


def test_list_hadiths_empty(client: TestClient) -> None:
    """GET /api/v1/hadiths returns empty paginated response when no data."""
    resp = client.get("/api/v1/hadiths")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_list_hadiths_with_data(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/hadiths returns hadiths from Neo4j."""
    mock_neo4j.execute_read.side_effect = [
        [{"total": 1}],
        [{"props": SAMPLE_HADITH}],
    ]
    resp = client.get("/api/v1/hadiths")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == "had-001"


def test_get_hadith_found(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/hadiths/{id} returns hadith when found."""
    mock_neo4j.execute_read.return_value = [{"props": SAMPLE_HADITH}]
    resp = client.get("/api/v1/hadiths/had-001")
    assert resp.status_code == 200
    assert resp.json()["id"] == "had-001"
    assert resp.json()["matn_en"] == "Actions are by intentions"


def test_get_hadith_not_found(client: TestClient) -> None:
    """GET /api/v1/hadiths/{id} returns 404 when not found."""
    resp = client.get("/api/v1/hadiths/nonexistent")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
