import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis
from sqlalchemy import delete

from backend.core.config import settings
from backend.core.database import AsyncSessionLocal, engine
from backend.db.models.refresh_token import RefreshToken
from backend.db.models.users import User
from backend.loader.redis_loader import close_redis_client
from backend.main import app


@pytest.fixture(scope="session")
def integration_requirements():
    test_database_url = os.getenv("DATABASE_URL")
    test_redis_url = os.getenv("REDIS_URL")

    if not test_database_url or not test_redis_url:
        pytest.skip(
            "Integration tests need DATABASE_URL and REDIS_URL set to real test services."
        )

    return {
        "database_url": test_database_url,
        "redis_url": test_redis_url,
    }


@pytest_asyncio.fixture(scope="function") 
async def integration_async_client(integration_requirements) -> AsyncIterator[AsyncClient]:
    await close_redis_client()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    await close_redis_client()


@pytest_asyncio.fixture(scope="function") 
async def integration_redis(integration_requirements) -> AsyncIterator[Redis]:
    client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@pytest_asyncio.fixture(autouse=True)
async def cleanup_integration_state(
    integration_requirements,
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
