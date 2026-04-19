# AGENTS.md — agente-derecho-api

Rules and context for AI agents working on this FastAPI backend.

---

## Stack

- **Python 3.12** — FastAPI + SQLAlchemy 2 (async) + Alembic
- **Database**: PostgreSQL (async via `asyncpg`)
- **Cache / rate-limit / denylist**: Redis (`redis.asyncio`)
- **Auth**: JWT (PyJWT) — access + refresh token pair (see below)
- **Tests**: pytest + pytest-asyncio; run with `pytest apps/api/tests/`
- **Migrations**: `alembic upgrade head` before every deploy

---

## Auth flow — Access + Refresh Tokens (PILAR 0.1)

Updated: 2026-04-16. The API issues a **short-lived access token (15 min)** and a
**long-lived refresh token (30 days)** on every login/register.

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/login` | No | Returns `{ access_token, refresh_token, token_type, expires_in }` |
| `POST` | `/api/auth/register` | No | Same response shape as login |
| `POST` | `/api/auth/refresh` | No (refresh token in body) | Rotate → new pair. Rate-limited 10/min per IP. |
| `POST` | `/api/auth/logout` | Bearer access token | Revoke one session (body: `{ refresh_token }`) |
| `POST` | `/api/auth/logout-all` | Bearer access token | Revoke all sessions → `{ revoked: N }` |
| `GET`  | `/api/auth/sessions` | Bearer access token | List active sessions for current user |

### JWT claims

**Access token** (`type: "access"`):
```json
{ "sub": "<user_id>", "type": "access", "exp": ..., "iat": ... }
```

**Refresh token** (`type: "refresh"`):
```json
{ "sub": "<user_id>", "type": "refresh", "jti": "<uuid>", "family_id": "<uuid>", "exp": ..., "iat": ... }
```

- `type` claim is **mandatory** — the backend rejects tokens where `type` doesn't match
  the expected value for the endpoint.
- `jti` is the unique token ID stored in the `refresh_tokens` table and the Redis denylist.
- `family_id` groups all rotated tokens that descended from the same original issue.

### Token rotation & reuse detection

- Every call to `/api/auth/refresh` **invalidates the old refresh token** and issues a new pair.
- If a **revoked** refresh token is presented, the entire `family_id` is revoked immediately
  and a `refresh.reuse_detected` WARNING is logged. The user is forced to re-login on all devices.
- The denylist lives in Redis (`tukijuris:denylist:<jti>`) with a TTL matching the token's
  remaining lifetime. Fail-open: if Redis is down, the DB is the fallback.

### Source of truth

`refresh_tokens` table (PostgreSQL) is the source of truth.
Redis denylist is a **post-commit write** — never the primary check.

```sql
-- Key columns
jti        TEXT NOT NULL UNIQUE   -- matches JWT jti claim
family_id  TEXT NOT NULL          -- for reuse detection
token_hash TEXT NOT NULL          -- SHA-256 hash of the raw token
revoked_at TIMESTAMPTZ            -- NULL = active
```

### Rate limiting

`/api/auth/refresh` has a dedicated Redis bucket: **10 requests / 60s per client IP**.
Exceeding the limit returns `429 Too Many Requests`. Fail-open if Redis unavailable.

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `REFRESH_TOKEN_TTL_DAYS` | `30` | Refresh token lifetime |
| `REDIS_KEY_PREFIX` | `tukijuris:` | Prefix for all Redis keys |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |

### Key files

| File | Role |
|------|------|
| `app/core/security.py` | JWT encode/decode, `type` + `jti` + `family_id` injection |
| `app/services/auth_service.py` | Login, register, refresh, logout, logout-all, sessions |
| `app/api/routes/auth.py` | FastAPI route handlers |
| `app/models/refresh_token.py` | SQLAlchemy `RefreshToken` model |
| `app/core/redis.py` | Denylist helpers, rate-limit helpers |
| `alembic/versions/*_add_refresh_tokens_table.py` | DB migration |
| `tests/unit/test_security.py` | JWT unit tests |
| `tests/unit/test_auth_service.py` | Service-layer unit tests |
| `tests/unit/test_auth_routes.py` | Route-level unit tests (TestClient) |

---

## Testing rules

- Unit tests: **no Docker required** — all external deps (DB, Redis) are mocked.
- Integration tests in `tests/integration/` require a live Postgres + Redis (use `docker-compose.yml`).
- Always run `pytest apps/api/tests/unit/` to verify before committing auth changes.
- 4 schema-level tests (`TestRefreshTokensSchema`) require Docker — known, non-blocking for local dev.

---

## Conventions

- Async everywhere: `async def` handlers, `AsyncSession`, `redis.asyncio`.
- No plaintext token material in logs — hash only.
- DB writes first, Redis writes post-commit (never the reverse).
- `alembic upgrade head` is mandatory before any deploy that touches models.
