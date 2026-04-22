# fix-refresh-family-kill

## Proposal

The `rotate()` method in `refresh_token_service.py` has a denylist fast-path (lines 200–208)
that raises `RevokedRefreshToken` before the DB branch executes. This means a reused gen-0
token hits the fast-path and returns 401 without ever reaching the `revoked_at is not None`
family-kill branch (lines 214–229), leaving gen-1 valid. The entire family is never killed.
This violates AGENTS.md auth-flow-pilar-0.1 §"Token rotation & reuse detection".
Root cause documented in engram topic `tukijuris/refresh-family-kill-bug` (corrected 2026-04-22).

## Spec

Acceptance criteria:
- `test_reuse_detection_kills_entire_family` passes (no longer xfail).
- `test_rotated_token_is_rejected`, `test_valid_rotation_chain_succeeds`, and
  `test_access_token_type_rejected_at_refresh_endpoint` continue to pass.
- Full regression: **1230 passed / 12 xfailed / 0 failed** (NET: +1 pass, -1 xfail vs baseline 1229/13).

## Design

**Option A (chosen)**: Demote the denylist fast-path from verdict to observability hint.
Keep the `contains()` call but, on hit, record the metric + log and continue to the DB branch.
The DB branch is the sole source of truth for reuse detection and family kill.

**Option B (rejected)**: Duplicate the family-kill logic inside the fast-path.
Rejected because it creates two sources of truth for the same invariant — future divergence
is guaranteed, and the existing DB branch already handles the case correctly.

## Tasks

- **T-01** — Remove `raise RevokedRefreshToken()` from the fast-path in `rotate()`
  (lines 200–208 of `refresh_token_service.py`). Keep `contains()` as observability:
  on hit, call `refresh_metrics.record_denylist_hit()` + `logger.info(...)`, then continue.
- **T-02** — Remove the `@pytest.mark.xfail(strict=True, ...)` decorator from
  `test_reuse_detection_kills_entire_family` in `test_auth_refresh_reuse.py` (lines 84–92).
  Leave the test body unchanged.
- **T-03** — Run targeted suite (`test_auth_refresh_reuse.py`) and full regression
  (`tests/`). Confirm 1230 passed / 12 xfailed / 0 failed.
