# Design: fix-rate-limit-architecture

**Project**: tukijuris
**Spec**: `sdd/fix-rate-limit-architecture/spec.md`
**Proposal**: `sdd/fix-rate-limit-architecture/proposal`
**Mode**: Standard (`strict_tdd: false` per `sdd-init/tukijuris`)

---

## 0. Reading the room (real code, not assumptions)

Before designing, I verified the actual current state of the affected files:

| File | Current state |
|------|---------------|
| `app/core/rate_limiter.py` | Sliding-window `RateLimiter` singleton with `check_rate_limit(key, max_requests, window_seconds)`. `RATE_LIMIT_TIERS = {"anonymous": (10, None), "free": (30, 100), "base": (120, 2000), "enterprise": (600, None)}` — tuple is `(per_minute, per_day)`. Already has `refresh_rate_limit` for `/auth/refresh` (10/min/IP). |
| `app/api/middleware.py` | `RateLimitMiddleware` runs both an authenticated `token:{sha256-hash}` bucket (60/min) AND an anonymous `ip:{ip}` bucket (10/min). Adds `X-RateLimit-*` headers to every response. |
| `app/api/deps.py` | Generic `check_rate_limit` dep keyed on `user:{user_id}` flat 60/min — NOT plan-aware, despite `_PLAN_LIMITS` constant. Comment explicitly says "BYOK: TukiJuris does not tier features by plan". This belief must be overturned by this change because the proposal/spec explicitly require plan-tiered WRITE limits. |
| `app/api/routes/auth.py` | `_set_session_cookies(response, refresh_token)` (line 127) and `_clear_session_cookies(response)` (line 155) already exist from `fix-auth-tokens`. Both call `response.set_cookie` / `response.delete_cookie` with explicit kwargs (`httponly`, `secure`, `samesite`, `path`). No `domain` kwarg today. |
| `app/config.py` | `app_debug: bool = True`, `cors_origins: list[str]` at line 55. NO `cookie_domain` setting yet. |
| `app/api/routes/` | 27 router files — full inventory in §6. |

**Reusing what works**: the existing `rate_limiter.check_rate_limit(key, max_requests, window_seconds)` already implements sliding-window semantics, fail-open framing, and per-key Redis TTL. The design REUSES this helper rather than introducing a competing INCR/TTL primitive (the snippet in the design brief was illustrative — building a parallel implementation would create two divergent rate-limiting code paths).

---

## 1. File-by-file changes

### 1.1 `apps/api/app/config.py` — add `cookie_domain`

```py
class Settings(BaseSettings):
    ...
    # Cross-domain cookie support. Empty string ("") = no Domain attribute → cookie
    # is host-scoped (correct for localhost dev and same-origin prod).
    # Set to ".tukijuris.net.pe" in production when api/web run on separate
    # subdomains so the browser sends cookies on cross-subdomain fetches.
    cookie_domain: str = ""
```

Also add a startup log line in `main.py` lifespan (or wherever settings are echoed):

```py
logger.info("Auth cookie domain: %r (empty = host-scoped)", settings.cookie_domain)
```

### 1.2 `apps/api/app/api/routes/auth.py` — domain injection on both helpers

Patch `_set_session_cookies`:

```py
def _set_session_cookies(response: Response, refresh_token: str) -> None:
    _secure = not settings.app_debug
    _domain = {"domain": settings.cookie_domain} if settings.cookie_domain else {}
    response.set_cookie(
        key=_REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=_secure,
        samesite="lax",
        path=_REFRESH_COOKIE_PATH,
        **_domain,
    )
    response.set_cookie(
        key=_TK_SESSION_COOKIE_NAME,
        value="1",
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        secure=_secure,
        samesite="lax",
        path=_TK_SESSION_COOKIE_PATH,
        **_domain,
    )
```

Same `**_domain` injection on both `response.delete_cookie` calls in `_clear_session_cookies`. Starlette's `delete_cookie` accepts `domain` as a kwarg — verified.

**Why kwarg-spread instead of `domain=settings.cookie_domain or None`**: Starlette stringifies `None` into the `Domain=None` literal in some versions. The kwarg-spread guarantees the `Domain` attribute is fully absent when unset, which is the only reliable way to get a host-only cookie on localhost.

### 1.3 `.env.example` and `.env.production.example`

