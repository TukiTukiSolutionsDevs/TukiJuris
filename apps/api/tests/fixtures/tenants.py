"""Cross-tenant isolation harness.

Provides `two_orgs_two_users` — an async context manager that creates two
independent org+user pairs, each with their own authenticated AsyncClient.

Usage:
    async with two_orgs_two_users() as pair:
        res = await pair.client_b.get(f"/api/resource/{resource_owned_by_a}")
        assert res.status_code == 404  # isolation

As a pytest fixture:
    @pytest_asyncio.fixture
    async def tenant_pair():
        async with two_orgs_two_users() as pair:
            yield pair
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator

from httpx import ASGITransport, AsyncClient

from app.main import app


@dataclass
class TenantPair:
    """Two independent org+user pairs with pre-authenticated clients."""

    org_a: dict       # {org_id, name}
    owner_a: dict     # {email, password, access_token, refresh_token}
    token_a: str      # Bearer-ready access token for owner_a
    org_b: dict
    owner_b: dict
    token_b: str
    client_a: AsyncClient  # Authorization header set to token_a
    client_b: AsyncClient  # Authorization header set to token_b


@asynccontextmanager
async def two_orgs_two_users(
    *,
    plan_a: str = "pro",  # noqa: ARG001
    plan_b: str = "pro",  # noqa: ARG001
) -> AsyncGenerator[TenantPair, None]:
    """Create two fully isolated org+user pairs.

    Each pair has its own AsyncClient instance so Authorization headers
    cannot cross-pollinate. Clients are properly closed on context exit.

    plan_a/plan_b are accepted for call-site symmetry; actual plan
    assignment is done by the subscription service and is outside this
    fixture's scope.
    """
    from tests.factories.user import make_user
    from tests.factories.org import make_org

    # Step 1: Register both users via a shared anonymous client
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as anon:
        user_a = await make_user(anon)
        user_b = await make_user(anon)

    # Step 2: Create orgs with authenticated clients — open two persistent clients
    async with (
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {user_a['access_token']}"},
        ) as client_a,
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            headers={"Authorization": f"Bearer {user_b['access_token']}"},
        ) as client_b,
    ):
        org_a = await make_org(client_a)
        org_b = await make_org(client_b)

        yield TenantPair(
            org_a=org_a,
            owner_a=user_a,
            token_a=user_a["access_token"],
            org_b=org_b,
            owner_b=user_b,
            token_b=user_b["access_token"],
            client_a=client_a,
            client_b=client_b,
        )
