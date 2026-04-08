"""Authentication session management endpoints.

OAuth login, token issuance, and email verification are handled by user-service.
This module retains only server-side session management for isnad-graph.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from src.api.middleware import require_auth
from src.auth.models import User
from src.auth.sessions import (
    destroy_session,
    get_idle_timeout_warning_seconds,
    list_user_sessions,
    touch_session,
)
from src.config import get_settings

log = structlog.get_logger(logger_name=__name__)

router = APIRouter()


# --- Session management endpoints ---


class SessionResponse(BaseModel):
    """Response model for a single session."""

    model_config = ConfigDict(frozen=True)

    session_id: str
    ip_address: str
    user_agent: str
    created_at: float
    last_active: float


class SessionListResponse(BaseModel):
    """Response model for listing active sessions."""

    model_config = ConfigDict(frozen=True)

    sessions: list[SessionResponse]
    idle_timeout_minutes: int
    warning_seconds: int


@router.get("/auth/sessions", response_model=SessionListResponse)
def list_sessions(user: User = Depends(require_auth)) -> SessionListResponse:
    """List all active sessions for the current user."""
    sessions = list_user_sessions(user.id)
    settings = get_settings().auth
    return SessionListResponse(
        sessions=[
            SessionResponse(
                session_id=s.session_id,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                created_at=s.created_at,
                last_active=s.last_active,
            )
            for s in sessions
        ],
        idle_timeout_minutes=settings.session_idle_timeout_minutes,
        warning_seconds=get_idle_timeout_warning_seconds(),
    )


@router.delete("/auth/sessions/{session_id}", status_code=204)
def revoke_session(session_id: str, user: User = Depends(require_auth)) -> None:
    """Revoke a specific session. Users can only revoke their own sessions."""
    from src.auth.sessions import get_session as get_sess

    session = get_sess(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="Cannot revoke another user's session")
    destroy_session(session_id)
    log.info("session_revoked", user_id=user.id, session_id=session_id)


@router.post("/auth/sessions/heartbeat", status_code=204)
def session_heartbeat(request: Request, user: User = Depends(require_auth)) -> None:
    """Keep the current session alive (reset idle timer)."""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing X-Session-ID header")
    alive = touch_session(session_id)
    if not alive:
        raise HTTPException(
            status_code=401,
            detail="Session has expired",
            headers={"X-Session-Idle-Timeout": "true"},
        )