```
# .env.example
COOKIE_DOMAIN=

# .env.production.example
COOKIE_DOMAIN=.tukijuris.net.pe
```

The leading dot in production is mandatory — it tells the browser the cookie is valid for `tukijuris.net.pe` and ALL subdomains (`api.tukijuris.net.pe`, `www.tukijuris.net.pe`, etc.).

### 1.4 `apps/api/app/core/rate_limiter.py` — `RateLimitBucket` enum + tier semantics

Add enum and a tiny lookup helper at the bottom of the existing module:

```py
from enum import Enum

class RateLimitBucket(str, Enum):
    READ = "read"
    WRITE = "write"

# Flat READ ceiling — applies to all authenticated users regardless of plan.
# 10 req/s sustained is well above any normal navigation pattern.
READ_LIMIT_PER_MIN = 600

def get_write_limit_for_plan(plan: str) -> int:
    """Resolve the per-minute WRITE limit for a user's plan.

    Falls back to the "free" tier if the plan key is unknown — defensive
    against (a) DB rows pre-dating plan-model-refactor and (b) typos.
    """
    tier = RATE_LIMIT_TIERS.get(plan) or RATE_LIMIT_TIERS["free"]
    return tier[0]  # (per_minute, per_day) — we only enforce per-minute here
```

`RATE_LIMIT_TIERS` keys remain `{"anonymous", "free", "base", "enterprise"}` for now. The lookup helper makes this change FORWARD-COMPATIBLE with `plan-model-refactor` (which renames `base→pro`, `enterprise→studio`) — when that change lands, only the dict literal needs swapping; no call sites change.

If `plan-model-refactor` HAS landed at apply time, the implementer updates the dict to `{"anonymous": (10, None), "free": (30, 100), "pro": (120, 2000), "studio": (600, None)}` AS A SINGLE-LINE EDIT. Both versions return correct results through `get_write_limit_for_plan`.

### 1.5 `apps/api/app/api/deps.py` — `RateLimitGuard` factory

DELETE the existing `check_rate_limit` function (lines 155-194) and the `_PLAN_LIMITS` constant block (lines 27-38). REPLACE with:

```py
from typing import Callable, Awaitable
from app.core.rate_limiter import (
    rate_limiter,
    RateLimitBucket,
    READ_LIMIT_PER_MIN,
    get_write_limit_for_plan,
)

def RateLimitGuard(bucket: RateLimitBucket) -> Callable[..., Awaitable[None]]:
    """FastAPI dependency factory: per-user, plan-aware rate limit guard.

    Use READ for cheap navigation/list endpoints (flat 600/min ceiling).
    Use WRITE for cost-bearing endpoints — limit comes from RATE_LIMIT_TIERS
    indexed by user.plan.

    Admin users bypass entirely (no Redis call, no counter increment).
    Fails open on Redis errors (logged at WARNING) so a cache outage does
    not lock the API.
    """
    async def dep(
        user: User = Depends(get_current_user),
    ) -> None:
        # Admin bypass — early return, never touches Redis
        if getattr(user, "is_admin", False):
            return

        if bucket is RateLimitBucket.READ:
            max_requests = READ_LIMIT_PER_MIN
            key = f"read:{user.id}"
        else:
            max_requests = get_write_limit_for_plan(user.plan)
            key = f"write:{user.id}"

        try:
            result = await rate_limiter.check_rate_limit(
                key=key,
                max_requests=max_requests,
                window_seconds=60,
            )
        except Exception as exc:
            # Fail-open: cache outage must not lock users out
            logger.warning("RateLimitGuard Redis error (fail-open): %s", exc)
            return

        if not result["allowed"]:
            retry_after = max(1, result["reset_at"] - int(time.time()))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error_code": "rate_limit_exceeded",
                    "bucket": bucket.value,
                    "limit": max_requests,
                    "used": max_requests,  # bucket full when not allowed
                    "retry_after_seconds": retry_after,
                    "detail": "Rate limit exceeded. Try again later.",
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(result["reset_at"]),
                },
            )

    return dep
```

