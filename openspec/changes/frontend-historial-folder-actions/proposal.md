# Proposal: Frontend Historial Folder Actions (Rename)

## Intent
To allow users to rename their existing folders directly from the Historial sidebar. The backend already supports renaming via `PUT /api/folders/{id}`, but the frontend UI is missing this capability (H7 audit gap). This change provides an inline-edit UX consistent with tag editing, surfacing validation errors to the user rather than swallowing them.

## Scope

### In Scope
- Inline renaming of existing folders in the Historial sidebar via an Edit icon on hover.
- Client-side validation: reject empty, whitespace-only, and unchanged names.
- Server-side error surfacing: show a `sonner` toast on success or error (e.g., 409 conflict: "Ya existe una carpeta con ese nombre").
- Optimistic update UI flow (immediate update, then background sync, revert on failure).
- MSW integration tests for rename paths (success, 409 conflict, validation).

### Out of Scope
- Expanding the scope to folder creation, deletion, or moving (already implemented).
- Fixing the swallowed 409 errors in OTHER folder handlers (added to follow-up backlog).
- Extracting `FolderSidebarItem` into a separate component (follow-up refactor).
- Feature gating (folders are available to all plans).

## Capabilities

### New Capabilities
- `historial-folders`: Management of folders in the Historial page, specifically covering the inline rename behavior, optimistic updates, and error handling.

### Modified Capabilities
None

## Approach
Implement the rename logic inline within `apps/web/src/app/historial/page.tsx`. Introduce `editingFolderId` and `editingFolderName` state variables. On hover, show an `Edit2` icon. Clicking it enters edit mode with an input field. Pressing `Enter` or blurring triggers an optimistic update (`fetch`/`PUT` to `/api/folders/{id}`), while `Escape` cancels. If the API returns 409 or another error, we revert the local state and display a `toast.error()`. Otherwise, `toast.success()` is shown and `fetchFolders()` is called in the background. We'll add MSW handlers for the folder endpoints to enable integration tests.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/web/src/app/historial/page.tsx` | Modified | Add inline rename UI, state, and API handler |
| `apps/web/tests/historial/folders.test.tsx` (or similar) | New | Integration tests for the folder rename functionality |
| `apps/web/tests/mocks/handlers.ts` | Modified | Add MSW mock handlers for `/api/folders/` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| 409 error not surfaced to the user | High | Specifically handle `res.status === 409` and show toast "Ya existe una carpeta con ese nombre" |
| First `sonner` usage on page | Low | Follow standard usage; verify toast renders correctly in the Historial page context. |

## Rollback Plan
Revert the changes in `apps/web/src/app/historial/page.tsx` and remove the added tests. No backend or database changes are required, making the frontend rollback trivial.

## Dependencies
- Backend `PUT /api/folders/{id}` endpoint (already exists and functioning).

## Success Criteria
- [ ] Users can click an Edit icon on a folder to rename it inline.
- [ ] Submitting an empty or unchanged name exits edit mode without an API call.
- [ ] Renaming to an existing folder name displays a 409 toast error and reverts the name.
- [ ] Successful rename updates the UI optimistically and shows a success toast.
- [ ] Integration tests verify the happy path and conflict scenarios using MSW.
