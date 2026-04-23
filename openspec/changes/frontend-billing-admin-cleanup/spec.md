# Admin Specification

## Purpose

Administrative capabilities and management interfaces.

## Requirements

### Requirement: Admin Invoices Tab

The admin panel MUST provide a dedicated "Facturas" tab for invoice management.

#### Scenario: Missing billing:update permission
- GIVEN an admin user lacks the `billing:update` permission
- WHEN they view the `/admin` page
- THEN the "Facturas" tab button MUST be disabled
- AND it MUST display a tooltip "Requiere permiso billing:update"

#### Scenario: Viewing the invoices tab
- GIVEN an admin user with the `billing:update` permission
- WHEN they navigate to the "Facturas" tab (`?tab=facturas`)
- THEN they MUST see a filter bar with status dropdown and Org ID input
- AND they MUST see a paginated table of invoices (page size 20, prev/next)
- AND the table MUST be horizontally scrollable on mobile devices

### Requirement: Admin Invoice Mutations

The admin invoices tab MUST allow authorized admins to refund or void invoices.

#### Scenario: Opening mutation modal
- GIVEN the admin is viewing the invoices table
- WHEN they click "Reembolsar" or "Anular" in a row's action menu
- THEN a confirmation modal MUST open showing the invoice summary and explanatory text

#### Scenario: Enforcing reason requirement
- GIVEN the mutation modal is open
- WHEN the reason textarea is empty or only whitespace
- THEN the submit button MUST be disabled

#### Scenario: Successful mutation
- GIVEN the modal is open with a valid reason
- WHEN the admin submits the form
- THEN the system MUST issue a `PATCH /api/admin/invoices/{invoice_id}` request
- AND upon success, show a toast indicating success, refetch the list, and close the modal

#### Scenario: Failed mutation
- GIVEN the admin submits the form
- WHEN the request fails
- THEN the system MUST show an error toast
- AND the modal MUST remain open with the reason text preserved# Analytics Specification

## Purpose

Analytics dashboard for usage and queries.

## Requirements

### Requirement: Organization-Scoped Analytics

The analytics dashboard MUST allow users to view data specific to their selected organization.

#### Scenario: Hydrating selected organization
- GIVEN a user accesses the `/analytics` page
- WHEN the page mounts
- THEN it MUST hydrate the selected organization from `localStorage["tk_selected_org_id"]`
- AND if the stored ID is invalid or missing, it MUST default to the first organization (`orgs[0].id`)

#### Scenario: Switching organization
- GIVEN the user is on the `/analytics` page
- WHEN they select a different organization via the `OrgSwitcher`
- THEN the system MUST persist the new selection to `localStorage`
- AND it MUST refetch all analytics data for the newly selected organization

#### Scenario: Single organization fallback
- GIVEN a user with only 1 organization
- WHEN they access the `/analytics` page
- THEN the `OrgSwitcher` MUST be hidden
- AND the analytics data MUST load for their single organization without requiring selection# Billing Specification

## Purpose

Billing management, subscription management, and invoice history for users.

## Requirements

### Requirement: Organization-Scoped Billing

The billing dashboard MUST synchronize with the user's selected organization.

#### Scenario: Switching organization
- GIVEN the user is on the `/billing` page
- WHEN they select a different organization via the `OrgSwitcher`
- THEN the system MUST persist the new selection to `localStorage["tk_selected_org_id"]`
- AND it MUST refetch all billing data (subscription, usage, checkout, invoices) for the new organization

### Requirement: Trial Retry Banner

The billing page MUST surface an actionable banner when a trial payment fails.

#### Scenario: Failed trial charge
- GIVEN the user's trial status is `"charge_failed"`
- WHEN they view the `/billing` page
- THEN a retry banner MUST be displayed above the plan comparison
- AND it MUST contain a "Reintentar cobro" button

#### Scenario: Normal trial state
- GIVEN the user's trial status is NOT `"charge_failed"`
- WHEN they view the `/billing` page
- THEN the retry banner MUST NOT be displayed

#### Scenario: Clicking retry (Success)
- GIVEN the retry banner is visible
- WHEN the user clicks "Reintentar cobro"
- THEN the button MUST become disabled with `aria-busy="true"`
- AND the system MUST call `POST /api/trials/{trial_id}/retry-charge`
- AND upon success, show a toast "Cobro reintentado. Actualizando estado..." and refetch the trial state

#### Scenario: Clicking retry (503 Service Unavailable)
- GIVEN the user clicks "Reintentar cobro"
- WHEN the server responds with a 503 error
- THEN the system MUST show a toast "El sistema de prueba no está disponible en este momento."

#### Scenario: Clicking retry (Generic Error)
- GIVEN the user clicks "Reintentar cobro"
- WHEN the server responds with a non-503 error
- THEN the system MUST show a toast "No se pudo reintentar el cobro. Intentá nuevamente."

### Requirement: Invoice History and Details

The billing page MUST display a history of the user's invoices.

#### Scenario: Viewing invoice history
- GIVEN the user is on the `/billing` page
- WHEN the organization ID resolves
- THEN the system MUST fetch `GET /api/billing/{org_id}/invoices`
- AND display an "Historial de pagos" table with "fecha" (DD/MM/YYYY), "estado" (colored badge), and "total"

#### Scenario: Empty invoice history
- GIVEN the user has no invoices
- WHEN the invoice list loads
- THEN the system MUST display the empty state "Todavía no tenés facturas."

#### Scenario: Loading and Error states
- GIVEN the invoice list is fetching
- THEN the system MUST show 3 skeleton rows
- AND IF the fetch fails, it MUST show "No se pudieron cargar las facturas." with a retry button

#### Scenario: Viewing invoice details
- GIVEN the invoice table is populated
- WHEN the user clicks on an invoice row
- THEN the system MUST fetch `GET /api/billing/{org_id}/invoices/{invoice_id}`
- AND display the full invoice details (subtotals, tax, items) in a modal or drawer# Shared UI Specification

## Purpose

Shared generic UI components used across the application.

## Requirements

### Requirement: Reusable Organization Switcher

The system MUST provide a reusable `<OrgSwitcher>` component for organization selection.

#### Scenario: Multiple organizations available
- GIVEN the user belongs to more than 1 organization
- WHEN the `<OrgSwitcher>` component is rendered
- THEN it MUST render a dropdown pill with the organizations
- AND it MUST include an `aria-label="Cambiar organización"`
- AND it MUST be keyboard navigable

#### Scenario: Single organization available
- GIVEN the user belongs to exactly 1 organization
- WHEN the `<OrgSwitcher>` component is rendered
- THEN it MUST be completely hidden from the DOM

#### Scenario: Pure presentational behavior
- GIVEN the `<OrgSwitcher>` component
- WHEN a user selects a different organization
- THEN it MUST call the provided `onChange(orgId)` prop
- AND it MUST NOT handle its own data fetching or persistence