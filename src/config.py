"""Application configuration via Pydantic Settings, loaded from .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Neo4jSettings(BaseSettings):
    """Neo4j graph database connection settings."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "isnad_graph_dev"

    model_config = SettingsConfigDict(env_prefix="NEO4J_")


class PostgresSettings(BaseSettings):
    """PostgreSQL connection settings."""

    dsn: str = "postgresql://isnad:isnad_dev@localhost:5432/isnad_graph"

    model_config = SettingsConfigDict(env_prefix="PG_")


class RateLimitSettings(BaseSettings):
    """Rate limiting configuration."""

    requests_per_minute: int = 120
    window_seconds: int = 60

    model_config = SettingsConfigDict(env_prefix="RATE_LIMIT_")


class RedisSettings(BaseSettings):
    """Redis cache connection settings."""

    url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class AuthSettings(BaseSettings):
    """Authentication settings for user-service JWT validation."""

    user_service_url: str = "http://localhost:8001"
    user_service_jwks_cache_ttl: int = 3600
    session_idle_timeout_minutes: int = 30
    session_idle_warning_seconds: int = 60
    max_concurrent_sessions: int = 5

    model_config = SettingsConfigDict(env_prefix="AUTH_")


class SecurityHeaderSettings(BaseSettings):
    """Configurable security headers. Production defaults; override for dev."""

    content_security_policy: str = "default-src 'self'; frame-ancestors 'none'"
    hsts_max_age: int = 63072000
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    x_frame_options: str = "DENY"
    x_xss_protection: str = "0"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
    )
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_resource_policy: str = "same-origin"

    model_config = SettingsConfigDict(env_prefix="SECURITY_")


class Settings(BaseSettings):
    """Root application settings, composed from nested service settings."""

    neo4j: Neo4jSettings = Neo4jSettings()
    postgres: PostgresSettings = PostgresSettings()
    redis: RedisSettings = RedisSettings()
    rate_limit: RateLimitSettings = RateLimitSettings()
    auth: AuthSettings = AuthSettings()
    security_headers: SecurityHeaderSettings = SecurityHeaderSettings()

    cors_origins: list[str] = ["http://localhost:3000"]

    log_level: str = "INFO"
    log_format: str = "console"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
