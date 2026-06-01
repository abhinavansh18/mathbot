"""
ProblemRepository — all database operations for the Problem model.
No business logic lives here. Services call repositories; repositories call the DB.
"""
import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.problem import Problem
from core.logging import get_logger

log = get_logger(__name__)


class ProblemRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        problem_id: str,
        user_id: str,
        session_id: str,
        query: str,
        problem_type: str,
    ) -> Problem:
        problem = Problem(
            id=uuid.UUID(problem_id),
            user_id=uuid.UUID(user_id),
            session_id=uuid.UUID(session_id) if session_id else None,
            query=query,
            problem_type=problem_type,
        )
        self.db.add(problem)
        await self.db.flush()
        log.info("problem.created", problem_id=problem_id)
        return problem

    async def get(self, problem_id: str) -> Optional[Problem]:
        result = await self.db.execute(
            select(Problem).where(Problem.id == uuid.UUID(problem_id))
        )
        return result.scalar_one_or_none()

    async def list_by_user(
        self, user_id: str, limit: int = 20, offset: int = 0
    ) -> List[Problem]:
        result = await self.db.execute(
            select(Problem)
            .where(Problem.user_id == uuid.UUID(user_id))
            .order_by(Problem.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
