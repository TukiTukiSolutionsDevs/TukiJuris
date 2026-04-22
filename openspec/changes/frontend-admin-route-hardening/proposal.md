# Proposal: frontend-admin-route-hardening

## Intent (Why)

Closes two security gaps from `frontend-coverage-audit`:
- **NEW-RISK-1**: AdminLayout client-side `is_admin` check is the ONLY guard for `/admin/*`. Middleware checks `tk_session` (auth) but not role. Non-admin users can request the route, the JS shell loads, and the client check kicks in — but the shell is exposed in the meantime.
- **NEW-RISK-2**: `/analytics/*` has NO role gate at all. Any auth user reaches the page; backend RBAC blocks the API but the page renders empty/error states instead of redirecting cleanly.

Owner decision (audit proposal): Server-side enforcement via middleware.

## Scope

### In Scope (What changes)

5 files, ~75 LOC total.

**Backend (apps/api)**:
1. **Modify** `apps/api/app/api/routes/auth.py`:
   - Update `_set_session_cookies(response, access_token, refresh_token, user: User)` to read `user.is_admin` instead of adding a boolean param. All callers (login, register, refresh rotation) will pass `user`.
   - Add `tk_admin` cookie (`httpOnly`, `Path=/`, `SameSite=Strict`, value=`1`) ONLY when `user.is_admin is True`. When `False` or unknown, ensure the cookie is DELETED via `response.delete_cookie('tk_admin', path='/')`.
   - `_clear_session_cookies(response)` — also clear `tk_admin`.
2. **Add/Modify** `apps/api/tests/unit/test_auth_cookies.py`:
   - `tk_admin` SET on login when `user.is_admin = True`.
   - `tk_admin` DELETED on login when `user.is_admin = False`.
   - `tk_admin` SET on refresh rotation when `user.is_admin = True`.
   - `tk_admin` CLEARED on logout.
   - `tk_admin` CLEARED on logout-all.

**Frontend (apps/web)**:
3. **Modify** `apps/web/src/lib/constants.ts`:
   - Add `ADMIN_MARKER_COOKIE = 'tk_admin'` and `ADMIN_MARKER_VALUE = '1'`.
   - Expand `ADMIN_PATH_PREFIXES` from `['/admin']` to `['/admin', '/analytics']`.
4. **Modify** `apps/web/src/middleware.ts`:
   - For paths matching any `ADMIN_PATH_PREFIXES`, check `request.cookies.get(ADMIN_MARKER_COOKIE)?.value === ADMIN_MARKER_VALUE`. If false → `NextResponse.redirect(new URL('/', request.url))`.
   - Maintain existing `tk_session` check. Order: auth first, then admin. Missing `tk_session` on admin path → `/login`. Present `tk_session` but missing `tk_admin` → `/`.
5. **Modify** `apps/web/src/app/analytics/page.tsx` (and sibling layouts rendering analytics shell):
   - Defense-in-depth: add `useIsAdmin()` (or `useAuth()` equivalent) check that calls `router.replace('/')` if non-admin.

### Out of Scope (Non-changes)
- DO NOT touch `apps/web/src/lib/auth.ts` (Sprint 3 owns the refresh-flow rewrite).
- DO NOT touch the JWT shape (`is_admin` claim already present).
- DO NOT add a `/403` page (simplifying to `/` redirect for MVP).
- DO NOT change `AdminLayout` (stays as defense-in-depth client-side check).
- NO new dependencies.
- Server Components migration of admin pages is out of scope.

## Capabilities

### New Capabilities
- `admin-routing`: Server-side route protection and role-based redirects for administrative paths (`/admin`, `/analytics`).

### Modified Capabilities
- None

## UX Contract After Change

| Scenario                                          | Behavior                                                              |
|---------------------------------------------------|-----------------------------------------------------------------------|
| Anonymous → `/admin/users`                        | Middleware redirects to `/login` (existing `tk_session` check)        |
| Auth non-admin → `/admin/users`                   | Middleware redirects to `/` (NEW: `tk_admin` cookie missing)          |
| Auth admin → `/admin/users`                       | Page loads normally (`tk_admin = '1'`)                                |
| Auth non-admin → `/analytics`                     | Middleware redirects to `/` (NEW)                                     |
| Auth admin → `/analytics`                         | Page loads normally                                                   |
| Admin gets demoted mid-session                    | Sees admin pages until next token refresh (≤15 min). Backend RBAC blocks all API calls — no data leak |
| Non-admin gets promoted                           | Must logout+login OR wait until next refresh to see admin UI          |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| **R1 — Staleness**: `tk_admin` lags real role by ≤15 min for active users. | High | Backend RBAC is authoritative on every API call; no data leak possible. Accepted trade-off (D1). |
| **R2 — Missed caller**: `_set_session_cookies` signature change requires updating ALL call sites. | Medium | Spec must enumerate callers; tasks must verify each. Add unit tests asserting helper behavior. |
| **R3 — Analytics page belt-and-suspenders**: Brief skeleton flash before redirect fires. | Low | Identical pattern to existing `AdminLayout`. Acceptable. |
| **R4 — Middleware matcher**: Ensure `/admin/**` and `/analytics/**` are covered. | Low | Current matcher `'/((?!_next/static|_next/image|favicon.ico).*)'` already includes them. |
| **R5 — Refresh-flow conflict**: Sprint 3 moves `access_token` to `httpOnly` cookie. | Medium | `tk_admin` cookie is INDEPENDENT and will COEXIST. Document for Sprint 3. |

## Rollback Plan

- Revert changes to `middleware.ts` to disable the `tk_admin` check.
- Revert the `_set_session_cookies` signature change in `auth.py`.

## Dependencies

- None (Independent of Sprint 3).

## Success Criteria (Acceptance Criteria)

- [ ] Backend test: `tk_admin` SET on login when `user.is_admin=True` (assert response cookies)
- [ ] Backend test: `tk_admin` DELETED on login when `user.is_admin=False`
- [ ] Backend test: `tk_admin` SET on refresh rotation when `user.is_admin=True`
- [ ] Backend test: `tk_admin` CLEARED on logout + logout-all
- [ ] Frontend Vitest test: middleware redirects auth-non-admin from `/admin/*` to `/`
- [ ] Frontend Vitest test: middleware redirects auth-non-admin from `/analytics/*` to `/`
- [ ] Frontend Vitest test: middleware allows auth-admin to `/admin/*` and `/analytics/*`
- [ ] Frontend Vitest test: middleware redirects anonymous from `/admin/*` to `/login` (regression)
- [ ] Frontend Vitest test: analytics page has `useIsAdmin` redirect (assert non-admin sees `router.replace('/')`)
- [ ] Backend pytest: 0 regressions in auth subset (149+ tests still pass)
- [ ] Frontend Vitest: full suite passing (206 baseline + new tests)
- [ ] Lint + tsc clean on all 5 changed files
- [ ] No drift outside the 5 files
