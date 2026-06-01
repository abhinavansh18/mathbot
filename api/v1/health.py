"""
/api/v1/health — liveness, readiness, and Prometheus metrics endpoints.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from cache.client import get_redis
from core.metrics import REGISTRY
from database.connection import get_db
from schemas.common import HealthCheck

router = APIRouter()


@router.get("/live", summary="Liveness probe — is the process running?")
async def liveness():
    return {"status": "alive"}


@router.get(
    "",
    response_model=HealthCheck,
    summary="Full health check — database and Redis connectivity",
)
async def health(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> HealthCheck:
    # Database
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"error: {exc}"

    # Redis
    redis_status = "ok"
    try:
        await redis.ping()
    except Exception as exc:
        redis_status = f"error: {exc}"

    overall = "healthy" if db_status == "ok" and redis_status == "ok" else "degraded"

    return HealthCheck(
        status=overall,
        database=db_status,
        redis=redis_status,
        llm="ok",   # LLM checked lazily — avoids slow health checks
    )


@router.get(
    "/metrics",
    response_class=PlainTextResponse,
    summary="Prometheus metrics endpoint",
    include_in_schema=False,
)
async def metrics():
    return PlainTextResponse(
        generate_latest(REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )
