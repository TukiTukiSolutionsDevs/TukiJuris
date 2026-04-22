# Spec — backend-change-password-endpoint

## 1. API contract

**POST /api/auth/change-password**

Request (Pydantic v2):
```python
class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)
```

Response: `204 No Content` on success (empty body).

Auth: required (Bearer token).
Rate limit: `RateLimitGuard(RateLimitBucket.WRITE)`.

## 2. Behavioral requirements (SHALL statements)

- **CP-1**: SHALL require valid Bearer access token; missing/invalid → 401.
- **CP-2**: SHALL apply WRITE rate-limit guard; exhausted → 429.
- **CP-3**: When `current_user.hashed_password is None` (OAuth user) → 400 `{"detail": {"code": "oauth_password_unsupported", "auth_provider": "<value>"}}`.
- **CP-4**: When `verify_password(current_password, current_user.hashed_password)` is False → 401 `{"detail": "invalid_credentials"}`.
- **CP-5**: SHALL invoke `validate_password(new_password)`; on failure → 422 with validator message.
- **CP-6**: When `new_password == current_password` → 400 `{"detail": "new_password_same_as_current"}`.
- **CP-7**: On valid input, SHALL UPDATE `User.hashed_password = hash_password(new_password)` in single transaction.
- **CP-8**: SHALL revoke ALL refresh-token sessions for the user (mirror `logout_all` at auth.py:500-563). Simplest path: revoke all including current.
- **CP-9**: SHALL emit audit event `auth.change_password` with `{user_id, ts}`. NO password material.
- **CP-10**: On success → HTTP 204, empty body.
- **CP-11**: Side-effect order: verify → validate → no-op check → hash → DB update → revoke → audit → return.

## 3. Test matrix

| ID   | Case                              | Setup                                           | Expected                                       |
|------|-----------------------------------|-------------------------------------------------|------------------------------------------------|
| T-01 | No Authorization header           | post no headers                                 | 401                                            |
| T-02 | Wrong current_password            | known hash, wrong current                       | 401, detail=invalid_credentials                |
| T-03 | Weak new_password                 | strong current, weak new                        | 422 with validator message                     |
| T-04 | OAuth user                        | auth_provider=microsoft, hashed_password=None   | 400, code=oauth_password_unsupported           |
| T-05 | new == current                    | both equal & valid                              | 400, detail=new_password_same_as_current       |
| T-06 | Happy path                        | valid token + correct current + strong new      | 204; verify_password(new) → True              |
| T-07 | Other sessions revoked            | user has 2 active refresh tokens                | 204; both refresh tokens revoked in DB         |
| T-08 | Audit event emitted               | mock AuditService                               | called once with auth.change_password          |
| T-09 | Rate limit                        | exhaust WRITE bucket                            | 429                                            |

## 4. Non-functional requirements
- **NFR-1**: No plaintext or hashed password in logs/audit/response.
- **NFR-2**: Single DB transaction (existing `db: AsyncSession` dep).
- **NFR-3**: Reuse `verify_password`, `hash_password` from `app/core/security.py` — no new crypto.
- **NFR-4**: No new env var or config required.

## 5. Out of scope
- Frontend integration (Sprint 1).
- Self-revocation only (deferred).
- Password history.
- 2FA prompt.

## 6. References
- Proposal: `openspec/changes/backend-change-password-endpoint/proposal.md` (engram #345).
- Reuse map: engram #344 (explore).
- Pattern: `apps/api/app/api/routes/auth.py:500-563` (logout_all).
- Crypto: `apps/api/app/core/security.py:33,42`.
- Validator: `apps/api/app/core/validators.py:14`.
- Auth dep: `apps/api/app/api/deps.py:47`.
- Rate limit: `apps/api/app/api/deps.py:350`.