# Spec — frontend-auth-refresh-flow

## 1. Scope summary
4 localized gaps, ~80-100 LOC across 6 files. NO core auth refactor (RF-1/2/3 already closed).

## 2. Behavioral requirements (FAR-* — Frontend Auth Refresh)

### NotificationBell (Gap 1, D1, D4)
- **FAR-1**: NotificationBell SHALL use `authFetch` (imported from `@/lib/auth/authClient`) for all `/api/notifications/*` calls. NO raw `fetch()` to authenticated endpoints.
- **FAR-2**: When the bell's fetch promise rejects (any error: 401 post-refresh, network, etc.), the component SHALL set `bellCount` to 0 in the catch block as a defensive fallback.
- **FAR-3**: NotificationBell SHALL NOT itself trigger redirects. authFetch's existing `onRefreshFailure` listener (wired in AuthContext) handles redirect; NotificationBell stays UI-only.

### Cross-tab logout sync (Gap 2, D2, D3)
- **FAR-4**: `apps/web/src/lib/auth/authClient.ts` SHALL maintain a lazy-initialized `BroadcastChannel('tukijuris:auth')` instance, guarded by `typeof BroadcastChannel !== 'undefined'` for SSR safety.
- **FAR-5**: The `logout()` and `logoutAll()` functions SHALL post `{ type: 'LOGOUT' }` on the channel BEFORE returning.
- **FAR-6**: `apps/web/src/lib/auth/AuthContext.tsx` AuthProvider SHALL register a listener on `BroadcastChannel('tukijuris:auth')` in its mount effect.
- **FAR-7**: On receipt of a `LOGOUT` message, AuthContext SHALL clear in-memory state and redirect to the public landing path (same path used by onRefreshFailure).
- **FAR-8**: Listener SHALL be cleaned up on AuthProvider unmount (via the useEffect return).
- **FAR-9**: NO login broadcast — only logout. Login auto-restores in other tabs via boot refresh.

### Test coverage (Gap 3)
- **FAR-10**: A Vitest test SHALL exist that asserts: when `onRefreshFailure` listener fires, AuthContext clears state AND triggers `router.push('/login')` (or whichever public path is used).
- **FAR-11**: A Vitest test SHALL exist that asserts: when BroadcastChannel `LOGOUT` is received, AuthContext clears state.

### Documentation (Gap 4, D5)
- **FAR-12**: `apps/api/AGENTS.md` "POST /api/auth/refresh" section SHALL document that refresh_token is read from the **Cookie header** (FastAPI `Cookie(default=None)` parameter), NOT from the request body. Web AGENTS.md is the source of truth for the cookie contract.

## 3. Test matrix (FRT-* — Frontend Refresh Tests)

| ID    | Case                                                    | Setup                                                            | Expected                                              |
|-------|---------------------------------------------------------|------------------------------------------------------------------|-------------------------------------------------------|
| FRT-1 | NotificationBell uses authFetch                         | Mock authFetch to return { count: 5 }                            | authFetch called with /api/notifications/unread-count; badge shows 5 |
| FRT-2 | NotificationBell catch resets count to 0                | Mock authFetch to throw                                          | bellCount === 0                                       |
| FRT-3 | onRefreshFailure clears AuthContext + redirects         | Trigger registered listener with onRefreshFailure event          | user state null; router.push('/login') called once    |
| FRT-4 | BroadcastChannel LOGOUT clears AuthContext              | Post message { type: 'LOGOUT' } to bc                            | user state null                                       |
| FRT-5 | (Optional) authClient logout posts BroadcastChannel msg | Spy on bc.postMessage; call authClient.logout()                  | postMessage called with { type: 'LOGOUT' }            |
| FRT-6 | (Optional) authClient logoutAll posts message           | Spy on bc.postMessage; call authClient.logoutAll()               | postMessage called with { type: 'LOGOUT' }            |

## 4. Non-functional requirements
- **AR-NFR-1**: SSR-safe — all BroadcastChannel access guarded by `typeof BroadcastChannel !== 'undefined'`.
- **AR-NFR-2**: NO new dependencies.
- **AR-NFR-3**: NO changes to login/register/refresh route handlers.
- **AR-NFR-4**: NO changes to `_set_session_cookies` or backend cookie infra.
- **AR-NFR-5**: NO regressions in existing 216 frontend tests + 1250 backend tests.
- **AR-NFR-6**: Lint+tsc clean on changed files.
- **AR-NFR-7**: BroadcastChannel browser support: Edge 79+, Safari 15.4+, Chrome 54+, Firefox 38+. Document in proposal.

## 5. Out of scope
- Login multi-tab broadcast (only logout)
- Refactoring authClient.ts refresh flow itself (correct as-is)
- Notifications feature page (Sprint 4)
- Updating sdd-init obs #4 (separate engram operation post-Sprint)

## 6. References
- Proposal: `openspec/changes/frontend-auth-refresh-flow/proposal.md` + engram topic
- Explore: engram topic `sdd/frontend-auth-refresh-flow/explore`
- Code refs:
  - `apps/web/src/components/NotificationBell.tsx` — fetch line(s) per explore
  - `apps/web/src/lib/auth/authClient.ts` — logout/logoutAll
  - `apps/web/src/lib/auth/AuthContext.tsx` — AuthProvider mount effect
  - `apps/api/AGENTS.md` — POST /api/auth/refresh section
- Test pattern reference: Sprint 1 `change-password.test.tsx`, Sprint 2 `analytics.admin.test.tsx`
