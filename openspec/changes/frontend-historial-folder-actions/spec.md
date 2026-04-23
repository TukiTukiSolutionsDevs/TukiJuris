# Specification: Frontend Historial Folder Actions

## Goal
Implement inline folder renaming functionality on the `/historial` page to close the H7 audit gap. Provide a smooth UX with optimistic updates, proper validation, and error surfacing, mirroring the existing tags inline edit pattern.

## Scope
### In Scope
- Inline renaming of existing folders in the Historial sidebar.
- Client-side validation for empty/unchanged names.
- Optimistic UI updates with revert on error.
- Server error handling and toast notifications (`sonner`).
- MSW integration tests for rename paths.

### Out of Scope
- Expanding scope to folder create, delete, or move (already implemented).
- Refactoring existing action handlers to use toasts/optimistic UI (except rename).
- Extracting `FolderSidebarItem` into a separate component.
- Fixing pre-existing `AddCardModal.tsx` tsc errors.

## Requirements

### FE-FOLDER-RENAME-UI — Inline edit UX
1. Hovering a folder row MUST reveal a pencil/Edit2 icon.
2. Clicking the icon MUST change the folder label into an `<input>` in edit mode.
3. The input MUST have `aria-label="Renombrar carpeta"` and auto-focus upon entering edit mode.
4. Pressing the `Enter` key MUST commit the rename.
5. Pressing the `Escape` key MUST cancel the rename (revert to original name, exit edit mode).
6. A `blur` event on the input MUST commit the rename (following the same path as Enter).
7. While committing, the input MUST be `disabled` and the edit icon hidden.
8. Only ONE folder CAN be in edit mode at a time (clicking a different folder's pencil MUST cancel the current edit and switch).

### FE-FOLDER-RENAME-VALIDATION — Client-side validation
1. The system MUST trim the folder name client-side before submitting.
2. If the trimmed name is empty, the system MUST cancel the edit (treat as Escape, no network call).
3. If the trimmed name is unchanged from the original, the system MUST cancel the edit (no-op, no network call).
4. The system MUST NOT validate length or uniqueness client-side (let the server enforce these rules).

### FE-FOLDER-RENAME-NETWORK — API call
1. The system MUST call `PUT /api/folders/{id}` with a `{ name: string }` JSON body via `authFetch`.
2. The UI MUST update optimistically, changing the local folder list state immediately with the new name (before the fetch resolves).
3. On 200/204 success: The system MUST keep the optimistic state and show a success toast "Carpeta renombrada" using `sonner`.
4. On 409 Conflict: The system MUST revert the local state to the original name and show an error toast "Ya existe una carpeta con ese nombre".
5. On any other non-ok response (400, 500, network fail): The system MUST revert the local state and show an error toast "No se pudo renombrar la carpeta".
6. The system MUST log the technical error to `console.error` in dev mode for non-ok responses.

### FE-FOLDER-RENAME-TESTS — Test coverage
1. The system MUST include a new integration test file in `apps/web/src/app/historial/__tests__/folders.test.tsx`.
2. The tests MUST mock the `/api/folders/*` endpoints using MSW.
3. The tests MUST cover the integration cases specified in the test matrix.
4. The tests MUST follow the render pattern used by other page integration tests (AuthContext wrapper, MSW setup).

## Definition of Done
- [ ] Users can click an Edit icon on a folder to enter rename mode.
- [ ] Enter and blur commit the rename, Escape cancels.
- [ ] Validation correctly handles empty and unchanged states.
- [ ] UI updates optimistically.
- [ ] Success shows a success toast.
- [ ] 409 Conflict reverts UI and shows "Ya existe..." error toast.
- [ ] Other errors revert UI and show generic error toast.
- [ ] No new tsc errors or eslint warnings on changed files.
- [ ] Existing folder create/delete/move behavior remains functional.
- [ ] All ACs covered by MSW integration tests passing.

## Test Matrix

| Test File | AC IDs | Scenario |
|-----------|---------|----------|
| `folders.test.tsx` | FE-FOLDER-RENAME-UI:4, FE-FOLDER-RENAME-NETWORK:1-3, FE-FOLDER-RENAME-TESTS:2-4 | Happy path — Enter commits, server returns 200, toast success visible, name updated in list. |
| `folders.test.tsx` | FE-FOLDER-RENAME-NETWORK:4, FE-FOLDER-RENAME-TESTS:2-4 | 409 conflict — server returns 409, error toast with "Ya existe..." text, name reverted. |
| `folders.test.tsx` | FE-FOLDER-RENAME-NETWORK:5, FE-FOLDER-RENAME-TESTS:2-4 | Generic error — server returns 500, generic error toast, name reverted. |
| `folders.test.tsx` | FE-FOLDER-RENAME-UI:5, FE-FOLDER-RENAME-TESTS:2-4 | Escape cancels — pressing Escape reverts optimistic update (no network call). |
| `folders.test.tsx` | FE-FOLDER-RENAME-VALIDATION:2, FE-FOLDER-RENAME-TESTS:2-4 | Empty/whitespace — clearing input and pressing Enter cancels edit (no network call). |
| `folders.test.tsx` | FE-FOLDER-RENAME-UI:6, FE-FOLDER-RENAME-NETWORK:1-3, FE-FOLDER-RENAME-TESTS:2-4 | Blur commits — typing + blur triggers the same path as Enter. |

## Dependencies
- **Files to touch**:
  - `apps/web/src/app/historial/page.tsx`
  - `apps/web/src/app/historial/__tests__/folders.test.tsx`
- **Precedent files to read**:
  - `apps/web/src/app/historial/page.tsx` (reference tag rename pattern already present)

## Rollout/Rollback
- **Rollout**: Deploy frontend code. No backend or database changes.
- **Rollback**: Revert commit. No data migration needed.
