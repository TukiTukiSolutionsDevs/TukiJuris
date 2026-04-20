---
change: backend-saas-test-coverage
spec: organizations
status: proposed
created: 2026-04-19
---

# Spec — Organizations test coverage

## 1. Scope
Coverage for the `organizations.py` routes focusing heavily on cross-tenant isolation (ownership isolation), seat count syncing, and strict role enforcement within an organization. Since the application lacks global database Row Level Security (RLS), every org-scoped route must be proven airtight.

## 2. Current state
- Existing tests: ~13 tests covering basic create, list, get, update, invite, list members.
- Known gaps: `DELETE /api/organizations/{org_id}/members/{user_id}` (member removal) is untested. Role enforcement (member vs admin/owner) is untested. Seat count sync via `subscription_service` on member changes is untested. Cross-tenant reads (user attempting to view an org they do not belong to) are untested.

## 3. Test catalog

1. ID: `orgs.int.001`
   - Name: `test_org_remove_member`
   - Layer: integration
   - File: `apps/api/tests/integration/test_organizations.py`
   - Intent: An org owner can successfully remove a member from the organization via `DELETE`.
   - Setup: Create org with owner A and member B. Auth as owner A.
   - Assertions: `DELETE` returns 204. `GET /members` no longer includes B.
   - Expected runtime: med
   - Dependency: NONE

2. ID: `orgs.int.002`
   - Name: `test_org_member_cannot_update_org`
   - Layer: integration
   - File: `apps/api/tests/integration/test_organizations.py`
   - Intent: A standard member cannot call `PATCH /api/organizations/{org_id}` to change org settings.
   - Setup: Create org, auth as standard member.
   - Assertions: Returns HTTP 403.
   - Expected runtime: med
   - Dependency: NONE

3. ID: `orgs.int.003`
   - Name: `test_org_owner_self_removal_rejected`
   - Layer: integration
   - File: `apps/api/tests/integration/test_organizations.py`
   - Intent: Verify an org owner cannot remove themselves if they are the sole owner.
   - Setup: Create org with owner A. A tries to remove A.
   - Assertions: Returns HTTP 400 or 403 with error explaining sole-owner restriction.
   - Expected runtime: med
   - Dependency: NONE

4. ID: `orgs.int.004`
   - Name: `test_org_cross_tenant_read_403`
   - Layer: integration
   - File: `apps/api/tests/integration/test_organizations.py`
   - Intent: Verify a user cannot read details of an org they are not a member of.
   - Setup: Org 1 with user A. Auth as user B. Call `GET /api/organizations/{org_id_1}`.
   - Assertions: Returns HTTP 403.
   - Expected runtime: med
   - Dependency: NONE

5. ID: `orgs.int.005`
   - Name: `test_org_seat_sync_on_member_add`
   - Layer: integration
   - File: `apps/api/tests/integration/test_organizations.py`
   - Intent: Ensure adding a member to a Studio plan org triggers `_sync_member_plans` and updates the subscription seat count.
   - Setup: Org on Studio plan. Mock/spy on `subscription_service`. Add member.
   - Assertions: Seat count is incremented via `subscription_service`.
   - Expected runtime: med
   - Dependency: NONE

6. ID: `orgs.int.006`
   - Name: `test_org_seat_sync_on_member_remove`
   - Layer: integration
   - File: `apps/api/tests/integration/test_organizations.py`
   - Intent: Ensure removing a member decreases the billed seat count.
   - Setup: Org on Studio plan with 2 members. Owner removes 1.
   - Assertions: Seat count is decremented via `subscription_service`.
   - Expected runtime: med
   - Dependency: NONE

## 4. Code fixes likely required
- None directly anticipated, but testing `_sync_member_plans` might reveal bugs if the integration between `organizations.py` and `billing.py` was loosely coupled and previously untested.
- The sole-owner self-removal logic might be missing, which would result in a bugfix.

## 5. Acceptance criteria
- `organizations.py` reaches effectively 100% route coverage.
- Seat synchronization logic is explicitly covered.
- Cross-tenant and role-based access checks are strictly enforced and tested.
- Zero new skips/xfails.

## 6. Out of scope / deferred
- `test_org_invite_blocked_during_active_trial` (Sprint 3 Batch 3 item #267).

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
