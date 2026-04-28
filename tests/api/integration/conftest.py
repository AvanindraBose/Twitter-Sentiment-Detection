import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import delete, text
# Point the app at dedicated test services before backend modules import settings.
from backend.core.config import settings
from backend.core.database import AsyncSessionLocal, Base, engine
from backend.db.models.refresh_token import RefreshToken
from backend.db.models.users import User
from backend.loader.redis_loader import close_redis_client
from backend.main import app

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL")

if not TEST_DATABASE_URL or not TEST_REDIS_URL:
    pytest.skip(
        "Integration tests are skipped until TEST_DATABASE_URL and TEST_REDIS_URL are set.",
        allow_module_level=True,
    )

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL

@pytest.fixture(scope="session")
def integration_requirements():
    return {
        "database_url": TEST_DATABASE_URL,
        "redis_url": TEST_REDIS_URL,
    }


@pytest_asyncio.fixture(scope="function")
async def integration_redis(
    integration_requirements,
) -> AsyncIterator[Redis]:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await client.ping()
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(autouse=True, scope="function")
async def integration_state(
    integration_requirements,
    integration_redis: Redis,
):
    await close_redis_client()
    await engine.dispose()

    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(User))
        await session.commit()

    async for key in integration_redis.scan_iter(match="rate:*"):
        await integration_redis.delete(key)

    yield

    await close_redis_client()
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def integration_async_client(
    integration_state,
) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