**Notes**:
- `Depends(get_current_user)` is the right primitive — it already enforces 401 for missing/invalid tokens, so an unauthenticated request never reaches this guard.
- The `detail` dict is what FastAPI serializes as the response body — that satisfies the spec §5 contract directly. (FastAPI emits `{"detail": <whatever you pass>}` when `detail` is a dict).
- Admin attribute is read defensively with `getattr(user, "is_admin", False)` so a transient model mismatch (e.g. running against a stale schema in tests) degrades to "treated as non-admin" rather than crashing.

### 1.6 `apps/api/app/api/middleware.py` — strip per-token bucket

In `RateLimitMiddleware.dispatch`, REPLACE the if/else branching block (lines 96-104) with:

```py
auth_header = request.headers.get("authorization", "")
if auth_header.startswith("Bearer "):
    # Per-user/plan limits are enforced by the RateLimitGuard dep on each
    # route. The middleware no longer counts authenticated requests — that
    # was double-counting against the per-route guard.
    return await call_next(request)

client_ip = request.client.host if request.client else "unknown"
key = f"ip:{client_ip}"
max_requests = _ANONYMOUS_REQUESTS_PER_MINUTE
```

Also delete the now-unused `import hashlib` and `_AUTHENTICATED_REQUESTS_PER_MINUTE` constant. Update the docstring + comments to reflect "anonymous-only abuse guard".

The header-attachment block at lines 135-139 still runs on anonymous requests; that's fine. For authenticated requests, the response goes through the call_next path WITHOUT middleware-level rate-limit headers — the `RateLimitGuard` dep is responsible for emitting `X-RateLimit-*` headers on its enforced routes.

**Anonymous-route IP guard left intact**: this is the abuse cap for `/auth/login`, `/auth/register`, OAuth callbacks, etc. when no Bearer token is presented. The dedicated `refresh_rate_limit` for `/auth/refresh` is unchanged.

### 1.7 Apply `RateLimitGuard` to routes — categorization

See §6 for the full table. Mechanical pattern per route:

```py
from app.core.rate_limiter import RateLimitBucket
from app.api.deps import RateLimitGuard

@router.get("/me", dependencies=[Depends(RateLimitGuard(RateLimitBucket.READ))])
async def me(...): ...
```

`Depends(...)` wrapping is required because `RateLimitGuard(...)` returns the inner `dep` callable, not the result. Using `dependencies=[...]` keeps the route signature clean (the guard returns `None` — no value to inject).

---

## 2. `RateLimitGuard` flow diagram

```
Request → get_current_user (401 if no/bad token)
            ↓
        RateLimitGuard(bucket)
            ├── user.is_admin? ──► return (skip)
            ├── bucket == READ?  ──► key=read:{uid}, limit=600
            └── bucket == WRITE? ──► key=write:{uid}, limit=tier_limit(plan)
                    ↓
            rate_limiter.check_rate_limit(...)
                    ├── Redis OK + allowed     ──► return
                    ├── Redis OK + not allowed ──► raise 429 (structured)
                    └── Redis error            ──► log WARNING, return (fail-open)
```

---

## 3. 429 response contract (spec §5 reconciled)

**Response body** (FastAPI serializes `HTTPException(detail=...)` as `{"detail": ...}`):

```json
{
  "detail": {
    "error_code": "rate_limit_exceeded",
    "bucket": "read",
    "limit": 600,
    "used": 600,
    "retry_after_seconds": 24,
    "detail": "Rate limit exceeded. Try again later."
  }
}
```

**Response headers**:
- `Retry-After: 24`
- `X-RateLimit-Limit: 600`
- `X-RateLimit-Remaining: 0`
- `X-RateLimit-Reset: <epoch>`

**Frontend contract**: `authClient.authFetch` should treat any 429 with `bucket: "read"` as a soft warning (toast, no logout). 429 with `bucket: "write"` should surface a "you've hit your usage limit" UI affordance with an upgrade CTA. This is documented for the FE follow-up but NOT in scope for this change.

---

## 4. Atomic change units (target: 15–20 tasks)

Each unit is a self-contained, reviewable patch. Numbered to reflect dependency order.

