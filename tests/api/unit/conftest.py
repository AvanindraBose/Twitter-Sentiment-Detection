from collections.abc import AsyncIterator
from unittest.mock import AsyncMock
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core import dependencies
from backend.main import app


class FakeScalarResult:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def setex(self, key: str, _ttl: int, value: int) -> None:
        self.store[key] = value

    async def incr(self, key: str) -> int:
        current = int(self.store.get(key, 0)) + 1
        self.store[key] = current
        return current

    async def ping(self) -> bool:
        return True


@pytest.fixture
def fake_redis() -> FakeRedis:
    return FakeRedis()


@pytest.fixture
def fake_db() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.rollback = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def unit_app(fake_db: AsyncMock, fake_redis: FakeRedis):
    async def override_get_db():
        yield fake_db

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[dependencies.get_db] = override_get_db
    app.dependency_overrides[dependencies.get_redis_client] = override_get_redis
    yield app
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(unit_app) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=unit_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def override_current_user():
    def _override(user_id: str = "test-user-id"):
        app.dependency_overrides[dependencies.get_current_user] = lambda: user_id
        return user_id

    yield _override
    app.dependency_overrides.pop(dependencies.get_current_user, None)


@pytest.fixture
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()
