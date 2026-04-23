# Tasks: frontend-uploads-list

## Phase 1: Backend route

- [x] 1.1 **BE-UPLOAD-LIST route + schema**
  - Desc: Add `UploadedDocumentListItem` and `GET /api/upload/` with Bearer auth, `RateLimitBucket.READ`, `created_at DESC`, and explicit mapping that omits private fields.
  - Files: `apps/api/app/api/routes/upload.py`
  - AC: `BE-UPLOAD-LIST`
  - DoD: 200 returns only `id, filename, file_type, file_size, page_count, conversation_id, created_at`; empty users get `[]`.
  - Deps: None

- [x] 1.2 **BE-UPLOAD-LIST integration tests**
  - Desc: Add pytest coverage for populated list, empty list, and privacy exclusion using existing tenant fixtures.
  - Files: `apps/api/tests/integration/test_upload.py`
  - AC: `BE-UPLOAD-LIST`, `FE-UPLOADS-TESTS`
  - DoD: Tests assert newest-first order, `[]` on empty, and strict absence of `storage_path` / `extracted_text`.
  - Deps: `1.1`

## Phase 2: Frontend Archivos tab

- [x] 2.1 **FE-UPLOADS-TAB navigation + lazy fetch states**
  - Desc: Extend `ActiveTab` and tab metadata with 6th-position `archivos`; add lazy-load, retry, loading, empty, and error state wiring inside the `DisclosureCard` flow.
  - Files: `apps/web/src/app/configuracion/page.tsx`
  - AC: `FE-UPLOADS-TAB`
  - DoD: Fetch runs only after tab activation; UI shows 3 skeleton rows, retry CTA, and required Spanish empty/error copy.
  - Deps: `1.1`

- [x] 2.2 **FE-UPLOADS-TABLE rendering + formatter helper**
  - Desc: Render uploads table with truncated filename, uppercase file-type badge, `DD/MM/YYYY` date formatting, no download action, and shared `formatFileSize` helper.
  - Files: `apps/web/src/app/configuracion/page.tsx`, `apps/web/src/app/configuracion/uploads-formatters.ts`
  - AC: `FE-UPLOADS-TABLE`
  - DoD: Table columns and formatting match spec for bytes / KB / MB boundaries and newest-first rows.
  - Deps: `2.1`

- [x] 2.3 **FE-UPLOADS-DELETE optimistic flow**
  - Desc: Add `Eliminar` action with native confirm dialog, optimistic row removal, inflight disable + `aria-busy`, rollback on failure, and success/error toasts.
  - Files: `apps/web/src/app/configuracion/page.tsx`
  - AC: `FE-UPLOADS-DELETE`
  - DoD: Cancel leaves state unchanged; success persists removal and toast; failure restores row and shows error toast.
  - Deps: `2.2`

## Phase 3: Verification

- [x] 3.1 **Frontend tests for tab, delete flow, and formatter**
  - Desc: Add MSW + AuthContext integration coverage for lazy-load, populated/empty/error states, delete success/failure/cancel, plus unit tests for formatter edges.
  - Files: `apps/web/src/app/configuracion/__tests__/uploads-tab.test.tsx`, `apps/web/src/app/configuracion/__tests__/uploads-formatters.test.ts`
  - AC: `FE-UPLOADS-TAB`, `FE-UPLOADS-TABLE`, `FE-UPLOADS-DELETE`, `FE-UPLOADS-TESTS`
  - DoD: New tests pass without changing pre-existing unrelated failures.
  - Deps: `2.3`

- [x] 3.2 **Cross-stack verification + baseline check**
  - Desc: Run targeted pytest, `pnpm --filter web test`, `tsc`, and eslint for changed files; confirm backend and frontend baseline pass/fail counts stay unchanged outside this change.
  - Files: `apps/api/tests/integration/test_upload.py`, `apps/web/src/app/configuracion/page.tsx`, `apps/web/src/app/configuracion/uploads-formatters.ts`, `apps/web/src/app/configuracion/__tests__/uploads-*`
  - AC: `FE-UPLOADS-TESTS`
  - DoD: Evidence captured for BE `1255 pass / 7 xfail` and FE `~451 total / ~436 pass / 15 pre-existing fail` baselines.
  - Deps: `1.2`, `3.1`

## Remediation (2026-04-23)

- [x] R1 — CRITICAL: `formatFileSize` changed from `"N B"` to `"N bytes"` for values < 1024. Formatter tests updated to match.
- [x] R2 — CRITICAL: TS errors in `uploads-tab.test.tsx` fixed. Added `UploadFixture` type to fix TS2322; replaced typed destructuring in filter callbacks with `args[0] as string` to fix TS2769 × 3. `tsc --noEmit` now clean on changed files.
- [x] R3 — WARN: Added exact-string assertions: `"Todavía no subiste ningún archivo."` (AT-3), `"No se pudieron cargar los archivos."` + `getByRole("button", { name: /reintentar/i })` (AT-4), `confirmSpy` called with exact dialog string including filename (AT-6 + AT-7).
- [x] R4 — WARN: Added AT-9 (retry refetch: error → success, asserts table renders). aria-busy assertion deferred — optimistic removal removes the row before `deletingUploadId` can be observed on the button; not testable via integration test without changing the UX pattern.
- [x] R5 — WARN: All 6 task checkboxes marked `[x]`. Remediation section appended.
- [x] R6 — WARN: Apply-progress in engram corrected to 9 integration + 6 formatter = 15 total tests (AT-9 added in remediation).
