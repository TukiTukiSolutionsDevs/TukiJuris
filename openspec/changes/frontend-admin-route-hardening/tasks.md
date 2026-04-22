# Tasks — frontend-admin-route-hardening

## Batch A — Backend cookie helper
- [x] **A1** Locate `_set_session_cookies` and `_clear_session_cookies` in `apps/api/app/api/routes/auth.py`. Note current signature + all callers (use grep). (BAH-5)
- [x] **A2** Update `_set_session_cookies` signature to accept `user: User` (in addition to or replacing existing role-related params). (BAH-1)
- [x] **A3** Inside `_set_session_cookies`: when `user.is_admin is True`, set cookie `tk_admin=1` with httponly=True, samesite='strict', secure=<env-conditional matching tk_session>, path='/', max_age matching tk_session lifetime. (BAH-2)
- [x] **A4** Inside `_set_session_cookies`: when `user.is_admin` is not True, call `response.delete_cookie('tk_admin', path='/')` to actively clear it. (BAH-3)
- [x] **A5** Update `_clear_session_cookies` to also `delete_cookie('tk_admin', path='/')`. (BAH-4)
- [x] **A6** Update ALL callers of `_set_session_cookies` (login, register, refresh rotation, OAuth callback if exists) to pass the user object. Use the grep result from A1. (BAH-5)
- [x] **A7** Verify the route still loads cleanly: `cd apps/api && python -c "from app.main import app; print('ok')"`.

## Batch B — Backend tests
Test file: `apps/api/tests/unit/test_auth_cookies.py` (new). Pattern: read a sibling auth test for pytest fixtures + ASGITransport setup.

- [x] **B1** BAT-1: Login admin → response Set-Cookie includes `tk_admin=1; HttpOnly; SameSite=Strict; Path=/`.
- [x] **B2** BAT-2: Login non-admin → response Set-Cookie includes a delete header for tk_admin (max-age=0 or expires=past).
- [x] **B3** BAT-3: Refresh rotation for admin → response sets tk_admin=1.
- [x] **B4** BAT-4: Logout for admin → response clears tk_admin.
- [x] **B5** BAT-5: Logout-all for admin → response clears tk_admin.
- [x] **B6** Run: `cd apps/api && python -m pytest tests/unit/test_auth_cookies.py -v --tb=short` — all 5 pass.
- [x] **B7** Run regression: `cd apps/api && python -m pytest tests/ -k "auth" -v --tb=short 2>&1 | tail -10` — 149+ passing, 0 new failures.

## Batch C — Frontend constants
- [x] **C1** `apps/web/src/lib/constants.ts`: add `export const ADMIN_MARKER_COOKIE = 'tk_admin';` and `export const ADMIN_MARKER_VALUE = '1';`. (FAH-1)
- [x] **C2** Same file: expand `ADMIN_PATH_PREFIXES` from current value (likely `['/admin']`) to `['/admin', '/analytics']`. (FAH-2)

## Batch D — Frontend middleware
- [x] **D1** `apps/web/src/middleware.ts`: import the new constants.
- [x] **D2** Add admin-path branch: AFTER the existing tk_session check, if pathname starts with any value in `ADMIN_PATH_PREFIXES`, check `request.cookies.get(ADMIN_MARKER_COOKIE)?.value === ADMIN_MARKER_VALUE`. If false → `NextResponse.redirect(new URL('/', request.url))`. (FAH-3)
- [x] **D3** Confirm matcher unchanged. (FAH-5)
- [x] **D4** Verify: `cd apps/web && npx tsc --noEmit` — 0 errors.

## Batch E — Analytics page defense-in-depth + tests
- [x] **E1** `apps/web/src/app/analytics/page.tsx`: add useEffect that reads user from AuthContext (or `useIsAdmin` if exists) and calls `router.replace('/')` if `!user.is_admin`. Show neutral loading state while user is unknown. (FAH-6)
- [x] **E2** Create `apps/web/src/__tests__/middleware.admin.test.ts` (or `apps/web/middleware.admin.test.ts` — applier picks). Pattern: import middleware function, construct NextRequest, assert NextResponse.
- [x] **E3** FAT-1: anonymous → /admin/users → redirect to /login.
- [x] **E4** FAT-2: auth non-admin → /admin/users → redirect to /.
- [x] **E5** FAT-3: auth admin → /admin/users → next() pass-through.
- [x] **E6** FAT-4: auth non-admin → /analytics → redirect to /.
- [x] **E7** FAT-5: auth admin → /analytics → next() pass-through.
- [x] **E8** FAT-6: analytics page test — render with non-admin AuthContext mock, assert router.replace('/') called. Co-locate with the page or in `__tests__/`.

## Batch F — Validation + apply-progress
- [x] **F1** `cd apps/web && npm test -- middleware.admin 2>&1 | tail -15` — all 5 middleware tests green.
- [x] **F2** `cd apps/web && npm test -- apps/web/src/app/analytics 2>&1 | tail -15` — analytics test green.
- [x] **F3** `cd apps/web && npm test 2>&1 | tail -10` — full suite. Baseline 206 + new ~6 = 212+. Zero NEW regressions vs baseline.
- [x] **F4** `cd apps/web && npx eslint src/lib/constants.ts src/middleware.ts src/app/analytics/page.tsx 2>&1 | tail -10` — 0 errors AND 0 warnings on changed files.
- [x] **F5** `cd apps/web && npx tsc --noEmit 2>&1 | grep -v AddCardModal | tail -10` — 0 errors excluding pre-existing AddCardModal.
- [x] **F6** `cd apps/api && python -m pytest tests/ -v --tb=short 2>&1 | tail -10` — 1235+ baseline + 5 new = 1240+. Zero regressions.
- [x] **F7** `cd apps/api && ruff check app/api/routes/auth.py tests/unit/test_auth_cookies.py` — 0 errors.
- [x] **F8** `cd apps/api && ruff format --check app/api/routes/auth.py tests/unit/test_auth_cookies.py` — clean.
- [x] **F9** `git status --short` — expect ONLY:
  - M apps/api/app/api/routes/auth.py
  - ?? apps/api/tests/unit/test_auth_cookies.py
  - M apps/web/src/lib/constants.ts
  - M apps/web/src/middleware.ts
  - M apps/web/src/app/analytics/page.tsx (or whichever analytics file)
  - ?? apps/web/src/__tests__/middleware.admin.test.ts (or sibling test file)
  - ?? openspec/changes/frontend-admin-route-hardening/ (proposal, spec, tasks, verify-report)
- [x] **F10** Save FINAL apply-progress to engram (topic_key: sdd/frontend-admin-route-hardening/apply-progress) with checkbox state + commit suggestion.

<!-- Remediation pass 2026-04-22: FIX-1 (spec drift BAH-1/BAH-5 -> bool), FIX-2 (analytics lint: authFetch deps), FIX-4 (matcher test FAH-5), FIX-5 (FAT-6 strengthened with mockReturnValue pattern). See verify-report #374. -->
