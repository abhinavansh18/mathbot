"""
Shared pytest fixtures.
These are available to every test file without needing to import them.
"""
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from unittest.mock import AsyncMock, MagicMock

# ── Event loop (needed for async tests) ──────────────────────────────────────
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ── In-memory SQLite database for tests ──────────────────────────────────────
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Fresh in-memory database for each test function."""
    from database.connection import Base
    from models import user, problem, session  # noqa — register models

    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        yield db

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ── Redis mock ────────────────────────────────────────────────────────────────
@pytest.fixture
def mock_redis():
    """In-memory dict-backed Redis mock."""
    store = {}

    redis = AsyncMock()
    redis.get = AsyncMock(side_effect=lambda k: store.get(k))
    redis.set = AsyncMock(side_effect=lambda k, v, **kw: store.update({k: v}))
    redis.setex = AsyncMock(side_effect=lambda k, ttl, v: store.update({k: v}))
    redis.delete = AsyncMock(side_effect=lambda k: store.pop(k, None))
    redis.incr = AsyncMock(side_effect=lambda k: store.update({k: store.get(k, 0) + 1}) or store[k])
    redis.expire = AsyncMock(return_value=True)
    redis.ping = AsyncMock(return_value=True)
    return redis


# ── FastAPI test client ───────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def client(test_db, mock_redis):
    """Async HTTP test client with overridden DB and Redis dependencies."""
    from main import app
    from database.connection import get_db
    from cache.client import get_redis

    app.dependency_overrides[get_db] = lambda: test_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Auth helpers ──────────────────────────────────────────────────────────────
@pytest.fixture
def auth_headers():
    """Returns valid Authorization headers for a test user."""
    from core.security import create_access_token
    token = create_access_token("test-user-id-123")
    return {"Authorization": f"Bearer {token}"}


# ── Sample data ───────────────────────────────────────────────────────────────
@pytest.fixture
def sample_solve_request():
    return {"query": "What is 2 + 2?", "session_id": None, "show_steps": True}


@pytest.fixture
def sample_integral_request():
    return {"query": "Integrate x^2 with respect to x", "session_id": None, "show_steps": True}
