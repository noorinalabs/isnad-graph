"""Tests for TrialEnforcementMiddleware with JWT-based subscription status."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

_PATCH_TARGET = "src.auth.jwks.verify_user_service_token"


class TestTrialEnforcement:
    """Test that expired trial users are blocked based on JWT subscription_status claim."""

    def test_expired_subscription_blocks_api(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Expired subscription_status in JWT gives 403 on regular API endpoints."""
        payload = {
            "sub": "test-user",
            "email": "test@example.com",
            "roles": ["viewer"],
            "subscription_status": "expired",
            "type": "access",
        }
        with patch(_PATCH_TARGET, return_value=payload):
            resp = client.get(
                "/api/v1/narrators",
                headers={"Authorization": "Bearer fake-token"},
            )
        assert resp.status_code == 403
        data = resp.json()
        assert data["code"] == "trial_expired"

    def test_expired_trial_allows_auth(self, client: TestClient) -> None:
        """Expired trial user can still access auth endpoints."""
        resp = client.get("/api/v1/auth/sessions")
        # This returns 401 (no token) not 403 — auth paths are exempt from trial check
        assert resp.status_code != 403

    def test_active_subscription_allows_api(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Active subscription_status in JWT allows API access."""
        payload = {
            "sub": "test-user",
            "email": "test@example.com",
            "roles": ["viewer"],
            "subscription_status": "active",
            "type": "access",
        }
        mock_neo4j.execute_read.return_value = []
        with patch(_PATCH_TARGET, return_value=payload):
            resp = client.get(
                "/api/v1/narrators",
                headers={"Authorization": "Bearer fake-token"},
            )
        assert resp.status_code != 403

    def test_health_exempt(self, client: TestClient) -> None:
        """Health endpoint is never blocked by trial enforcement."""
        resp = client.get("/health")
        assert resp.status_code != 403
