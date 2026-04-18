# Changelog — agente-derecho (monorepo)

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) + [Semantic Versioning](https://semver.org/).
Dates in ISO 8601 (YYYY-MM-DD).

Per-package changelogs: [`apps/api/CHANGELOG.md`](apps/api/CHANGELOG.md)

---

## [Unreleased] — PILAR 0.1: Refresh Token Auth

> **Date**: 2026-04-16
> **Scope**: `apps/api` — Auth service

### ⚠️ BREAKING CHANGES

#### Auth flow migrated to access + refresh token pair

**Before**: `POST /api/auth/login` and `POST /api/auth/register` returned a single
long-lived JWT valid for **24 hours**. Clients stored it and reused it indefinitely.

**After**: Both endpoints now return a **short-lived access token (15 min)** paired with
a **long-lived refresh token (30 days)**.

**Client impact on deploy**:
- All existing sessions are **immediately invalidated** — clients will receive `401` on
  their next authenticated request.
- Clients must implement the refresh flow (see `apps/web/AGENTS.md`) or prompt re-login.
- There is no automatic migration path.

### Added

- `POST /api/auth/refresh` — exchange a refresh token for a new access + refresh pair
  (mandatory rotation). Rate-limited: **10 req/min per IP**.
- `POST /api/auth/logout` — revoke one refresh token (single-device logout).
- `POST /api/auth/logout-all` — revoke all refresh tokens for the current user.
- `GET /api/auth/sessions` — list active refresh token sessions for the current user.
- Rotation-on-use: old refresh token is invalidated on every successful refresh call.
- Reuse detection: presenting a revoked refresh token kills the **entire token family**
  and forces re-login on all devices.
- Redis denylist with TTL for fast rejection of revoked JTIs (no DB round-trip needed).
- New table `refresh_tokens` as the source of truth (DB first, Redis denylist post-commit).
- JWT claim `type` (`access` | `refresh`) is now mandatory in all tokens.
- JWT claims `jti` and `family_id` are now present in every refresh token.
- Rate limit bucket: `/api/auth/refresh` has its own 10/min-per-IP bucket (separate from
  the global rate limiter). Fail-open if Redis is unavailable.
- Observability counters: `refresh_rotations_total`, `refresh_reuse_detected_total`,
  `refresh_denylist_hits_total`.
- Structured log events: `refresh.issued`, `refresh.rotated`, `refresh.reuse_detected`,
  `refresh.revoked`. No token material is ever written to logs.

### Changed

- `POST /api/auth/login` — response schema: `{ access_token, refresh_token, token_type, expires_in }`
  (previously `{ access_token, token_type }`).
- `POST /api/auth/register` — same schema change as login.
- Access token TTL: **24h → 15min**.
- New env var `REFRESH_TOKEN_TTL_DAYS` (default `30`).
- New env var `REDIS_KEY_PREFIX` (default `tukijuris:`).

### Database migration required

```bash
alembic upgrade head
```

New table `refresh_tokens` with indexes on `jti`, `user_id`, `family_id`.
See `apps/api/alembic/versions/` for the migration file.

---

<!-- next release goes above this line -->
