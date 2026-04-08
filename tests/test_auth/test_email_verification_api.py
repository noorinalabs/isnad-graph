"""Tests for email verification API endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.auth.tokens import create_access_token
from src.auth.verification import (
    _resend_counts,
    _verification_store,
    generate_and_store_verification,
)


@pytest.fixture(autouse=True)
def _clear_stores() -> None:
    """Clear in-memory stores between tests."""
    _verification_store.clear()
    _resend_counts.clear()


class TestSendVerification:
    def test_sends_verification_email(self, client: TestClient) -> None:
        token = create_access_token("google:user-new", role="viewer")
        with patch("src.api.routes.auth.send_verification_email") as mock_send:
            res = client.post(
                "/api/v1/auth/send-verification",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert res.status_code == 200
        assert res.json()["message"] == "Verification email sent"
        mock_send.assert_called_once()

    def test_already_verified_user_skipped(self, client: TestClient, mock_neo4j: MagicMock) -> None:
        mock_neo4j.execute_read.return_value = [
            {
                "u": {
                    "email": "user@example.com",
                    "name": "Test",
                    "provider": "google",
                    "is_admin": False,
                    "role": "viewer",
                    "email_verified": True,
                }
            }
        ]
        token = create_access_token("google:user-verified", role="viewer")
        res = client.post(
            "/api/v1/auth/send-verification",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200
        assert res.json()["message"] == "Email already verified"

    def test_rate_limited(self, client: TestClient) -> None:
        token = create_access_token("google:user-rate", role="viewer")
        with patch("src.api.routes.auth.send_verification_email"):
            for _ in range(3):
                client.post(
                    "/api/v1/auth/send-verification",
                    headers={"Authorization": f"Bearer {token}"},
                )
            res = client.post(
                "/api/v1/auth/send-verification",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert res.status_code == 429


class TestVerifyEmail:
    def test_valid_verification(self, client: TestClient, mock_neo4j: MagicMock) -> None:
        code, token = generate_and_store_verification("google:user-verify")
        res = client.post(
            "/api/v1/auth/verify-email",
            json={"token": token, "code": code},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["verified"] is True
        assert data["message"] == "Email verified successfully"
        mock_neo4j.execute_write.assert_called()

    def test_invalid_code(self, client: TestClient) -> None:
        _, token = generate_and_store_verification("google:user-bad-code")
        res = client.post(
            "/api/v1/auth/verify-email",
            json={"token": token, "code": "000000"},
        )
        assert res.status_code == 400

    def test_invalid_token(self, client: TestClient) -> None:
        generate_and_store_verification("google:user-bad-token")
        res = client.post(
            "/api/v1/auth/verify-email",
            json={"token": "garbage", "code": "123456"},
        )
        assert res.status_code == 400

    def test_code_cannot_be_reused(self, client: TestClient, mock_neo4j: MagicMock) -> None:
        code, token = generate_and_store_verification("google:user-reuse")
        client.post(
            "/api/v1/auth/verify-email",
            json={"token": token, "code": code},
        )
        res = client.post(
            "/api/v1/auth/verify-email",
            json={"token": token, "code": code},
        )
        assert res.status_code == 400


class TestResendVerification:
    def test_resends_successfully(self, client: TestClient) -> None:
        token = create_access_token("google:user-resend", role="viewer")
        with patch("src.api.routes.auth.send_verification_email"):
            res = client.post(
                "/api/v1/auth/resend-verification",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert res.status_code == 200
        assert res.json()["message"] == "Verification email sent"

    def test_resend_rate_limited(self, client: TestClient) -> None:
        token = create_access_token("google:user-resend-limit", role="viewer")
        with patch("src.api.routes.auth.send_verification_email"):
            for _ in range(3):
                client.post(
                    "/api/v1/auth/resend-verification",
                    headers={"Authorization": f"Bearer {token}"},
                )
            res = client.post(
                "/api/v1/auth/resend-verification",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert res.status_code == 429
