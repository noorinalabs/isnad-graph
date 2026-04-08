"""Tests for auth middleware with user-service JWT validation."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _mock_verify(payload: dict[str, object]):
    """Return a mock for verify_user_service_token that returns the given payload."""
    mock = MagicMock(return_value=payload)
    return mock


_VALID_PAYLOAD = {
    "sub": "test-user",
    "email": "test@example.com",
    "roles": ["viewer"],
    "subscription_status": "active",
    "type": "access",
}


class TestProtectedEndpoints:
    """Protected /api/v1/ endpoints should return 401 without a token."""

    def test_narrators_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/v1/narrators")
        assert resp.status_code == 401

    def test_hadiths_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/v1/hadiths")
        assert resp.status_code == 401

    def test_collections_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/v1/collections")
        assert resp.status_code == 401

    def test_narrators_accessible_with_valid_jwt(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        mock_neo4j.execute_read.return_value = []
        mock = _mock_verify(_VALID_PAYLOAD)
        with patch("src.auth.jwks.verify_user_service_token", mock):
            resp = client.get(
                "/api/v1/narrators",
                headers={"Authorization": "Bearer fake-token"},
            )
        assert resp.status_code != 401


class TestPublicEndpoints:
    """Health and auth endpoints should be accessible without a token."""

    def test_health_is_public(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code != 401
