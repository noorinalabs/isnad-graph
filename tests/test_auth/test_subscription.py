"""Tests for subscription/trial endpoints and models."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.auth.models import (
    TRIAL_DURATION_DAYS,
    SubscriptionResponse,
    SubscriptionStatus,
    SubscriptionTier,
)


class TestSubscriptionModels:
    """Test subscription-related model enums and constants."""

    def test_subscription_tiers(self) -> None:
        assert SubscriptionTier.TRIAL == "trial"
        assert SubscriptionTier.INDIVIDUAL == "individual"
        assert SubscriptionTier.TEAM == "team"
        assert SubscriptionTier.ENTERPRISE == "enterprise"

    def test_subscription_statuses(self) -> None:
        assert SubscriptionStatus.TRIAL == "trial"
        assert SubscriptionStatus.ACTIVE == "active"
        assert SubscriptionStatus.EXPIRED == "expired"
        assert SubscriptionStatus.CANCELLED == "cancelled"

    def test_trial_duration(self) -> None:
        assert TRIAL_DURATION_DAYS == 7

    def test_subscription_response_model(self) -> None:
        resp = SubscriptionResponse(
            tier="trial",
            status="trial",
            days_remaining=5,
            trial_start=datetime(2026, 1, 1, tzinfo=UTC),
            trial_expires=datetime(2026, 1, 8, tzinfo=UTC),
        )
        assert resp.tier == "trial"
        assert resp.days_remaining == 5
        assert resp.trial_expires is not None


class TestSubscriptionEndpoint:
    """Test GET /api/v1/auth/subscription."""

    def test_subscription_returns_trial_info(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Active trial user should get trial info with days remaining."""
        now = datetime.now(UTC)
        expires = now + timedelta(days=5)

        # Mock the require_auth dependency user
        from src.api.middleware import require_auth
        from src.auth.models import User

        async def fake_user() -> User:
            return User(
                id="test-user",
                email="test@example.com",
                name="Test User",
                provider="google",
                provider_user_id="test-user",
                created_at=now,
                subscription_tier="trial",
                subscription_status="trial",
                trial_start=now,
                trial_expires=expires,
            )

        client.app.dependency_overrides[require_auth] = fake_user  # type: ignore[union-attr]

        resp = client.get("/api/v1/auth/subscription")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "trial"
        assert data["status"] == "trial"
        assert data["days_remaining"] >= 4  # at least 4 days
        assert data["trial_expires"] is not None

    def test_subscription_expired_trial(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Expired trial should return expired status."""
        now = datetime.now(UTC)
        expired = now - timedelta(days=1)

        from src.api.middleware import require_auth
        from src.auth.models import User

        async def fake_user() -> User:
            return User(
                id="test-user",
                email="test@example.com",
                name="Test User",
                provider="google",
                provider_user_id="test-user",
                created_at=now - timedelta(days=8),
                subscription_tier="trial",
                subscription_status="trial",
                trial_start=now - timedelta(days=8),
                trial_expires=expired,
            )

        client.app.dependency_overrides[require_auth] = fake_user  # type: ignore[union-attr]

        resp = client.get("/api/v1/auth/subscription")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "expired"
        assert data["days_remaining"] == 0

    def test_subscription_active_plan(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Active paid subscription should return unlimited days."""
        now = datetime.now(UTC)

        from src.api.middleware import require_auth
        from src.auth.models import User

        async def fake_user() -> User:
            return User(
                id="test-user",
                email="test@example.com",
                name="Test User",
                provider="google",
                provider_user_id="test-user",
                created_at=now,
                subscription_tier="individual",
                subscription_status="active",
                trial_start=now - timedelta(days=10),
                trial_expires=now - timedelta(days=3),
            )

        client.app.dependency_overrides[require_auth] = fake_user  # type: ignore[union-attr]

        resp = client.get("/api/v1/auth/subscription")
        assert resp.status_code == 200
        data = resp.json()
        assert data["tier"] == "individual"
        assert data["status"] == "active"
        assert data["days_remaining"] == -1
