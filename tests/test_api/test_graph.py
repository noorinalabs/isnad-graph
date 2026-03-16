"""Tests for graph traversal endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient


def test_narrator_chains_found(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/graph/narrator/{id}/chains returns chains."""
    mock_neo4j.execute_read.side_effect = [
        # exists check
        [{"id": "nar-001"}],
        # chain rows
        [
            {
                "chain_id": "ch-001",
                "hadith_id": "had-001",
                "matn_ar": "متن الحديث",
                "matn_en": "Hadith text",
                "grade": "sahih",
            }
        ],
    ]
    resp = client.get("/api/v1/graph/narrator/nar-001/chains")
    assert resp.status_code == 200
    body = resp.json()
    assert body["narrator_id"] == "nar-001"
    assert body["total"] == 1
    assert body["chains"][0]["chain_id"] == "ch-001"


def test_narrator_chains_not_found(client: TestClient) -> None:
    """GET /api/v1/graph/narrator/{id}/chains returns 404 for unknown narrator."""
    resp = client.get("/api/v1/graph/narrator/nonexistent/chains")
    assert resp.status_code == 404


def test_hadith_chain_found(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/graph/hadith/{id}/chain returns chain visualization."""
    mock_neo4j.execute_read.side_effect = [
        # exists check
        [{"id": "had-001"}],
        # chain visualization rows
        [
            {
                "chain_id": "ch-001",
                "source_id": "nar-001",
                "source_name_ar": "الراوي الأول",
                "source_name_en": "Narrator One",
                "source_gen": "companion",
                "target_id": "nar-002",
                "target_name_ar": "الراوي الثاني",
                "target_name_en": "Narrator Two",
                "target_gen": "successor",
            }
        ],
    ]
    resp = client.get("/api/v1/graph/hadith/had-001/chain")
    assert resp.status_code == 200
    body = resp.json()
    assert body["hadith_id"] == "had-001"
    assert len(body["nodes"]) == 2
    assert len(body["edges"]) == 1
    assert body["edges"][0]["relationship"] == "TRANSMITTED_TO"


def test_hadith_chain_not_found(client: TestClient) -> None:
    """GET /api/v1/graph/hadith/{id}/chain returns 404 for unknown hadith."""
    resp = client.get("/api/v1/graph/hadith/nonexistent/chain")
    assert resp.status_code == 404


def test_narrator_network_found(client: TestClient, mock_neo4j: MagicMock) -> None:
    """GET /api/v1/graph/narrator/{id}/network returns ego network."""
    mock_neo4j.execute_read.side_effect = [
        # exists check
        [{"id": "nar-001"}],
        # network row
        [
            {
                "center_name_ar": "الراوي المركزي",
                "center_name_en": "Central Narrator",
                "center_gen": "companion",
                "teachers": [
                    {
                        "id": "nar-010",
                        "name_ar": "المعلم",
                        "name_en": "Teacher",
                        "gen": "companion",
                        "rel": "teacher",
                    }
                ],
                "students": [
                    {
                        "id": "nar-020",
                        "name_ar": "الطالب",
                        "name_en": "Student",
                        "gen": "successor",
                        "rel": "student",
                    }
                ],
            }
        ],
    ]
    resp = client.get("/api/v1/graph/narrator/nar-001/network")
    assert resp.status_code == 200
    body = resp.json()
    assert body["narrator_id"] == "nar-001"
    assert body["teachers"] == 1
    assert body["students"] == 1
    assert len(body["nodes"]) == 3  # center + teacher + student
    assert len(body["edges"]) == 2


def test_narrator_network_not_found(client: TestClient) -> None:
    """GET /api/v1/graph/narrator/{id}/network returns 404 for unknown narrator."""
    resp = client.get("/api/v1/graph/narrator/nonexistent/network")
    assert resp.status_code == 404
