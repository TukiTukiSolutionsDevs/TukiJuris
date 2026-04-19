# Changelog — agente-derecho-api

All notable changes to this project will be documented in this file.
Format: [Semantic Versioning](https://semver.org/). Dates in ISO 8601 (YYYY-MM-DD).

---

## [Unreleased] — PILAR 0.1: Refresh Token Auth

### ⚠️ BREAKING CHANGES

#### Auth flow migrated to access + refresh token pair

**Before**: `POST /api/auth/login` returned a single long-lived JWT (`access_token`).
Clients stored this token and used it indefinitely.

**After**: `POST /api/auth/login` and `POST /api/auth/register` both return an
`access_token` (short-lived, 15 min) **and** a `refresh_token` (long-lived, 30 days).

**Client impact**:
- Existing clients that store a single token and never refresh will receive `401`
  after 15 minutes. They must implement the refresh flow or prompt re-login.
- There is no automatic migration — all existing sessions are invalidated on deploy.
- Clients must treat a `401` on a protected endpoint as a signal to refresh or
  re-authenticate (see frontend guidance below).

---

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/refresh` | Exchange a refresh token for a new access + refresh pair (rotation). Rate-limited: 10 req/min per IP. |
| `POST` | `/api/auth/logout` | Revoke a single refresh token (single-device logout). Requires Bearer access token. |
| `POST` | `/api/auth/logout-all` | Revoke all refresh tokens for the current user (all-device logout). |
| `GET`  | `/api/auth/sessions` | List active refresh token sessions for the current user. |

---

### Changed Endpoints

| Endpoint | Change |
|----------|--------|
| `POST /api/auth/login` | Now returns `{ access_token, refresh_token, token_type, expires_in }` instead of `{ access_token, token_type }`. |
| `POST /api/auth/register` | Same schema change as login — returns token pair. |

---

### Security

- **Token rotation**: every refresh call invalidates the old refresh token and issues a new one.
- **Reuse detection**: presenting a revoked refresh token kills the entire token family and forces re-login on all devices.
- **Token denylist**: revoked JTIs are cached in Redis for fast rejection without DB round-trips.
- **Refresh-specific rate limit**: `/api/auth/refresh` is rate-limited to 10 req/min per IP (separate bucket from the global rate limiter). Fail-open if Redis is unavailable.

---

### Observability

New in-memory counters (accessible via internal metrics):
- `refresh_rotations_total` — successful token rotations.
- `refresh_reuse_detected_total` — reuse-detection events (security signal).
- `refresh_denylist_hits_total` — JTIs added to the denylist.

Structured log events emitted by the service:
- `refresh.issued` (INFO) — new token pair created.
- `refresh.rotated` (INFO) — token rotated successfully.
- `refresh.reuse_detected` (WARNING) — revoked token presented; family killed.
- `refresh.revoked` (INFO) — token revoked (logout / logout-all).

**No token material (plaintext or hash) is ever written to logs.**

---

### Database

New table: `refresh_tokens`

```sql
CREATE TABLE refresh_tokens (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    jti        TEXT NOT NULL UNIQUE,
    user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    family_id  TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_refresh_tokens_jti      ON refresh_tokens (jti);
CREATE INDEX ix_refresh_tokens_user_id  ON refresh_tokens (user_id);
CREATE INDEX ix_refresh_tokens_family   ON refresh_tokens (family_id);
```

Migration: `alembic/versions/XXX_add_refresh_tokens_table.py`
Run `alembic upgrade head` before deploying.

---

### Configuration

New environment variables (all optional — defaults shown):

| Variable | Default | Description |
|----------|---------|-------------|
| `REFRESH_TOKEN_TTL_DAYS` | `30` | Refresh token lifetime in days. |
| `REDIS_KEY_PREFIX` | `tukijuris:` | Prefix for all Redis keys (denylist + rate limiter). |
