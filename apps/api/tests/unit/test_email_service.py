"""Unit tests — email service resilience (sub-batch D.4b).

Spec IDs:
  notifications.unit.011  test_email_send_mock_provider_happy_path
  notifications.unit.012  test_email_bounce_handling_fallback

Uses fresh EmailService() instances (not the module-level singleton) to avoid
cross-test pollution. Monkeypatches settings.email_enabled=True so _send()
reaches the provider instead of short-circuiting to the console-disabled path.

Run:
  docker exec tukijuris-api-1 pytest tests/unit/test_email_service.py -v --tb=short
"""
from __future__ import annotations

import logging

from app.config import settings
from app.services.email_service import EmailService
from tests.mocks.email import FailingMockEmailProvider, MockEmailProvider


# ---------------------------------------------------------------------------
# notifications.unit.011 — happy path
# ---------------------------------------------------------------------------


async def test_email_send_mock_provider_happy_path(monkeypatch) -> None:
    """Spec: notifications.unit.011

    EmailService with MockEmailProvider: send_password_reset() returns True,
    captures the outbound email, and embeds the reset URL in the HTML body.
    """
    monkeypatch.setattr(settings, "email_enabled", True)

    mock = MockEmailProvider()
    svc = EmailService()
    svc._provider = mock

    result = await svc.send_password_reset(
        to="user@test.com", reset_url="https://app.test/reset?token=abc123"
    )

    assert result is True
    assert mock.last_sent is not None, "MockEmailProvider captured no email"
    assert mock.last_sent.to == "user@test.com"
    assert "https://app.test/reset?token=abc123" in mock.last_sent.html
    assert "contrasena" in mock.last_sent.subject.lower()


# ---------------------------------------------------------------------------
# notifications.unit.012 — bounce / provider failure
# ---------------------------------------------------------------------------


async def test_email_bounce_handling_fallback(monkeypatch, caplog) -> None:
    """Spec: notifications.unit.012

    FailingMockEmailProvider raises RuntimeError. EmailService._send() must
    catch it, emit a WARNING log, and return False — no exception propagates.
    """
    monkeypatch.setattr(settings, "email_enabled", True)

    svc = EmailService()
    svc._provider = FailingMockEmailProvider()

    with caplog.at_level(logging.WARNING, logger="app.services.email_service"):
        result = await svc.send_password_reset(
            to="bounce@test.com", reset_url="https://app.test/reset?token=xyz"
        )

    assert result is False, "Expected False when provider raises, got True"
    assert any("Failed to send" in r.message for r in caplog.records), (
        f"Expected WARNING 'Failed to send'; got: {[r.message for r in caplog.records]}"
    )
