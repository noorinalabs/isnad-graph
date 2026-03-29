"""Authentication endpoints for OAuth login flows and email/password auth."""

from __future__ import annotations

import logging
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse, Response

from src.api.middleware import require_auth
from src.auth.models import (
    AuthorizationUrlResponse,
    EmailLoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    User,
    UserPublic,
)
from src.auth.providers import PROVIDERS, get_provider, retrieve_pkce_verifier, store_pkce_verifier
from src.auth.rate_limit import check_rate_limit
from src.auth.tokens import create_access_token, create_refresh_token, revoke_token, verify_token
from src.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


def _build_redirect_uri(provider: str) -> str:
    """Build the OAuth callback redirect URI from settings."""
    base = get_settings().auth.oauth_redirect_base_url.rstrip("/")
    return f"{base}/api/v1/auth/callback/{provider}"


def _set_token_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly cookie pair and a readable expiry metadata cookie on a response."""
    settings = get_settings().auth
    common: dict[str, object] = {
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
        "path": "/",
    }
    if settings.cookie_domain:
        common["domain"] = settings.cookie_domain
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.access_token_expire_minutes * 60,
        **common,  # type: ignore[arg-type]
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.refresh_token_expire_days * 86400,
        **common,  # type: ignore[arg-type]
    )
    # Non-httpOnly metadata cookie so the frontend can read token expiry
    # and trigger proactive refresh before the access token expires.
    expires_at = int(time.time()) + settings.access_token_expire_minutes * 60
    meta_common: dict[str, object] = {
        "httponly": False,
        "samesite": "lax",
        "secure": settings.cookie_secure,
        "path": "/",
    }
    if settings.cookie_domain:
        meta_common["domain"] = settings.cookie_domain
    response.set_cookie(
        key="token_expires_at",
        value=str(expires_at),
        max_age=settings.access_token_expire_minutes * 60,
        **meta_common,  # type: ignore[arg-type]
    )


def _build_token_response(user_id: str) -> tuple[TokenResponse, str, str]:
    """Create access + refresh tokens and build a TokenResponse."""
    settings = get_settings().auth
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    token_resp = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )
    return token_resp, access_token, refresh_token


def _get_client_ip(request: Request) -> str:
    """Extract client IP from the request."""
    return request.client.host if request.client else "unknown"


# --- Email/password registration ---


@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(request: Request, body: RegisterRequest) -> Response:
    """Register a new user with email and password.

    Rate limited to 3 requests per minute per IP.
    """
    client_ip = _get_client_ip(request)
    if not check_rate_limit(f"register:{client_ip}", max_requests=3, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many registration attempts. Try again later.",
            headers={"Retry-After": "60"},
        )

    from src.auth.passwords import hash_password
    from src.auth.pg_users import create_email_user, ensure_users_table
    from src.utils.pg_client import PgClient

    password_hash = hash_password(body.password)

    pg = PgClient()
    try:
        ensure_users_table(pg)
        try:
            user = create_email_user(
                pg,
                email=body.email,
                name=body.name,
                password_hash=password_hash,
            )
        except Exception as exc:
            err_msg = str(exc).lower()
            if "unique" in err_msg or "duplicate" in err_msg or "ix_users_email" in err_msg:
                raise HTTPException(
                    status_code=409,
                    detail="An account with this email already exists",
                ) from exc
            raise
    finally:
        pg.close()

    logger.info("User registered: email=%s, id=%s", body.email, user.id)

    token_resp, access_token, refresh_token = _build_token_response(user.id)
    response = JSONResponse(content=token_resp.model_dump(), status_code=201)
    _set_token_cookies(response, access_token, refresh_token)
    return response


# --- Email/password login ---


@router.post("/auth/login/email", response_model=TokenResponse)
def login_email(request: Request, body: EmailLoginRequest) -> Response:
    """Authenticate with email and password.

    Rate limited to 5 requests per minute per IP.
    """
    client_ip = _get_client_ip(request)
    if not check_rate_limit(f"login_email:{client_ip}", max_requests=5, window_seconds=60):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts. Try again later.",
            headers={"Retry-After": "60"},
        )

    from src.auth.passwords import verify_password
    from src.auth.pg_users import ensure_users_table, get_user_by_email
    from src.utils.pg_client import PgClient

    email = body.email.strip().lower()

    pg = PgClient()
    try:
        ensure_users_table(pg)
        user = get_user_by_email(pg, email)
    finally:
        pg.close()

    if user is None or user.provider != "email" or user.password_hash is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Account suspended")

    logger.info("Email login: email=%s, id=%s", email, user.id)

    token_resp, access_token, refresh_token = _build_token_response(user.id)
    response = JSONResponse(content=token_resp.model_dump())
    _set_token_cookies(response, access_token, refresh_token)
    return response


# --- OAuth login ---


@router.post(
    "/auth/login/{provider}",
    response_model=AuthorizationUrlResponse,
)
def login(provider: str) -> AuthorizationUrlResponse:
    """Initiate OAuth flow — return the provider's authorization URL."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    oauth_provider = get_provider(provider)
    state = secrets.token_urlsafe(32)
    redirect_uri = _build_redirect_uri(provider)
    url, verifier = oauth_provider.get_authorization_url(redirect_uri=redirect_uri, state=state)

    # Persist PKCE verifier so the callback can use it
    store_pkce_verifier(state, verifier)

    return AuthorizationUrlResponse(authorization_url=url)


