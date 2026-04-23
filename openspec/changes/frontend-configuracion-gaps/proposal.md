# Proposal: frontend-configuracion-gaps

## Intent

Implement the missing frontend components for Dev API Keys (H1) and Active Sessions (H2) within the user configuration area (`/configuracion`). This addresses the gaps identified in the exploration phase for Sprint 7a, allowing users to manage their developer API keys and view active sessions.

## Scope

### In Scope
- **H1 (Dev API Keys)**: Full CRUD UI for API keys (list, create, revoke) within a new `devkeys` tab in `/configuracion`.
- **H1**: Show-once modal to display the `full_key` upon creation, with a copy button and mandatory acknowledgment.
- **H1**: Optional expiry date and available scopes selection during creation.
- **H2 (Sessions)**: Read-only list of active sessions in the `perfil` tab of `/configuracion`.
- **H2**: Display session details (created_at, expires_at, truncated jti) and highlight the current session if feasible.
- **H2**: Integration with the existing "logout-all" functionality.
- **Cross-cutting**: MSW integration tests, unit tests for the show-once modal, and Sonner toast feedback for actions.

### Out of Scope
- H5 (RBAC admin) and H6 (Audit log) — Deferred to Sprint 7b.
- Editing existing Dev API keys (name/scopes).
- Plan-gating for Dev API keys.
- Per-session revocation (backend does not support this yet).
- Modifying pre-existing failing tests or eslint warnings.

## Capabilities

### New Capabilities
- `dev-api-keys`: Management of developer API keys including creation, listing, and revoking.
- `user-sessions`: Viewing active user sessions and revoking all sessions.

### Modified Capabilities
- None

## Approach

- **H1**: Introduce a new `devkeys` tab (or sub-section) in the `/configuracion` page. Use `authFetch` to interact with `/api/keys/`. Implement a specialized `CopyOnceModal` component to handle the critical requirement of showing the full API key only once safely.
- **H2**: Add a new section in the `perfil` tab above the existing logout-all button. Fetch sessions from `/api/auth/sessions` and render them in a simple table. The existing logout-all button will serve as the sole revocation method.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/app/configuracion/page.tsx` | Modified | Add dev API keys tab/section and sessions section |
| `src/components/configuracion/` | New | Add components for Dev API keys list, create modal, and sessions list |
| `src/components/ui/` | New | Add reusable `CopyOnceModal` component |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Show-once UX risk for H1 | High | Implement a strict `CopyOnceModal` that requires explicit acknowledgment before dismissal. Add unit tests. |
| Current session highlight risk | Medium | If `jti` cannot be safely decoded client-side, we will omit the highlight and document the decision. |

## Rollback Plan

Revert the commits introducing the new UI components in `/configuracion` and remove the associated MSW test handlers. The backend APIs will remain unaffected.

## Dependencies

- Existing backend endpoints: `/api/keys/` and `/api/auth/sessions`.

## Success Criteria

- [ ] Users can create, view, and revoke Dev API keys in the `/configuracion` area.
- [ ] The full Dev API key is shown exactly once upon creation, with a clear warning and copy button.
- [ ] Users can view a list of their active sessions in the `/configuracion` profile tab.
- [ ] MSW integration tests cover critical paths (create, list, revoke, errors) for both features.
