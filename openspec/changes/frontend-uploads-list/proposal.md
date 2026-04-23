# Proposal: frontend-uploads-list

## Intent

Address the L2 audit gap where users can POST file uploads but have no UI to view or manage them. This requires adding a new GET endpoint to list user uploads and building a dedicated "Archivos" tab in the configuration page.

## Scope

### In Scope
- `GET /api/upload/` backend endpoint returning current user's uploads (ordered by created_at DESC).
- Explicit Pydantic model (`UploadedDocumentListItem`) for response schema, guaranteeing omission of internal fields.
- New "Archivos" tab in `/configuracion` containing a `DisclosureCard` with a table of files.
- File deletion capability via the existing `DELETE /api/upload/{id}` endpoint with native `confirm()` flow.
- Formatters for file sizes (KB/MB) and dates (`es-AR`).
- Comprehensive testing on both backend and frontend.

### Out of Scope
- File download capability (binary stream endpoint required, deferred).
- Bulk actions (delete, rename, move).
- Uploading files directly from this new tab (kept strictly in chat interface).
- Modifying `AddCardModal.tsx` or resolving pre-existing test/lint issues.

## Capabilities

### New Capabilities
- `upload-management`: Listing and deleting user-uploaded documents securely.

### Modified Capabilities
None

## Approach

**Backend**: Implement `GET /api/upload/` using `RateLimitBucket.READ` and bearer auth. We will use a select statement filtered by `user_id` and ordered by `created_at DESC`. Crucially, an explicitly mapped Pydantic response model will guarantee `storage_path` and `extracted_text` remain private. Test using the existing `tenant_pair` fixture to guarantee isolation.

**Frontend**: Extend the `ActiveTab` type in `apps/web/src/app/configuracion/page.tsx` with "archivos". Create a table UI wrapped in a `DisclosureCard`. The tab will lazy-fetch uploads using `authFetch`. Each row displays filename, type, size, and date, along with an "Eliminar" action (using `confirm()` and `sonner` toasts for feedback). Empty, loading, and error states will be clearly mapped.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/api/app/api/routes/upload.py` | Modified | Add `GET /` endpoint for listing documents |
| `apps/api/tests/integration/test_upload.py` | Modified | Add isolated list tests checking privacy |
| `apps/web/src/app/configuracion/page.tsx` | Modified | Add "archivos" tab and UI |
| `apps/web/src/app/configuracion/__tests__/uploads-tab.test.tsx` | New | Add frontend behavior tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Data leak (`storage_path` exposed) | High | Use explicit `UploadedDocumentListItem` schema; add explicit assertions in tests |
| Broken "Descargar" action | Med | Omit the download button entirely for MVP; do not implement stub |
| Destructive action accident | Med | Require explicit native `confirm()` before firing DELETE |

## Rollback Plan

Revert the PR containing these changes. The UI will lose the "Archivos" tab, and the backend will drop the new `GET /api/upload/` endpoint without breaking existing chat upload flows since database schema is unchanged.

## Dependencies

- None

## Success Criteria

- [ ] A user can navigate to `/configuracion` and click the "Archivos" tab.
- [ ] A user sees only their own previously uploaded files in the new tab.
- [ ] A user can click "Eliminar", confirm, and see the file removed from the UI and backend.
- [ ] Test suite ensures `storage_path` is never present in the API response.
