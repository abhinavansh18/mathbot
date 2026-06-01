"""
Structured request/response logging middleware.
Logs every request with method, path, status code, and latency.
"""
import time
import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        # Bind request context to all log statements in this request's scope
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )

        log = structlog.get_logger()
        log.info("request.started")

        response = await call_next(request)

        latency_ms = (time.monotonic() - start) * 1000
        log.info(
            "request.completed",
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
        )

        # Pass request_id back in response headers for client correlation
        response.headers["X-Request-ID"] = request_id
        return response
