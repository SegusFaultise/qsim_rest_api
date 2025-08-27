# tests/conftest.py

import pytest
from httpx import AsyncClient, ASGITransport  # <-- Import ASGITransport
from app.main import app

@pytest.fixture(scope="module")
async def test_client():
    """
    Creates a test client for making API requests.
    """
    # Use ASGITransport to allow httpx to interface with the FastAPI app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
