# Proposal: frontend-auth-refresh-flow (re-framed scope)

## Intent

The initial audit listed RF-1, RF-2, and RF-3 as open issues regarding token storage and refresh mechanisms. However, the explore phase confirmed they are ALREADY CLOSED in code (the hybrid model with in-memory access token and httpOnly refresh cookie is fully implemented). 

The real intent of this change is to address 4 smaller, adjacent gaps in the auth surface:
1. Fix a silent 401 failure in `NotificationBell`.
2. Ensure cross-tab logout synchronization via `BroadcastChannel`.
3. Add missing test coverage for the `onRefreshFailure` redirect behavior.
4. Correct stale documentation in the backend API `AGENTS.md`.

## Scope

### In Scope
- **Gap 1**: Update `apps/web/src/components/NotificationBell.tsx` to use `authFetch` instead of raw `fetch()`. On error, defensively set `bellCount` to 0.
- **Gap 2**: Implement `BroadcastChannel('tukijuris:auth')` in `apps/web/src/lib/auth/authClient.ts` to broadcast `LOGOUT` events across tabs, and listen for them in `AuthContext` to clear state and redirect.
- **Gap 3**: Add test coverage in `apps/web/src/lib/auth/__tests__/AuthContext.test.tsx` for the `onRefreshFailure` redirect path and the new `LOGOUT` broadcast.
- **Gap 4**: Update `apps/api/AGENTS.md` to reflect that the `refresh_token` is read from the `Cookie` header, not the request body.

### Out of Scope
- Login multi-tab synchronization (we only broadcast logout; login auto-restores via cookie on boot or next API call).
- Refactoring `lib/auth/authClient.ts`'s core refresh flow (it is already correct).
- Modifying `_set_session_cookies` or backend cookie infrastructure.
- Modifying login/register/refresh route handlers.
- 2FA / MFA features.
- Server-side rendering of authenticated pages.
- The notifications feature page itself (Sprint 4 `frontend-notifications-feature`).

## Capabilities

> This section is the CONTRACT between proposal and specs phases.

### New Capabilities
None

### Modified Capabilities
- `auth-session`: Expanding the session lifecycle capability to include cross-tab logout synchronization and updating the NotificationBell component to honor the existing session refresh contract.

## Approach

1. **NotificationBell (`apps/web/src/components/NotificationBell.tsx`)**: Import `clientAuthFetch` directly from `@/lib/auth/authClient` (matching patterns in other app components). Replace raw `fetch` with `clientAuthFetch`. Add a catch block setting `bellCount` to 0 to handle cases where refresh succeeds but the retry still returns 401 (e.g., revoked permissions).
2. **Cross-Tab Logout (`apps/web/src/lib/auth/authClient.ts` & `AuthContext.tsx`)**: Lazy-init a `BroadcastChannel('tukijuris:auth')` (checking `typeof BroadcastChannel !== 'undefined'` for SSR safety). On `logout()` and `logoutAll()`, post a `{ type: 'LOGOUT' }` message. In `AuthContext.tsx`, add a `useEffect` listener that clears in-memory state and redirects to the public landing page upon receiving a `LOGOUT` message.
3. **Docs & Tests**: Add missing assertions in `AuthContext.test.tsx` and fix `AGENTS.md`. Add `NotificationBell.test.tsx` if no test exists yet to verify `authFetch` usage and error handling.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/web/src/components/NotificationBell.tsx` | Modified | Replaces raw fetch with `authFetch`, adds defensive state fallback. |
| `apps/web/src/lib/auth/authClient.ts` | Modified | Adds BroadcastChannel logout broadcast. |
| `apps/web/src/lib/auth/AuthContext.tsx` | Modified | Adds BroadcastChannel listener to clear state on cross-tab logout. |
| `apps/web/src/lib/auth/__tests__/AuthContext.test.tsx` | Modified | Adds tests for onRefreshFailure and BroadcastChannel. |
| `apps/web/src/components/__tests__/NotificationBell.test.tsx` | New | Adds component test verifying authFetch usage. |
| `apps/api/AGENTS.md` | Modified | Corrects refresh endpoint documentation to specify Cookie usage. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| **R1**: BroadcastChannel SSR issues in Next.js | High | Lazy-init guard `typeof BroadcastChannel !== 'undefined'` ensures it only runs in the browser. |
| **R2**: BroadcastChannel browser support | Low | Modern browsers fully support it. Acceptable for Tukijuris's user base. |
| **R3**: NotificationBell component test setup | Medium | Applier may need to set up AuthContext mocks and MSW handlers (following Sprint 1's `change-password.test.tsx` pattern). |

## Rollback Plan

Revert the commits touching `NotificationBell.tsx`, `authClient.ts`, and `AuthContext.tsx`. The API documentation fix and new tests can remain safely or be reverted along with the code changes.

## Dependencies

- No external dependencies required.

## UX Contract After Change

| Scenario | Behavior |
|----------|----------|
| Access token expires while bell dropdown is open | `authFetch` refreshes silently; new fetch succeeds; badge updates. |
| Refresh fails (revoked) while bell open | `onRefreshFailure` → AuthContext clears state → redirect to `/login`. |
| Tab A logs out | Tab B receives BroadcastChannel LOGOUT → clears state → redirects to `/login` (within milliseconds). |
| User opens 3 tabs simultaneously | All 3 share the refresh cookie; each tab boots independently with fresh access token. |
| Refresh + retry STILL returns 401 | `NotificationBell` catch sets `bellCount=0`; user sees clean state. |

## Success Criteria

- [ ] `NotificationBell` uses `authFetch` (not raw fetch) for `/api/notifications/*` endpoints.
- [ ] `NotificationBell` catch handler sets `bellCount` to 0 on error.
- [ ] `BroadcastChannel('tukijuris:auth')` is created in authClient (lazy, SSR-safe).
- [ ] `logout()` and `logoutAll()` post a `LOGOUT` message.
- [ ] `AuthContext` listens to BroadcastChannel and clears state on `LOGOUT`.
- [ ] Vitest test verifies `onRefreshFailure` listener fires → `AuthContext` clears + redirects.
- [ ] Vitest test verifies BroadcastChannel LOGOUT → receiving `AuthContext` clears state.
- [ ] Vitest test verifies `NotificationBell` uses `authFetch` and sets `bellCount=0` on fetch rejection.
- [ ] `apps/api/AGENTS.md` refresh section documents Cookie-based contract.
- [ ] All existing tests pass (no regressions).
- [ ] Lint+tsc clean on changed files.