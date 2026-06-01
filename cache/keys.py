"""
Centralised cache key builders.
All Redis keys are defined here — never construct key strings inline elsewhere.
This prevents key collisions and makes invalidation straightforward.
"""
import hashlib


def solve_cache_key(query: str) -> str:
    """Deterministic key for a solve result based on query content."""
    query_hash = hashlib.sha256(query.strip().lower().encode()).hexdigest()[:16]
    return f"solve:{query_hash}"


def session_key(session_id: str) -> str:
    return f"session:{session_id}"


def rate_limit_key(user_id: str, route: str) -> str:
    return f"rate:{user_id}:{route}"


def revoked_token_key(token: str) -> str:
    token_hash = hashlib.sha256(token.encode()).hexdigest()[:16]
    return f"revoked:{token_hash}"


def user_key(user_id: str) -> str:
    return f"user:{user_id}"
