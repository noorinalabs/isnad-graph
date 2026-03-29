"""Tests for email/password registration and login endpoints."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.auth.models import User


@pytest.fixture(autouse=True)
def _reset_rate_limit_store() -> Iterator[None]:
    """Clear in-memory rate limit store between tests."""
    from src.auth import rate_limit

    rate_limit._memory_store.clear()
    yield
    rate_limit._memory_store.clear()


def _make_email_user(
    email: str = "test@example.com",
    name: str = "Test User",
    user_id: str = "uuid-123",
    password_hash: str = "$argon2id$v=19$m=19456,t=2,p=1$salt$hash",
) -> User:
    return User(
        id=user_id,
        email=email,
        name=name,
        provider="email",
        provider_user_id=email,
        password_hash=password_hash,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    def test_register_success(self, client: TestClient) -> None:
        mock_user = _make_email_user()
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.passwords.PasswordHasher.hash", return_value="$argon2id$hashed"),
            patch("src.auth.pg_users.create_email_user", return_value=mock_user),
            patch("src.auth.pg_users.ensure_users_table"),
        ):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "securepass123",
                    "name": "Test User",
                },
            )

        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        # httpOnly cookies should be set
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    def test_register_password_hash_not_in_response(self, client: TestClient) -> None:
        mock_user = _make_email_user()
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.passwords.PasswordHasher.hash", return_value="$argon2id$hashed"),
            patch("src.auth.pg_users.create_email_user", return_value=mock_user),
            patch("src.auth.pg_users.ensure_users_table"),
        ):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": "securepass123",
                    "name": "Test User",
                },
            )

        assert resp.status_code == 201
        body_text = resp.text
        assert "password_hash" not in body_text
        assert "$argon2id" not in body_text

    def test_register_duplicate_email_409(self, client: TestClient) -> None:
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.passwords.PasswordHasher.hash", return_value="$argon2id$hashed"),
            patch(
                "src.auth.pg_users.create_email_user",
                side_effect=Exception("duplicate key value violates unique constraint"),
            ),
            patch("src.auth.pg_users.ensure_users_table"),
        ):
            resp = client.post(
                "/api/v1/auth/register",
                json={"email": "dup@example.com", "password": "securepass123", "name": "Test"},
            )

        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]

    def test_register_invalid_email_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "securepass123", "name": "Test"},
        )
        assert resp.status_code == 422

    def test_register_short_password_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "short", "name": "Test"},
        )
        assert resp.status_code == 422

    def test_register_empty_name_422(self, client: TestClient) -> None:
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "securepass123", "name": "   "},
        )
        assert resp.status_code == 422

    def test_register_unicode_name(self, client: TestClient) -> None:
        mock_user = _make_email_user(name="عبد الله محمد")
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.passwords.PasswordHasher.hash", return_value="$argon2id$hashed"),
            patch("src.auth.pg_users.create_email_user", return_value=mock_user),
            patch("src.auth.pg_users.ensure_users_table"),
        ):
            resp = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "arabic@example.com",
                    "password": "securepass123",
                    "name": "عبد الله محمد",
                },
            )

        assert resp.status_code == 201

    def test_register_rate_limit_429(self, client: TestClient) -> None:
        with patch("src.api.routes.auth.check_rate_limit", return_value=False):
            resp = client.post(
                "/api/v1/auth/register",
                json={"email": "test@example.com", "password": "securepass123", "name": "Test"},
            )

        assert resp.status_code == 429
        assert "Retry-After" in resp.headers


class TestEmailLogin:
    """Tests for POST /api/v1/auth/login/email."""

    def test_login_success(self, client: TestClient) -> None:
        mock_user = _make_email_user()
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.pg_users.get_user_by_email", return_value=mock_user),
            patch("src.auth.pg_users.ensure_users_table"),
            patch("src.auth.passwords.PasswordHasher.verify", return_value=True),
        ):
            resp = client.post(
                "/api/v1/auth/login/email",
                json={"email": "test@example.com", "password": "securepass123"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "access_token" in resp.cookies

    def test_login_wrong_password_401(self, client: TestClient) -> None:
        mock_user = _make_email_user()
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.pg_users.get_user_by_email", return_value=mock_user),
            patch("src.auth.pg_users.ensure_users_table"),
            patch("src.auth.passwords.verify_password", return_value=False),
        ):
            resp = client.post(
                "/api/v1/auth/login/email",
                json={"email": "test@example.com", "password": "wrongpassword"},
            )

        assert resp.status_code == 401
        assert "Invalid email or password" in resp.json()["detail"]

    def test_login_nonexistent_user_401(self, client: TestClient) -> None:
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.pg_users.get_user_by_email", return_value=None),
            patch("src.auth.pg_users.ensure_users_table"),
        ):
            resp = client.post(
                "/api/v1/auth/login/email",
                json={"email": "noone@example.com", "password": "securepass123"},
            )

        assert resp.status_code == 401

    def test_login_oauth_user_cannot_use_email_login(self, client: TestClient) -> None:
        """Users who registered via OAuth cannot login with email/password."""
        oauth_user = User(
            id="uuid-456",
            email="oauth@example.com",
            name="OAuth User",
            provider="google",
            provider_user_id="google-123",
            password_hash=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.pg_users.get_user_by_email", return_value=oauth_user),
            patch("src.auth.pg_users.ensure_users_table"),
        ):
            resp = client.post(
                "/api/v1/auth/login/email",
                json={"email": "oauth@example.com", "password": "anypassword"},
            )

        assert resp.status_code == 401

    def test_login_suspended_user_403(self, client: TestClient) -> None:
        mock_user = User(
            id="uuid-789",
            email="suspended@example.com",
            name="Suspended",
            provider="email",
            provider_user_id="suspended@example.com",
            password_hash="$argon2id$v=19$m=19456,t=2,p=1$salt$hash",
            is_suspended=True,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.pg_users.get_user_by_email", return_value=mock_user),
            patch("src.auth.pg_users.ensure_users_table"),
            patch("src.auth.passwords.PasswordHasher.verify", return_value=True),
        ):
            resp = client.post(
                "/api/v1/auth/login/email",
                json={"email": "suspended@example.com", "password": "securepass123"},
            )

        assert resp.status_code == 403

    def test_login_rate_limit_429(self, client: TestClient) -> None:
        with patch("src.api.routes.auth.check_rate_limit", return_value=False):
            resp = client.post(
                "/api/v1/auth/login/email",
                json={"email": "test@example.com", "password": "securepass123"},
            )

        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    def test_login_password_hash_not_in_response(self, client: TestClient) -> None:
        mock_user = _make_email_user()
        with (
            patch("src.api.routes.auth.check_rate_limit", return_value=True),
            patch("src.auth.pg_users.get_user_by_email", return_value=mock_user),
            patch("src.auth.pg_users.ensure_users_table"),
            patch("src.auth.passwords.PasswordHasher.verify", return_value=True),
        ):
            resp = client.post(
                "/api/v1/auth/login/email",
                json={"email": "test@example.com", "password": "securepass123"},
            )

        assert resp.status_code == 200
        assert "password_hash" not in resp.text
        assert "$argon2id" not in resp.text


class TestMeEndpointPasswordExclusion:
    """Test that /auth/me never returns password_hash."""

    def test_me_excludes_password_hash(self, client: TestClient) -> None:
        from src.auth.tokens import create_access_token

        token = create_access_token("uuid-123")
        mock_user = _make_email_user()
        with patch("src.auth.pg_users.get_user_by_id", return_value=mock_user):
            resp = client.get(
                "/api/v1/auth/me",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "password_hash" not in data
        assert "$argon2id" not in resp.text


class TestPasswordHashing:
    """Unit tests for argon2id password hashing."""

    def test_hash_and_verify(self) -> None:
        from src.auth.passwords import hash_password, verify_password

        password = "my-secure-password-123"
        hashed = hash_password(password)
        assert hashed.startswith("$argon2id$")
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self) -> None:
        from src.auth.passwords import hash_password, verify_password

        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_unicode_password(self) -> None:
        from src.auth.passwords import hash_password, verify_password

        password = "كلمة_المرور_العربية_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestRateLimit:
    """Unit tests for per-endpoint rate limiting."""

    def test_rate_limit_allows_under_threshold(self) -> None:
        from src.auth.rate_limit import check_rate_limit

        with patch("src.auth.rate_limit.get_redis_client", return_value=None):
            for _ in range(3):
                assert check_rate_limit("test:127.0.0.1", max_requests=3) is True

    def test_rate_limit_blocks_over_threshold(self) -> None:
        from src.auth.rate_limit import check_rate_limit

        with patch("src.auth.rate_limit.get_redis_client", return_value=None):
            for _ in range(5):
                check_rate_limit("test2:127.0.0.1", max_requests=5)
            assert check_rate_limit("test2:127.0.0.1", max_requests=5) is False


class TestRegisterRequestValidation:
    """Unit tests for RegisterRequest model validation."""

    def test_valid_request(self) -> None:
        from src.auth.models import RegisterRequest

        req = RegisterRequest(email="user@example.com", password="12345678", name="Test")
        assert req.email == "user@example.com"

    def test_email_normalized_lowercase(self) -> None:
        from src.auth.models import RegisterRequest

        req = RegisterRequest(email="User@Example.COM", password="12345678", name="Test")
        assert req.email == "user@example.com"

    def test_invalid_email_rejected(self) -> None:
        from src.auth.models import RegisterRequest

        with pytest.raises(Exception):
            RegisterRequest(email="not-email", password="12345678", name="Test")

    def test_short_password_rejected(self) -> None:
        from src.auth.models import RegisterRequest

        with pytest.raises(Exception):
            RegisterRequest(email="user@example.com", password="short", name="Test")

    def test_empty_name_rejected(self) -> None:
        from src.auth.models import RegisterRequest

        with pytest.raises(Exception):
            RegisterRequest(email="user@example.com", password="12345678", name="   ")
