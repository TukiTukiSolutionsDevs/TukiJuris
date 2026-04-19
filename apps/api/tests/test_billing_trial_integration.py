"""Tests — billing webhook trial branches (TD.4).

Validates that:
  - Culqi charge.succeeded with metadata.trial_id → mark_charged called (not _handle_checkout_completed)
  - Culqi charge.succeeded without trial_id → normal checkout path unchanged
  - MP preapproval with matching trial provider_card_token → mark_charged called
  - MP preapproval with no matching trial → normal subscription update path

Direct handler calls (same pattern as test_billing_webhook_invoice_creation.py).
No real DB required.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_billing_trial_integration.py -v
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_request(raw: bytes) -> MagicMock:
    req = MagicMock()
    req.body = AsyncMock(return_value=raw)
    req.headers = {}
    return req


def _make_idem(is_new: bool = True) -> MagicMock:
    idem = MagicMock()
    idem.record_and_check = AsyncMock(return_value=(is_new, MagicMock()))
    idem.update_response = AsyncMock()
    return idem


def _make_audit() -> MagicMock:
    audit = MagicMock()
    audit.log_action = AsyncMock()
    return audit


def _mock_db(trial=None) -> AsyncMock:
    """DB mock that returns a trial (or None) for Trial lookups."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = trial
    db.execute = AsyncMock(return_value=mock_result)
    return db


def _make_trial_svc() -> MagicMock:
    svc = MagicMock()
    svc.mark_charged = AsyncMock()
    return svc


def _culqi_payload_with_trial(trial_id: str, charge_id: str | None = None) -> bytes:
    cid = charge_id or f"chr_{uuid.uuid4().hex[:10]}"
    return json.dumps({
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": "charge.succeeded",
        "data": {
            "id": cid,
            "metadata": {
                "trial_id": trial_id,
                "user_id": str(uuid.uuid4()),
                "plan_code": "pro",
            },
        },
        "metadata": {
            "trial_id": trial_id,
            "user_id": str(uuid.uuid4()),
            "plan_code": "pro",
        },
    }).encode()


def _culqi_payload_without_trial(org_id: str | None = None, plan: str = "pro") -> bytes:
    oid = org_id or str(uuid.uuid4())
    cid = f"chr_{uuid.uuid4().hex[:10]}"
    return json.dumps({
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": "charge.succeeded",
        "data": {
            "id": cid,
            "metadata": {"org_id": oid, "plan": plan, "seats_count": 0},
        },
        "metadata": {"org_id": oid, "plan": plan, "seats_count": 0},
    }).encode()


def _mp_preapproval_payload(preapproval_id: str, status: str = "authorized") -> bytes:
    return json.dumps({
        "id": f"evt_{uuid.uuid4().hex[:10]}",
        "type": "preapproval",
        "status": status,
        "data": {"id": preapproval_id},
        "metadata": {"org_id": str(uuid.uuid4()), "plan": "pro"},
    }).encode()


# ---------------------------------------------------------------------------
# Culqi charge.succeeded — trial path
# ---------------------------------------------------------------------------


class TestCulqiTrialBranch:
    @pytest.mark.asyncio
    async def test_charge_succeeded_with_trial_id_calls_mark_charged(self):
        """trial_id in metadata → mark_charged called, no _handle_checkout_completed."""
        from app.api.routes.billing import culqi_webhook

        trial_id = uuid.uuid4()
        charge_id = f"chr_{uuid.uuid4().hex[:10]}"
        raw = _culqi_payload_with_trial(str(trial_id), charge_id)

        db = _mock_db()
        trial_svc = _make_trial_svc()
        idem = _make_idem()
        inv_svc = MagicMock()
        inv_svc.create_from_culqi_charge = AsyncMock()

        with patch("app.config.settings") as mock_settings, \
             patch("app.api.routes.billing._handle_checkout_completed") as mock_checkout:
            mock_settings.culqi_webhook_secret = None

            result = await culqi_webhook(
                request=_make_request(raw),
                db=db,
                audit=_make_audit(),
                idem=idem,
                inv_svc=inv_svc,
                trial_svc=trial_svc,
            )

        assert result == {"status": "ok"}
        trial_svc.mark_charged.assert_called_once_with(
            trial_id, charge_id=charge_id, provider="culqi"
        )
        mock_checkout.assert_not_called()
        # No invoice created for trial charges
        inv_svc.create_from_culqi_charge.assert_not_called()

    @pytest.mark.asyncio
    async def test_charge_succeeded_invalid_trial_uuid_does_not_crash(self):
        """Invalid trial_id UUID → exception caught, webhook still returns ok."""
        from app.api.routes.billing import culqi_webhook

        raw = json.dumps({
            "id": f"evt_{uuid.uuid4().hex[:10]}",
            "type": "charge.succeeded",
            "data": {
                "id": "chr_test",
                "metadata": {"trial_id": "not-a-uuid"},
            },
            "metadata": {"trial_id": "not-a-uuid"},
        }).encode()

        db = _mock_db()
        trial_svc = _make_trial_svc()
        idem = _make_idem()

        with patch("app.config.settings") as mock_settings:
            mock_settings.culqi_webhook_secret = None

            result = await culqi_webhook(
                request=_make_request(raw),
                db=db,
                audit=_make_audit(),
                idem=_make_idem(),
                inv_svc=MagicMock(),
                trial_svc=trial_svc,
            )

        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_charge_succeeded_without_trial_id_takes_normal_path(self):
        """No trial_id → normal _handle_checkout_completed path, no mark_charged."""
        from app.api.routes.billing import culqi_webhook

        raw = _culqi_payload_without_trial()

        db = _mock_db()
        trial_svc = _make_trial_svc()
        idem = _make_idem()

        with patch("app.config.settings") as mock_settings, \
             patch("app.api.routes.billing._handle_checkout_completed") as mock_checkout:
            mock_settings.culqi_webhook_secret = None

            result = await culqi_webhook(
                request=_make_request(raw),
                db=db,
                audit=_make_audit(),
                idem=idem,
                inv_svc=MagicMock(),
                trial_svc=trial_svc,
            )

        assert result == {"status": "ok"}
        mock_checkout.assert_called_once()
        trial_svc.mark_charged.assert_not_called()

    @pytest.mark.asyncio
    async def test_duplicate_culqi_event_returns_duplicate_ignored(self):
        """Duplicate event_id → idempotency check returns is_new=False → skip."""
        from app.api.routes.billing import culqi_webhook

        trial_id = uuid.uuid4()
        raw = _culqi_payload_with_trial(str(trial_id))

        idem = _make_idem(is_new=False)
        trial_svc = _make_trial_svc()

        with patch("app.config.settings") as mock_settings:
            mock_settings.culqi_webhook_secret = None

            result = await culqi_webhook(
                request=_make_request(raw),
                db=_mock_db(),
                audit=_make_audit(),
                idem=idem,
                inv_svc=MagicMock(),
                trial_svc=trial_svc,
            )

        assert result == {"status": "duplicate_ignored"}
        trial_svc.mark_charged.assert_not_called()


