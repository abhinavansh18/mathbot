"""
Redis async client wrapper.
All cache interactions go through this module — never import redis directly elsewhere.
"""
from typing import Optional

import redis.asyncio as aioredis

from core.config import settings
from core.logging import get_logger

log = get_logger(__name__)

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency — yields the shared Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class CacheClient:
    """
    Thin wrapper around Redis with typed get/set/delete helpers.
    Use this in services rather than calling Redis directly.
    """

    def __init__(self, redis: aioredis.Redis):
        self._r = redis

    async def get(self, key: str) -> Optional[str]:
        try:
            return await self._r.get(key)
        except Exception as exc:
            log.warning("cache.get_failed", key=key, error=str(exc))
            return None

    async def set(self, key: str, value: str, ttl: int = settings.CACHE_TTL_SECONDS) -> bool:
        try:
            await self._r.setex(key, ttl, value)
            return True
        except Exception as exc:
            log.warning("cache.set_failed", key=key, error=str(exc))
            return False

    async def delete(self, key: str) -> bool:
        try:
            await self._r.delete(key)
            return True
        except Exception as exc:
            log.warning("cache.delete_failed", key=key, error=str(exc))
            return False

    async def increment(self, key: str, ttl: Optional[int] = None) -> int:
        """Atomic increment — used for rate limiting counters."""
        count = await self._r.incr(key)
        if count == 1 and ttl:
            await self._r.expire(key, ttl)
        return count
