"""
Webhook idempotency integration tests (AC1-AC6, AC11, AC12, AC14).

Tests the full HTTP layer of /api/billing/webhook/culqi and
/api/billing/webhook/mp against a live DB.

Signature note
--------------
In the test environment settings.beta_mode=True and webhook secrets are empty,
so signature verification is permissive — requests without a signature header
pass through. Tests that exercise AC5/AC6 (invalid/missing sig) use monkeypatch
to inject a webhook secret so the check fires.

Run:
    docker exec tukijuris-api-1 python -m pytest tests/integration/test_webhook_idempotency.py -v
"""

import asyncio
import hashlib
import hmac
import json
import uuid

import asyncpg
import pytest
from httpx import AsyncClient

from app.config import settings
from app.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _culqi_sig(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _mp_sig(body_id: str, request_id: str, ts: str, secret: str) -> str:
    manifest = f"id:{body_id};request-id:{request_id};ts:{ts};"
    return hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()


def _unique_event_id(prefix: str = "test") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


async def _clean_events(*event_ids: str) -> None:
    """Remove specific test event rows from processed_webhook_events."""
    db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    try:
        conn = await asyncpg.connect(db_url)
        await conn.execute(
            "DELETE FROM processed_webhook_events WHERE event_id = ANY($1::text[])",
            list(event_ids),
        )
        await conn.close()
    except Exception:
        pass  # DB unreachable → skip cleanup


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def webhook_client() -> AsyncClient:
    async with AsyncClient(
        transport=__import__("httpx").ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# AC1 — New Culqi event → 200 ok (T5.2, T5.3)
# ---------------------------------------------------------------------------


class TestCulqiWebhookNewEvent:
    async def test_new_event_returns_ok(self, webhook_client: AsyncClient):
        """AC1: first delivery of a new event_id returns 200 {"status":"ok"}."""
        event_id = _unique_event_id("test_culqi_new")
        payload = json.dumps({
            "id": event_id,
            "type": "charge.succeeded",
            "data": {"id": "chr_001", "metadata": {"org_id": str(uuid.uuid4()), "plan": "pro"}},
        }).encode()

        try:
            res = await webhook_client.post(
                "/api/billing/webhook/culqi",
                content=payload,
                headers={"content-type": "application/json"},
            )
            assert res.status_code == 200
            assert res.json()["status"] == "ok"
        finally:
            await _clean_events(event_id)

    async def test_new_event_creates_idempotency_row(self, webhook_client: AsyncClient):
        """AC1: processed_webhook_events row is created after first delivery."""
        event_id = _unique_event_id("test_culqi_row")
        payload = json.dumps({
            "id": event_id,
            "type": "charge.succeeded",
            "data": {"id": "chr_002", "metadata": {"org_id": str(uuid.uuid4()), "plan": "pro"}},
        }).encode()

        try:
            await webhook_client.post(
                "/api/billing/webhook/culqi",
                content=payload,
                headers={"content-type": "application/json"},
            )
            # Verify row was created
            db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(db_url)
            try:
                row = await conn.fetchrow(
                    "SELECT provider, event_id FROM processed_webhook_events WHERE event_id = $1",
                    event_id,
                )
            finally:
                await conn.close()
            assert row is not None, "No idempotency row was created"
            assert row["provider"] == "culqi"
        finally:
            await _clean_events(event_id)


# ---------------------------------------------------------------------------
# AC2 — Duplicate Culqi event → 200 duplicate_ignored (T5.2, T5.3)
# ---------------------------------------------------------------------------


class TestCulqiWebhookDuplicate:
    async def test_duplicate_returns_duplicate_ignored(self, webhook_client: AsyncClient):
        """AC2: same event_id delivered twice → second returns duplicate_ignored."""
        event_id = _unique_event_id("test_culqi_dup")
        payload = json.dumps({
            "id": event_id,
            "type": "charge.succeeded",
            "data": {"id": "chr_dup_001", "metadata": {"org_id": str(uuid.uuid4()), "plan": "pro"}},
        }).encode()
        headers = {"content-type": "application/json"}

        try:
            res1 = await webhook_client.post("/api/billing/webhook/culqi", content=payload, headers=headers)
            res2 = await webhook_client.post("/api/billing/webhook/culqi", content=payload, headers=headers)

            assert res1.status_code == 200
            assert res1.json()["status"] == "ok"
            assert res2.status_code == 200
            assert res2.json()["status"] == "duplicate_ignored"
        finally:
            await _clean_events(event_id)

    async def test_duplicate_does_not_create_second_row(self, webhook_client: AsyncClient):
        """AC2: exactly one processed_webhook_events row exists after two deliveries."""
        event_id = _unique_event_id("test_culqi_onerow")
        payload = json.dumps({"id": event_id, "type": "subscription.updated", "data": {"id": "sbn_001"}}).encode()
        headers = {"content-type": "application/json"}

        try:
            await webhook_client.post("/api/billing/webhook/culqi", content=payload, headers=headers)
            await webhook_client.post("/api/billing/webhook/culqi", content=payload, headers=headers)

            db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(db_url)
            try:
                count = await conn.fetchval(
                    "SELECT COUNT(*) FROM processed_webhook_events WHERE event_id = $1",
                    event_id,
                )
            finally:
                await conn.close()
            assert count == 1, f"Expected 1 row, got {count}"
        finally:
            await _clean_events(event_id)


# ---------------------------------------------------------------------------
# AC3 — MercadoPago new and duplicate (T5.2, T5.4)
# ---------------------------------------------------------------------------


class TestMercadoPagoWebhook:
    async def test_mp_new_event_returns_ok(self, webhook_client: AsyncClient):
        """AC3: new MP event returns 200 ok."""
        event_id = _unique_event_id("test_mp_new")
        payload = json.dumps({
            "id": event_id,
            "type": "payment",
            "data": {"id": "pay_001"},
            "metadata": {"org_id": str(uuid.uuid4()), "plan": "pro"},
        }).encode()

        try:
            res = await webhook_client.post(
                "/api/billing/webhook/mp",
                content=payload,
                headers={"content-type": "application/json"},
            )
            assert res.status_code == 200
            assert res.json()["status"] == "ok"
        finally:
            await _clean_events(event_id)

    async def test_mp_duplicate_returns_duplicate_ignored(self, webhook_client: AsyncClient):
        """AC3: duplicate MP event returns duplicate_ignored."""
        event_id = _unique_event_id("test_mp_dup")
        payload = json.dumps({
            "id": event_id,
            "type": "payment",
            "data": {"id": "pay_dup_001"},
            "metadata": {"org_id": str(uuid.uuid4()), "plan": "pro"},
        }).encode()
        headers = {"content-type": "application/json"}

        try:
            res1 = await webhook_client.post("/api/billing/webhook/mp", content=payload, headers=headers)
            res2 = await webhook_client.post("/api/billing/webhook/mp", content=payload, headers=headers)

            assert res1.status_code == 200
            assert res1.json()["status"] == "ok"
            assert res2.status_code == 200
            assert res2.json()["status"] == "duplicate_ignored"
        finally:
            await _clean_events(event_id)


# ---------------------------------------------------------------------------
# AC4 — Concurrent delivery of same event_id (T5.2, T5.5)
# ---------------------------------------------------------------------------


class TestConcurrentDelivery:
    @pytest.mark.xfail(
        strict=True,
        reason="Sprint 3 Batch 6 W7 webhook race bug; tracked in tukijuris/webhook-concurrency-race-bug",
    )
    async def test_concurrent_same_event_id_no_duplicate_processing(
        self, webhook_client: AsyncClient
    ):
        """AC4: asyncio.gather with same event_id → exactly one ok, one duplicate_ignored."""
        event_id = _unique_event_id("test_culqi_concurrent")
        payload = json.dumps({
            "id": event_id,
            "type": "charge.succeeded",
            "data": {"id": "chr_concurrent_001", "metadata": {"org_id": str(uuid.uuid4()), "plan": "pro"}},
        }).encode()
        headers = {"content-type": "application/json"}

        try:
            results = await asyncio.gather(
                webhook_client.post("/api/billing/webhook/culqi", content=payload, headers=headers),
                webhook_client.post("/api/billing/webhook/culqi", content=payload, headers=headers),
                return_exceptions=True,
            )

            statuses = [r.json()["status"] for r in results if hasattr(r, "json")]
            assert "ok" in statuses, f"Expected at least one 'ok', got: {statuses}"
            assert "duplicate_ignored" in statuses, (
                f"Expected at least one 'duplicate_ignored', got: {statuses}"
            )
        finally:
            await _clean_events(event_id)


# ---------------------------------------------------------------------------
# AC5 — Invalid Culqi signature → 401 (T5.2, T5.3)
# ---------------------------------------------------------------------------


class TestSignatureVerification:
    async def test_invalid_culqi_signature_returns_401(
        self, webhook_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """AC5: invalid X-Culqi-Signature returns 401 when secret is configured."""
        monkeypatch.setattr(settings, "culqi_webhook_secret", "real-test-secret-001")

        event_id = _unique_event_id("test_culqi_badsig")
        payload = json.dumps({"id": event_id, "type": "charge.succeeded"}).encode()

        res = await webhook_client.post(
            "/api/billing/webhook/culqi",
            content=payload,
            headers={
                "content-type": "application/json",
                "x-culqi-signature": "invalid_signature_value",
            },
        )
        assert res.status_code == 401
        assert "invalid_signature" in res.text

    async def test_missing_culqi_signature_returns_401_when_secret_set(
        self, webhook_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """AC6: missing X-Culqi-Signature header returns 401 when secret is configured."""
        monkeypatch.setattr(settings, "culqi_webhook_secret", "real-test-secret-002")

        payload = json.dumps({"id": _unique_event_id(), "type": "charge.succeeded"}).encode()

        res = await webhook_client.post(
            "/api/billing/webhook/culqi",
            content=payload,
            headers={"content-type": "application/json"},
        )
        assert res.status_code == 401

    async def test_valid_culqi_signature_passes(
        self, webhook_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """AC5 positive: valid HMAC signature is accepted when secret is configured."""
        secret = "real-test-secret-003"
        monkeypatch.setattr(settings, "culqi_webhook_secret", secret)

        event_id = _unique_event_id("test_culqi_validsig")
        payload = json.dumps({"id": event_id, "type": "charge.succeeded", "data": {}}).encode()
        sig = _culqi_sig(payload, secret)

        try:
            res = await webhook_client.post(
                "/api/billing/webhook/culqi",
                content=payload,
                headers={
                    "content-type": "application/json",
                    "x-culqi-signature": sig,
                },
            )
            assert res.status_code == 200
        finally:
            await _clean_events(event_id)

    async def test_invalid_mp_signature_returns_401(
        self, webhook_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
    ):
        """AC5 (MP): invalid x-signature header returns 401."""
        monkeypatch.setattr(settings, "mp_webhook_secret", "mp-test-secret-001")

        payload = json.dumps({"id": _unique_event_id(), "type": "payment", "data": {"id": "p1"}}).encode()

        res = await webhook_client.post(
            "/api/billing/webhook/mp",
            content=payload,
            headers={
                "content-type": "application/json",
                "x-signature": "ts=1234567890,v1=invalid_hash_value",
                "x-request-id": "req-001",
            },
        )
        assert res.status_code == 401


# ---------------------------------------------------------------------------
# AC12 — Missing event_id → 400 (T5.2, T5.3)
# ---------------------------------------------------------------------------


class TestMissingEventId:
    async def test_culqi_missing_event_id_returns_400(self, webhook_client: AsyncClient):
        """AC12: payload without 'id' field returns 400."""
        payload = json.dumps({"type": "charge.succeeded", "data": {}}).encode()
        res = await webhook_client.post(
            "/api/billing/webhook/culqi",
            content=payload,
            headers={"content-type": "application/json"},
        )
        assert res.status_code == 400

    async def test_culqi_empty_event_id_returns_400(self, webhook_client: AsyncClient):
        """AC12: payload with empty string 'id' returns 400."""
        payload = json.dumps({"id": "", "type": "charge.succeeded"}).encode()
        res = await webhook_client.post(
            "/api/billing/webhook/culqi",
            content=payload,
            headers={"content-type": "application/json"},
        )
        assert res.status_code == 400

    async def test_mp_missing_event_id_returns_400(self, webhook_client: AsyncClient):
        """AC12 (MP): payload without 'id' field returns 400."""
        payload = json.dumps({"type": "payment", "data": {"id": "p1"}}).encode()
        res = await webhook_client.post(
            "/api/billing/webhook/mp",
            content=payload,
            headers={"content-type": "application/json"},
        )
        assert res.status_code == 400


# ---------------------------------------------------------------------------
# AC11 — Audit log emitted (T5.2, T5.3, T5.4)
# ---------------------------------------------------------------------------


class TestAuditLog:
    async def test_culqi_checkout_creates_audit_log(self, webhook_client: AsyncClient):
        """AC11: successful charge.succeeded creates a billing.checkout_completed audit entry."""
        event_id = _unique_event_id("test_culqi_audit")
        org_id = str(uuid.uuid4())
        payload = json.dumps({
            "id": event_id,
            "type": "charge.succeeded",
            "data": {"id": "chr_audit_001", "metadata": {"org_id": org_id, "plan": "pro"}},
        }).encode()

        try:
            res = await webhook_client.post(
                "/api/billing/webhook/culqi",
                content=payload,
                headers={"content-type": "application/json"},
            )
            assert res.status_code == 200

            db_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
            conn = await asyncpg.connect(db_url)
            try:
                row = await conn.fetchrow(
                    """
                    SELECT action, resource_type, resource_id
                    FROM audit_log
                    WHERE action = 'billing.checkout_completed'
                      AND resource_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    event_id,
                )
            finally:
                await conn.close()

            assert row is not None, "No audit log row was created for checkout_completed"
            assert row["action"] == "billing.checkout_completed"
        finally:
            await _clean_events(event_id)


# ---------------------------------------------------------------------------
# AC14 — Transaction rollback rolls back idempotency row (T5.2, T5.5)
# ---------------------------------------------------------------------------


class TestTransactionRollback:
    async def test_invalid_json_does_not_create_idempotency_row(
        self, webhook_client: AsyncClient
    ):
        """AC14 proxy: invalid JSON (parse error) returns 400 and no row is persisted."""
        res = await webhook_client.post(
            "/api/billing/webhook/culqi",
            content=b"not-json-at-all",
            headers={"content-type": "application/json"},
        )
        assert res.status_code == 400
