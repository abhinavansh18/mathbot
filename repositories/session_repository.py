"""
SessionRepository — database operations for Session model (cold storage).
Hot session data lives in Redis. This is the persistence fallback.
"""
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession as AsyncDBSession

from models.session import Session
from core.logging import get_logger

log = get_logger(__name__)


class SessionRepository:
    def __init__(self, db: AsyncDBSession):
        self.db = db

    async def get(self, session_id: str) -> Optional[Session]:
        result = await self.db.execute(
            select(Session).where(Session.id == uuid.UUID(session_id))
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        session_id: str,
        user_id: str,
        messages_json: str,
        summary: Optional[str] = None,
    ) -> Session:
        existing = await self.get(session_id)
        if existing:
            existing.messages_json = messages_json
            if summary:
                existing.summary = summary
            await self.db.flush()
            return existing

        session = Session(
            id=uuid.UUID(session_id),
            user_id=uuid.UUID(user_id),
            messages_json=messages_json,
            summary=summary,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def delete(self, session_id: str) -> bool:
        session = await self.get(session_id)
        if session:
            await self.db.delete(session)
            await self.db.flush()
            return True
        return False
