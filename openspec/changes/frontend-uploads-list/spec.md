# Specification: frontend-uploads-list

## Goal

Address the L2 audit gap by allowing users to securely view and delete their uploaded documents natively within the application's configuration area. This eliminates the "blind drop" upload issue by providing visibility and lifecycle control over files submitted to the system.

## Scope

### In Scope
- A new backend endpoint `GET /api/upload/` to list current user uploads.
- Explicit schema guarantees to prevent leaking internal metadata (`storage_path`, `extracted_text`).
- A new "Archivos" tab inside the `/configuracion` frontend view.
- A table view showing file details with size and date formatters.
- Deletion capabilities using optimistic UI updates and native confirmation dialogs.
- Automated testing at both integration (Pytest) and unit/behavior (MSW+Vitest) layers.

### Out of Scope
- File download capability (no binary stream endpoint exists; deferred).
- Bulk actions (select multiple to delete).
- Uploading files from the new tab (uploads remain contextual to the chat).
- Resolving pre-existing `tsc` or `eslint` issues in unmodified files.

## Requirements

### 1. BE-UPLOAD-LIST
- The system MUST expose `GET /api/upload/` requiring Bearer authentication.
- The endpoint MUST apply the `RateLimitBucket.READ` rate limiter.
- The system MUST return the current user's uploaded documents ordered by `created_at` descending.
- The endpoint MUST strictly use an explicit Pydantic model (`UploadedDocumentListItem`) to return: `id`, `filename`, `file_type`, `file_size`, `page_count`, `conversation_id`, and `created_at`.
- The endpoint MUST NOT return `storage_path` or `extracted_text` under any circumstances.
- If no files exist for the user, the endpoint MUST return `[]` with status 200 OK.

### 2. FE-UPLOADS-TAB
- The frontend MUST include "archivos" within the `/configuracion` `ActiveTab` union.
- The system MUST render "Archivos" in the 6th position of the configuration tab navigation.
- The tab content MUST be wrapped in the application's standard `DisclosureCard` pattern.
- The system MUST lazy-fetch the uploads list only upon activating the tab.
- While fetching, the system MUST display a loading state consisting of 3 skeleton rows.
- If the fetch fails, the system MUST display the error message "No se pudieron cargar los archivos." along with a retry button.
- If the fetch returns an empty array, the system MUST display the empty state message "Todavía no subiste ningún archivo."

### 3. FE-UPLOADS-TABLE
- The system MUST display document data in a table structure with columns for: filename, file type, file size, created at, and actions.
- The filename column MUST align left and truncate with an ellipsis upon text overflow.
- The file type column MUST display the extension as an uppercase badge.
- The file size column MUST be formatted programmatically (`< 1024` = "X bytes", `< 1024*1024` = "X.Y KB", `>= 1024*1024` = "X.Y MB").
- The created at column MUST be formatted as "DD/MM/YYYY".
- The system MUST display rows ordered newest first, matching the backend's default sort order.
- The table MUST NOT include a "Descargar" action.

### 4. FE-UPLOADS-DELETE
- Each table row MUST contain an "Eliminar" action button.
- Clicking "Eliminar" MUST trigger a native confirmation prompt: `¿Eliminar "{filename}"? Esta acción no se puede deshacer.`
- If the user cancels the confirmation, the system MUST abort the action with no state changes.
- If the user confirms, the system MUST optimistically remove the row from the UI and fire a `DELETE /api/upload/{id}` request.
- The delete button MUST be disabled and show `aria-busy` while the network request is inflight.
- Upon successful deletion, the system MUST display a success toast stating "Archivo eliminado".
- Upon a failed deletion, the system MUST revert the optimistic UI update (restoring the row) and display an error toast stating "No se pudo eliminar el archivo".

### 5. FE-UPLOADS-TESTS
- The system MUST include unit tests covering the file-size formatter edge cases (bytes, KB, MB boundaries).
- The system MUST include frontend integration tests using MSW and AuthContext to verify tab lazy-loading, table rendering, empty/error states, and the optimistic delete flow.
- The backend MUST include integration tests verifying that `GET /api/upload/` lists records correctly, handles empty states, and mathematically guarantees the absence of `storage_path` and `extracted_text` in the response payloads.

## DoD Checklist

- [ ] `GET /api/upload/` implemented and verified to prevent sensitive metadata exposure.
- [ ] Backend integration tests written (happy path, empty state, security assertions).
- [ ] "Archivos" tab integrated into `/configuracion` with lazy loading behavior.
- [ ] Uploads table rendered correctly using specified formatters and badge styling.
- [ ] Deletion logic implemented with optimistic UI updates and confirmation dialogs.
- [ ] Frontend unit and integration tests written (MSW-mocked flows for success, empty, and error cases).
- [ ] Pipeline NFRs verified (no new TSC errors, no new ESlint warnings, no regression on existing tabs).

## Test Matrix

| Area | Type | Scenario | Expected Outcome |
|------|------|----------|------------------|
| BE | Integration | User fetches uploads with 2 existing files | 200 OK; returns 2 rows sorted by `created_at` DESC |
| BE | Integration | User fetches uploads with 0 files | 200 OK; returns `[]` |
| BE | Security | Verify list response schema constraints | Keys `storage_path` and `extracted_text` are strictly missing |
| FE | Unit | File size boundaries (500B, 1024B, 1048576B) | Correctly outputs "500 bytes", "1.0 KB", "1.0 MB" |
| FE | Integration | Tab activation | Triggers lazy fetch; displays loading skeletons |
| FE | Integration | Empty state response from MSW | Displays "Todavía no subiste ningún archivo." |
| FE | Integration | Error state response from MSW | Displays "No se pudieron cargar los archivos." + retry |
| FE | Integration | Deletion confirmed, succeeds | Optimistic remove; `DELETE` sent; success toast visible |
| FE | Integration | Deletion confirmed, fails | Optimistic remove reverted; error toast visible |
| FE | Integration | Deletion canceled | No network request sent; row stays visible |

## Dependencies
- None.

## Rollout/Rollback
- **Rollout**: Deployed via standard PR merge. The new endpoint goes live first; the frontend tab becomes available seamlessly upon client refresh.
- **Rollback**: Standard git revert. Frontend tab hides the route; backend endpoint is dropped safely as it introduces no schema migrations.
