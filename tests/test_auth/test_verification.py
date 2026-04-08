"""Tests for email verification logic."""

from __future__ import annotations

import time

import pytest

from src.auth.verification import (
    _resend_counts,
    _verification_store,
    check_resend_rate_limit,
    generate_and_store_verification,
    validate_verification,
)


@pytest.fixture(autouse=True)
def _clear_stores() -> None:
    """Clear in-memory stores between tests."""
    _verification_store.clear()
    _resend_counts.clear()


class TestGenerateAndStoreVerification:
    def test_generates_code_and_token(self) -> None:
        code, token = generate_and_store_verification("user-123")
        assert len(code) == 6
        assert code.isdigit()
        assert len(token) > 0

    def test_stores_in_memory_when_redis_unavailable(self) -> None:
        code, token = generate_and_store_verification("user-456")
        assert "user-456" in _verification_store
        stored_code, stored_token, _ = _verification_store["user-456"]
        assert stored_code == code
        assert stored_token == token


class TestValidateVerification:
    def test_valid_code_and_token(self) -> None:
        code, token = generate_and_store_verification("user-789")
        user_id = validate_verification(token, code)
        assert user_id == "user-789"

    def test_code_consumed_after_use(self) -> None:
        code, token = generate_and_store_verification("user-consumed")
        validate_verification(token, code)
        with pytest.raises(ValueError, match="expired or was already used"):
            validate_verification(token, code)

    def test_wrong_code_rejected(self) -> None:
        code, token = generate_and_store_verification("user-wrong")
        with pytest.raises(ValueError, match="Invalid verification code"):
            validate_verification(token, "000000")

    def test_invalid_token_rejected(self) -> None:
        generate_and_store_verification("user-invalid-token")
        with pytest.raises(ValueError, match="Invalid verification token"):
            validate_verification("garbage-token", "123456")

    def test_expired_code_rejected(self) -> None:
        code, token = generate_and_store_verification("user-expired")
        # Manually expire the entry
        stored_code, stored_token, _ = _verification_store["user-expired"]
        _verification_store["user-expired"] = (stored_code, stored_token, time.time() - 100000)
        with pytest.raises(ValueError, match="expired"):
            validate_verification(token, code)


class TestCheckResendRateLimit:
    def test_allows_within_limit(self) -> None:
        assert check_resend_rate_limit("user-rate") is True
        assert check_resend_rate_limit("user-rate") is True
        assert check_resend_rate_limit("user-rate") is True

    def test_blocks_after_limit(self) -> None:
        for _ in range(3):
            assert check_resend_rate_limit("user-limited") is True
        assert check_resend_rate_limit("user-limited") is False

    def test_different_users_independent(self) -> None:
        for _ in range(3):
            check_resend_rate_limit("user-a")
        assert check_resend_rate_limit("user-a") is False
        assert check_resend_rate_limit("user-b") is True
