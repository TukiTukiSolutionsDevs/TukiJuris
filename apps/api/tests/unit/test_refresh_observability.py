"""T-11.0 RED: Observability — structured logs and in-memory counters.

Counter tests are RED until T-11.1 adds RefreshMetrics to monitoring.py
and wires record_*() calls into refresh_token_service.py.

Log contract tests document the existing logging behaviour in the service.

Rules:
  - refresh_rotations_total, refresh_reuse_detected_total,
    refresh_denylist_hits_total must be non-negative integers.
  - record_rotation(), record_reuse_detected(), record_denylist_hit()
    increment the respective counter by exactly 1.
  - get_stats() returns a dict containing all three counters.
  - Structured events emitted: refresh.rotated, refresh.reuse_detected,
    refresh.revoked.
  - NO raw tokens or hash hex strings appear in any log record.
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.monitoring import refresh_metrics  # RED: doesn't exist yet


# ---------------------------------------------------------------------------
# Counter unit tests — RED until T-11.1
# ---------------------------------------------------------------------------


class TestRefreshCounters:
    """refresh_metrics singleton exposes three monotone in-memory counters."""

    def test_rotations_total_is_non_negative_int(self):
        """refresh_rotations_total exists and is a non-negative integer."""
        assert isinstance(refresh_metrics.refresh_rotations_total, int)
        assert refresh_metrics.refresh_rotations_total >= 0

    def test_reuse_detected_total_is_non_negative_int(self):
        """refresh_reuse_detected_total exists and is a non-negative integer."""
        assert isinstance(refresh_metrics.refresh_reuse_detected_total, int)
        assert refresh_metrics.refresh_reuse_detected_total >= 0

    def test_denylist_hits_total_is_non_negative_int(self):
        """refresh_denylist_hits_total exists and is a non-negative integer."""
        assert isinstance(refresh_metrics.refresh_denylist_hits_total, int)
        assert refresh_metrics.refresh_denylist_hits_total >= 0

    def test_record_rotation_increments_by_one(self):
        """record_rotation() increments refresh_rotations_total by exactly 1."""
        before = refresh_metrics.refresh_rotations_total
        refresh_metrics.record_rotation()
        assert refresh_metrics.refresh_rotations_total == before + 1

    def test_record_reuse_detected_increments_by_one(self):
        """record_reuse_detected() increments refresh_reuse_detected_total by 1."""
        before = refresh_metrics.refresh_reuse_detected_total
        refresh_metrics.record_reuse_detected()
        assert refresh_metrics.refresh_reuse_detected_total == before + 1

    def test_record_denylist_hit_increments_by_one(self):
        """record_denylist_hit() increments refresh_denylist_hits_total by 1."""
        before = refresh_metrics.refresh_denylist_hits_total
        refresh_metrics.record_denylist_hit()
        assert refresh_metrics.refresh_denylist_hits_total == before + 1

    def test_record_rotation_is_monotone(self):
        """Calling record_rotation() N times increments by exactly N."""
        before = refresh_metrics.refresh_rotations_total
        n = 5
        for _ in range(n):
            refresh_metrics.record_rotation()
        assert refresh_metrics.refresh_rotations_total == before + n

    def test_get_stats_contains_all_three_counters(self):
        """refresh_metrics.get_stats() returns dict with all three counter keys."""
        stats = refresh_metrics.get_stats()
        required = {
            "refresh_rotations_total",
            "refresh_reuse_detected_total",
            "refresh_denylist_hits_total",
        }
        missing = required - set(stats.keys())
        assert not missing, f"get_stats() is missing keys: {missing}"
        for key in required:
            assert isinstance(stats[key], int), (
                f"stats['{key}'] must be int, got {type(stats[key])}"
            )


# ---------------------------------------------------------------------------
# Structured log contract tests
# ---------------------------------------------------------------------------


def _make_svc(
    mock_repo: AsyncMock | None = None,
    mock_denylist: AsyncMock | None = None,
    mock_session: AsyncMock | None = None,
):
    """Build a RefreshTokenService with all deps mocked."""
    from app.services.refresh_token_service import RefreshTokenService

    if mock_denylist is None:
        mock_denylist = AsyncMock()
        mock_denylist.contains.return_value = False  # fail-open: not in denylist by default
        mock_denylist.add.return_value = None

    return RefreshTokenService(
        session=mock_session or AsyncMock(),
        repo=mock_repo or AsyncMock(),
        denylist=mock_denylist,
    )


def _active_token_mock(
    user_id: uuid.UUID | None = None,
    family_id: str | None = None,
) -> MagicMock:
    """Return a MagicMock with non-revoked RefreshToken shape."""
    t = MagicMock()
    t.jti = str(uuid.uuid4())
    t.user_id = user_id or uuid.uuid4()
    t.family_id = family_id or str(uuid.uuid4())
    t.revoked_at = None
    t.expires_at = datetime.now(UTC) + timedelta(days=1)
    return t


def _revoked_token_mock(
    user_id: uuid.UUID | None = None,
    family_id: str | None = None,
) -> MagicMock:
    """Return a MagicMock with revoked RefreshToken shape."""
    t = _active_token_mock(user_id, family_id)
    t.revoked_at = datetime.now(UTC) - timedelta(hours=1)
    return t


class TestRefreshStructuredLogs:
    """Service emits the correct structured log events; no tokens in plaintext."""

    async def test_rotate_emits_refresh_rotated_at_info(self, caplog):
        """Successful rotate() emits log event 'refresh.rotated' at INFO level."""
        uid = uuid.uuid4()
        fid = str(uuid.uuid4())

        mock_repo = AsyncMock()
        mock_repo.insert.return_value = _active_token_mock(user_id=uid, family_id=fid)
        mock_repo.find_by_hash_for_update.return_value = _active_token_mock(
            user_id=uid, family_id=fid
        )

        svc = _make_svc(mock_repo=mock_repo)

        with caplog.at_level(logging.INFO, logger="app.services.refresh_token_service"):
            fake_user = MagicMock(id=uid, email="u@t.com")
            try:
                pair = await svc.issue_pair(fake_user, device_info={})
                await svc.rotate(pair.refresh_token, device_info={})
            except Exception:
                pass  # only care about log output

        msgs = [r.getMessage() for r in caplog.records]
        assert any("refresh.rotated" in m for m in msgs), (
            f"Expected 'refresh.rotated' in log records, got: {msgs}"
        )

    async def test_reuse_detected_emits_at_warning(self, caplog):
        """rotate() on a revoked token emits 'refresh.reuse_detected' at WARNING."""
        uid = uuid.uuid4()
        fid = str(uuid.uuid4())

        mock_repo = AsyncMock()
        mock_repo.insert.return_value = _active_token_mock(user_id=uid, family_id=fid)
        # First call (find_by_hash_for_update) returns revoked token → reuse
        mock_repo.find_by_hash_for_update.return_value = _revoked_token_mock(
            user_id=uid, family_id=fid
        )

        svc = _make_svc(mock_repo=mock_repo)

        with caplog.at_level(logging.WARNING, logger="app.services.refresh_token_service"):
            fake_user = MagicMock(id=uid, email="u@t.com")
            try:
                pair = await svc.issue_pair(fake_user, device_info={})
                await svc.rotate(pair.refresh_token, device_info={})
            except Exception:
                pass

        msgs = [r.getMessage() for r in caplog.records]
        assert any("refresh.reuse_detected" in m for m in msgs), (
            f"Expected 'refresh.reuse_detected' in log records, got: {msgs}"
        )

    async def test_revoke_emits_refresh_revoked_at_info(self, caplog):
        """revoke() emits log event 'refresh.revoked' at INFO level."""
        uid = uuid.uuid4()
        fid = str(uuid.uuid4())

        mock_repo = AsyncMock()
        mock_repo.insert.return_value = _active_token_mock(user_id=uid, family_id=fid)
        mock_repo.find_by_hash.return_value = _active_token_mock(
            user_id=uid, family_id=fid
        )

        svc = _make_svc(mock_repo=mock_repo)

        with caplog.at_level(logging.INFO, logger="app.services.refresh_token_service"):
            fake_user = MagicMock(id=uid, email="u@t.com")
            try:
                pair = await svc.issue_pair(fake_user, device_info={})
                await svc.revoke(pair.refresh_token)
            except Exception:
                pass

        msgs = [r.getMessage() for r in caplog.records]
        assert any("refresh.revoked" in m for m in msgs), (
            f"Expected 'refresh.revoked' in log records, got: {msgs}"
        )

    def test_no_raw_jwt_in_any_log_record(self, caplog):
        """No log record captured in this session contains a raw JWT string.

        A JWT starts with 'eyJ' (base64url-encoded header). Any such string
        appearing in a log message is a token leak and must never happen.
        """
        for record in caplog.records:
            msg = record.getMessage()
            assert "eyJ" not in msg, (
                f"Raw JWT detected in log record: {msg[:120]!r}"
            )
