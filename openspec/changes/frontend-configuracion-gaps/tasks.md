# Tasks: frontend-configuracion-gaps

## Phase 1: Batch 1 — CopyOnceModal foundation

- [x] 1.1 Create `apps/web/src/components/ui/CopyOnceModal.tsx` with open/close control, warning copy, clipboard action, and blocked Escape/outside dismissal. AC: AC3.1-AC3.4. DoD: secret visible once, only explicit close path works. Deps: none.
- [x] 1.2 Add `apps/web/src/components/ui/__tests__/CopyOnceModal.test.tsx` for render, `navigator.clipboard.writeText`, transient copied state, and dismissal guards. AC: AC6.1. DoD: unit tests cover copy + restricted dismissal. Deps: 1.1.

## Phase 2: Batch 2 — Dev API keys list + revoke

- [x] 2.1 Create `apps/web/src/components/configuracion/DevApiKeysSection.tsx` to fetch `/api/keys`, render loading/empty/table states, and normalize status/date display. AC: AC1.1-AC1.3. DoD: table shows name/prefix/scopes/created/expires/status with empty and loading states. Deps: none.
- [x] 2.2 Add revoke action in `apps/web/src/components/configuracion/DevApiKeysSection.tsx` using confirm + `DELETE /api/keys/{id}` + toast + optimistic/refetched row update; wire section into `apps/web/src/app/configuracion/page.tsx`. AC: AC1.4-AC1.5. DoD: revoke success/error feedback works from `/configuracion`. Deps: 2.1.
- [x] 2.3 Add `apps/web/src/app/configuracion/__tests__/dev-api-keys.test.tsx` MSW cases for populated list, empty state, revoke success, and revoke failure. AC: AC1.1-AC1.5, AC6.2. DoD: list/revoke flows covered with backend mocks. Deps: 2.2.

## Phase 3: Batch 3 — Dev API keys create + show-once integration

- [x] 3.1 Extend `apps/web/src/components/configuracion/DevApiKeysSection.tsx` with create form/modal for name, scopes, optional expiry, pending state, and 422 field errors via `POST /api/keys`. AC: AC2.1-AC2.4. DoD: creation UI submits with disabled pending button and inline validation. Deps: 2.1.
- [x] 3.2 Integrate `CopyOnceModal` into create success flow so `full_key` is shown once, copied, cleared on explicit close, and list refetched after close. AC: AC2.5, AC3.1-AC3.5. DoD: success opens modal, secret is destroyed on close, list refreshes. Deps: 1.1, 3.1.
- [x] 3.3 Extend `apps/web/src/app/configuracion/__tests__/dev-api-keys.test.tsx` for create success modal, copy feedback, and 422/server-error cases. AC: AC2.1-AC2.5, AC3.1-AC3.5, AC6.2. DoD: creation and show-once regressions are covered by MSW. Deps: 3.2.

## Phase 4: Batch 4 — Sessions list (read-only)

- [x] 4.1 Create `apps/web/src/components/configuracion/SessionsList.tsx` for `/api/auth/sessions` loading/empty/table states, truncated `jti`, note text, and best-effort current-session badge if JWT decode stays lightweight. AC: AC4.1-AC4.5, AC5.1-AC5.2. DoD: read-only sessions UI renders above logout-all without adding revoke-per-session. Deps: none.
- [x] 4.2 Wire `SessionsList` into `apps/web/src/app/configuracion/page.tsx` above `data-testid="logout-all-btn"`; add `apps/web/src/app/configuracion/__tests__/sessions-list.test.tsx` for populated, empty, and error states. AC: AC4.1-AC4.5, AC6.3. DoD: perfil tab preserves logout-all flow and sessions tests pass. Deps: 4.1.

## Phase 5: Batch 5 — Verification

- [x] 5.1 Run targeted test files, `tsc`, and eslint on changed files; update `openspec/changes/frontend-configuracion-gaps/tasks.md` checkboxes during implementation. AC: AC6.1-AC6.3, DoD checklist. DoD: no new TypeScript/ESLint errors and changed flows verified. Deps: 1.2, 2.3, 3.3, 4.2.

## Remediation batch — 2026-04-22

- [x] R1 — `DevApiKeysSection.tsx`: parse FastAPI array 422 detail → field-level `fieldErrors` state; render inline below name input (`data-testid="create-error-name"`); keep string-detail fallback in shared alert; add `aria-busy={creating}` to submit button. New test: "shows field-level 422 error next to the name input when detail is an array".
- [x] R2 — `SessionsList.tsx`: fix `truncateJti` to `jti.slice(0, 8) + '...'` (was `first8…last4`); fix badge text from "Actual" to "Sesión actual". New tests: jti format assertion + badge text assertion.
- [x] R3 — `DevApiKeysSection.tsx`: align copy — revoke toast "Clave revocada" (was "Clave revocada correctamente"); empty-state "No tenés claves creadas todavía" (was "Sin claves de API"). Updated existing toast test assertion accordingly.
- [x] R4 — `tasks.md`: all original task checkboxes marked `[x]`; this remediation section appended.
