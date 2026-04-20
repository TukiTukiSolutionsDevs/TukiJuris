---
change: backend-saas-test-coverage
spec: notifications
status: proposed
created: 2026-04-19
---

# Spec — Notifications test coverage

## 1. Scope
Coverage for the `notifications.py` and `emails.py` domains. This includes the entire notification CRUD lifecycle (create, list with pagination, mark-as-read, clear-all, preferences), email sending paths, and bounce handling fallback. As there is currently no test coverage for this 377-line domain, the focus is on establishing baseline functional behavior and security isolation.

## 2. Current state
- Existing tests: 0 tests for both `notifications.py` and `emails.py`.
- Known gaps: The entire domain is dark. Auth gates, ownership isolation, pagination, notification counting, and email provider abstractions are entirely untested.
- Pre-existing failures unrelated: None.

## 3. Test catalog
1. `notifications.unit.001`
   - Name: `test_notification_list_401_no_auth`
   - Layer: integration
   - File: `apps/api/tests/integration/test_notifications.py`
   - Intent: Ensure the notifications endpoints block unauthenticated requests.
   - Setup: No token
   - Assertions: GET `/api/notifications/` returns 401 Unauthorized.
   - Expected runtime: fast
   - Dependency: NONE
2. `notifications.unit.002`
   - Name: `test_notification_create_system_to_user`
   - Layer: unit
   - File: `apps/api/tests/unit/test_notification_service.py`
   - Intent: Validate the internal service can construct and persist a system notification.
   - Setup: Mock DB, User A
   - Assertions: Service successfully writes to DB; `is_read` defaults to False.
   - Expected runtime: fast
   - Dependency: NONE
3. `notifications.unit.003`
   - Name: `test_notification_list_pagination`
   - Layer: integration
   - File: `apps/api/tests/integration/test_notifications.py`
   - Intent: Verify pagination parameters on the notifications list endpoint.
   - Setup: User A with 15 notifications
   - Assertions: GET with `limit=10` returns exactly 10 items.
   - Expected runtime: fast
   - Dependency: NONE
4. `notifications.unit.004`
   - Name: `test_notification_unread_count`
   - Layer: integration
   - File: `apps/api/tests/integration/test_notifications.py`
   - Intent: Validate the unread-count endpoint returns accurate aggregations.
   - Setup: User A with 3 unread, 2 read notifications
   - Assertions: GET `/api/notifications/unread-count` returns `{"count": 3}`.
   - Expected runtime: fast
   - Dependency: NONE
5. `notifications.unit.005`
   - Name: `test_notification_mark_read_happy_path`
   - Layer: integration
   - File: `apps/api/tests/integration/test_notifications.py`
   - Intent: Verify an individual notification can be marked as read.
   - Setup: User A, Unread Notification A
   - Assertions: PATCH to `{id}/read` returns 200; `is_read` changes to True.
   - Expected runtime: fast
   - Dependency: NONE
6. `notifications.unit.006`
   - Name: `test_notification_mark_read_ownership_404`
   - Layer: integration
   - File: `apps/api/tests/integration/test_notifications.py`
   - Intent: Prevent cross-tenant data modification.
   - Setup: User A, User B, Notification B (owned by B)
   - Assertions: User A PATCH to `Notification B` returns 403 or 404.
   - Expected runtime: fast
   - Dependency: NONE
7. `notifications.unit.007`
   - Name: `test_notification_clear_all_for_user`
   - Layer: integration
   - File: `apps/api/tests/integration/test_notifications.py`
   - Intent: Validate the mark-all-read bulk endpoint.
   - Setup: User A with 5 unread notifications
   - Assertions: PATCH `/api/notifications/read-all` returns 200; all 5 become read.
   - Expected runtime: fast
   - Dependency: NONE
8. `notifications.unit.008`
   - Name: `test_notification_preferences_crud`
   - Layer: integration
   - File: `apps/api/tests/integration/test_notifications.py`
   - Intent: Ensure a user can update their opt-in/opt-out notification settings.
   - Setup: User A
   - Assertions: PATCH updates preferences; GET reflects them.
   - Expected runtime: fast
   - Dependency: NONE
9. `notifications.unit.009`
   - Name: `test_email_password_reset_request_flow`
   - Layer: integration
   - File: `apps/api/tests/integration/test_emails.py`
   - Intent: Validate that requesting a password reset fires an email.
   - Setup: User A, Mocked Email Provider
   - Assertions: Returns 200; mock provider tracks an outbound email.
   - Expected runtime: fast
   - Dependency: NONE
10. `notifications.unit.010`
    - Name: `test_email_password_reset_confirm_flow`
    - Layer: integration
    - File: `apps/api/tests/integration/test_emails.py`
    - Intent: Validate that a valid token allows password change.
    - Setup: Valid reset token generated
    - Assertions: Submitting the valid token changes password and invalidates token.
    - Expected runtime: fast
    - Dependency: NONE
11. `notifications.unit.011`
    - Name: `test_email_send_mock_provider_happy_path`
    - Layer: unit
    - File: `apps/api/tests/unit/test_email_service.py`
    - Intent: Validate `email_service.py` sends generic payloads cleanly.
    - Setup: Mock Email Adapter
    - Assertions: `send_email` executes without raising errors and formats HTML.
    - Expected runtime: fast
    - Dependency: NONE
12. `notifications.unit.012`
    - Name: `test_email_bounce_handling_fallback`
    - Layer: unit
    - File: `apps/api/tests/unit/test_email_service.py`
    - Intent: Ensure external email provider errors are caught gracefully.
    - Setup: Mock Email Adapter raising HTTPException
    - Assertions: Exception is logged/handled, preventing 500 crashes on non-critical paths.
    - Expected runtime: fast
    - Dependency: NONE

## 4. Code fixes likely required
- None inherently expected unless the `email_service.py` is entirely broken due to missing environment variables. Tests will need to patch/mock the provider.

## 5. Acceptance criteria
- All 12 tests pass.
- Zero new unjustified skips.
- Coverage delta target ≥ 85% for `notifications.py` and `emails.py`.
- No regression in the 1111 currently-passing tests.

## 6. Out of scope / deferred
- Real email provider tests (e.g. Resend/SendGrid) are blocked pending Item 3b from Sprint 3. The specs deliberately use mock providers to test the domain logic without external I/O.
- Frontend tests.

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
- Prior relevant archives (cite engram topic keys)
