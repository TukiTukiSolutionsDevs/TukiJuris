# fix-payment-failed-notification

## Proposal
When Culqi/MP webhook fires `_handle_payment_failed`, the handler only marks the
subscription `past_due`. It does NOT notify the org owner — silent failure.

## Spec
- Create an in-app notification (`payment.failed`) for the org owner.
- Send a `payment_failed` email to the org owner.
- Both dispatches are fail-safe: a failure must never prevent the `past_due` stamp.
- Owner resolved via `OrgMembership.role == "owner"` (no direct owner FK on Organization).

## Design
Inside `_handle_payment_failed`, after `await db.flush()` (past_due stamp):
1. Query `OrgMembership` (role=owner, is_active=True) for the subscription's org.
2. Query `User` from membership.user_id.
3. `notification_service.create(db, user_id, type, title, message, action_url)`.
4. `db.flush()` after notification.
5. Query `Organization` for org.name, then `email_service.send_payment_failed(to, org_name, plan)`.
6. Outer try/except guards (1-5) so past_due is always preserved.
7. Inner try/except guards (5) so email failure doesn't kill the notification.

## Tasks
- [x] Add `PAYMENT_FAILED_TEMPLATE` + `send_payment_failed` to `EmailService`
- [x] Add top-level imports (`notification_service`, `email_service`) to `billing.py`
- [x] Add notification + email block in `_handle_payment_failed`
- [x] Rewrite `test_handle_payment_failed_notification_triggered` (remove xfail)
- [x] All tests pass: 1233 passed, 9 xfailed, 0 failed
