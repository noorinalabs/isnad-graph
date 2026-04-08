"""Authentication module — JWT validation via user-service JWKS."""

from __future__ import annotations

from src.auth.jwks import fetch_jwks, invalidate_jwks_cache, verify_user_service_token
from src.auth.models import ROLE_HIERARCHY, Role, User
from src.auth.sessions import (
    SessionInfo,
    create_session,
    destroy_all_user_sessions,
    destroy_session,
    get_session,
    list_user_sessions,
    touch_session,
)

__all__ = [
    "ROLE_HIERARCHY",
    "Role",
    "SessionInfo",
    "User",
    "create_session",
    "destroy_all_user_sessions",
    "destroy_session",
    "fetch_jwks",
    "get_session",
    "invalidate_jwks_cache",
    "list_user_sessions",
    "touch_session",
    "verify_user_service_token",
]
