# Spec — frontend-admin-route-hardening

## 1. Scope
Cross-stack change. 5 files, ~75 LOC.

Backend: `apps/api/app/api/routes/auth.py` + new test file `apps/api/tests/unit/test_auth_cookies.py`.
Frontend: `apps/web/src/lib/constants.ts`, `apps/web/src/middleware.ts`, `apps/web/src/app/analytics/page.tsx`.

## 2. Backend behavioral requirements (BAH-* — Backend Admin Hardening)

- **BAH-1**: `_set_session_cookies(response, access_token, refresh_token, *, is_admin: bool)` SHALL accept `is_admin: bool` as a keyword-only parameter.
- **BAH-2**: When `user.is_admin is True`, `_set_session_cookies` SHALL set cookie `tk_admin=1` with attributes: `httponly=True, samesite='strict', secure=<env-conditional>, path='/', max_age=<token TTL or session>`.
- **BAH-3**: When `user.is_admin is not True` (False, None, missing), `_set_session_cookies` SHALL call `response.delete_cookie('tk_admin', path='/')` to actively clear any stale value.
- **BAH-4**: `_clear_session_cookies(response)` SHALL also clear `tk_admin` (delete_cookie call).
- **BAH-5**: All current callers of `_set_session_cookies` SHALL be updated to pass `is_admin` (derived from the user object at the call site, OR — for refresh — decoded from the freshly-issued access token via `jose_jwt`).
- **BAH-6**: `logout` SHALL still call `_clear_session_cookies`. `logout-all` SHALL still call `_clear_session_cookies` for the current response (other devices' cookies are server-controlled separately).

## 3. Frontend behavioral requirements (FAH-* — Frontend Admin Hardening)

- **FAH-1**: `apps/web/src/lib/constants.ts` SHALL export:
  - `ADMIN_MARKER_COOKIE = 'tk_admin'`
  - `ADMIN_MARKER_VALUE = '1'`
- **FAH-2**: `ADMIN_PATH_PREFIXES` SHALL include both `/admin` and `/analytics` (current value: `['/admin']` per explore).
- **FAH-3**: Middleware (`apps/web/src/middleware.ts`) SHALL, for any request whose pathname matches ANY of `ADMIN_PATH_PREFIXES`:
  1. First check existing `tk_session` cookie (auth) — if missing, redirect to `/login` (existing behavior, no regression).
  2. Then check `request.cookies.get(ADMIN_MARKER_COOKIE)?.value === ADMIN_MARKER_VALUE` — if false, `NextResponse.redirect(new URL('/', request.url))`.
- **FAH-4**: Middleware SHALL NOT alter behavior for non-admin paths (no change to existing routing logic for `/buscar`, `/chat`, etc.).
- **FAH-5**: Middleware matcher SHALL remain unchanged (current `'/((?!_next/static|_next/image|favicon.ico).*)'` already covers `/admin/**` and `/analytics/**`).
- **FAH-6**: `apps/web/src/app/analytics/page.tsx` SHALL include a defense-in-depth client-side check: read user from AuthContext (or `useIsAdmin` hook if available), and if `!user.is_admin`, call `router.replace('/')` in a `useEffect`. Show neutral loading state while user is unknown.

## 4. Backend test matrix (BAT-*)

Test file: `apps/api/tests/unit/test_auth_cookies.py` (new) OR add to existing `test_auth*.py` (applier picks based on file size).

| ID    | Case                                          | Setup                                                  | Expected                                            |
|-------|-----------------------------------------------|--------------------------------------------------------|-----------------------------------------------------|
| BAT-1 | tk_admin SET on login (admin user)            | Login as user with `is_admin=True`                     | Response Set-Cookie includes `tk_admin=1` with httponly/samesite=strict |
| BAT-2 | tk_admin DELETED on login (non-admin user)    | Login as user with `is_admin=False`                    | Response Set-Cookie includes a delete header for tk_admin (max-age=0 or expires=past) |
| BAT-3 | tk_admin SET on refresh rotation (admin user) | Login admin, then call /api/auth/refresh              | Refresh response sets tk_admin=1                     |
| BAT-4 | tk_admin CLEARED on logout                    | Login admin, then logout                               | Logout response clears tk_admin                      |
| BAT-5 | tk_admin CLEARED on logout-all                | Login admin, then logout-all                           | Logout-all response clears tk_admin                  |

## 5. Frontend test matrix (FAT-*)

Test file: `apps/web/src/__tests__/middleware.admin.test.ts` (new) OR `apps/web/src/middleware.test.ts` if a sibling test already exists. Pattern: import the middleware function directly; construct a `NextRequest` via Next.js test helpers; assert the response.

| ID    | Case                                                | Setup                                                | Expected                                       |
|-------|-----------------------------------------------------|------------------------------------------------------|------------------------------------------------|
| FAT-1 | Anonymous → /admin/users                            | NextRequest, no cookies                              | NextResponse redirect to /login                |
| FAT-2 | Auth non-admin → /admin/users                       | NextRequest with tk_session=1, NO tk_admin           | NextResponse redirect to /                     |
| FAT-3 | Auth admin → /admin/users                           | NextRequest with tk_session=1 + tk_admin=1           | NextResponse.next() (pass-through)             |
| FAT-4 | Auth non-admin → /analytics                         | NextRequest with tk_session=1, NO tk_admin           | NextResponse redirect to /                     |
| FAT-5 | Auth admin → /analytics                             | NextRequest with tk_session=1 + tk_admin=1           | NextResponse.next() (pass-through)             |

Plus 1 page-level test:
| FAT-6 | Analytics page useEffect redirects non-admin       | Render with AuthContext mock { user: { is_admin: false } } | router.replace('/') called |

## 6. Non-functional requirements

- **AH-NFR-1**: NO new dependencies (backend or frontend).
- **AH-NFR-2**: NO change to JWT shape (`is_admin` claim already present per explore).
- **AH-NFR-3**: NO change to existing auth flow contracts (login/register/refresh/logout response shapes unchanged at the JSON level).
- **AH-NFR-4**: Backend tests run with existing pytest infra (`cd apps/api && python -m pytest`). Frontend tests run with existing Vitest (`cd apps/web && npm test`).
- **AH-NFR-5**: Lint + tsc clean on all 5 modified files.
- **AH-NFR-6**: Backend AGENTS.md rule "DB writes first, Redis writes post-commit" is NOT applicable here (no DB writes added). Cookie writes are part of the response, not a separate side effect.

## 7. Out of scope
- /403 page
- httpOnly access_token migration (Sprint 3)
- AdminLayout refactor (stays as-is, defense-in-depth)
- AdminSidebar fix (Notificaciones link wrongly points to /configuracion — separate change)
- Org switcher / multi-org (different change)

## 8. Implementation note — `is_admin: bool` vs `user: User`

The original spec drafted `user: User` as the new parameter for `_set_session_cookies`. During implementation it became clear this was impractical for the `refresh` route: the refresh handler receives only a `TokenPair` (freshly-issued JWTs) and has no `User` ORM object in scope. Fetching the user from the DB solely to pass it here would add a round-trip with no benefit.

The implemented contract uses `is_admin: bool` instead:
- `login` and `register` handlers: `is_admin=bool(user.is_admin)` (User is already in scope).
- `refresh` handler: `is_admin` is decoded from the freshly-issued `access_token` via `jose_jwt.decode` (the token is guaranteed valid at this point; fallback `False` on `JWTError`).

This is functionally equivalent and avoids coupling the cookie helper to the ORM layer. Spec updated 2026-04-22 to reflect reality (remediation pass after verify-report #374).

## 9. References
- Proposal: `openspec/changes/frontend-admin-route-hardening/proposal.md` + engram #368
- Explore: engram topic `sdd/frontend-admin-route-hardening/explore`
- Backend pattern: `_set_session_cookies` in `apps/api/app/api/routes/auth.py`
- Frontend pattern: existing tk_session check in `apps/web/src/middleware.ts`
- Backend AGENTS.md: `apps/api/AGENTS.md`
- Backend test pattern: `apps/api/tests/test_auth*.py`
- Frontend test pattern: `apps/web/src/app/configuracion/__tests__/change-password.test.tsx` (Sprint 1) and middleware tests if any exist
