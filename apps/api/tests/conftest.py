"""
Test configuration and shared fixtures for Agente Derecho API.

All tests are integration tests that exercise the real FastAPI app via
ASGITransport (no real HTTP server needed). Tests that touch the database
require PostgreSQL to be running — they will gracefully fail with a clear
error if the DB is not available, rather than silently passing.
"""

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


# ---------------------------------------------------------------------------
# Event loop — single loop for the entire session (avoids loop-reuse errors)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# HTTP clients
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated async HTTP client wired to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncClient:
    """
    Authenticated client.

    Registers a unique test user on each test run and sets the
    Authorization header so subsequent requests are authenticated.
    Falls back to login if the email already exists (409).
    """
    email = f"test-{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPassword123!"

    res = await client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    if res.status_code == 409:
        res = await client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )

    data = res.json()
    assert "access_token" in data, f"Auth setup failed: {res.status_code} {data}"
    client.headers["Authorization"] = f"Bearer {data['access_token']}"
    return client
