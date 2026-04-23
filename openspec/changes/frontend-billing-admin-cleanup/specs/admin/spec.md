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
- AND the modal MUST remain open with the reason text preserved