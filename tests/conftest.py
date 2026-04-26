# tests/conftest.py — truly global
import pytest
from dotenv import load_dotenv

@pytest.fixture(scope="session", autouse=True)
def load_env():
    load_dotenv()

# For Fast API Async endpoints
# @pytest.fixture(scope="session")
# def event_loop():
#     # shared async event loop for all tests
#     import asyncio
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()