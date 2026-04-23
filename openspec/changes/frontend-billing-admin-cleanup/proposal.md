# Proposal: frontend-billing-admin-cleanup

**Change Name**: frontend-billing-admin-cleanup
**Project**: tukijuris
**Type**: feature / cleanup
**Status**: proposed

## Intent
Implement the second phase of the frontend medium/low gaps cleanup (Sprint 8b). This phase focuses exclusively on billing and administrative gaps in the frontend application to synchronize with existing backend capabilities. 

The primary goals are:
1. Provide users with multi-organization support in analytics and billing screens (M7).
2. Surface actionable UI for failed trial payments (M9).
3. Allow users to view their invoice history and details (L5).
4. Provide authorized administrators a dedicated, secure interface to refund and void invoices (M8).

## Proposed Solution

This sprint will deliver four distinct, well-contained UI features:

1. **Org Switcher Component (M7)**
   - Extract a reusable `OrgSwitcher` component in `apps/web/src/components/`.
   - Place a dropdown pill above the main content in `/analytics` and `/billing`.
   - Hide the component entirely when the user has only 1 organization.
   - Persist the selected organization in `localStorage["tk_selected_org_id"]` and hydrate on mount. Default to `orgs[0]` if the stored ID is invalid or missing.
   - Force a data refetch for the page when the organization changes.

2. **Trial Retry-Charge Banner (M9)**
   - Introduce a conditional banner at the top of the `/billing` page.
   - Displays only when `trial.status === "charge_failed"`.
   - Contains a brief description and a "Reintentar cobro" button, disabled with an `aria-busy` state while pending.
   - Triggers `POST /api/trials/{trial_id}/retry-charge` via `authFetch`.
   - Uses `sonner` toasts for feedback. Handles 503 errors gracefully (for when `TRIALS_ENABLED=false`).
   
3. **Invoice History + Detail (L5)**
   - Add a new "Historial de pagos" section below the plan comparison on the `/billing` page.
   - Fetch `GET /api/billing/{org_id}/invoices` after the `orgId` resolves.
   - Render a table with date (formatted), status (colored badge), and total (currency).
   - Display a clean empty state ("Todavía no tenés facturas.") or skeleton loaders while fetching.
   - When a row is clicked, fetch the invoice details (`GET /api/billing/{org_id}/invoices/{invoice_id}`) and display them in a modal/drawer.

4. **Admin Facturas Tab (SECURITY CRITICAL) (M8)**
   - Introduce a new "Facturas" tab inside the `/admin` view, alongside "Resumen" and "Auditoría".
   - Client-side gate the entire tab content behind the `hasPermission("billing:update")` check. If the admin lacks this permission, the tab appears disabled with a tooltip ("Requiere permiso billing:update").
   - Display a paginated table matching the audit log pattern from Sprint 7b (page size 20, prev/next).
   - Include columns for date, organization name, total, and status badge. Allow filtering by status (paid, pending, refunded, void) and optionally `org_id`.
   - Each row features an action menu ("Reembolsar", "Anular"). Actions open a confirmation modal requiring a `reason` via a textarea before issuing a `PATCH /api/admin/invoices/{invoice_id}` request.
   - Success and error states are handled via `sonner` toasts, with a subsequent refetch of the list.
   - Note: The existing read-only `InvoicesTable` in the "Resumen" tab remains; the new tab is strictly the mutation surface.

## Architecture & Approach

- **Data Fetching:** All network requests will utilize `authFetch` to ensure tokens are attached and refresh flows are respected.
- **Component Reusability:** The `OrgSwitcher` will be extracted as a common component. The admin pagination and filtering will mirror the existing Sprint 7b audit log patterns.
- **Feedback:** UI interactions (mutations) will rely heavily on `sonner` toasts and clear loading states (`aria-busy`, skeletons).
- **Security Posture:** The M8 Facturas tab represents a significant mutation surface. We rely on the established `hasPermission` utility to ensure the UI is unrenderable/unactionable without `billing:update`. The backend already enforces this via `require_admin` and permission checks.

## Out of Scope

- File upload UI (L2) — Requires backend `GET /api/upload/` list endpoint first.
- Creating any new backend routes or endpoints.
- Bulk actions on administrative invoices (not supported by the backend `PATCH` endpoint).
- Invoice PDF downloads.
- Modifying `AddCardModal.tsx` — This component currently has 15 pre-existing failing tests and 51 ESLint warnings which will be tackled in a separate technical debt sprint.