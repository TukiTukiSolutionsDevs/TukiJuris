# Proposal: frontend-fix-critical-bugs

## Intent

Closes gaps C1 (silent broken feature) and C3 (dead code with security risk) from `frontend-coverage-audit`.
Backend-change-password-endpoint just shipped (55998f5) — the page's existing call will start working but with awful UX (generic errors, silent logout 15min later). This change fixes both issues by improving the UX flow, error mapping, and cleaning up dead code.

## Scope

### In Scope
- Force immediate logout after successful password change.
- Map specific error codes to user-friendly Spanish messages.
- Hide password change section for OAuth users (proactive UI).
- Delete `apps/web/src/lib/api.ts` completely.
- Add Vitest test file for the change-password functionality.
- Update MSW handlers with a default success handler for the endpoint.

### Out of Scope
- Refresh flow / token rotation (Sprint 3)
- Notifications feature (Sprint 2)
- Admin route hardening (Sprint 2)
- BYOK / sessions UI (Sprint 4)

## Capabilities

### New Capabilities
None

### Modified Capabilities
- `user-settings`: Update password change flow with specific error messages, OAuth handling, and forced immediate logout.

## Approach

**D1 — Session-revocation UX**: Force immediate logout after successful password change. Show a toast `"Contraseña actualizada. Por seguridad, iniciá sesión de nuevo."`, wait ~1.5s, then call the existing `logout()` function from `AuthContext` to redirect to `/login`.
**D2 — Error code mapping**: Switch on `res.status` and `data.detail` to show specific Spanish messages for 400 (OAuth unsupported, same password), 401 (invalid credentials, expired token), 422 (validation errors), and 429 (rate limiting).
**D3 — OAuth proactive UI**: Hide the "Cambiar contraseña" section when `profile.auth_provider !== 'email'`. Show a notice card: `"Tu cuenta usa inicio de sesión con {provider}. La contraseña se gestiona en {provider}."`
**D4 — lib/api.ts deletion**: `git rm apps/web/src/lib/api.ts` entirely. It has 0 callers and 0 re-exports.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/web/src/app/configuracion/page.tsx` | Modified | Add error-code mapping, force immediate logout, hide section for OAuth users |
| `apps/web/src/lib/api.ts` | Removed | Entire file deleted |
| `apps/web/src/app/configuracion/__tests__/change-password.test.tsx` | New | Vitest test file (covers 6 paths) |
| `apps/web/src/test/msw/handlers.ts` | Modified | Add default POST `/api/auth/change-password` mock and error factory |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Forced logout surprises users mid-session | Low | 1.5s toast read time + clear copy ("por seguridad") |
| AuthContext logout fails during network calls | Low | Use `try { await logout() } finally { router.push('/login') }` to ensure redirect |
| `auth_provider` missing from profile | Low | Fall back to reactive 400 handling (D2 row) |
| Deleting `lib/api.ts` breaks build | Low | Run `npx tsc --noEmit` after delete to catch silent references |

## Rollback Plan

Revert the commit changing `configuracion/page.tsx` and restoring `lib/api.ts`.

## Dependencies

- Backend endpoint `POST /api/auth/change-password` is already shipped (commit 55998f5).

## Success Criteria

- [ ] Submitting valid form → 204 → toast → logout invoked → user lands on `/login`
- [ ] Wrong current password → inline Spanish message, form NOT reset, no logout
- [ ] Weak new password → 422 Spanish message visible
- [ ] new == current → 400 Spanish message visible
- [ ] OAuth user (`auth_provider != 'email'`) → password section hidden, info card shown instead
- [ ] Rate-limited → 429 Spanish message visible
- [ ] `apps/web/src/lib/api.ts` does not exist anymore
- [ ] No file imports `@/lib/api` (root) — only sub-paths like `@/lib/api/trial` remain
- [ ] All Vitest tests pass: `cd apps/web && npm test` — 6+ new tests for change-password + no regressions
- [ ] `cd apps/web && npm run lint` — 0 errors
- [ ] `cd apps/web && npx tsc --noEmit` — 0 errors
