"""
Async SQLAlchemy engine and session factory.
Everything in repositories/ uses get_db() as a FastAPI dependency.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# ── ORM base class ─────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Engine ─────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,          # logs SQL in development
    future=True,
)

AsyncSessionFactory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── FastAPI dependency ─────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """Yield an async DB session; auto-closes after the request."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Startup helper ─────────────────────────────────────────────────────────────
async def create_tables() -> None:
    """
    Creates all tables that don't exist yet.
    In production, use Alembic migrations instead.
    """
    # Import models so Base knows about them
    from models import user, problem, session  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
