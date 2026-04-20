"""Unit tests — billing webhook HMAC helpers (billing.unit.001, billing.unit.002).

Tests _verify_culqi_hmac and _verify_mp_hmac tamper-detection.
Pure-function helpers — no DB or Redis required.

Run:
    docker exec tukijuris-api-1 pytest tests/unit/test_payment_webhooks.py -v
"""

import hashlib
import hmac
import json

import pytest

from app.api.routes.billing import _verify_culqi_hmac, _verify_mp_hmac


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _culqi_sig(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _mp_sig(data_id: str, request_id: str, ts: str, secret: str) -> str:
    manifest = f"id:{data_id};request-id:{request_id};ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


# ---------------------------------------------------------------------------
# billing.unit.001 — Culqi HMAC tamper detection
# ---------------------------------------------------------------------------


class TestVerifyCulqiHmac:
    """billing.unit.001 — _verify_culqi_hmac rejects tampered signatures."""

    SECRET = "culqi_test_secret_abc123"
    BODY = b'{"type":"charge.succeeded","id":"evt_001","data":{"id":"chg_001"}}'

    def test_valid_signature_accepted(self):
        sig = _culqi_sig(self.BODY, self.SECRET)
        assert _verify_culqi_hmac(self.BODY, sig, self.SECRET) is True

    def test_tampered_body_rejected(self):
        """Changing the body invalidates the signature."""
        sig = _culqi_sig(self.BODY, self.SECRET)
        tampered = self.BODY.replace(b"charge.succeeded", b"charge.failed")
        assert _verify_culqi_hmac(tampered, sig, self.SECRET) is False

    def test_tampered_signature_rejected(self):
        """Flipping the first char of the signature causes mismatch."""
        sig = _culqi_sig(self.BODY, self.SECRET)
        bad_sig = ("f" if sig[0] != "f" else "0") + sig[1:]
        assert _verify_culqi_hmac(self.BODY, bad_sig, self.SECRET) is False

    def test_wrong_secret_rejected(self):
        sig = _culqi_sig(self.BODY, self.SECRET)
        assert _verify_culqi_hmac(self.BODY, sig, "wrong_secret") is False


# ---------------------------------------------------------------------------
# billing.unit.002 — MercadoPago HMAC tamper detection
# ---------------------------------------------------------------------------


class TestVerifyMpHmac:
    """billing.unit.002 — _verify_mp_hmac rejects tampered signatures."""

    SECRET = "mp_test_secret_xyz789"
    DATA_ID = "pay_12345"
    REQUEST_ID = "req-abc-001"
    TS = "1700000000"

    def _body(self, data_id: str | None = None) -> bytes:
        return json.dumps({
            "id": "evt_mp_001",
            "type": "payment",
            "data": {"id": data_id or self.DATA_ID},
        }).encode()

    def _sig_header(self, data_id: str | None = None) -> str:
        v1 = _mp_sig(data_id or self.DATA_ID, self.REQUEST_ID, self.TS, self.SECRET)
        return f"ts={self.TS},v1={v1}"

    def test_valid_signature_accepted(self):
        body = self._body()
        sig = self._sig_header()
        assert _verify_mp_hmac(body, sig, self.REQUEST_ID, self.SECRET) is True

    def test_tampered_data_id_rejected(self):
        """Body contains a different data_id than what was signed."""
        body = self._body(data_id="pay_TAMPERED")
        sig = self._sig_header(data_id=self.DATA_ID)  # signed original
        assert _verify_mp_hmac(body, sig, self.REQUEST_ID, self.SECRET) is False

    def test_corrupted_v1_hash_rejected(self):
        body = self._body()
        zeroed_sig = f"ts={self.TS},v1=" + "0" * 64
        assert _verify_mp_hmac(body, zeroed_sig, self.REQUEST_ID, self.SECRET) is False

    def test_missing_ts_rejected(self):
        """x-signature without ts= part returns False."""
        body = self._body()
        v1 = _mp_sig(self.DATA_ID, self.REQUEST_ID, self.TS, self.SECRET)
        sig_no_ts = f"v1={v1}"  # ts omitted
        assert _verify_mp_hmac(body, sig_no_ts, self.REQUEST_ID, self.SECRET) is False

    def test_wrong_secret_rejected(self):
        body = self._body()
        sig = self._sig_header()
        assert _verify_mp_hmac(body, sig, self.REQUEST_ID, "wrong_secret") is False
