import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import delete, text


TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
TEST_REDIS_URL = os.getenv("TEST_REDIS_URL")

if not TEST_DATABASE_URL or not TEST_REDIS_URL:
    pytest.skip(
        "Integration tests are skipped until TEST_DATABASE_URL and TEST_REDIS_URL are set.",
        allow_module_level=True,
    )

# Make the app use the dedicated test services before backend modules import settings.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = TEST_REDIS_URL

from backend.core.config import settings
from backend.core.database import AsyncSessionLocal, Base, engine
from backend.db.models.refresh_token import RefreshToken
from backend.db.models.users import User
from backend.loader.redis_loader import close_redis_client
from backend.main import app


@pytest_asyncio.fixture(scope="session")
async def integration_requirements():
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Integration tests skipped: test database is unavailable ({exc}).")

    redis_client = Redis.from_url(TEST_REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
    except Exception as exc:
        await redis_client.aclose()
        pytest.skip(f"Integration tests skipped: test redis is unavailable ({exc}).")
    await redis_client.aclose()

    return {
        "database_url": TEST_DATABASE_URL,
        "redis_url": TEST_REDIS_URL,
    }


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_integration_schema(integration_requirements):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def integration_async_client(
    integration_requirements,
) -> AsyncIterator[AsyncClient]:
    await close_redis_client()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    await close_redis_client()


@pytest_asyncio.fixture(scope="function")
async def integration_redis(
    integration_requirements,
) -> AsyncIterator[Redis]:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_integration_state(
    integration_requirements,
    prepare_integration_schema,
    integration_redis: Redis,
):
    await close_redis_client()

    async with AsyncSessionLocal() as session:
        await session.execute(delete(RefreshToken))
        await session.execute(delete(User))
        await session.commit()

    async for key in integration_redis.scan_iter(match="rate:*"):
        await integration_redis.delete(key)

    yield

    await close_redis_client()
    await engine.dispose()
