# Tasks: Frontend Historial Folder Actions

## Phase 1: Inline Rename UI

- [x] 1.1 Add rename state and edit-session guards in `apps/web/src/app/historial/page.tsx`. Files: same. AC IDs: FE-FOLDER-RENAME-UI-2, UI-3, UI-5, UI-8. DoD: only one folder can enter edit mode, original name is preserved, and focus lands in the inline input. Dependencies: none.
- [x] 1.2 Render the folder inline editor and hover `Edit2` action in `apps/web/src/app/historial/page.tsx`. Files: same. AC IDs: FE-FOLDER-RENAME-UI-1, UI-2, UI-3, UI-4, UI-5, UI-6, UI-7. DoD: hover reveals pencil, edit mode swaps label for `aria-label="Renombrar carpeta"` input, Enter/Escape/blur are wired, and pending save disables the input and hides the icon. Dependencies: 1.1.

## Phase 2: Rename Request + Optimistic Flow

- [x] 2.1 Implement `handleRenameFolder` in `apps/web/src/app/historial/page.tsx` with trim-first validation and optimistic local folder updates before `authFetch(PUT /api/folders/{id})`. Files: same. AC IDs: FE-FOLDER-RENAME-VALIDATION-1, VALIDATION-2, VALIDATION-3, VALIDATION-4, FE-FOLDER-RENAME-NETWORK-1, NETWORK-2. DoD: empty or unchanged names cancel without a request; valid names update local state immediately. Dependencies: 1.1.
- [x] 2.2 Complete success/error handling in `apps/web/src/app/historial/page.tsx`: keep optimistic state on 200/204, revert on 409/other failures, show `sonner` toasts, and log technical errors only in dev. Files: same. AC IDs: FE-FOLDER-RENAME-NETWORK-3, NETWORK-4, NETWORK-5, NETWORK-6, FE-FOLDER-RENAME-NFR-1. DoD: success/conflict/generic paths behave correctly and existing create/delete/move folder flows still work. Dependencies: 2.1.

## Phase 3: Integration Tests + Verification

- [x] 3.1 Add `apps/web/src/app/historial/__tests__/folders.test.tsx` with the Historial page render harness, mocked auth/layout/router/image modules, and MSW handlers for initial folder loads plus `PUT /api/folders/:id`. Files: `apps/web/src/app/historial/__tests__/folders.test.tsx`, `apps/web/src/test/msw/handlers.ts` (only if shared defaults are needed). AC IDs: FE-FOLDER-RENAME-TESTS-1, TESTS-2, TESTS-4. DoD: tests can mount the page and override rename responses per scenario. Dependencies: 1.2, 2.2.
- [x] 3.2 Cover the six rename scenarios in `apps/web/src/app/historial/__tests__/folders.test.tsx`: Enter success, blur success, 409 revert, generic error revert, Escape cancel, and whitespace cancel. Files: same. AC IDs: FE-FOLDER-RENAME-UI-4, UI-5, UI-6, FE-FOLDER-RENAME-VALIDATION-2, FE-FOLDER-RENAME-NETWORK-1, NETWORK-3, NETWORK-4, NETWORK-5, FE-FOLDER-RENAME-TESTS-3. DoD: all matrix cases pass with toast assertions and explicit no-network assertions where required. Dependencies: 3.1.
- [x] 3.3 Run `pnpm --filter web test`, targeted `tsc` on changed files, and `eslint` on changed files; capture any unchanged baseline failures separately. Files: changed frontend files only. AC IDs: FE-FOLDER-RENAME-NFR-1. DoD: rename coverage passes and no new lint/type regressions are introduced by this change. Dependencies: 3.2.

## Remediation (post-verify)

- [x] R1 Fix cancel-then-switch: `pendingRenameSwitch` ref guards blur from committing when another folder's pencil is clicked (FE-FOLDER-RENAME-UI-8). Files: `apps/web/src/app/historial/page.tsx`.
- [x] R2 Update tasks.md checkboxes: all 7 original tasks marked complete.
- [x] R3 Add cross-folder switch test (test 7): two folders, click A pencil → type → click B pencil → assert A cancelled (no PUT), B in edit mode. Files: `apps/web/src/app/historial/__tests__/folders.test.tsx`.
