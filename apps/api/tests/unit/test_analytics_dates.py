"""Unit test — analytics date-range boundary contract (sub-batch D.2).

Spec ID: observability.unit.009  test_analytics_date_range_logic

FIX-05 investigation result: _date_range is correctly implemented as:
    start = now - timedelta(days=days)
    return start, now

No off-by-one exists. This test acts as a regression guard to lock the
inclusive/exclusive boundary contract in perpetuity.

Contract:
  - start: inclusive lower bound — exactly `days` days before `end`
  - end:   the current UTC moment (exclusive upper bound in queries via >=/:since)
  - window: timedelta(days=days), tolerance < 1 second

Run with:
  docker exec tukijuris-api-1 pytest tests/unit/test_analytics_dates.py -v --tb=short
"""

from datetime import UTC, datetime, timedelta


def test_analytics_date_range_logic() -> None:
    """_date_range(30): start = now − 30 days (inclusive), end = now.

    Spec: observability.unit.009 (FIX-05 regression guard — non-issue)

    Verifies three invariants:
      1. end falls within the measurement window [before_call, after_call]
      2. start is exactly (end − 30 days), tolerance < 1 second
      3. The window span is exactly 30 days, no off-by-one

    The 1-second tolerance absorbs any clock skew between the Python calls
    wrapping _date_range.
    """
    from app.api.routes.analytics import _date_range

    before = datetime.now(UTC)
    start, end = _date_range(30)
    after = datetime.now(UTC)

    # Invariant 1: end is a current UTC timestamp
    assert before <= end <= after, (
        f"end={end!r} is outside the measurement window [{before!r}, {after!r}]"
    )

    # Invariant 2: start is exactly (end − 30 days) — no off-by-one
    # Inclusive lower bound: queries use `created_at >= start`
    expected_start = end - timedelta(days=30)
    delta_seconds = abs((start - expected_start).total_seconds())
    assert delta_seconds < 1.0, (
        f"start is {delta_seconds:.3f}s away from (end − 30d). "
        f"start={start!r}, expected≈{expected_start!r}"
    )

    # Invariant 3: window span is exactly 30 days
    window_days = (end - start).total_seconds() / 86400
    assert abs(window_days - 30) < (1 / 86400), (  # tolerance: 1 second expressed in days
        f"Window span is {window_days:.6f} days, expected 30.000000. "
        "Off-by-one would manifest as 29 or 31 days."
    )
