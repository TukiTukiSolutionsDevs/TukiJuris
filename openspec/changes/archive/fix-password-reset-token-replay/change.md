# fix-password-reset-token-replay

**Engram ref**: `tukijuris/password-reset-token-replay-bug` (obs #311)
**Status**: applied

## Proposal

Password-reset JWTs have no server-side tracking of consumption. The same 15-min
token can be submitted twice — allowing an attacker with one-shot token exposure to
reuse it within its TTL window.

## Spec

- `POST /api/auth/password-reset/confirm` MUST reject a token whose `iat` predates
  the user's last password change.
- On successful reset, stamp `users.password_updated_at = now()`.
- On every confirm attempt, if `user.password_updated_at` is set and
  `iat < password_updated_at.timestamp()` → 400 "Token invalido o ya utilizado".
- Invalidates ALL pre-reset tokens automatically (stronger than per-JTI denylist).

## Design — Option B (DB-first, no Redis)

Add `password_updated_at: DateTime(timezone=True), nullable=True` to `users`.

**Rejected**:
- Option A (Redis JTI denylist): requires adding `jti` claim + Redis uptime dependency.
- Option C (hybrid): over-engineered for this scope.

**Why B**: DB is source of truth; survives Redis down + server restart; matches
refresh-token pattern from sdd-init.

## Tasks

- [x] Add `password_updated_at` column to `app/models/user.py`
- [x] Migration `016_add_password_updated_at.py` (down_revision: `015_trials`)
- [x] `alembic upgrade head`
- [x] Guard in `confirm_password_reset` — compare `iat` vs `password_updated_at`
- [x] Stamp `password_updated_at` on successful reset
- [x] Remove `@pytest.mark.xfail` from `test_email_password_reset_confirm_flow`
- [x] All tests pass: 1231 passed, 11 xfailed, 0 failed
- [x] Single commit + archive
