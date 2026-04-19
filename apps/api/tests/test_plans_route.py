"""Integration tests for GET /api/plans.

Covers all 18 ACs from the get-plans-endpoint spec.
Uses the shared unauthenticated `client` fixture (httpx AsyncClient via ASGITransport).
No @pytest.mark.asyncio needed — pytest-asyncio is configured globally (auto mode).

Run:
    docker exec tukijuris-api-1 python -m pytest tests/test_plans_route.py -v
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.config import settings


# ---------------------------------------------------------------------------
# AC1 — no auth required, 200 OK
# ---------------------------------------------------------------------------


async def test_get_plans_no_auth_returns_200(client: AsyncClient):
    """GET /api/plans without Authorization header returns 200."""
    res = await client.get("/api/plans")
    assert res.status_code == 200


async def test_get_plans_ignores_auth_header(client: AsyncClient):
    """GET /api/plans with a bogus Bearer token still returns 200 (no auth gate)."""
    res = await client.get("/api/plans", headers={"Authorization": "Bearer bogus"})
    assert res.status_code == 200


# ---------------------------------------------------------------------------
# AC2 — response root shape
# ---------------------------------------------------------------------------


async def test_response_root_keys(client: AsyncClient):
    """Response root contains exactly plans, beta_mode, currency_default."""
    res = await client.get("/api/plans")
    data = res.json()
    assert set(data.keys()) == {"plans", "beta_mode", "currency_default"}


async def test_currency_default_is_pen(client: AsyncClient):
    """Root currency_default is PEN."""
    res = await client.get("/api/plans")
    assert res.json()["currency_default"] == "PEN"


async def test_plans_is_list(client: AsyncClient):
    """Root plans field is a list."""
    res = await client.get("/api/plans")
    assert isinstance(res.json()["plans"], list)


# ---------------------------------------------------------------------------
# AC3 — order: free → pro → studio
# ---------------------------------------------------------------------------


async def test_plans_ordered_free_pro_studio(client: AsyncClient):
    """Plans array is exactly ordered: free, pro, studio."""
    res = await client.get("/api/plans")
    ids = [p["id"] for p in res.json()["plans"]]
    assert ids == ["free", "pro", "studio"]


async def test_exactly_three_plans(client: AsyncClient):
    """Response contains exactly three plans."""
    res = await client.get("/api/plans")
    assert len(res.json()["plans"]) == 3


# ---------------------------------------------------------------------------
# AC4 — every plan has required structural fields
# ---------------------------------------------------------------------------


async def test_each_plan_has_required_keys(client: AsyncClient):
    """Every plan entry has all required fields."""
    required = {
        "id", "display_name", "currency",
        "base_price", "seat_price", "base_seats_included",
        "subtotal_amount", "tax_amount", "total_amount",
        "features", "limits", "byok_supported",
    }
    res = await client.get("/api/plans")
    for plan in res.json()["plans"]:
        missing = required - set(plan.keys())
        assert not missing, f"Plan {plan['id']} missing fields: {missing}"


async def test_every_plan_currency_is_pen(client: AsyncClient):
    """Every plan has currency=PEN."""
    res = await client.get("/api/plans")
    for plan in res.json()["plans"]:
        assert plan["currency"] == "PEN", f"{plan['id']} currency mismatch"


# ---------------------------------------------------------------------------
# AC5 — every plan has subtotal_amount, tax_amount, total_amount
# ---------------------------------------------------------------------------


async def test_all_plans_have_amount_fields(client: AsyncClient):
    """Every plan includes subtotal_amount, tax_amount, total_amount as strings."""
    res = await client.get("/api/plans")
    for plan in res.json()["plans"]:
        for field in ("subtotal_amount", "tax_amount", "total_amount"):
            assert field in plan
            # Pydantic v2 serializes Decimal as string
            assert isinstance(plan[field], str), (
                f"{plan['id']}.{field} should be a string, got {type(plan[field])}"
            )


# ---------------------------------------------------------------------------
# AC6 — free plan: base=0.00, total=0.00
# ---------------------------------------------------------------------------


async def test_free_plan_zero_pricing(client: AsyncClient):
    """Free plan: base_price, total_amount, tax_amount, subtotal_amount all 0.00."""
    res = await client.get("/api/plans")
    free = res.json()["plans"][0]
    assert free["id"] == "free"
    assert free["base_price"] == "0.00"
    assert free["seat_price"] == "0.00"
    assert free["subtotal_amount"] == "0.00"
    assert free["tax_amount"] == "0.00"
    assert free["total_amount"] == "0.00"


# ---------------------------------------------------------------------------
# AC7 — pro plan exact values
# ---------------------------------------------------------------------------


async def test_pro_plan_pricing_exact(client: AsyncClient):
    """Pro plan: base=70.00, subtotal=70.00, tax=12.60, total=82.60."""
    res = await client.get("/api/plans")
    pro = res.json()["plans"][1]
    assert pro["id"] == "pro"
    assert pro["base_price"] == "70.00"
    assert pro["seat_price"] == "0.00"
    assert pro["subtotal_amount"] == "70.00"
    assert pro["tax_amount"] == "12.60"
    assert pro["total_amount"] == "82.60"


# ---------------------------------------------------------------------------
# AC8 & AC9 — studio plan exact values
# ---------------------------------------------------------------------------


async def test_studio_plan_base_fields(client: AsyncClient):
    """Studio plan: base=299.00, seat=40.00, base_seats_included=5."""
    res = await client.get("/api/plans")
    studio = res.json()["plans"][2]
    assert studio["id"] == "studio"
    assert studio["base_price"] == "299.00"
    assert studio["seat_price"] == "40.00"
    assert studio["base_seats_included"] == 5


async def test_studio_plan_amounts_exact(client: AsyncClient):
    """Studio plan (5 base seats, no overage): subtotal=299.00, tax=53.82, total=352.82."""
    res = await client.get("/api/plans")
    studio = res.json()["plans"][2]
    assert studio["subtotal_amount"] == "299.00"
    assert studio["tax_amount"] == "53.82"
    assert studio["total_amount"] == "352.82"


# ---------------------------------------------------------------------------
# AC10 — features are human-readable es-PE strings
# ---------------------------------------------------------------------------


async def test_features_are_human_readable_strings(client: AsyncClient):
    """Every feature entry is a non-empty string with a space (not a machine key)."""
    res = await client.get("/api/plans")
    for plan in res.json()["plans"]:
        for feature in plan["features"]:
            assert isinstance(feature, str) and len(feature) > 0
            # Machine keys look like snake_case; human labels have spaces
            assert " " in feature, (
                f"Feature '{feature}' in plan {plan['id']} looks like a machine key"
            )


async def test_free_plan_features_only_chat(client: AsyncClient):
    """Free plan features: only Chat con IA legal (chat=True, rest False)."""
    res = await client.get("/api/plans")
    free = res.json()["plans"][0]
    assert free["features"] == ["Chat con IA legal"]


async def test_pro_plan_features(client: AsyncClient):
    """Pro plan features: chat, pdf_export, file_upload, byok_enabled, priority_support."""
    res = await client.get("/api/plans")
    pro = res.json()["plans"][1]
    expected = [
        "Chat con IA legal",
        "Exportar conversaciones a PDF",
        "Subir archivos (PDF, DOCX)",
        "Trae tu propia API key (BYOK)",
        "Soporte prioritario",
    ]
    assert pro["features"] == expected


async def test_studio_plan_features_all_six(client: AsyncClient):
    """Studio plan features: all six labels including team seats."""
    res = await client.get("/api/plans")
    studio = res.json()["plans"][2]
    assert "Asientos para tu equipo" in studio["features"]
    assert len(studio["features"]) == 6


# ---------------------------------------------------------------------------
# AC11 — limits dict exposed per plan
# ---------------------------------------------------------------------------


async def test_free_plan_chat_per_day_is_ten(client: AsyncClient):
    """Free plan limits.chat_per_day == 10 (daily cap)."""
    res = await client.get("/api/plans")
    free = res.json()["plans"][0]
    assert free["limits"]["chat_per_day"] == 10


async def test_pro_chat_per_day_is_null(client: AsyncClient):
    """Pro plan limits.chat_per_day is null (unlimited)."""
    res = await client.get("/api/plans")
    pro = res.json()["plans"][1]
    assert pro["limits"]["chat_per_day"] is None


async def test_studio_chat_per_day_is_null(client: AsyncClient):
    """Studio plan limits.chat_per_day is null (unlimited)."""
    res = await client.get("/api/plans")
    studio = res.json()["plans"][2]
    assert studio["limits"]["chat_per_day"] is None


# ---------------------------------------------------------------------------
# AC12 — byok_supported matrix
# ---------------------------------------------------------------------------


async def test_byok_supported_matrix(client: AsyncClient):
    """free=False, pro=True, studio=True."""
    res = await client.get("/api/plans")
    plans = {p["id"]: p for p in res.json()["plans"]}
    assert plans["free"]["byok_supported"] is False
    assert plans["pro"]["byok_supported"] is True
    assert plans["studio"]["byok_supported"] is True


# ---------------------------------------------------------------------------
# AC13 — display names Spanish
# ---------------------------------------------------------------------------


async def test_display_names_spanish(client: AsyncClient):
    """Display names are exactly Gratuito, Profesional, Estudio."""
    res = await client.get("/api/plans")
    plans = {p["id"]: p for p in res.json()["plans"]}
    assert plans["free"]["display_name"] == "Gratuito"
    assert plans["pro"]["display_name"] == "Profesional"
    assert plans["studio"]["display_name"] == "Estudio"


# ---------------------------------------------------------------------------
# AC14 — beta_mode reflects settings
# ---------------------------------------------------------------------------


async def test_beta_mode_matches_settings(client: AsyncClient):
    """beta_mode root field matches app.config.settings.beta_mode."""
    res = await client.get("/api/plans")
    assert res.json()["beta_mode"] == settings.beta_mode


# ---------------------------------------------------------------------------
# AC15 — Cache-Control header
# ---------------------------------------------------------------------------


async def test_cache_control_header_present(client: AsyncClient):
    """Response includes Cache-Control: public, max-age=3600."""
    res = await client.get("/api/plans")
    cc = res.headers.get("cache-control", "")
    assert "public" in cc
    assert "max-age=3600" in cc


# ---------------------------------------------------------------------------
# AC18 — endpoint visible in OpenAPI schema
# ---------------------------------------------------------------------------


async def test_endpoint_in_openapi_schema(client: AsyncClient):
    """GET /openapi.json includes /api/plans path with tag 'plans'."""
    res = await client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert "/api/plans" in schema["paths"], "'/api/plans' not found in OpenAPI paths"
    get_op = schema["paths"]["/api/plans"]["get"]
    assert "plans" in get_op.get("tags", []), "tag 'plans' not present on /api/plans"
