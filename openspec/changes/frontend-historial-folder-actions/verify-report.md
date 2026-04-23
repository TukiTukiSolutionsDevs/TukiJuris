# Verification Report

**Change**: frontend-historial-folder-actions  
**Mode**: Standard  
**Date**: 2026-04-22

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 7 |
| Tasks complete | 0 |
| Tasks incomplete | 7 |

`openspec/changes/frontend-historial-folder-actions/tasks.md` still has every checkbox unchecked, but the implementation evidence in `apps/web/src/app/historial/page.tsx`, `apps/web/src/app/historial/__tests__/folders.test.tsx`, and the apply-progress artifact shows the planned work was executed. This is task-artifact drift, not proof that the code is missing.

---

## Build & Tests Execution

**Targeted rename tests**: ✅ 6 passed / 0 failed  
Command: `npm test -- src/app/historial/__tests__/folders.test.tsx`

**Full web suite**: ✅ Baseline preserved  
Command: `npm test`
- Result: 268 passed / 15 failed / 0 skipped
- The 15 failures are the same pre-existing auth/onboarding redirect failures already called out in the verification brief.

**TypeScript**: ✅ No new changed-file errors  
Command: `npm exec tsc -- --noEmit --pretty false`
- Output only reports the excluded baseline error:
  - `src/components/trials/AddCardModal.tsx(25,48): error TS2554: Expected 2 arguments, but got 3.`

**ESLint**: ✅ No new changed-hunk warnings or errors  
Command: `npm exec eslint -- "src/app/historial/page.tsx" "src/app/historial/__tests__/folders.test.tsx"`
- Result: 0 errors / 3 warnings
- All 3 warnings are pre-existing `react-hooks/exhaustive-deps` warnings at `src/app/historial/page.tsx:165,176,187`, outside the rename diff hunks.

**Coverage**: ➖ Not run (no threshold/config required for this change)

---

## Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| FE-FOLDER-RENAME-UI | Click rename icon enters inline edit with focused `aria-label="Renombrar carpeta"` input | `src/app/historial/__tests__/folders.test.tsx > openRenameInput` + all 6 tests | ✅ COMPLIANT |
| FE-FOLDER-RENAME-UI | Enter commits rename | `src/app/historial/__tests__/folders.test.tsx > Enter commits → server 200 → toast success → name updated in sidebar` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-UI | Escape cancels rename | `src/app/historial/__tests__/folders.test.tsx > Escape exits edit mode without firing PUT, name unchanged` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-UI | Blur commits rename | `src/app/historial/__tests__/folders.test.tsx > blur triggers same commit path → server 200 → toast success` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-UI | Clicking a different folder pencil cancels current edit and switches | (none; static evidence in `src/app/historial/page.tsx:558-559,584-588` shows blur commits instead of canceling) | ❌ FAILING |
| FE-FOLDER-RENAME-VALIDATION | Trimmed empty/whitespace input cancels without network call | `src/app/historial/__tests__/folders.test.tsx > clearing input and pressing Enter cancels without firing PUT` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-VALIDATION | Unchanged trimmed name cancels without network call | Static evidence: `src/app/historial/page.tsx:433-440` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-NETWORK | PUT `/api/folders/{id}` via `authFetch` with `{ name }` body | Static evidence: `src/app/historial/page.tsx:449-452` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-NETWORK | Optimistic update happens before request resolves | Static evidence: `src/app/historial/page.tsx:442-446` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-NETWORK | 200/204 keeps optimistic state and shows success toast | `src/app/historial/__tests__/folders.test.tsx > Enter commits...`; `src/app/historial/__tests__/folders.test.tsx > blur triggers same commit path...` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-NETWORK | 409 reverts and shows duplicate-name toast | `src/app/historial/__tests__/folders.test.tsx > 409 → error toast 'Ya existe...' → name reverted to original` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-NETWORK | 400/500/network errors revert and show generic toast | `src/app/historial/__tests__/folders.test.tsx > 500 → error toast 'No se pudo...' → name reverted to original` + static catch path `src/app/historial/page.tsx:473-480` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-NETWORK | Dev-only `console.error` for technical failures | Static evidence: `src/app/historial/page.tsx:461-470,478-479` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-TESTS | New integration file with 6 rename tests exists and passes | `src/app/historial/__tests__/folders.test.tsx` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-TESTS | `/api/folders/*` handled with MSW | `src/app/historial/__tests__/folders.test.tsx:110-115,192-196,225-228,259-263,294-298` | ✅ COMPLIANT |
| FE-FOLDER-RENAME-NFR | No new changed-file TS/lint regressions; page not extracted; folder create/delete/move handlers still present | test + tsc + eslint + diff evidence | ✅ COMPLIANT |