| # | Unit | Files | Type |
|---|------|-------|------|
| 1 | Add `cookie_domain: str = ""` setting + startup log | `app/config.py`, `app/main.py` | config |
| 2 | Update `.env.example` and `.env.production.example` with `COOKIE_DOMAIN` | repo root + apps/api root | config |
| 3 | Inject `domain=` kwarg in `_set_session_cookies` and `_clear_session_cookies` | `app/api/routes/auth.py` | feature |
| 4 | Add `RateLimitBucket` enum, `READ_LIMIT_PER_MIN`, `get_write_limit_for_plan` | `app/core/rate_limiter.py` | feature |
| 5 | Implement `RateLimitGuard` factory with admin bypass and fail-open | `app/api/deps.py` | feature |
| 6 | Delete legacy `check_rate_limit` dep and `_PLAN_LIMITS` block | `app/api/deps.py` | refactor |
| 7 | Strip authenticated `token:{hash}` bucket from `RateLimitMiddleware` | `app/api/middleware.py` | refactor |
| 8 | (Conditional) Update `RATE_LIMIT_TIERS` keys to `pro`/`studio` if `plan-model-refactor` has landed; otherwise leave `base`/`enterprise` and add a TODO comment | `app/core/rate_limiter.py` | config |
| 9 | Apply `RateLimitGuard(READ)` to `auth.py` GET routes (`/me`, `/sessions`) | `app/api/routes/auth.py` | feature |
| 10 | Apply `RateLimitGuard(READ)` to `conversations.py`, `bookmarks.py`, `historial`/`folders.py`, `tags.py`, `search.py`, `notifications.py`, `analytics.py`, `billing.py` GETs | listed routes | feature |
| 11 | Apply `RateLimitGuard(WRITE)` to `chat.py` (`POST /chat`) | `app/api/routes/chat.py` | feature |
| 12 | Apply `RateLimitGuard(WRITE)` to `stream.py` and any streaming POST endpoints | `app/api/routes/stream.py` | feature |
| 13 | Apply `RateLimitGuard(WRITE)` to `documents.py` (`/ingest`) and `upload.py` | `app/api/routes/documents.py`, `upload.py` | feature |
| 14 | Apply `RateLimitGuard(WRITE)` to `billing.py` (`/checkout`, mutations) | `app/api/routes/billing.py` | feature |
| 15 | Apply `RateLimitGuard(WRITE)` to remaining mutating routes (`api_keys`, `memory`, `feedback`, `organizations`, `rbac_admin`, `oauth` POSTs, `analysis`, `export`, `emails`, `shared`, `conversations` POST/DELETE) | listed routes | feature |
| 16 | Confirm `/health`, `/docs`, `/openapi.json` remain ungated (no guard) | `app/api/routes/health.py` | verify |
| 17 | Tests: `test_rate_limit_guard.py` (READ ceiling, WRITE tier, admin bypass, plan upgrade, fail-open) | `tests/unit/` | test |
| 18 | Tests: `test_rate_limit_middleware.py` (anonymous IP guard still works, no double-counting on authenticated calls) | `tests/unit/` | test |
| 19 | Tests: `test_cookie_domain.py` (empty → no `Domain=`; set → `Domain=.example.com`; both cookies carry it; clear path also carries it) | `tests/unit/` | test |
| 20 | Add a 1-line `# RATE LIMIT: categorize new routes as READ or WRITE` comment at the top of each router file as a maintenance reminder | all router files | doc |

**Total: 20 atomic units.**

Tasks 9–15 are split per router file so each commit is small and reviewable; an alternative is to fold them into one "apply guards" task, but separation gives `sdd-verify` per-file granularity.

---

## 5. Test strategy (concrete)

### 5.1 `tests/unit/test_rate_limit_guard.py` (NEW)

