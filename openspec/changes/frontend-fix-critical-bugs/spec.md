# Spec — frontend-fix-critical-bugs

## 1. Scope summary
Two surfaces:
- **C1 surface**: `apps/web/src/app/configuracion/page.tsx` `handleChangePassword` handler (lines ~461–491) and surrounding UI for the password section.
- **C3 surface**: `apps/web/src/lib/api.ts` (entire file deletion) + verification that no consumer imports break.

Plus testing infra:
- `apps/web/src/test/msw/handlers.ts` (default success mock + error factory)
- `apps/web/src/app/configuracion/__tests__/change-password.test.tsx` (new test file)

## 2. Behavioral requirements (FCB-* SHALL statements)

### Error mapping (D2)
- **FCB-1**: When the backend returns `401` with detail `"invalid_credentials"`, the UI SHALL display "La contraseña actual es incorrecta." in the form's error region. The form fields SHALL NOT be reset. No logout SHALL be triggered.
- **FCB-2**: When the backend returns `400` with detail `{ code: "oauth_password_unsupported", auth_provider: "<provider>" }`, the UI SHALL display "Tu cuenta usa inicio de sesión social ({provider}). No se puede cambiar contraseña aquí." (with `{provider}` interpolated).
- **FCB-3**: When the backend returns `400` with detail `"new_password_same_as_current"`, the UI SHALL display "La nueva contraseña debe ser distinta a la actual."
- **FCB-4**: When the backend returns `422`, the UI SHALL display the validator's message verbatim if present; else fallback "La nueva contraseña no cumple los requisitos."
- **FCB-5**: When the backend returns `429`, the UI SHALL display "Demasiados intentos. Esperá un momento e intentá de nuevo."
- **FCB-6**: When the backend returns `401` with NO detail (or `"token_expired"`), the UI SHALL display "Tu sesión expiró. Iniciá sesión de nuevo." and trigger the logout flow.

### Success path (D1 — forced logout)
- **FCB-7**: When the backend returns `204`, the UI SHALL show a toast "Contraseña actualizada. Por seguridad, iniciá sesión de nuevo." with at least 1500 ms visibility.
- **FCB-8**: ~1500 ms after the toast appears, the UI SHALL invoke the AuthContext `logout()` function. If `logout()` rejects, the UI SHALL still navigate to `/login` (use `try/finally`).
- **FCB-9**: Form inputs SHALL be cleared after the toast appears (cosmetic; the user is leaving the page anyway).

### OAuth proactive UI (D3)
- **FCB-10**: When the loaded user profile has `auth_provider !== 'email'` (or whatever the local-auth marker is — applier confirms during exploration), the UI SHALL hide the "Cambiar contraseña" form section entirely and SHALL render an info card: "Tu cuenta usa inicio de sesión con {provider}. La contraseña se gestiona en {provider}."
- **FCB-11**: If `auth_provider` is unavailable on the profile (legacy / loading), the UI SHALL show the form by default and rely on the reactive 400 handler (FCB-2) to surface the error after submit.

### Cleanup (D4)
- **FCB-12**: The file `apps/web/src/lib/api.ts` SHALL be deleted from the repository.
- **FCB-13**: After deletion, `cd apps/web && npx tsc --noEmit` SHALL succeed with 0 errors. ESLint SHALL also pass.

### Testing infra (D2/D3 enablement)
- **FCB-14**: `apps/web/src/test/msw/handlers.ts` SHALL register a default `POST /api/auth/change-password` handler returning `204 No Content`.
- **FCB-15**: `apps/web/src/test/msw/handlers.ts` SHALL export an `authHandlers.changePasswordError(detail, status)` factory (or equivalent) for per-test overrides.

## 3. Test matrix (FCT-* — Vitest + Testing Library + MSW)

Test file: `apps/web/src/app/configuracion/__tests__/change-password.test.tsx`

| ID    | Test case                                       | Setup (MSW handler / state)                                  | Expected                                                                 |
|-------|-------------------------------------------------|--------------------------------------------------------------|--------------------------------------------------------------------------|
| FCT-1 | Success → toast + logout                        | Default 204                                                  | Toast visible with success copy; after 1500ms `logout()` mock called once; redirect to /login |
| FCT-2 | Wrong current password (401 invalid_credentials)| `changePasswordError("invalid_credentials", 401)`            | Error region shows "La contraseña actual es incorrecta."; form NOT reset; logout NOT called |
| FCT-3 | OAuth user error (400 oauth_password_unsupported)| `changePasswordError({code, auth_provider:"microsoft"}, 400)`| Error region interpolates "(microsoft)" string                            |
| FCT-4 | new == current (400 new_password_same_as_current)| `changePasswordError("new_password_same_as_current", 400)`   | Error region shows "La nueva contraseña debe ser distinta a la actual."   |
| FCT-5 | Weak new (422)                                  | `changePasswordError("Mínimo 8 caracteres", 422)`            | Error region shows the verbatim validator message                         |
| FCT-6 | Rate-limit (429)                                | `changePasswordError(null, 429)`                             | Error region shows "Demasiados intentos. Esperá un momento e intentá de nuevo." |
| FCT-7 | OAuth profile hides section                     | profile.auth_provider="microsoft"                            | Password section NOT rendered; info card text "gestionada en microsoft" visible |
| FCT-8 | logout failure during success path              | Default 204; mock logout to throw                            | Despite `logout()` rejection, router.push('/login') is called             |

## 4. Non-functional requirements
- **FCB-NFR-1**: All UI strings SHALL be in Spanish (es-419 / Argentine).
- **FCB-NFR-2**: NO new dependencies. NO new fetcher abstractions.
- **FCB-NFR-3**: NO modifications to `apps/web/src/lib/auth.ts` (refresh flow lives in Sprint 3).
- **FCB-NFR-4**: NO modifications to sidebars, notifications, middleware, or any non-listed file.
- **FCB-NFR-5**: After the change, `cd apps/web && npm test && npm run lint && npx tsc --noEmit` MUST all pass.

## 5. Out of scope
- Refresh-token flow / token rotation (Sprint 3 `frontend-auth-refresh-flow`).
- Notifications page or bell-icon fixes (Sprint 2).
- Admin route hardening (Sprint 2).
- BYOK / sessions / RBAC UI (Sprint 4 `frontend-high-gaps`).
- Aside / sidebar audit cleanup.
- i18n abstraction for the new strings.

## 6. References
- Proposal: `openspec/changes/frontend-fix-critical-bugs/proposal.md` + engram obs #358
- Explore: engram topic `sdd/frontend-fix-critical-bugs/explore`
- Backend contract: commit 55998f5 + `openspec/changes/backend-change-password-endpoint/spec.md`
- MSW handler pattern: `apps/web/src/test/msw/handlers.ts`
- Test pattern reference: `apps/web/src/app/configuracion/__tests__/logout-all.test.tsx`