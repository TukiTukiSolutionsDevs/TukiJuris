# Tasks — backend-change-password-endpoint

## Batch A — Schema & route stub (no behavior yet)
- [x] **A1** Add `ChangePasswordRequest` Pydantic schema in the same module that holds other auth schemas (read explore reuse_map / current auth.py imports to find location). Fields per spec section 1.
- [x] **A2** Add empty `POST /api/auth/change-password` route stub in `apps/api/app/api/routes/auth.py`. Use `get_current_user` + `RateLimitGuard(RateLimitBucket.WRITE)` deps. Return 204 with no body. (CP-1, CP-2, CP-10)
- [x] **A3** Verify the new route registers cleanly: `cd apps/api && python -c "from app.main import app; print([r.path for r in app.routes if 'change-password' in r.path])"` should print the route. NO test runs yet.

## Batch B — Behavior implementation
- [x] **B1** Implement OAuth guard: if `current_user.hashed_password is None`, raise `HTTPException(400, detail={"code": "oauth_password_unsupported", "auth_provider": current_user.auth_provider})`. (CP-3)
- [x] **B2** Implement `verify_password` check: wrong current → `HTTPException(401, detail="invalid_credentials")`. (CP-4)
- [x] **B3** Implement `validate_password(new_password)` call: invalid → `HTTPException(422, detail=<validator message>)`. (CP-5)
- [x] **B4** Implement no-op guard: if `new_password == current_password` → `HTTPException(400, detail="new_password_same_as_current")`. (CP-6)
- [x] **B5** Hash + UPDATE: `current_user.hashed_password = hash_password(new_password)`; commit transaction. (CP-7, NFR-2)
- [x] **B6** Revoke ALL refresh-token sessions for the user (mirror logout_all at `auth.py:500-563`): call equivalent of `RefreshTokenService.revoke_all(user.id)` + denylist loop if applicable. (CP-8)
- [x] **B7** Emit audit event `auth.change_password` via `AuditService` with `{user_id, ts}` payload. NO password material. (CP-9, NFR-1)
- [x] **B8** Confirm side-effect order matches CP-11: verify → validate → no-op check → hash → DB update → revoke → audit → return.

## Batch C — Tests (test file: `apps/api/tests/test_auth_change_password.py`)
For each, follow the existing pattern in nearby `test_auth*.py` files (use `httpx.AsyncClient` + `ASGITransport`, factories from `conftest.py`).

- [x] **C1** T-01: no Authorization header → 401.
- [x] **C2** T-02: wrong current_password → 401, detail=invalid_credentials.
- [x] **C3** T-03: weak new_password (e.g. "abc") → 422 with validator message.
- [x] **C4** T-04: OAuth user (auth_provider="microsoft", hashed_password=None) → 400, code=oauth_password_unsupported.
- [x] **C5** T-05: new_password == current_password → 400, detail=new_password_same_as_current.
- [x] **C6** T-06: happy path → 204; subsequent `verify_password(new, refreshed_user.hashed_password)` is True.
- [x] **C7** T-07: user has 2 active refresh tokens; after change → both revoked in DB.
- [x] **C8** T-08: AuditService mocked → called once with `auth.change_password` event name and `{user_id}` (assert NO password fields).
- [x] **C9** T-09: exhaust WRITE rate-limit bucket → 429.

## Batch D — Validation
- [x] **D1** Run unit subset: `cd apps/api && python -m pytest tests/test_auth_change_password.py -v --tb=short` — all 9 tests green.
- [x] **D2** Run full auth file siblings to detect regressions: `cd apps/api && python -m pytest tests/ -k "auth" -v --tb=short`.
- [x] **D3** Lint check: `cd apps/api && ruff check app/api/routes/auth.py tests/test_auth_change_password.py` — no errors.
- [x] **D4** Format check: `cd apps/api && ruff format --check app/api/routes/auth.py tests/test_auth_change_password.py`.
- [x] **D5** Save apply-progress to engram before returning (topic_key: `sdd/backend-change-password-endpoint/apply-progress`) with checkbox status snapshot.

<!-- Remediation pass 2026-04-22: FIX-1 (CP-3 guard) + FIX-2 (single transaction) + FIX-3 (T-04 real DB user). See apply-progress + verify-report-2 in engram. -->
