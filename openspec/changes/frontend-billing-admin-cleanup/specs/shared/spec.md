# Shared UI Specification

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