# ---------------------------------------------------------------------------
# MP preapproval — trial path
# ---------------------------------------------------------------------------


class TestMPTrialBranch:
    @pytest.mark.asyncio
    async def test_preapproval_with_matching_trial_calls_mark_charged(self):
        """Preapproval event + matching trial in DB → mark_charged called."""
        from app.api.routes.billing import mercadopago_webhook

        preapproval_id = f"preaprob_{uuid.uuid4().hex[:10]}"
        trial_id = uuid.uuid4()

        # DB mock returns a trial with matching provider_card_token
        trial = MagicMock()
        trial.id = trial_id
        db = _mock_db(trial=trial)

        trial_svc = _make_trial_svc()
        raw = _mp_preapproval_payload(preapproval_id, status="authorized")

        with patch("app.config.settings") as mock_settings, \
             patch("app.api.routes.billing._handle_subscription_updated") as mock_sub_update:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=_make_audit(),
                idem=_make_idem(),
                inv_svc=MagicMock(),
                trial_svc=trial_svc,
            )

        assert result == {"status": "ok"}
        trial_svc.mark_charged.assert_called_once_with(
            trial_id, charge_id=preapproval_id, provider="mp"
        )
        mock_sub_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_preapproval_cancelled_with_trial_does_not_mark_charged(self):
        """Preapproval cancelled + trial found → cancelled branch, no mark_charged."""
        from app.api.routes.billing import mercadopago_webhook

        preapproval_id = f"preaprob_{uuid.uuid4().hex[:10]}"
        trial = MagicMock()
        trial.id = uuid.uuid4()
        db = _mock_db(trial=trial)

        trial_svc = _make_trial_svc()
        raw = _mp_preapproval_payload(preapproval_id, status="cancelled")

        with patch("app.config.settings") as mock_settings, \
             patch("app.api.routes.billing._handle_subscription_deleted") as mock_sub_del:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=_make_audit(),
                idem=_make_idem(),
                inv_svc=MagicMock(),
                trial_svc=trial_svc,
            )

        assert result == {"status": "ok"}
        trial_svc.mark_charged.assert_not_called()
        mock_sub_del.assert_called_once()

    @pytest.mark.asyncio
    async def test_preapproval_no_matching_trial_takes_subscription_path(self):
        """Preapproval + no matching trial → subscription update path."""
        from app.api.routes.billing import mercadopago_webhook

        preapproval_id = f"preaprob_{uuid.uuid4().hex[:10]}"
        db = _mock_db(trial=None)  # No trial found

        trial_svc = _make_trial_svc()
        raw = _mp_preapproval_payload(preapproval_id, status="authorized")

        with patch("app.config.settings") as mock_settings, \
             patch("app.api.routes.billing._handle_subscription_updated") as mock_sub_update:
            mock_settings.mp_webhook_secret = None

            result = await mercadopago_webhook(
                request=_make_request(raw),
                db=db,
                audit=_make_audit(),
                idem=_make_idem(),
                inv_svc=MagicMock(),
                trial_svc=trial_svc,
            )

        assert result == {"status": "ok"}
        trial_svc.mark_charged.assert_not_called()
        mock_sub_update.assert_called_once()
