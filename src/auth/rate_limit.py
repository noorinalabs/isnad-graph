"""Per-endpoint rate limiting with Redis backend and in-memory fallback."""

from __future__ import annotations

import logging
import time

import redis as redis_lib

from src.utils.redis_client import get_redis_client

logger = logging.getLogger(__name__)

# In-memory fallback store: key -> list of timestamps
_memory_store: dict[str, list[float]] = {}


def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60) -> bool:
    """Check if the request is within the rate limit.

    Args:
        key: Unique rate limit key (e.g. "register:{ip}" or "login:{ip}").
        max_requests: Maximum number of requests in the window.
        window_seconds: Sliding window size in seconds.

    Returns:
        True if the request is allowed, False if rate limited.
    """
    now = time.time()

    result = _check_redis(key, max_requests, window_seconds, now)
    if result is not None:
        return result

    return _check_memory(key, max_requests, window_seconds, now)


def _check_redis(key: str, max_requests: int, window_seconds: int, now: float) -> bool | None:
    """Try Redis-backed rate limit check. Returns None if Redis unavailable."""
    redis_client = get_redis_client()
    if redis_client is None:
        return None

    redis_key = f"ratelimit:{key}"
    window_start = now - window_seconds

    try:
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(redis_key, "-inf", window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, window_seconds + 1)
        results = pipe.execute()
        count: int = results[1]
        return count < max_requests
    except redis_lib.ConnectionError, redis_lib.TimeoutError, OSError:
        logger.warning("Redis rate limit check failed, falling back to in-memory")
        return None


def _check_memory(key: str, max_requests: int, window_seconds: int, now: float) -> bool:
    """In-memory sliding window rate limit check."""
    window_start = now - float(window_seconds)
    timestamps = _memory_store.get(key, [])
    timestamps = [t for t in timestamps if t > window_start]

    if len(timestamps) >= max_requests:
        _memory_store[key] = timestamps
        return False

    timestamps.append(now)
    _memory_store[key] = timestamps
    return True
