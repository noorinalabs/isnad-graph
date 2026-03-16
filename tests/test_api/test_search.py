"""Tests for search endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_search_returns_results(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/search?q=test returns matching narrators and hadiths."""
    mock_neo4j.execute_read.side_effect = [
        # narrator search
        [
            {
                "id": "nar-001",
                "name_ar": "اختبار",
                "name_en": "test narrator",
                "type": "narrator",
                "score": 1.0,
            }
        ],
        # hadith search
        [
            {
                "id": "had-001",
                "matn_ar": "نص اختبار",
                "matn_en": "test hadith text",
                "type": "hadith",
                "score": 1.0,
            }
        ],
    ]
    resp = client.get("/api/v1/search?q=test")
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "test"
    assert body["total"] == 2
    assert body["results"][0]["type"] == "narrator"
    assert body["results"][1]["type"] == "hadith"


def test_search_empty_results(client: TestClient) -> None:
    """GET /api/v1/search?q=xyz returns empty results when nothing matches."""
    resp = client.get("/api/v1/search?q=xyz")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["results"] == []


def test_search_requires_query(client: TestClient) -> None:
    """GET /api/v1/search without q param returns 422."""
    resp = client.get("/api/v1/search")
    assert resp.status_code == 422


def test_semantic_search_returns_503(client: TestClient) -> None:
    """GET /api/v1/search/semantic returns 503 (pgvector not wired)."""
    resp = client.get("/api/v1/search/semantic?q=test")
    assert resp.status_code == 503
    body = resp.json()
    assert "not yet available" in body["detail"].lower()
