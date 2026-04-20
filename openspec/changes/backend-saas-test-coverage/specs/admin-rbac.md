---
change: backend-saas-test-coverage
spec: admin-rbac
status: proposed
created: 2026-04-19
---

# Spec — Admin & RBAC test coverage

## 1. Scope
Coverage for `admin.py`, `admin_saas.py`, and `rbac_admin.py` routes. Primary focus is ensuring 403 authorization guards (defense-in-depth) function correctly, and RBAC assignment/revocation flows are properly integrated.
Deliberately OUT:
- `test_admin.py defense-in-depth` Sprint 3 Batch 3 item (we will not duplicate its specific tests, but we will add route-specific coverage for non-admin rejection).
- Sprint 3 Batch 3 items `test_role_consistency_flow` and `test_backfill_is_admin`.

## 2. Current state
- Existing tests: Good coverage for metrics, audit log, and `admin_saas_panel` (revenue, BYOK).
- Known gaps: `GET /api/admin/users`, `/api/admin/activity`, `/api/admin/knowledge` have no route-level 403 coverage. RBAC assign/revoke integration test is missing. `_ensure_admin` is duplicated locally in `admin_saas.py`, `admin_invoices.py`, and `admin_trials.py`.

## 3. Test catalog

1. ID: `admin-rbac.unit.001`
   - Name: `test_admin_ensure_admin_non_admin_raises`
   - Layer: unit
   - File: `apps/api/tests/unit/test_admin_helpers.py`
   - Intent: Ensure the local `_ensure_admin` helper function raises HTTPException(403) when passed a user with `is_admin=False`.
   - Setup: Mock user without admin rights.
   - Assertions: Raises 403.
   - Expected runtime: fast
   - Dependency: FIX-1

2. ID: `admin-rbac.int.001`
   - Name: `test_admin_users_non_admin_403`
   - Layer: integration
   - File: `apps/api/tests/integration/test_admin_routes.py`
   - Intent: Verify `GET /api/admin/users` rejects non-admin users.
   - Setup: Standard user auth fixture.
   - Assertions: HTTP 403.
   - Expected runtime: med
   - Dependency: NONE

3. ID: `admin-rbac.int.002`
   - Name: `test_admin_activity_non_admin_403`
   - Layer: integration
   - File: `apps/api/tests/integration/test_admin_routes.py`
   - Intent: Verify `GET /api/admin/activity` rejects non-admin users.
   - Setup: Standard user auth fixture.
   - Assertions: HTTP 403.
   - Expected runtime: med
   - Dependency: NONE

4. ID: `admin-rbac.int.003`
   - Name: `test_admin_knowledge_non_admin_403`
   - Layer: integration
   - File: `apps/api/tests/integration/test_admin_routes.py`
   - Intent: Verify `GET /api/admin/knowledge` rejects non-admin users.
   - Setup: Standard user auth fixture.
   - Assertions: HTTP 403.
   - Expected runtime: med
   - Dependency: NONE

5. ID: `admin-rbac.int.004`
   - Name: `test_rbac_assign_role_integration`
   - Layer: integration
   - File: `apps/api/tests/integration/test_rbac_admin.py`
   - Intent: Full lifecycle integration: Assign a role to a user via `POST /api/admin/rbac/users/{id}/roles`, then verify `GET /api/admin/rbac/roles/{id}/permissions` reflects it.
   - Setup: Admin auth fixture, target standard user, predefined test role.
   - Assertions: Returns 200 on assign, permissions endpoint includes the new granted powers.
   - Expected runtime: med
   - Dependency: NONE

6. ID: `admin-rbac.int.005`
   - Name: `test_rbac_revoke_role_integration`
   - Layer: integration
   - File: `apps/api/tests/integration/test_rbac_admin.py`
   - Intent: Revoke a role from a user and verify rejection on endpoints requiring that role.
   - Setup: Admin auth, target user with active role.
   - Assertions: HTTP 200 on `DELETE /api/admin/rbac/users/{user_id}/roles/{role_id}`.
   - Expected runtime: med
   - Dependency: NONE

## 4. Code fixes likely required
- **FIX-1**: Unify the `_ensure_admin` local functions scattered across `admin_saas.py`, `admin_invoices.py`, and `admin_trials.py`. It should ideally consume the RBAC dependency or a centralized `is_admin` guard to prevent security divergence.

## 5. Acceptance criteria
- All admin routes have explicit non-admin 403 tests.
- RBAC assign/revoke lifecycle is covered end-to-end.
- Centralized `_ensure_admin` is unit tested.
- Zero new skips/xfails.

## 6. Out of scope / deferred
- `test_admin.py defense-in-depth` (Sprint 3 Batch 3 item #267).
- `test_role_consistency_flow` and `test_backfill_is_admin` (Sprint 3 Batch 3).

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
