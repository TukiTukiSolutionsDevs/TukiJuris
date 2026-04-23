# Admin RBAC Management Specification

## Purpose

Defines the backend endpoints and frontend UI for managing user roles within the admin dashboard.

## Requirements

### Requirement: Backend Roles Endpoint (BE-ADMIN-USERROLES)

The system MUST provide a `GET /api/admin/users/{user_id}/roles` endpoint. This endpoint MUST require the `roles:read` permission. It SHALL call `RBACService.get_user_roles(user_id)` and return a list of role objects matching existing assign/revoke endpoint schemas.

#### Scenario: Successful Role Fetch
- GIVEN an admin user with `roles:read` permission
- WHEN a request is made to `GET /api/admin/users/{user_id}/roles`
- THEN the system MUST return 200 OK
- AND the response MUST contain the list of roles for that user

#### Scenario: Missing Permission
- GIVEN a user without `roles:read` permission
- WHEN a request is made to the endpoint
- THEN the system MUST return 403 Forbidden

#### Scenario: User Not Found
- GIVEN an admin user with `roles:read` permission
- WHEN a request is made for a non-existent user
- THEN the system MUST return 404 Not Found

### Requirement: Inline RBAC Expansion (FE-RBAC-EXPAND)

The system MUST display a "Roles" button on each row of the `/admin` users table ONLY if the admin has `roles:write` permission. Clicking this button MUST expand the row to show current roles as chips with a revoke ("x") icon, and a dropdown to assign new roles.

#### Scenario: Assigning a Role
- GIVEN an expanded user row
- WHEN the admin selects a role from the dropdown and clicks "Asignar"
- THEN the system MUST optimistically update the UI
- AND show a success toast "Rol asignado"

#### Scenario: Revoking a Role
- GIVEN an expanded user row with existing roles
- WHEN the admin clicks the "x" icon on a role chip
- THEN the system MUST optimistically update the UI
- AND show a success toast "Rol revocado"

#### Scenario: Self-Demotion Protection
- GIVEN an expanded row matching the current admin's `user_id`
- WHEN the admin views their roles
- THEN the revoke ("x") icon MUST be disabled
- AND a tooltip "No podés modificar tus propios roles" MUST be displayed

#### Scenario: Super Admin Assignment Guard
- GIVEN an expanded user row
- WHEN the admin selects "super_admin" from the dropdown and clicks "Asignar"
- THEN the system MUST show a confirm dialog "¿Estás seguro? Asignar super_admin otorga acceso total."
- AND only proceed if confirmed

### Requirement: RBAC Tests and Standards (FE-ADMIN-TESTS & FE-ADMIN-NFR)

The system MUST include pytest coverage for the backend route (200, 403, 404). Frontend tests MUST verify the expand panel, rendering of roles, assignment, revocation, self-row protection, and the `super_admin` confirmation dialog. The new route MUST follow existing FastAPI router conventions.

#### Scenario: Full Stack Test Coverage
- GIVEN the automated test suites
- WHEN the tests run
- THEN backend tests MUST cover all role endpoint outcomes
- AND frontend MSW tests MUST mock endpoints and verify UI interactions and toasts