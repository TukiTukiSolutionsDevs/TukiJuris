# SDD Proposal: backend-change-password-endpoint

## Why
- Frontend gap C1 from `frontend-coverage-audit`: `apps/web/src/app/configuracion/page.tsx:474` calls `POST /api/auth/change-password`. Endpoint missing → silent prod failure for all users trying to change their password from the settings page.
- Owner decision: ship the backend endpoint (D1 default).

## What changes
- New route `POST /api/auth/change-password` in `apps/api/app/api/routes/auth.py`.
- New Pydantic request schema `ChangePasswordRequest { current_password: str, new_password: str }` colocated with other auth schemas.
- New test file `apps/api/tests/test_auth_change_password.py` (integration test based on existing `test_auth.py` pattern).
- NO new service file (auth lives in route per explore finding).
- NO migration (no model changes — `hashed_password` column already exists on `User`).
- NO new dependency.

## Endpoint contract
- **Path**: `/api/auth/change-password`
- **Method**: POST
- **Auth**: required (`get_current_user` dep)
- **Rate limit**: `RateLimitGuard(RateLimitBucket.WRITE)` dep
- **Request body** (JSON):
  ```json
  { "current_password": "string (1..128)", "new_password": "string (8..128)" }
  ```
- **Success**: `204 No Content`
- **Errors**:
  - `401 Unauthorized` — no/invalid token (raised by `get_current_user`)
  - `401 Unauthorized` `{ "detail": "invalid_credentials" }` — wrong `current_password` (mirrors login pattern)
  - `400 Bad Request` `{ "detail": { "code": "oauth_password_unsupported", "auth_provider": "..." } }` — OAuth user without local password
  - `422 Unprocessable Entity` — `new_password` fails `validate_password()`
  - `429 Too Many Requests` — rate limit hit (raised by `RateLimitGuard(WRITE)`)
  - `400 Bad Request` `{ "detail": "new_password_same_as_current" }` — extra guard: reject no-op

## Side effects (in order, atomic)
1. Verify `current_password` against `current_user.hashed_password` via `verify_password()`.
2. Validate `new_password` via `validate_password()`.
3. Reject if `new_password == current_password` (avoid no-op).
4. Hash new password via `hash_password()`.
5. UPDATE `user.hashed_password` in DB.
6. **Revoke all OTHER refresh-token sessions**: call equivalent of `revoke_all(user.id)` BUT exclude current session's `jti` if available. If excluding current session is non-trivial, revoke ALL sessions including current — frontend will refresh-flow back in. (Trade-off: simpler backend implementation vs forced relogin).
7. Emit `auth.change_password` audit event.
8. Return 204.

## Migration
None.

## Out of scope
- Frontend wiring (handled in Sprint 1 `frontend-fix-critical-bugs`).
- Password-reset endpoint.
- Self-revocation of current session (proposer defaults to the simplest approach, which may mean revoking all sessions including current, relying on frontend refresh-flow to recover).

## Risks
- **Race**: concurrent password change could leave inconsistent state. Mitigation: SQLAlchemy session is per-request, single transaction. Acceptable.
- **Lock-out**: if revoking current session, user must log in again immediately after change. UX acceptable (better-than-bug status quo).
- **Audit data leak**: NEVER log plaintext or hashed values. Only `user_id` + event name + timestamp.

## Acceptance criteria
- [ ] Authenticated user with valid `current_password` and strong `new_password` → 204; subsequent login with `new_password` works; subsequent login with `current_password` fails.
- [ ] Wrong `current_password` → 401 `invalid_credentials`.
- [ ] Weak `new_password` → 422 with validators message.
- [ ] OAuth user → 400 `oauth_password_unsupported`.
- [ ] No token → 401.
- [ ] Other refresh tokens for the user become invalid post-change.
- [ ] Rate limit returns 429 after threshold.
