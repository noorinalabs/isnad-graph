"""Auth-related Pydantic models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Role(StrEnum):
    """User roles with hierarchical privilege levels."""

    VIEWER = "viewer"
    EDITOR = "editor"
    MODERATOR = "moderator"
    ADMIN = "admin"


ROLE_HIERARCHY: dict[Role, int] = {
    Role.VIEWER: 0,
    Role.EDITOR: 1,
    Role.MODERATOR: 2,
    Role.ADMIN: 3,
}


class SubscriptionTier(StrEnum):
    """Billing subscription tiers."""

    TRIAL = "trial"
    INDIVIDUAL = "individual"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(StrEnum):
    """Subscription lifecycle states."""

    TRIAL = "trial"
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


TRIAL_DURATION_DAYS = 7


class User(BaseModel):
    """Authenticated user."""

    model_config = ConfigDict(frozen=True)

    id: str
    email: str
    name: str
    provider: str
    provider_user_id: str
    created_at: datetime
    is_admin: bool = False
    role: str | None = None
    email_verified: bool = False
    subscription_tier: str | None = None
    subscription_status: str | None = None
    trial_start: datetime | None = None
    trial_expires: datetime | None = None


class TokenResponse(BaseModel):
    """OAuth token pair response."""

    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class VerifyEmailRequest(BaseModel):
    """Request body for POST /auth/verify-email."""

    model_config = ConfigDict(frozen=True)

    token: str
    code: str


class VerifyEmailResponse(BaseModel):
    """Response body for POST /auth/verify-email."""

    model_config = ConfigDict(frozen=True)

    verified: bool
    message: str


class SubscriptionResponse(BaseModel):
    """Subscription status returned by GET /auth/subscription."""

    model_config = ConfigDict(frozen=True)

    tier: str
    status: str
    days_remaining: int
    trial_start: datetime | None = None
    trial_expires: datetime | None = None


class AuthorizationUrlResponse(BaseModel):
    """Authorization URL for OAuth redirect."""

    model_config = ConfigDict(frozen=True)

    authorization_url: str
