"""Argon2id password hashing and verification."""

from __future__ import annotations

from argon2 import PasswordHasher, Type
from argon2.exceptions import VerifyMismatchError

# OWASP-recommended argon2id parameters
_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
    type=Type.ID,
)


def hash_password(password: str) -> str:
    """Hash a password using argon2id. Returns the PHC-format hash string."""
    return str(_hasher.hash(password))


def verify_password(password: str, hash_str: str) -> bool:
    """Verify a password against an argon2id hash. Returns True if valid."""
    try:
        return bool(_hasher.verify(hash_str, password))
    except VerifyMismatchError:
        return False