**Compliance summary**: 15 compliant / 1 failing

---

## Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| FE-FOLDER-RENAME-UI | ❌ Partial implementation | Hover rename button, inline input, Enter/Escape/blur wiring, saving disable state, and single-edit-by-state are present; however the “switch folders while editing” rule is not implemented as specified because blur commits instead of canceling. |
| FE-FOLDER-RENAME-VALIDATION | ✅ Implemented | `handleRenameFolder` trims first and exits early for empty or unchanged names without issuing `authFetch`. |
| FE-FOLDER-RENAME-NETWORK | ✅ Implemented | Uses `authFetch(PUT /api/folders/{id})`, updates local folder state optimistically, preserves success state, reverts on 409/other failures, and logs technical errors in development. |
| FE-FOLDER-RENAME-TESTS | ✅ Implemented with one gap | The requested 6 MSW integration tests exist and pass, but there is no regression test for the required folder-switch cancellation behavior. |
| FE-FOLDER-RENAME-NFR | ✅ Implemented with caveat | No new changed-hunk TS/lint regressions were introduced; create/delete/move handlers remain in place; no new folder component was extracted. |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Keep implementation inline in `page.tsx` | ✅ Yes | Rename logic and JSX remain in the existing monolith page. |
| Introduce `sonner` for rename success/error surfacing | ✅ Yes | `toast.success` / `toast.error` added only for rename flow. |
| Preserve existing create/delete/move flows | ✅ Yes | Existing handlers remain present and unchanged in the diff. |
| Single-edit switch should cancel current edit before switching | ⚠️ Deviated | Current blur path commits current rename instead of canceling before opening the next folder. |
| Separate design artifact | ➖ N/A | No standalone `design.md` exists for this change; verification used spec, tasks, proposal, explore, and apply-progress. |

---

## Issues Found

### CRITICAL

1. **Switching from one folder rename to another does not follow the spec; it commits on blur instead of canceling the current edit before switching.**  
   Evidence: `apps/web/src/app/historial/page.tsx:558-559` calls `handleRenameFolder()` on input blur whenever `folderRenameSaving` is false. The other folder's rename button only sets the new edit target at `apps/web/src/app/historial/page.tsx:584-588`; there is no cancellation path for the current edit. This contradicts FE-FOLDER-RENAME-UI-8.

### WARNING

1. **The tasks artifact was not updated, so task completion cannot be inferred from `tasks.md` alone.**  
   Evidence: `openspec/changes/frontend-historial-folder-actions/tasks.md:5-17` leaves all 7 tasks unchecked even though code/test/apply-progress evidence shows the work was performed.

2. **There is no automated regression test for the required “switch to another folder while editing” behavior, which is why the spec gap escaped the current 6-test suite.**  
   Evidence: `apps/web/src/app/historial/__tests__/folders.test.tsx:139-318` covers Enter success, blur success, 409, 500, Escape, and empty input, but no scenario exercises clicking a second folder rename action while the first input is active.

### SUGGESTION

1. After remediation, add one integration test with two folders that verifies clicking the second pencil cancels the first edit and opens the second input without firing the first rename request.

---

## Verdict

**FAIL**

The rename flow is MOSTLY correct: the 6 requested integration tests pass, optimistic/error behavior is in place, and no new changed-file quality regressions were introduced. BUT the UI still misses one explicit spec requirement: switching to another folder while editing commits instead of canceling. Remediate that gap before shipping.
