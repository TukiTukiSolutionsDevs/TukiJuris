---
change: backend-saas-test-coverage
spec: billing
status: proposed
created: 2026-04-19
---

# Spec — Billing test coverage

## 1. Scope
Coverage for the billing domain, specifically addressing deferred warnings from `payment-webhook-idempotency` and `trials-lifecycle`. Covers Webhook HMAC tamper detection, plan downgrade handler logic, trial retry edge cases, and `me_invoices` access gates.
Deliberately OUT:
- Sprint 3 Batch 6 items (webhook concurrency race W7 bug, F8 refund webhook handler, F2 PLAN_PRICING dedupe).
- MP missing-header test (Sprint 3 Batch 3).

## 2. Current state
- Existing tests: ~14 files including `test_billing.py`, `test_webhook_idempotency.py`, `test_invoice_service.py`, `test_trial_service.py`. Excellent coverage.
- Known gaps: `_verify_culqi_hmac` and `_verify_mp_hmac` tampered signatures, `_handle_subscription_deleted` downgrade logic, `me_invoices` org 403, and `retry_charge` when `TRIALS_ENABLED=False`.
- Pre-existing failures: 1 known (webhook race bug W7 in billing.py), tracking in Batch 6.

## 3. Test catalog

1. ID: `billing.unit.001`
   - Name: `test_verify_culqi_hmac_tampered`
   - Layer: unit
   - File: `apps/api/tests/unit/test_payment_webhooks.py`
   - Intent: Ensure Culqi webhook validation fails with an invalid or tampered signature.
   - Setup: Generate valid payload, pass incorrect HMAC header.
   - Assertions: Function returns `False`.
   - Expected runtime: fast
   - Dependency: NONE

2. ID: `billing.unit.002`
   - Name: `test_verify_mp_hmac_tampered`
   - Layer: unit
   - File: `apps/api/tests/unit/test_payment_webhooks.py`
   - Intent: Ensure MP webhook validation fails with an invalid or tampered signature.
   - Setup: Generate valid payload, pass incorrect MP signature string.
   - Assertions: Function returns `False`.
   - Expected runtime: fast
   - Dependency: NONE

3. ID: `billing.unit.003`
   - Name: `test_handle_subscription_deleted_downgrade`
   - Layer: unit
   - File: `apps/api/tests/unit/test_subscription_service.py`
   - Intent: Verify that a subscription deletion event correctly triggers a downgrade to the free plan and handles retention logic.
   - Setup: Mock DB, active pro subscription.
   - Assertions: User plan reverts to `free`, DB updated successfully.
   - Expected runtime: fast
   - Dependency: NONE

4. ID: `billing.unit.004`
   - Name: `test_handle_payment_failed_notification_triggered`
   - Layer: unit
   - File: `apps/api/tests/unit/test_subscription_service.py`
   - Intent: Ensure that a failed payment webhook successfully enqueues or triggers a notification to the owner.
   - Setup: Mock `notification_service`.
   - Assertions: `notification_service.create` is called with failure reason.
   - Expected runtime: fast
   - Dependency: NONE

5. ID: `billing.int.001`
   - Name: `test_me_invoices_non_member_403`
   - Layer: integration
   - File: `apps/api/tests/integration/test_me_invoices.py`
   - Intent: Check that accessing `GET /api/billing/{org_id}/invoices` for an org the user does not belong to returns 403.
   - Setup: Create org with user A, authenticate as user B.
   - Assertions: HTTP 403.
   - Expected runtime: med
   - Dependency: NONE

6. ID: `billing.int.002`
   - Name: `test_retry_charge_trials_disabled`
   - Layer: integration
   - File: `apps/api/tests/integration/test_trials_routes.py`
   - Intent: Verify `POST /api/trials/retry-charge` returns a 404/503 appropriately when the feature flag `TRIALS_ENABLED` is False.
   - Setup: Override app settings `TRIALS_ENABLED=False`.
   - Assertions: Returns HTTP 404/503.
   - Expected runtime: med
   - Dependency: NONE

## 4. Code fixes likely required
- None anticipated for testability; these cover already implemented code paths from previous architectural changes (e.g. `payment-webhook-idempotency` deferred warnings).

## 5. Acceptance criteria
- All tests in §3 pass.
- Zero new skips/xfails.
- HMAC verification has dedicated tamper-detection unit tests.
- Deferred payment-webhook-idempotency warnings (related to testing) are resolved.

## 6. Out of scope / deferred
- MP missing-header test (in Sprint 3 Batch 3).
- `test_org_invite_blocked_during_active_trial` (in Sprint 3 Batch 3).
- Webhook concurrency race bug (W7) -> Sprint 3 Batch 6.
- hmac compare_digest raw bytes refactor -> Sprint 3 Batch 6.
- PATCH 409 vs 422 reconcile -> Sprint 3 Batch 6.

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
- Engram memory: `tukijuris/webhook-concurrency-race-bug`