| Test | Setup | Assertion |
|------|-------|-----------|
| `test_read_bucket_allows_below_ceiling` | Free user, mock rate_limiter to return `{allowed: True}` | Guard returns None |
| `test_read_bucket_429_at_601` | Free user, mock rate_limiter to return `{allowed: False, reset_at: now+30, limit: 600}` | Raises 429 with `bucket=read`, `limit=600`, `Retry-After` header |
| `test_write_bucket_uses_plan_tier` | Free user (plan="free"), assert `check_rate_limit` called with `max_requests=30` | Verify the limit value passed to Redis matches `RATE_LIMIT_TIERS["free"][0]` |
| `test_write_bucket_base_user` | Base user (plan="base"), assert called with `max_requests=120` | Verify tier resolution |
| `test_write_bucket_enterprise_user` | Enterprise user, assert called with `max_requests=600` | Verify tier resolution |
| `test_write_bucket_unknown_plan_falls_back_to_free` | User with `plan="garbage"`, assert called with `max_requests=30` | Defensive fallback |
| `test_admin_bypass_skips_redis_entirely` | Admin user (`is_admin=True`), `rate_limiter` mock raises if called | `check_rate_limit` NEVER invoked, guard returns None |
| `test_fail_open_on_redis_exception` | Mock `check_rate_limit` to raise `ConnectionError` | Guard returns None, WARNING log emitted, no 429 |
| `test_429_body_shape` | Trigger 429, capture exception | `exc.detail` matches contract dict (error_code, bucket, limit, used, retry_after_seconds, detail) |
| `test_429_headers` | Trigger 429 | `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining: 0`, `X-RateLimit-Reset` all present |
| `test_plan_upgrade_does_not_carry_counter` | Conceptual: user_id-keyed bucket, plan goes free→base mid-window. Mock 30 prior requests, plan now base (limit 120). Next call with `allowed=True` from mock. | Guard does NOT raise; `check_rate_limit` called with `max_requests=120` (new tier reflected immediately) |

All tests use `Depends` overrides — `app.dependency_overrides[get_current_user] = lambda: fake_user` — and a `MagicMock`-patched `rate_limiter`. No Docker required (`tests/unit/`).

### 5.2 `tests/unit/test_rate_limit_middleware.py` (UPDATE existing or NEW)

| Test | Assertion |
|------|-----------|
| `test_anonymous_ip_bucket_still_enforced` | Hit `/api/auth/login` 11 times from same IP → 11th gets 429. Existing test should still pass. |
| `test_authenticated_request_skips_middleware_counter` | Hit any authenticated route with valid Bearer token. Patch `rate_limiter.check_rate_limit` to record calls. Assert middleware does NOT call it for the auth-bearing request (the per-route guard call is fine — assert on `key` arg: middleware never passes `token:` keys). |
| `test_no_token_hash_in_redis_keys` | Search call args — assert no key starts with `token:`. |

### 5.3 `tests/unit/test_cookie_domain.py` (NEW)