@router.get("/auth/callback/{provider}")
async def callback(provider: str, code: str, state: str) -> RedirectResponse:
    """Handle OAuth callback — upsert user in PG, set httpOnly cookies, redirect."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    oauth_provider = get_provider(provider)
    redirect_uri = _build_redirect_uri(provider)

    # Retrieve PKCE verifier stored during login
    code_verifier = retrieve_pkce_verifier(state)

    try:
        user_info = await oauth_provider.exchange_code(
            code=code, redirect_uri=redirect_uri, code_verifier=code_verifier
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"OAuth exchange failed: {exc}") from exc

    # Upsert user in PostgreSQL
    from src.auth.pg_users import ensure_users_table, upsert_user
    from src.utils.pg_client import PgClient

    pg = PgClient()
    try:
        ensure_users_table(pg)
        user = upsert_user(
            pg,
            provider=user_info.provider,
            provider_user_id=user_info.provider_user_id,
            email=user_info.email or None,
            name=user_info.name,
        )
    finally:
        pg.close()

    settings = get_settings().auth
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    redirect_url = settings.frontend_redirect_url.rstrip("/")
    response = RedirectResponse(url=redirect_url, status_code=302)
    _set_token_cookies(response, access_token, refresh_token)
    return response


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(request: Request, body: RefreshRequest | None = None) -> Response:
    """Refresh an access token using a valid refresh token (with rotation).

    Accepts the refresh token from a JSON body OR from the httpOnly
    ``refresh_token`` cookie (for browser clients that cannot read the cookie).
    Returns new tokens as JSON AND sets updated httpOnly cookies.
    """
    token = body.refresh_token if body else None
    if not token:
        token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")  # noqa: B904

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token is not a refresh token")

    user_id = payload.get("sub")
    if not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Revoke the old refresh token (rotation)
    revoke_token(token)

    token_resp, new_access, new_refresh = _build_token_response(user_id)

    response = JSONResponse(content=token_resp.model_dump())
    _set_token_cookies(response, new_access, new_refresh)
    return response


@router.post("/auth/logout", status_code=204)
def logout(user: User = Depends(require_auth)) -> Response:
    """Invalidate the current session — clear auth cookies."""
    response = Response(status_code=204)
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/")
    response.delete_cookie("token_expires_at", path="/")
    return response


@router.get("/auth/me", response_model=UserPublic)
def me(user: User = Depends(require_auth)) -> UserPublic:
    """Return the current authenticated user from PostgreSQL."""
    return UserPublic.from_user(user)
