"""documents-search unit — _log_search_history fail-safe (FIX-04 regression guard).

Spec ID:
  documents-search.unit.008  test_search_history_db_write_failure_safe

Run:
  docker exec tukijuris-api-1 pytest tests/unit/test_search_logging.py -v
"""

from __future__ import annotations

import logging
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.routes.search import _log_search_history


class TestSearchHistoryFailSafe:
    """T-E-09 — FIX-04 fail-safe regression guard."""

    async def test_search_history_db_write_failure_safe(
        self,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """documents-search.unit.008 — DB error in _log_search_history is swallowed + WARNING logged.

        Contract:
        - A DB failure during history logging MUST NOT propagate to the caller.
        - The failure MUST be logged at WARNING level for observability.

        FIX-04: The except block previously used logger.debug, which silently hid
        failures. Changed to logger.warning so on-call engineers can detect DB issues
        through log-based alerts without search being degraded.
        """
        user_id = uuid.uuid4()

        # Build a broken session: enters fine, but commit raises.
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock(side_effect=RuntimeError("DB unavailable — test injection"))

        broken_cm = AsyncMock()
        broken_cm.__aenter__ = AsyncMock(return_value=mock_session)
        broken_cm.__aexit__ = AsyncMock(return_value=False)

        broken_factory = MagicMock(return_value=broken_cm)

        with (
            patch("app.core.database.async_session_factory", broken_factory),
            caplog.at_level(logging.WARNING, logger="app.api.routes.search"),
        ):
            # Must NOT raise — fail-safe contract
            await _log_search_history(
                db_factory=None,
                user_id=user_id,
                query="contrato de trabajo",
                filters=None,
                results_count=5,
            )

        warning_records = [
            r
            for r in caplog.records
            if r.levelno >= logging.WARNING and "search history" in r.message.lower()
        ]
        assert warning_records, (
            "Expected at least one WARNING log about history failure. "
            f"All records captured: {[(r.levelname, r.message) for r in caplog.records]}"
        )
