# Specification: frontend-configuracion-gaps

## Goal
Implement the missing frontend components for managing Dev API Keys (H1) and viewing Active Sessions (H2) within the `/configuracion` area, providing essential administrative capabilities to authenticated users.

## Scope
- **In Scope**:
  - Dev API keys table (list, create, revoke) under a new or updated section in `/configuracion`.
  - Secure show-once modal (`CopyOnceModal`) for displaying the newly generated full key.
  - Active sessions table (view only) under the `perfil` tab, integrating with the existing logout-all action.
  - Client-side JWT decoding to highlight the current session (best effort).
  - Component unit tests and MSW integration tests for key flows.
- **Out of Scope**:
  - Editing existing Dev API keys.
  - Plan-based entitlement gating for Dev API keys.
  - Revoking individual sessions via a `jti`-specific endpoint (unsupported by backend).

## Requirements

### 1. FE-CFG-DEVKEYS-LIST
The system MUST render a table of existing developer API keys in the `/configuracion` page under a "Claves de API" section.
- **AC1.1**: The table displays: name, prefix, scopes, created_at, expires_at (or "Sin vencimiento"), and status (active/revoked).
- **AC1.2**: Empty state displays "No tenés claves creadas todavía".
- **AC1.3**: Loading state displays skeleton rows or a spinner.
- **AC1.4**: Clicking "Revocar" triggers a confirmation dialog; upon confirmation, the system calls `DELETE /api/keys/{id}`.
- **AC1.5**: On successful revocation, display a "Clave revocada" toast and update the row state. On error, display "No se pudo revocar la clave".

### 2. FE-CFG-DEVKEYS-CREATE
The system MUST provide a form to create a new API key.
- **AC2.1**: Clicking "Crear nueva clave" opens a form with fields: name (required), scopes (checkboxes), and expires_at (optional).
- **AC2.2**: The submit button is disabled while pending (aria-busy).
- **AC2.3**: Submission triggers `POST /api/keys` via authFetch.
- **AC2.4**: Validation errors (422) display field-level messages.
- **AC2.5**: Success triggers the Show-Once Secret Modal. Other errors display a toast message.

### 3. FE-CFG-DEVKEYS-SHOW-ONCE
The system MUST securely display the newly created `full_key` exactly once.
- **AC3.1**: The `CopyOnceModal` automatically opens post-creation, displaying the `full_key` with a "Copiar" button and a warning.
- **AC3.2**: Clicking "Copiar" writes to clipboard and shows a transient "Copiado" success state inline and via toast.
- **AC3.3**: The modal CANNOT be dismissed by clicking outside or pressing Escape.
- **AC3.4**: The only dismissal path is an explicit "Cerrar" button (e.g., "Ya copié la clave, cerrar").
- **AC3.5**: Upon closing, the modal unmounts, the secret is destroyed from memory, and the list is refetched.

### 4. FE-CFG-SESSIONS-LIST
The system MUST render a read-only list of active sessions.
- **AC4.1**: Displayed in the `perfil` tab above the existing logout-all button.
- **AC4.2**: The table displays: created_at, expires_at, and jti (first 8 chars truncated).
- **AC4.3**: Empty state displays "No hay sesiones activas".
- **AC4.4**: Loading state displays a skeleton or spinner.
- **AC4.5**: Includes a note: "Para cerrar una sesión, usá Cerrar todas las sesiones."

### 5. FE-CFG-SESSIONS-CURRENT
The system SHOULD highlight the user's current session.
- **AC5.1**: If the JWT can be safely decoded client-side, highlight the row matching the decoded `jti` with a "Sesión actual" badge.
- **AC5.2**: If decoding adds significant bundle weight or risk, this requirement may be skipped (documented Best Effort).

### 6. FE-CFG-TESTS
The system MUST be tested for functionality and regressions.
- **AC6.1**: Unit test `CopyOnceModal`: renders correctly, copy button integrates with clipboard, and dismissal is restricted to the explicit close button.
- **AC6.2**: Integration tests for Dev keys list, create, and revoke paths (including error states) using MSW.
- **AC6.3**: Integration tests for the Sessions list path (populated, empty, error).

## Definition of Done
- [ ] Dev API Keys UI is functional (list, create, revoke).
- [ ] `CopyOnceModal` implemented with strict dismissal constraints.
- [ ] Active Sessions UI is functional.
- [ ] Unit and MSW integration tests added and passing.
- [ ] No new TypeScript or ESLint errors.
- [ ] No regressions in existing `/configuracion` tabs.

## Test Matrix
| Feature | Scenario | Test Type | Expected Outcome |
|---------|----------|-----------|------------------|
| Dev Keys | List 0 keys | Integration | Shows empty state text |
| Dev Keys | List 2 keys | Integration | Renders rows correctly |
| Dev Keys | Create success | Integration | Shows CopyOnceModal with `full_key` |
| Dev Keys | Create 422 | Integration | Shows field validation errors |
| Dev Keys | Revoke success | Integration | Toast success, row updates |
| Dev Keys | Revoke error | Integration | Toast error |
| Modal | Copy button | Unit | Calls `navigator.clipboard.writeText` |
| Modal | Dismissal | Unit | Blocks Escape/click-outside, allows "Cerrar" |
| Sessions | List 1 session | Integration | Shows row with truncated JTI |
| Sessions | Empty list | Integration | Shows empty state text |

## Dependencies
- **Files to touch**:
  - `src/app/configuracion/page.tsx`
  - `src/components/configuracion/*` (new components)
  - `src/components/ui/CopyOnceModal.tsx` (new)
- **Precedent files to read**:
  - `apps/web/src/app/admin/_components/BYOKTable.tsx`
  - `apps/web/src/app/configuracion/__tests__/logout-all.test.tsx`

## Rollout/Rollback Notes
- **Rollout**: Safe to deploy independently as it only reads/writes to existing backend APIs.
- **Rollback**: Revert UI component additions in `/configuracion` and remove the components. No DB migrations involved.