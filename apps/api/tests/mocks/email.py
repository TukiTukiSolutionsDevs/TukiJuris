"""Mock email provider for test isolation.

Replaces the real EmailProvider (Resend/SMTP/Console) with an in-memory
implementation that captures outbound email intent without touching any vendor.

Usage (as a pytest fixture):
    async def test_password_reset_sends_email(mock_email_provider, auth_client):
        res = await auth_client.post("/api/auth/password-reset", json={...})
        assert res.status_code == 200
        assert mock_email_provider.last_sent is not None
        assert "reset" in mock_email_provider.last_sent.subject.lower()

Usage (failing variant):
    async def test_email_failure_is_graceful(mock_email_provider_failing, auth_client):
        ...  # route should still return 200 on non-critical email paths
"""
from __future__ import annotations

from dataclasses import dataclass

import pytest
import pytest_asyncio

from app.services.email_service import EmailProvider, email_service


@dataclass
class SentEmail:
    """Captured outbound email payload."""

    to: str
    subject: str
    html: str


class MockEmailProvider(EmailProvider):
    """In-memory EmailProvider that captures sent messages instead of emitting them."""

    def __init__(self) -> None:
        self.sent: list[SentEmail] = []

    async def send(self, to: str, subject: str, html: str) -> bool:  # type: ignore[override]
        """Capture the email and return True (success)."""
        self.sent.append(SentEmail(to=to, subject=subject, html=html))
        return True

    @property
    def last_sent(self) -> SentEmail | None:
        """Return the most recently captured email, or None if none sent yet."""
        return self.sent[-1] if self.sent else None

    def reset(self) -> None:
        """Clear all captured emails — call between tests if reusing the instance."""
        self.sent.clear()


class FailingMockEmailProvider(EmailProvider):
    """EmailProvider that always raises — tests graceful degradation on non-critical paths."""

    async def send(self, to: str, subject: str, html: str) -> bool:  # type: ignore[override]
        raise RuntimeError("Mock email provider: send() intentionally failed for test")


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def mock_email_provider() -> MockEmailProvider:
    """Swap in the MockEmailProvider for the duration of one test.

    Replaces email_service.provider and restores the original on teardown.
    Does NOT use app.dependency_overrides because email_service is imported
    as a singleton, not via FastAPI Depends.
    """
    mock = MockEmailProvider()
    original_provider = email_service.provider
    email_service.provider = mock  # type: ignore[assignment]
    yield mock
    email_service.provider = original_provider  # type: ignore[assignment]


@pytest_asyncio.fixture
async def mock_email_provider_failing() -> FailingMockEmailProvider:
    """Swap in the FailingMockEmailProvider — for resilience / bounce tests."""
    mock = FailingMockEmailProvider()
    original_provider = email_service.provider
    email_service.provider = mock  # type: ignore[assignment]
    yield mock
    email_service.provider = original_provider  # type: ignore[assignment]
