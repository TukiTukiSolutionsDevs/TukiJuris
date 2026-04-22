# Tasks — frontend-fix-critical-bugs

## Batch A — Testing infra (lay the foundation first; tests can fail until B/C done)
- [x] **A1** Add default `POST /api/auth/change-password` → `204 No Content` handler to `apps/web/src/test/msw/handlers.ts`. (FCB-14)
- [x] **A2** Export `authHandlers.changePasswordError(detail, status)` factory in the same file. (FCB-15)
- [x] **A3** Verify MSW infra still loads: `cd apps/web && npx tsc --noEmit -p tsconfig.json` — 0 errors. (NFR confirmation)

## Batch B — Error mapping + forced logout in handleChangePassword
Edit ONLY `apps/web/src/app/configuracion/page.tsx`. Locate `handleChangePassword` (~line 461).

- [x] **B1** Extract a pure helper `mapChangePasswordError(status: number, detail: unknown): string` co-located in the same file (or alongside the page) implementing the FCB-1..FCB-6 mapping. Use a switch on `status` first, then narrow on `detail` shape. Document the contract via inline comments referencing FCB IDs. (FCB-1..FCB-6)
- [x] **B2** Replace the current generic error handling in the catch path with `setError(mapChangePasswordError(res.status, data))` (or equivalent). (FCB-1..FCB-6)
- [x] **B3** On `res.ok` (204) success, replace existing success behavior with: show success toast "Contraseña actualizada. Por seguridad, iniciá sesión de nuevo." (FCB-7). Use the existing toast/notification mechanism — explore step found it.
- [x] **B4** After 1500 ms, invoke AuthContext `logout()` then `router.push('/login')`. Wrap in `try { await logout() } finally { router.push('/login') }` to satisfy FCB-8 + R2.
- [x] **B5** Clear form state (currentPassword + newPassword) immediately after the toast appears. (FCB-9)

## Batch C — OAuth proactive UI
- [x] **C1** Identify how the page already accesses the user profile (likely AuthContext or a dedicated hook — confirm by reading the page imports). Report the exact source.
- [x] **C2** Conditionally hide the "Cambiar contraseña" form section when `profile.auth_provider !== 'email'` (use the actual local-auth marker; confirm by reading the User type in `lib/auth` or backend schema). Render an info card instead with copy: "Tu cuenta usa inicio de sesión con {provider}. La contraseña se gestiona en {provider}." (FCB-10)
- [x] **C3** If `profile.auth_provider` is undefined / loading, default to showing the form (rely on FCB-2 reactive handling). (FCB-11)

## Batch D — Dead-code cleanup
- [x] **D1** Run `rg -l "from .*['\"]@/lib/api['\"]" apps/web/src apps/web/src/app` to confirm 0 root-level importers. (Pre-deletion safety check.)
- [x] **D2** Delete `apps/web/src/lib/api.ts`: `git rm apps/web/src/lib/api.ts`. (FCB-12)
- [x] **D3** Run `cd apps/web && npx tsc --noEmit` — 0 errors. (FCB-13)

## Batch E — Tests
Test file: `apps/web/src/app/configuracion/__tests__/change-password.test.tsx`. Pattern: read `apps/web/src/app/configuracion/__tests__/logout-all.test.tsx` first.

- [x] **E1** FCT-1: Success → toast + logout invoked + router.push('/login'). Use vi.useFakeTimers() to advance the 1500 ms.
- [x] **E2** FCT-2: Wrong current password (401 invalid_credentials) → Spanish error visible, form NOT reset, logout NOT called.
- [x] **E3** FCT-3: OAuth user error (400 oauth_password_unsupported, auth_provider=microsoft) → "(microsoft)" interpolated in the error.
- [x] **E4** FCT-4: new == current (400 new_password_same_as_current) → Spanish error.
- [x] **E5** FCT-5: Weak new (422 with verbatim Spanish validator message) → message shown verbatim.
- [x] **E6** FCT-6: Rate-limit (429) → Spanish "demasiados intentos" copy.
- [x] **E7** FCT-7: profile.auth_provider="microsoft" → password section NOT in DOM; info card visible.
- [x] **E8** FCT-8: logout rejects but router.push('/login') still called (mock logout to throw).

## Batch F — Validation
- [x] **F1** `cd apps/web && npm test -- src/app/configuracion/__tests__/change-password.test.tsx` — all 8 tests green.
- [x] **F2** `cd apps/web && npm test` — full suite. Goal: existing 95+ tests still pass + 8 new = 103+. Zero regressions.
- [x] **F3** `cd apps/web && npm run lint` — 0 errors.
- [x] **F4** `cd apps/web && npx tsc --noEmit` — 0 errors.
- [x] **F5** `git status --short apps/web/` — expect:
  - modified: `apps/web/src/app/configuracion/page.tsx`
  - modified: `apps/web/src/test/msw/handlers.ts`
  - deleted: `apps/web/src/lib/api.ts`
  - new: `apps/web/src/app/configuracion/__tests__/change-password.test.tsx`
  - NOTHING ELSE outside this set.
- [x] **F6** Save FINAL apply-progress to engram (`topic_key: sdd/frontend-fix-critical-bugs/apply-progress`).

<!-- Remediation pass 2026-04-22: FIX-1 (FCT-9 for FCB-6 — added test + fixed page.tsx setTimeout+redirect), FIX-2 (FCT-1 form-reset assertion for FCB-9), FIX-3 (tasks.md synced), FIX-4 (lint warnings inspected). See verify-report #364. -->
