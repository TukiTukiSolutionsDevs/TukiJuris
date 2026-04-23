# Tasks: frontend-admin-gaps

## Phase 1: Backend route

- [x] 1.1 **BE-ADMIN-USERROLES route** — Add `GET /api/admin/users/{user_id}/roles` in `apps/api/app/api/routes/rbac_admin.py`; call `RBACService.get_user_roles`, reuse `UserRoleResponse` shape, keep `roles:read` + rate-limit conventions. **AC:** BE-ADMIN-USERROLES. **Deps:** none. **DoD:** 200/403/404 behavior matches spec.
- [x] 1.2 **BE-ADMIN-USERROLES pytest** — Add `apps/api/tests/integration/test_admin_user_roles_get.py` covering happy path, missing permission, and unknown user using seeded-role patterns from `test_rbac_admin.py`. **AC:** BE-ADMIN-USERROLES. **Deps:** 1.1. **DoD:** new file passes standalone.

## Phase 2: Admin tab navigation foundation

- [x] 2.1 **FE-ADMIN-TABS page shell** — Refactor `apps/web/src/app/admin/page.tsx` into top tabs (`Resumen`, `Auditoría`) driven by `?tab=` via Next navigation/search params; preserve current metrics/users content inside Resumen. **AC:** FE-ADMIN-TABS, FE-ADMIN-NFR. **Deps:** none. **DoD:** `/admin` defaults to Resumen and `/admin?tab=auditoria` deep-links client-side.
- [x] 2.2 **FE-ADMIN-TESTS tab coverage** — Create/update admin page tests in `apps/web/src/app/admin/__tests__/page.tabs.test.tsx` (and any impacted admin tests) to assert tab rendering, toggling, and legacy content under Resumen. **AC:** FE-ADMIN-TESTS, FE-ADMIN-NFR. **Deps:** 2.1. **DoD:** prior admin assertions no longer depend on monolithic layout.

## Phase 3: RBAC inline panel

- [x] 3.1 **FE-RBAC-EXPAND data/client wiring** — Extend `apps/web/src/lib/api/admin.ts` with get/assign/revoke role helpers and types; create RBAC UI helpers in `apps/web/src/app/admin/_components/UserRolesPanel.tsx` (or equivalent) for per-row fetch, optimistic updates, and rollback. **AC:** FE-RBAC-EXPAND. **Deps:** 1.1, 2.1. **DoD:** expanded row can list current roles and mutate local state safely.
- [x] 3.2 **FE-RBAC-EXPAND row UX** — Update `apps/web/src/app/admin/page.tsx` and/or extracted users-table components to add the `Roles` button behind `roles:write`, self-row revoke disable + tooltip, and `super_admin` confirm before POST. **AC:** FE-RBAC-EXPAND, FE-ADMIN-NFR. **Deps:** 3.1. **DoD:** assign/revoke flows show expected success/error toasts and guards.
- [x] 3.3 **FE-RBAC-EXPAND tests** — Add Vitest/MSW coverage in `apps/web/src/app/admin/__tests__/rbac-panel.test.tsx` for expand, fetch, assign, revoke, self-row protection, and `super_admin` confirmation. **AC:** FE-RBAC-EXPAND, FE-ADMIN-TESTS. **Deps:** 3.2. **DoD:** mocked network flows and toast assertions pass.

## Phase 4: Audit log tab

- [x] 4.1 **FE-AUDITLOG-TAB component** — Add `apps/web/src/app/admin/_components/AuditLogTab.tsx` with filter bar, loading/empty states, expandable JSON rows, and URL-synced filters using `/api/admin/audit-log`. **AC:** FE-AUDITLOG-TAB. **Deps:** 2.1. **DoD:** applying/clearing filters refetches and row expansion reveals `<pre>` JSON.
- [x] 4.2 **FE-AUDITLOG-PAGINATION behavior** — Implement fixed page-size 20, prev/next boundaries, total/page indicator, and reset-to-page-1 on filter changes in `AuditLogTab.tsx` plus shared pagination helpers if needed. **AC:** FE-AUDITLOG-PAGINATION. **Deps:** 4.1. **DoD:** Next disables on short page and Previous disables on first page.
- [x] 4.3 **FE-AUDITLOG tests** — Add `apps/web/src/app/admin/__tests__/audit-log-tab.test.tsx` with MSW cases for filters, URL updates, loading/empty states, row expansion, and pagination boundaries. **AC:** FE-AUDITLOG-TAB, FE-AUDITLOG-PAGINATION, FE-ADMIN-TESTS. **Deps:** 4.2. **DoD:** all specified UI scenarios are asserted.

## Phase 5: Verification

- [x] 5.1 **Cross-stack verification** — Run `pytest apps/api/tests/integration/test_admin_user_roles_get.py`, the relevant web test suite for admin changes, and changed-file `tsc`/`eslint` checks. **AC:** FE-ADMIN-NFR, FE-ADMIN-TESTS, BE-ADMIN-USERROLES. **Deps:** 1.2, 2.2, 3.3, 4.3. **DoD:** backend tests green, frontend admin suite green, no new TS/ESLint regressions.

## Remediation (post-verify batch)

- [x] R1 **409 differentiation in RBAC toasts** — `UserRolesPanel.tsx`: assign/revoke handlers now check `err.status === 409` and show "No podés modificar tus propios roles"; generic failures show "No se pudo modificar los roles"; success shows "Rol asignado" / "Rol revocado".
- [x] R2 **Audit log table column contract** — `AuditLogTab.tsx`: replaced merged Recurso + hidden Actor columns with 5 distinct non-hidden columns (Timestamp, Actor, Acción, Tipo recurso, ID recurso); added `overflow-x-auto` wrapper; colSpan updated 5→6.
- [x] R3 **super_admin confirm copy** — `UserRolesPanel.tsx`: confirm text now exactly "¿Estás seguro? Asignar super_admin otorga acceso total."
- [x] R4 **Self-row tooltip copy** — `UserRolesPanel.tsx`: tooltip now exactly "No podés modificar tus propios roles".
- [x] R5 **Audit empty-state copy** — `AuditLogTab.tsx`: empty state now exactly "No hay entradas que coincidan con los filtros."
- [x] R6 **ESLint missing dep** — `page.tsx:253`: added `authFetch` to `useCallback` deps array.
- [x] R7 **tasks.md checkboxes** — All 10 original tasks marked `[x]`; this remediation section appended.
- [x] R8 **Tests for 409 + copy** — `rbac-panel.test.tsx`: updated 5 stale assertions + added 4 new tests (409 assign, 409 revoke, confirm copy, tooltip copy). `audit-log-tab.test.tsx`: added 3 new tests (empty-state copy, column headers, separate resource cells).
