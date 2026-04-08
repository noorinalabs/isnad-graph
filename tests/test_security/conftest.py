"""Security test fixtures.

Provides a FastAPI TestClient that does NOT bypass auth, so we can test
authentication and authorization enforcement end-to-end.

Tokens are now validated via user-service JWKS (RS256). These fixtures
create test tokens and patch the JWKS validation to simulate various
failure modes.
"""

from __future__ import annotations

import secrets
import time
from unittest.mock import MagicMock, patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jose import jwt

# ---------------------------------------------------------------------------
# RSA key pair for test tokens
# ---------------------------------------------------------------------------

_TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_TEST_PEM = _TEST_PRIVATE_KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
)


def _make_token(
    *,
    sub: str = "test-user-id",
    token_type: str = "access",
    expire_minutes: int = 30,
    expired: bool = False,
    extra_claims: dict[str, object] | None = None,
) -> str:
    """Create an RS256 JWT token for testing."""
    now = int(time.time())
    payload: dict[str, object] = {
        "sub": sub,
        "email": f"{sub}@example.com",
        "roles": ["viewer"],
        "subscription_status": "active",
        "type": token_type,
        "exp": now - 3600 if expired else now + expire_minutes * 60,
        "iat": now - 7200 if expired else now,
        "jti": secrets.token_hex(16),
    }
    if extra_claims:
        payload.update(extra_claims)
    return str(jwt.encode(payload, _TEST_PEM, algorithm="RS256"))


@pytest.fixture
def valid_token() -> str:
    """A valid access token for a regular (non-admin) user."""
    return _make_token(sub="regular-user-001")


@pytest.fixture
def admin_token() -> str:
    """A valid access token for an admin user."""
    return _make_token(sub="admin-user-001", extra_claims={"roles": ["admin"]})


@pytest.fixture
def expired_token() -> str:
    """An expired JWT access token."""
    return _make_token(expired=True)


@pytest.fixture
def refresh_token_as_access() -> str:
    """A refresh token (wrong type for protected endpoints)."""
    return _make_token(sub="test-user-id", token_type="refresh")


@pytest.fixture
def forged_token() -> str:
    """A token signed with a different RSA key (simulates invalid signature)."""
    wrong_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    wrong_pem = wrong_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    now = int(time.time())
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "roles": ["viewer"],
        "subscription_status": "active",
        "type": "access",
        "exp": now + 3600,
        "iat": now,
        "jti": secrets.token_hex(16),
    }
    return str(jwt.encode(payload, wrong_pem, algorithm="RS256"))


@pytest.fixture
def mock_neo4j() -> MagicMock:
    """Mock Neo4jClient that returns no results by default."""
    client = MagicMock()
    client.execute_read.return_value = []
    client.execute_write.return_value = []
    return client


@pytest.fixture
def app(mock_neo4j: MagicMock) -> FastAPI:
    """FastAPI app with mocked Neo4j but real auth middleware (no bypass).

    Patches verify_user_service_token to validate against the test RSA key
    so we can test real JWT validation logic without a running user-service.
    """
    from src.api.app import create_app

    application = create_app()
    application.state.neo4j = mock_neo4j
    return application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Test client with real auth enforcement.

    Patches JWKS validation so that valid test tokens are accepted and
    invalid ones are rejected with appropriate errors.
    """
    import base64

    pub = _TEST_PRIVATE_KEY.public_key()
    pub_numbers = pub.public_numbers()

    def _int_to_b64(n: int, length: int) -> str:
        return base64.urlsafe_b64encode(n.to_bytes(length, "big")).rstrip(b"=").decode()

    test_jwks = {
        "keys": [
            {
                "kty": "RSA",
                "use": "sig",
                "alg": "RS256",
                "kid": "test-key-1",
                "n": _int_to_b64(pub_numbers.n, 256),
                "e": _int_to_b64(pub_numbers.e, 3),
            }
        ]
    }

    with patch("src.auth.jwks.fetch_jwks", return_value=test_jwks):
        yield TestClient(app, raise_server_exceptions=False)
