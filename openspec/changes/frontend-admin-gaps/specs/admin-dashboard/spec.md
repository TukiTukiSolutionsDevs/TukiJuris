# Admin Dashboard Specification

## Purpose

Defines the structure and navigation of the admin dashboard, replacing the previous monolithic layout with a tab-based navigation system to support expanding administrative capabilities.

## Requirements

### Requirement: Admin Tab Navigation (FE-ADMIN-TABS)

The system MUST provide a top horizontal tab navigation on the `/admin` page. The system SHALL support at least two tabs: "Resumen" (default) and "Auditoría". The active tab MUST be driven by a URL search parameter (`?tab=resumen` or `?tab=auditoria`). Tab switching SHALL be client-side without full page reloads.

#### Scenario: Default Tab Selection
- GIVEN an admin user navigates to `/admin` without query parameters
- WHEN the page loads
- THEN the "Resumen" tab MUST be active
- AND the existing users table and metrics MUST be displayed

#### Scenario: Deep Linking to Audit Log
- GIVEN an admin user navigates to `/admin?tab=auditoria`
- WHEN the page loads
- THEN the "Auditoría" tab MUST be active

### Requirement: Admin Dashboard Tests (FE-ADMIN-TESTS)

The system MUST include automated tests verifying the tabbed navigation and URL parameter integration. Existing admin tests MUST be updated to assert against the "Resumen" tab.

#### Scenario: Tab Navigation Testing
- GIVEN the test suite runs for the admin page
- WHEN the tests assert navigation and rendering
- THEN tests MUST verify that Resumen and Auditoría tabs exist and can be toggled
- AND tests MUST verify deep linking works

### Requirement: Admin Dashboard Non-Functional Requirements (FE-ADMIN-NFR)

The system MUST preserve all existing admin functionality. The refactored components MUST NOT introduce new TypeScript errors or ESLint warnings. The existing admin middleware and cookie gate MUST NOT be regressed.

#### Scenario: Refactor Safety
- GIVEN the admin page has been refactored
- WHEN the build and lint processes run
- THEN no new TSC errors or ESLint warnings SHALL appear
- AND existing functionality MUST operate normally