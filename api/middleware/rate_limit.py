"""
Rate limiting middleware using Redis sliding window counters.
Limits are configured per-route in core/config.py.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from cache.client import CacheClient
from cache.keys import rate_limit_key
from core.config import settings
from core.logging import get_logger

log = get_logger(__name__)

# Map route prefixes to (limit, window_seconds)
ROUTE_LIMITS: dict[str, tuple[int, int]] = {
    "/api/v1/solve": (settings.RATE_LIMIT_SOLVE_PER_MINUTE, 60),
    "/api/v1/ocr":   (settings.RATE_LIMIT_OCR_PER_MINUTE, 60),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Only rate-limit authenticated routes
        user_id = getattr(request.state, "user_id", None)
        if not user_id:
            return await call_next(request)

        for route_prefix, (limit, window) in ROUTE_LIMITS.items():
            if request.url.path.startswith(route_prefix):
                try:
                    redis = request.app.state.redis
                    cache = CacheClient(redis)
                    key = rate_limit_key(user_id, route_prefix)
                    count = await cache.increment(key, ttl=window)

                    if count > limit:
                        log.warning(
                            "rate_limit.exceeded",
                            user_id=user_id,
                            route=route_prefix,
                            count=count,
                        )
                        return JSONResponse(
                            status_code=429,
                            content={
                                "error": "Rate limit exceeded.",
                                "detail": f"Max {limit} requests per {window}s on this endpoint.",
                            },
                        )
                except Exception as exc:
                    # On Redis failure, fail open (don't block users)
                    log.warning("rate_limit.redis_error", error=str(exc))

        return await call_next(request)
