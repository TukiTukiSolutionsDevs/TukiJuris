<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

<!-- BEGIN:auth-flow-pilar-0.1 -->
## Auth Flow — Access + Refresh Tokens (PILAR 0.1)

Updated: 2026-04-16. The API now returns a **short-lived access token (15 min)** and a
**long-lived refresh token (30 days)** on every login/register call.

### ⚠️ Breaking change for existing clients

Existing clients that stored a single long-lived JWT will receive `401` after 15 min.
They must implement the refresh flow described below or prompt re-login.

---

### Endpoints

| Method | Path | Auth required | Description |
|--------|------|--------------|-------------|
| `POST` | `/api/auth/login` | No | Returns `{ access_token, refresh_token, token_type, expires_in }` |
| `POST` | `/api/auth/register` | No | Same response shape as login |
| `POST` | `/api/auth/refresh` | No (refresh token in body) | Rotate refresh token → new pair. Rate-limited 10/min per IP. |
| `POST` | `/api/auth/logout` | Bearer access token | Revoke one refresh token (single-device logout) |
| `POST` | `/api/auth/logout-all` | Bearer access token | Revoke all sessions → `{ revoked: N }` |
| `GET`  | `/api/auth/sessions` | Bearer access token | List active sessions |

---

### Token storage rules

- `access_token` → **memory only** (React state / Zustand). NEVER `localStorage`.
- `refresh_token` → `httpOnly` cookie (preferred) or secure isolated store.

---

### Refresh flow

```typescript
// Call when access token expires OR any API returns 401
POST /api/auth/refresh
Body: { refresh_token: "<current>" }

// Success → replace BOTH tokens atomically. Old refresh token is now invalid.
// 401 error_codes: invalid_refresh_token | expired_refresh_token |
//                  revoked_refresh_token | reuse_detected
// 429 → rate limit hit, back off 60s, then force re-login
```

**Token rotation**: old refresh token is invalidated on every successful rotate.
**Reuse detection**: using a revoked token kills the entire session family → force re-login
and show a security alert.

---

### 401 handling pattern

```typescript
if (response.status === 401) {
  try {
    const pair = await POST('/api/auth/refresh', { refresh_token });
    // store pair.access_token in memory, pair.refresh_token in secure store
    // retry original request once with new access_token
  } catch {
    clearTokens();
    redirectTo('/login');  // session expired or security event
  }
}
```

**One retry only.** If the retried request also returns 401, force re-login.

---

### Error codes

| `error_code` | Meaning | Action |
|-------------|---------|--------|
| `invalid_refresh_token` | Bad JWT | Force re-login |
| `expired_refresh_token` | Token TTL elapsed | Force re-login |
| `revoked_refresh_token` | Explicit logout | Force re-login |
| `reuse_detected` | Security: revoked token reused | Force re-login + security alert |

<!-- END:auth-flow-pilar-0.1 -->
