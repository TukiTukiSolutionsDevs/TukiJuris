# Tasks: Frontend Billing Admin Cleanup

## Phase 1: OrgSwitcher foundation

- [x] 1.1 Create `apps/web/src/components/OrgSwitcher.tsx` as a pure presentational selector; hide for 0/1 orgs, keep `aria-label="Cambiar organización"`, and emit only `onChange(orgId)`.
- [x] 1.2 Add `apps/web/src/components/__tests__/OrgSwitcher.test.tsx` for multi-org render, single-org hidden DOM, keyboard navigation, and `onChange` behavior.

## Phase 2: Analytics wiring

- [x] 2.1 Update `apps/web/src/app/analytics/page.tsx` to fetch orgs, hydrate `localStorage["tk_selected_org_id"]`, fall back to `orgs[0].id`, render `OrgSwitcher`, persist changes, and refetch all analytics queries on org switch.
- [x] 2.2 Add `apps/web/src/app/analytics/__tests__/analytics.org-switcher.test.tsx` covering hydration, invalid stored-org fallback, single-org hidden state, persistence, and refetch after switch.

## Phase 3: Billing wiring + retry + invoices

- [x] 3.1 Create `apps/web/src/app/billing/_components/TrialRetryBanner.tsx` for `charge_failed` trials, pending CTA state, `POST /api/trials/{trial_id}/retry-charge`, 503/generic toast handling, and trial refetch callback.
- [x] 3.2 Create `apps/web/src/app/billing/_components/InvoiceHistorySection.tsx` for list/detail fetches, 3 skeleton rows, empty/error retry states, status badge, date/total columns, and modal/drawer details.
- [x] 3.3 Update `apps/web/src/app/billing/page.tsx` to manage org hydration/persistence, render `OrgSwitcher`, scope subscription/usage/checkout/invoices by org, and place retry banner above plan comparison.
- [x] 3.4 Add `apps/web/src/app/billing/__tests__/billing.page.test.tsx` for org switching, retry banner visibility/actions, invoice loading-empty-error states, and invoice detail fetch on row click.

## Phase 4: Admin Facturas tab (security critical)

- [x] 4.1 Create `apps/web/src/app/admin/_components/AdminInvoicesTab.tsx` using the `AuditLogTab` URL/filter/pagination pattern for status + `org_id`, mobile horizontal scroll, row action menu, confirmation modal, whitespace-safe reason validation, PATCH mutation, toast feedback, and refetch.
- [x] 4.2 Update `apps/web/src/app/admin/page.tsx` and `apps/web/src/app/admin/__tests__/page.tabs.test.tsx` to add `?tab=facturas`, disable the tab with tooltip when `hasPermission("billing:update")` is false, and render the tab only as an actionable surface when allowed.
- [x] 4.3 Add `apps/web/src/app/admin/__tests__/admin-invoices-tab.test.tsx` for permission gating, filter/pagination behavior, modal opening, disabled submit without reason, success close+refetch, and error preservation.

## Phase 5: Verification

- [x] 5.1 Run the affected web test suites plus `tsc` and `eslint` on changed files; record any blockers before moving to `sdd-apply` verification.

## Remediation (post-verify)

- [x] R1 Fix `AdminInvoicesTab.tsx` toast copy to exactly match spec FE-ADMIN-FACTURAS: success → `"Factura reembolsada"` / `"Factura anulada"`; error → `"No se pudo reembolsar la factura"` / `"No se pudo anular la factura"`. Branch error by `action`. Updated `admin-invoices-tab.test.tsx` with exact-string assertions on all 4 paths (refund success, refund error, void success, void error).
- [x] R2 Mark all tasks `[x]` in this file and append remediation section (this entry).
- [x] R3 Toast copy assertions in `admin-invoices-tab.test.tsx` now pin exact spec strings — regression detection is active (covered by R1).
- [x] R4 Created `apps/web/src/app/billing/__tests__/trial-gate.test.tsx` with 2 page-level integration tests: `charge_failed` → banner visible; `active` → banner absent. Follows the same `mockAuthFetch` + stub-sub-components pattern as `org-switcher.test.tsx`.
