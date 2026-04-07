"""Tests for TrialEnforcementMiddleware."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.auth.tokens import create_access_token


class TestTrialEnforcement:
    """Test that expired trial users are blocked from API but not auth/billing."""

    def test_expired_trial_blocks_api(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Expired trial user gets 403 on regular API endpoints."""
        token = create_access_token("test-user", role="viewer")

        # Mock Neo4j to return expired trial
        expired = datetime.now(UTC) - timedelta(days=1)
        mock_neo4j.execute_read.return_value = [
            {"status": "expired", "expires": expired}
        ]

        resp = client.get(
            "/api/v1/narrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert data["code"] == "trial_expired"

    def test_expired_trial_allows_auth(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Expired trial user can still access auth endpoints."""
        token = create_access_token("test-user", role="viewer")

        mock_neo4j.execute_read.return_value = [
            {"status": "expired", "expires": datetime.now(UTC) - timedelta(days=1)}
        ]

        resp = client.get(
            "/api/v1/auth/providers",
        )
        assert resp.status_code == 200

    def test_active_trial_allows_api(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Active trial user can access API normally."""
        token = create_access_token("test-user", role="viewer")

        active_expires = datetime.now(UTC) + timedelta(days=5)
        mock_neo4j.execute_read.return_value = [
            {"status": "trial", "expires": active_expires}
        ]

        resp = client.get(
            "/api/v1/narrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        # Will get 200 or some other status from the actual narrators route,
        # but NOT 403 from trial enforcement
        assert resp.status_code != 403

    def test_health_exempt(self, client: TestClient) -> None:
        """Health endpoint always accessible regardless of trial status."""
        resp = client.get("/health")
        assert resp.status_code == 200
