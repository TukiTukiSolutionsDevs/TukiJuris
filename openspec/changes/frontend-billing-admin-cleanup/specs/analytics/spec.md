# Analytics Specification

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
- AND the analytics data MUST load for their single organization without requiring selection