| Test | Setup | Assertion |
|------|-------|-----------|
| `test_no_domain_attr_when_setting_empty` | Override `settings.cookie_domain = ""`, call login, parse `Set-Cookie` headers via `response.headers.get_list("set-cookie")` | Neither cookie string contains `Domain=` |
| `test_domain_present_when_set` | Override `settings.cookie_domain = ".example.com"`, call login | Both `refresh_token` and `tk_session` cookies contain `Domain=.example.com` |
| `test_domain_carried_on_logout` | Override `settings.cookie_domain = ".example.com"`, call logout | Both delete-cookie headers contain `Domain=.example.com` (otherwise the browser won't expire them) |
| `test_domain_carried_on_register` | Same as login for `/auth/register` | Both cookies have `Domain=` |
| `test_domain_carried_on_refresh` | Same for `/auth/refresh` | Both cookies have `Domain=` |
| `test_domain_carried_on_oauth_google_callback` | Same for OAuth callback | Both cookies have `Domain=` |

**Critical**: use `response.headers.get_list("set-cookie")` per the `fix-auth-tokens` archive gotcha — `.items()` joins multi-value headers with `, ` and breaks parsing.

---

## 6. Route categorization (full inventory of `apps/api/app/api/routes/`)

I read the directory listing — 27 router files. Categorization below is the AUTHORITATIVE binding for the apply phase. Implementer should grep each file and add the appropriate `dependencies=[Depends(RateLimitGuard(...))]` to each route.

| Router file | Routes | Bucket |
|-------------|--------|--------|
| `health.py` | `GET /health`, `GET /api/health` | **NONE** (exempt at middleware level) |
| `auth.py` | `GET /me`, `GET /sessions` | READ |
| `auth.py` | `POST /login`, `POST /register`, `POST /refresh`, `POST /logout`, `POST /logout-all`, password reset | **NONE** (these have anonymous IP middleware OR the dedicated `refresh_rate_limit` already; adding plan-aware guard would require a logged-in user which they don't have) |
| `oauth.py` | `GET /google/callback`, `GET /microsoft/callback` | **NONE** (anonymous flow; protected by anonymous IP middleware) |
| `conversations.py` | `GET /conversations`, `GET /conversations/{id}` | READ |
| `conversations.py` | `POST /conversations`, `PATCH`, `DELETE` | WRITE |
| `chat.py` | `POST /chat` | WRITE |
| `stream.py` | `POST /chat/stream` (or any streaming endpoints) | WRITE |
| `documents.py` | `GET /documents`, `GET /documents/{id}` | READ |
| `documents.py` | `POST /documents/ingest`, `DELETE` | WRITE |
| `upload.py` | `POST /upload` | WRITE |
| `bookmarks.py` | `GET /bookmarks` | READ |
| `bookmarks.py` | `POST`, `DELETE` | WRITE |
| `folders.py` (historial) | `GET` | READ |
| `folders.py` | `POST`, `PATCH`, `DELETE` | WRITE |
| `search.py` (`/buscar`) | `GET /buscar` | READ |
| `tags.py` | `GET` | READ |
| `tags.py` | `POST`, `DELETE` | WRITE |
| `notifications.py` | `GET` | READ |
| `notifications.py` | `POST` (mark read), `DELETE` | WRITE |
| `analytics.py` | `GET /analytics` | READ |
| `billing.py` | `GET /billing` (subscription state) | READ |
| `billing.py` | `POST /billing/checkout`, webhook handlers | WRITE |
| `api_keys.py` | `GET` | READ |
| `api_keys.py` | `POST`, `DELETE` | WRITE |
| `memory.py` | `GET` | READ |
| `memory.py` | `POST`, `PATCH`, `DELETE` | WRITE |
| `feedback.py` | `POST` | WRITE |
| `organizations.py` | `GET` | READ |
| `organizations.py` | `POST`, `PATCH`, `DELETE` | WRITE |
| `rbac_admin.py` | `GET` | READ |
| `rbac_admin.py` | `POST`, `PATCH`, `DELETE` | WRITE |
| `admin.py` | all routes | (admin-only — admins always bypass; classify as WRITE for non-admin defense-in-depth) |
| `analysis.py` | `POST` | WRITE |
| `export.py` | `POST` (generates PDF) | WRITE |
| `emails.py` | `POST` | WRITE |
| `shared.py` | `POST` | WRITE |
| `v1.py` | thin wrapper — guards inherit from underlying routers | (skip; underlying routers are guarded) |
| `api_keys.py`-via-`get_authenticated_user` | API-key authenticated calls | Same WRITE/READ classification — `RateLimitGuard` works against `User` regardless of auth method |

**Default rule**: any new route added without explicit categorization defaults to READ. The 1-line comment from atomic unit #20 enforces this convention.

**Exempt list** (NO guard, NOT counted):
- `/health`, `/api/health` (load balancer probes)
- `/docs`, `/redoc`, `/openapi.json` (already exempt at middleware level)

---

## 7. Migration & rollout

### 7.1 Order of deployment

The atomic units are ordered so each commit leaves the API in a working state:
1. Setting + cookie domain changes (1–3) — backward-compatible, no behavior change for existing config.
2. RateLimitGuard machinery (4–6) — new factory exists but no route uses it yet; the OLD `check_rate_limit` is removed in step 6, but no route imports it (verify with grep before merging step 6).
3. Middleware cleanup (7) — at this point the per-token middleware bucket is gone, but no per-route guard is wired yet. **WINDOW OF UNGATED AUTHENTICATED ACCESS** — between step 7 merging and step 9+ landing, authenticated routes are limited only by infrastructure capacity. Mitigation: ship 7→15 in a single deploy, or temporarily keep middleware bucket and remove it as the LAST step.
4. Apply guards (9–15) — one router at a time.
5. Tests (17–19).

**Recommendation**: reorder so middleware cleanup (7) happens AFTER all guards are wired (9–15). Adjusted apply order: 1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 7, 17, 18, 19, 20. The `sdd-tasks` phase should reflect this corrected order.

### 7.2 Production cutover checklist

- [ ] Set `COOKIE_DOMAIN=.tukijuris.net.pe` in production env (NOT in dev/staging unless they share TLD)
- [ ] Deploy
- [ ] Smoke-test login → cookies present in browser devtools with `Domain=.tukijuris.net.pe`
- [ ] Verify `GET /me` returns 200 from `app.tukijuris.net.pe` (or wherever the FE lives) — confirms cross-subdomain cookie delivery
- [ ] Hammer-test: 700 GETs in 60s from one user → 600 succeed, ~100 return 429 with `bucket: "read"`
- [ ] Hammer-test free user: 35 chat POSTs in 60s → 30 succeed, ~5 return 429 with `bucket: "write"`
- [ ] Admin user: 200 chat POSTs in 60s → all succeed

### 7.3 Rollback

Each unit is independently revertable. The risk-prone units are #6 (deletes legacy dep) and #7 (deletes per-token middleware bucket). If a regression surfaces post-deploy, revert #7 first (restores authenticated bucket as a safety net), then investigate the offending guard.

---

## 8. Risks & mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| Misclassifying `/chat/stream` as READ (denial-of-wallet) | HIGH | Categorization table in §6 is authoritative; `sdd-verify` should check each WRITE-listed route file for `RateLimitGuard(RateLimitBucket.WRITE)` presence. |
| Reordering atomic units leaves an unguarded window | MEDIUM | §7.1 corrected order: middleware cleanup is the LAST behavioral change. |
| `COOKIE_DOMAIN=".tukijuris.net.pe"` set in dev (`localhost`) breaks login | MEDIUM | Default empty in `.env.example`. README/operator docs explicitly warn. |
| Browser caches old cookie after domain change | LOW | Hard cutover; `_clear_session_cookies` with the new domain reissues correctly on next login. Operators may need to re-issue cookies via login if existing cookies hold a different `Domain`. |
| `plan-model-refactor` lands while this change is in-flight, dict keys mismatch | LOW | `get_write_limit_for_plan` falls back to `"free"` for unknown keys. Worst case: pro/studio users temporarily get free-tier WRITE limits until the dict is updated. |
| Fail-open abuse during Redis outage | LOW (accepted) | Anonymous IP middleware still active for unauth endpoints; outages are short-lived; documented in spec §3. |
| Sliding-window double-decrement edge case | LOW | Reusing existing `rate_limiter.check_rate_limit` which already handles "denied requests don't consume quota" via `zrem` cleanup (line 77 of `rate_limiter.py`). |

---

## 9. Open items (deferred to apply phase)

- **API key auth**: routes guarded by `get_authenticated_user` (not `get_current_user`) — `RateLimitGuard` uses `Depends(get_current_user)` so API-key callers will skip the guard entirely. **Decision needed**: either swap `RateLimitGuard` to depend on `get_authenticated_user`, or accept that API-key calls are governed by a separate per-key quota (not in scope here). Recommendation: swap to `get_authenticated_user` since both code paths return a `User` and the guard's logic is identical. Apply-phase implementer should verify.
- **Redis key prefix**: existing `rate_limiter.check_rate_limit` prepends `ratelimit:` so final keys are `ratelimit:read:{uid}` / `ratelimit:write:{uid}`. AGENTS.md mentions `tukijuris:` as `REDIS_KEY_PREFIX` but the rate limiter does NOT use it — that's a pre-existing inconsistency, not introduced by this change. Out of scope.
- **Frontend 429 handling**: this design covers the API contract only. FE should be updated separately to differentiate `bucket: "read"` (toast) vs `bucket: "write"` (upgrade CTA).

---

## 10. Definition of Done

Mirrors spec §7 acceptance criteria with concrete verifiable signals:

1. ✅ `RateLimitGuard(RateLimitBucket.READ)` and `RateLimitGuard(RateLimitBucket.WRITE)` defined and importable from `app.api.deps`.
2. ✅ `RateLimitMiddleware` no longer references `token:`, `_AUTHENTICATED_REQUESTS_PER_MINUTE`, or `hashlib`.
3. ✅ `RateLimitGuard` wraps the redis call in `try/except`, logs WARNING on failure, returns None.
4. ✅ Admin path verified: `is_admin=True` users execute zero Redis calls (asserted in test).
5. ✅ `cookie_domain` setting threads through both helpers; tests verify presence/absence on Set-Cookie.
6. ✅ 429 responses match the JSON contract in §3 and include `Retry-After` header.
7. ✅ All routes in §6 carry the appropriate guard (verified via `sdd-verify` grep over each router file).
8. ✅ `pytest tests/unit/ -v --tb=short` passes 100%.
