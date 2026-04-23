# Admin Audit Log Specification

## Purpose

Defines the frontend interface for viewing and filtering system-wide audit logs, providing visibility into administrative and system actions.

## Requirements

### Requirement: Audit Log Interface (FE-AUDITLOG-TAB)

The system MUST render the Audit Log within the "Auditoría" tab of the admin dashboard. The UI SHALL include a filter bar at the top containing text inputs for Actor, Action, Resource Type, and date pickers for Date From and Date To. The UI MUST display results in a paginated table.

#### Scenario: Applying Filters
- GIVEN the Audit Log tab is active
- WHEN the admin enters filter criteria and clicks "Aplicar filtros"
- THEN the system MUST trigger a refetch with the corresponding query parameters
- AND update the URL query state

#### Scenario: Clearing Filters
- GIVEN active filters in the Audit Log tab
- WHEN the admin clicks "Limpiar"
- THEN the system MUST reset all filters to default
- AND refetch the unfiltered log

#### Scenario: Expanding Audit Log Row
- GIVEN a populated audit log table
- WHEN the admin clicks on a specific row
- THEN the row MUST expand to display `before_state` and `after_state` as pretty-printed JSON inside `<pre>` blocks

#### Scenario: Empty and Loading States
- GIVEN an audit log fetch is in progress or returns no results
- WHEN the data is resolving
- THEN the system MUST show a loading skeleton or spinner
- AND if no results, show "No hay entradas que coincidan con los filtros."

### Requirement: Audit Log Pagination (FE-AUDITLOG-PAGINATION)

The system MUST paginate the audit log results with a fixed page size of 20. Pagination controls SHALL include prev/next buttons, current page indicator, and total count. The page index MUST reset to 1 when filters are changed.

#### Scenario: Pagination Boundaries
- GIVEN the pagination controls
- WHEN at the first page (offset 0)
- THEN the "Previous" button MUST be disabled
- AND WHEN fewer than 20 rows are returned on the current page
- THEN the "Next" button MUST be disabled

### Requirement: Audit Log Tests (FE-ADMIN-TESTS)

The system MUST include frontend tests using Vitest and MSW. Tests SHALL verify the filter bar, URL parameter updates, row expansion (JSON diff visibility), empty/loading states, and pagination boundaries.

#### Scenario: Audit Log UI Tests
- GIVEN the frontend test suite
- WHEN the audit log tests run
- THEN all filter, pagination, and expansion behaviors MUST be verified against MSW mocked responses