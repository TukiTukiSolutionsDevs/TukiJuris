---
change: backend-saas-test-coverage
spec: auth
status: proposed
created: 2026-04-19
---

# Spec — Auth test coverage

## 1. Scope
Coverage for authentication and OAuth routes/services, filling gaps left from prior Sprints. 
Deliberately OUT: 
- Frontend e2e tests (like `login-page e2e`) which are part of Sprint 3 Batch 3.

## 2. Current state
- Existing tests: ~7 files in `tests/unit/test_refresh_*.py`, plus `test_auth.py`, `test_oauth_*.py`, `test_logout.py`, `test_me_endpoint.py`. Excellent overall coverage.
- Known gaps: `GET /api/auth/sessions` (list), `PUT /api/auth/me` input validation, OAuth Microsoft callback error handling, `_has_privileged_role` internal helper isolation.
- Pre-existing failures: 1 known (webhook race bug W7), unrelated to this domain.

## 3. Test catalog

1. ID: `auth.unit.001`
   - Name: `test_auth_sessions_list_shape`
   - Layer: unit
   - File: `apps/api/tests/unit/test_auth_sessions.py`
   - Intent: Ensure `GET /api/auth/sessions` returns the correct list of active sessions for the user.
   - Setup: Mock DB with 2 active sessions and 1 expired session.
   - Assertions: Returns HTTP 200, length is 2, fields include `id`, `user_agent`, `ip_address`, `last_active`.
   - Expected runtime: fast (<100ms)
   - Dependency: NONE

2. ID: `auth.unit.002`
   - Name: `test_profile_update_validation_rejected`
   - Layer: unit
   - File: `apps/api/tests/unit/test_auth_me.py`
   - Intent: Ensure `PUT /api/auth/me` with invalid data (e.g., malformed email, too long name) returns HTTP 422.
   - Setup: Auth fixture.
   - Assertions: Returns HTTP 422 Unprocessable Entity.
   - Expected runtime: fast
   - Dependency: NONE

3. ID: `auth.unit.003`
   - Name: `test_has_privileged_role_helper_false`
   - Layer: unit
   - File: `apps/api/tests/unit/test_auth_helpers.py`
   - Intent: Verify `_has_privileged_role` isolated helper returns False for non-privileged users.
   - Setup: Mock user object with standard role.
   - Assertions: Function returns `False`.
   - Expected runtime: fast
   - Dependency: NONE

4. ID: `auth.unit.004`
   - Name: `test_oauth_microsoft_code_exchange_failure`
   - Layer: unit
   - File: `apps/api/tests/unit/test_oauth_microsoft.py`
   - Intent: Test Microsoft OAuth callback path when token exchange returns an error (HTTP 400 from MS).
   - Setup: Mock `httpx.AsyncClient.post` to return 400.
   - Assertions: Returns HTTP 400 to user with explicit error message.
   - Expected runtime: fast
   - Dependency: NONE

5. ID: `auth.int.001`
   - Name: `test_onboarding_complete_invalid_body`
   - Layer: integration
   - File: `apps/api/tests/integration/test_onboarding_flow.py`
   - Intent: Submitting an invalid body to `POST /api/auth/me/onboarding` fails.
   - Setup: DB fixture, valid user access token.
   - Assertions: HTTP 422 response.
   - Expected runtime: med
   - Dependency: NONE

6. ID: `auth.int.002`
   - Name: `test_refresh_token_wrong_type_rejected`
   - Layer: integration
   - File: `apps/api/tests/integration/test_refresh_token.py`
   - Intent: Explicitly verify that presenting an access token (type='access') to `/api/auth/refresh` fails.
   - Setup: Generate valid access token.
   - Assertions: HTTP 401 Unauthorized.
   - Expected runtime: med
   - Dependency: NONE

## 4. Code fixes likely required
- None anticipated; the tests are targeting existing hardened implementations lacking explicit test suite coverage.

## 5. Acceptance criteria
- All tests in §3 pass.
- Zero new skips/xfails.
- Test coverage for `apps/api/app/api/routes/auth.py` and `oauth.py` reaches effectively 100% (minus acceptable `pragma: no cover`).
- No regression in the 1111 currently-passing tests.

## 6. Out of scope / deferred
- `login-page e2e` frontend tests (Sprint 3 Batch 3 item).
- Fixing `redirect_slashes` cross-origin bug.

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
