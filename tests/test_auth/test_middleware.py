"""Tests for auth middleware and protected endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from src.auth.tokens import create_access_token, create_refresh_token


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

    def test_narrators_accessible_with_token(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        mock_neo4j.execute_read.return_value = []
        token = create_access_token("test-user")
        resp = client.get(
            "/api/v1/narrators",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code != 401

    def test_narrators_accessible_with_cookie(
        self, client: TestClient, mock_neo4j: MagicMock
    ) -> None:
        """Cookie-based auth fallback should work when no Authorization header is sent."""
        mock_neo4j.execute_read.return_value = []
        token = create_access_token("cookie-user")
        client.cookies.set("access_token", token)
        resp = client.get("/api/v1/narrators")
        assert resp.status_code != 401

    def test_header_takes_precedence_over_cookie(self, client: TestClient) -> None:
        """When both header and cookie are present, the header token is used."""
        header_token = create_access_token("header-user")
        cookie_token = create_access_token("cookie-user")
        client.cookies.set("access_token", cookie_token)
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {header_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == "header-user"

    def test_cookie_auth_returns_user(self, client: TestClient) -> None:
        """Cookie auth should return the correct user identity."""
        token = create_access_token("cookie-user-id")
        client.cookies.set("access_token", token)
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        assert resp.json()["id"] == "cookie-user-id"


class TestPublicEndpoints:
    """Health and auth endpoints should be accessible without a token."""

    def test_health_is_public(self, client: TestClient) -> None:
        resp = client.get("/")
        assert resp.status_code != 401

    def test_auth_login_is_public(self, client: TestClient) -> None:
        resp = client.post("/api/v1/auth/login/google")
        assert resp.status_code != 401

    def test_auth_me_requires_auth(self, client: TestClient) -> None:
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401


class TestAuthMeEndpoint:
    def test_returns_user_info(self, client: TestClient) -> None:
        token = create_access_token("my-user-id")
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "my-user-id"

    def test_rejects_refresh_token(self, client: TestClient) -> None:
        token = create_refresh_token("my-user-id")
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401


class TestRefreshEndpoint:
    def test_refresh_returns_new_tokens(self, client: TestClient) -> None:
        refresh = create_refresh_token("my-user-id")
        client.cookies.set("refresh_token", refresh)
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        # Tokens must be in httpOnly cookies, not in the response body
        assert "access_token" not in data
        assert "refresh_token" not in data
        assert "access_token" in resp.cookies
        assert "refresh_token" in resp.cookies

    def test_refresh_with_no_cookie(self, client: TestClient) -> None:
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    def test_refresh_with_invalid_token(self, client: TestClient) -> None:
        client.cookies.set("refresh_token", "garbage")
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401

    def test_refresh_with_access_token_rejected(self, client: TestClient) -> None:
        access = create_access_token("my-user-id")
        client.cookies.set("refresh_token", access)
        resp = client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401


class TestRBAC:
    """Test role-based access control."""

    def test_admin_route_rejects_viewer(self, client: TestClient) -> None:
        token = create_access_token("viewer-user", role="viewer")
        resp = client.get(
            "/api/v1/admin/health/live",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403

    def test_admin_route_allows_admin(self, client: TestClient) -> None:
        token = create_access_token("admin-user", role="admin")
        resp = client.get(
            "/api/v1/admin/health/live",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code != 403

    def test_auth_me_includes_role(self, client: TestClient) -> None:
        token = create_access_token("role-user", role="researcher")
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "researcher"

    def test_default_role_is_viewer(self, client: TestClient) -> None:
        token = create_access_token("no-role-user")
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["role"] == "viewer"
