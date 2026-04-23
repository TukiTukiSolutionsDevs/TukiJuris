# Billing Specification

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
- AND display the full invoice details (subtotals, tax, items) in a modal or drawer