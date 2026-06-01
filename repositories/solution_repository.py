"""
SolutionRepository — database operations for Solution model.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.problem import Solution
from core.logging import get_logger

log = get_logger(__name__)


class SolutionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        problem_id: str,
        answer: str,
        confidence: float,
        latency_ms: float,
        latex_answer: Optional[str] = None,
        steps_json: Optional[str] = None,
        tools_used: Optional[str] = None,
    ) -> Solution:
        solution = Solution(
            id=uuid.uuid4(),
            problem_id=uuid.UUID(problem_id),
            answer=answer,
            latex_answer=latex_answer,
            steps_json=steps_json,
            confidence=confidence,
            tools_used=tools_used,
            latency_ms=latency_ms,
        )
        self.db.add(solution)
        await self.db.flush()
        return solution

    async def get_by_problem(self, problem_id: str) -> Optional[Solution]:
        result = await self.db.execute(
            select(Solution).where(Solution.problem_id == uuid.UUID(problem_id))
        )
        return result.scalar_one_or_none()
