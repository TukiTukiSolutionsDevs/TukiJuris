# Spec: fix-rate-limit-architecture

## 1. Overview
The current rate-limiting architecture doubly penalizes legitimate usage through redundant buckets (middleware per-IP + per-token generic route checks) and fails to differentiate between lightweight data reads (like fetching chat history) and heavy resource-intensive operations (like LLM stream generation). This change splits rate-limiting into explicit READ and WRITE buckets, drops the redundant authenticated middleware limit, wires actual plan limits to the WRITE bucket, and ensures cookies are correctly domain-scoped in production to handle subdomains.

## 2. Functional Requirements

### 2.1 Dependency Factory: `RateLimitGuard`
- Create a new dependency factory: `RateLimitGuard(kind: Literal["read", "write"] = "write")` to replace generic `check_rate_limit` usages.
- **Admin Bypass**: If `user.is_admin` is True, bypass the rate limit immediately and return early without recording a request.
- **READ Bucket**:
  - Keys based on `read:{user_id}`.
  - Flat limit of 600 requests per minute (window: 60s).
- **WRITE Bucket**:
  - Keys based on `write:{user_id}`.
  - Limit dynamically resolved from `RATE_LIMIT_TIERS[user.plan]` in `rate_limiter.py` (window: 60s).
- On limit exceeded, raise `HTTPException` returning a 429 status code with the newly structured contract (see Section 5).

### 2.2 Middleware Cleanup
- Refactor `RateLimitMiddleware` (`apps/api/app/api/middleware.py`).
- Strip the authenticated per-user bucket entirely.
- Retain only the IP-based anonymous abuse guard (`ip:{client_ip}`) for unauthenticated endpoints.

### 2.3 Explicit Route Categorization
All authenticated routes must apply the appropriate guard:
- **READ** operations (`RateLimitGuard("read")`):
  - `/me`
  - `/conversations/list`
  - `/bookmarks/*`
  - `/historial/*`
  - `/buscar`
  - Plan/subscription read endpoints
  - *Default categorization for new or uncategorized routes to prevent breaking navigation.*
- **WRITE** operations (`RateLimitGuard("write")`):
  - `/chat`
  - `/chat/stream`
  - `/documents/ingest`
  - `/documents/upload`
  - `/billing/checkout`
  - `/llm-key` (POST)

### 2.4 Cross-Domain Cookie Configuration
- `COOKIE_DOMAIN` environment variable logic added to `Settings`.
- `_set_session_cookies` and `_clear_session_cookies` (from `fix-auth-tokens`) updated to apply `domain=settings.cookie_domain` if `COOKIE_DOMAIN` is not empty.

## 3. Non-Functional Requirements
- **Performance**: Redis dependency lookup and increment must take < 2ms to keep READ overhead invisible.
- **Availability (Fail-Open)**: If the Redis connection fails or times out, `RateLimitGuard` must swallow the exception, log a warning, and allow the request through. This ensures core functionality degrades gracefully instead of hard-locking users during cache outages.
- **Shared Constraints**: Counters are shared globally per-user via Redis. Concurrent tabs or devices will deduct from the same shared bucket.

## 4. Data/Schema
- **No DB Schema Changes**.
- `RATE_LIMIT_TIERS` dictionary currently matches keys: `free`, `base`, `enterprise`.
- Implementation must use the existing `RATE_LIMIT_TIERS` keys based on `user.plan` logic. If `plan-model-refactor` has modified this to `free/pro/studio`, the mapping will reflect those exact keys. We code to the interface, retrieving the `[0]` index (requests_per_minute) from the tuple.

## 5. API Contract
When a rate limit is exceeded, the API raises an `HTTPException(429)` returning the following payload shape:

```json
{
  "error_code": "rate_limit_exceeded",
  "bucket": "read", // or "write"
  "limit": 600,
  "used": 600,
  "retry_after_seconds": 24,
  "detail": "Rate limit exceeded. Try again later."
}
```
The response headers must also include `Retry-After: 24` (where 24 is calculated from the time remaining in the window).

## 6. Test Strategy
1. **Free User Verification**:
   - Call `/historial` (READ) 50 times -> Success (well under 600 limit).
   - POST to `/chat` (WRITE) using a Free tier user -> Verify it succeeds until hitting `RATE_LIMIT_TIERS["free"][0]` (e.g., 30), then throws 429 on the 31st request.
2. **Base/Pro User Verification**:
   - POST to `/chat` using a Base/Pro user -> Verify it hits 429 precisely after reaching its respective `RATE_LIMIT_TIERS` tier.
3. **Admin Exemption Verification**:
   - POST to `/chat` using an Admin user 200 times -> Verify 0 429 responses, regardless of tier.
4. **Cookie Domain Injection**:
   - Override settings to `cookie_domain=".tukijuris.net.pe"` during test -> Assert `_set_session_cookies` sets the `domain=` directive on the `Set-Cookie` header.

## 7. Acceptance Criteria
1. `RateLimitGuard("read")` and `RateLimitGuard("write")` are correctly implemented and wired into all targeted route functions.
2. The global `RateLimitMiddleware` no longer tracks/punishes authenticated users (the `token:{hash}` logic is deleted).
3. Redis exceptions inside `RateLimitGuard` fail-open with logging.
4. Admins bypass the guard entirely.
5. Production `COOKIE_DOMAIN` works accurately without breaking local dev (local uses `""` / `None`).
6. A 429 returns the structured JSON and `Retry-After` header defined in the contract.

## 8. Risks & Mitigations
- **Misclassification**: Accidentally classifying a costly endpoint (like `/chat/stream`) as READ.
  - *Mitigation*: Ensure explicit code review over `RateLimitGuard("write")` bindings.
- **Fail-Open Abuse**: A malicious actor causing Redis timeouts to bypass limits.
  - *Mitigation*: Acceptable risk. The overarching IP-based abuse middleware still provides a coarse last line of defense, and Redis outages are expected to be short-lived.
- **Shared Counter**: Users opening many tabs might hit the READ limit.
  - *Mitigation*: The READ limit is set to 600/min (10 req/s sustained), which is practically unreachable for normal UI navigation.
- **Cookie Misconfiguration**: Setting an invalid `COOKIE_DOMAIN` blocking login.
  - *Mitigation*: Default `.env.example` to `""` so new setups work natively without cross-domain requirements. Document `.tukijuris.net.pe` precisely in prod guides.

## 9. Open Questions
- If a user changes their plan mid-window, does the rate limit retroactively apply to the current window count? *(Assumed Yes: Since the `limit` is evaluated per request, if `current_count >= new_limit`, they get 429'd immediately.)*
- Does the IP-based middleware count still increment for authenticated users? *(Assumed Yes: IP abuse tracking remains orthogonal to the authenticated account limits.)*
