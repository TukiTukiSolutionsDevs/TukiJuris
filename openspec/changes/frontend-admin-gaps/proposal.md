# Proposal: frontend-admin-gaps (Sprint 7b — H5 + H6)

## Intent

Implement the frontend UI and necessary backend route support for the RBAC admin capabilities (H5) and the Audit Log (H6). This brings the admin features into the user interface, improving administrator visibility and control over user roles and system-wide audits.

## Scope

### In Scope
- Add missing backend route `GET /api/admin/users/{user_id}/roles` with `roles:read` protection.
- Refactor the existing `apps/web/src/app/admin/page.tsx` monolith to use top horizontal tab navigation (Resumen, Auditoría).
- Implement H5 (RBAC Admin) as an expandable row in the existing users table for role assignment/revocation.
- Add permission gate (`roles:write`), self-demotion protection, and `super_admin` assignment guard.
- Implement optimistic local updates for role assignments/revocations with toast notifications.
- Implement H6 (Audit Log) in the new "Auditoría" tab with filters (actor, action, resource, date), pagination, and an expandable row view for before/after state JSON diffs.

### Out of Scope
- Backend audit log filters beyond what already exists.
- Audit log export (CSV/PDF/JSON download).
- Bulk role assignment.
- Role hierarchy/dependency enforcement (handled by backend).
- Modifying `AddCardModal.tsx`, pre-existing failing tests, or pre-existing eslint warnings.
- Any `/configuracion` changes (handled in Sprint 7a).
- Additional redaction of PII on the frontend (renders what the backend provides).

## Capabilities

### New Capabilities
- `admin-audit-log`: Viewing system-wide audit logs with filtering and pagination capabilities.
- `admin-rbac-management`: Viewing, assigning, and revoking user roles from the admin panel.

### Modified Capabilities
- `admin-dashboard`: Modified to include tabbed navigation instead of a single monolithic page.

## Approach

1.  **Backend Route**: First, implement and test the new backend endpoint `GET /api/admin/users/{user_id}/roles`.
2.  **Admin Page Refactor**: Refactor `app/admin/page.tsx` to support tab-based navigation while preserving the existing users table under "Resumen". Update existing tests to navigate to the "Resumen" tab.
3.  **H5 RBAC UI**: Extend the user table rows with an expandable "Roles" panel. Fetch roles on expand. Add logic for assignment (`POST`), revocation (`DELETE`), and guards against self-demotion and `super_admin` assignment.
4.  **H6 Audit Log UI**: Create the "Auditoría" tab component. Implement API integration with `GET /api/admin/audit-log` using the specified filters. Build an expandable row to display `before_state` and `after_state` JSON in `<pre>` blocks.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/api/routers/admin.py` (or equiv) | Modified | Add `GET /api/admin/users/{user_id}/roles` endpoint. |
| `backend/tests/` | Modified | Add pytest for the new roles endpoint. |
| `apps/web/src/app/admin/page.tsx` | Modified | Refactor into tabbed layout. |
| `apps/web/src/app/admin/components/` | New/Modified | Refactored users table, new role assignment, new audit log components. |
| `apps/web/tests/admin/` | Modified | Update existing tests to pass under the new tab structure. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Admin monolith refactor breaks existing tests | High | Start with the refactor, update existing tests immediately to target the new tab, and verify CI green before continuing. |
| Backend missing route | Low | Explicitly ordered as the first task. |
| Unintended super_admin assignment | Medium | Confirmation dialog added to the UI before dispatching the POST request. |
| Self-demotion | Medium | Frontend disables revoke on the active admin user's row. Backend `409` handling with specific toasts acts as a fallback. |

## Rollback Plan

Revert the PR containing the `frontend-admin-gaps` branch. Since the backend changes are additive (one new `GET` route) and the frontend is mostly isolated to the `/admin` route (which is admin-only), there is low risk of user-facing disruption.

## Dependencies

- Completion of Sprint 7a (`/configuracion` changes - H1 + H2).
- Backend must be updated with `GET /api/admin/users/{user_id}/roles` before frontend implementation.

## Success Criteria

- [ ] Backend route `GET /api/admin/users/{user_id}/roles` returns correct role shapes and passes pytest.
- [ ] Existing admin tests pass under the new tab-nav structure.
- [ ] Admin with `roles:write` can view, assign, and revoke roles via expandable user rows.
- [ ] Self-demotion is prevented in UI (disabled button).
- [ ] Assigning `super_admin` prompts a confirmation dialog.
- [ ] Audit Log tab renders correctly with functional filters, pagination, and JSON diff rows.
- [ ] No regression on existing `/admin` behavior.
