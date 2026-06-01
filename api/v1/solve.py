"""
/api/v1/solve — submit a math problem and receive a solution.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.middleware.auth import get_current_user
from cache.client import CacheClient, get_redis
from core.exceptions import AgentTimeoutError
from database.connection import get_db
from schemas.solve import SolveRequest, SolveResponse
from services.math_service import MathService

router = APIRouter()


@router.post(
    "",
    response_model=SolveResponse,
    summary="Solve a math problem",
    description="Submit a plain-text or LaTeX math problem. Returns structured solution with steps.",
)
async def solve_problem(
    request: SolveRequest,
    user_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> SolveResponse:
    cache = CacheClient(redis)
    service = MathService(db=db, cache=cache, user_id=user_id)
    try:
        return await service.solve(request)
    except AgentTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Agent timed out: {exc}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
