"""Integration tests — analysis route (sub-batch E.2b).

Spec IDs covered:
  - documents-search.unit.009  test_analysis_submit_mock_llm_happy_path   [PASS]
  - documents-search.unit.010  test_analysis_cross_tenant_isolation        [XFAIL — no doc_id param]

Route exercised:
  POST /api/analysis/case — structured legal analysis of a situation.

LLM patch target: app.services.llm_adapter.llm_service.completion
(analysis route calls llm_service.completion() directly, NOT via legal_orchestrator).

Run with:
  docker exec tukijuris-api-1 pytest apps/api/tests/integration/test_analysis.py -v --tb=short
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

# ---------------------------------------------------------------------------
# Shared mock — mirrors the dict shape returned by LLMService.completion()
# (see app/services/llm_adapter.py — returns content, model, tokens_used)
# ---------------------------------------------------------------------------

_LLM_PATH = "app.services.llm_adapter.llm_service.completion"

_MOCK_COMPLETION = {
    "content": (
        "Análisis legal simulado.\n\n"
        "1. ÁREAS DEL DERECHO: Derecho laboral.\n"
        "2. NORMATIVA APLICABLE: Ley de Productividad y Competitividad Laboral D.S. 003-97-TR.\n"
        "3. RECOMENDACIÓN: Consultar con un abogado especialista."
    ),
    "model": "mock-model",
    "tokens_used": 150,
    "prompt_tokens": 80,
    "completion_tokens": 70,
}


# ---------------------------------------------------------------------------
# documents-search.unit.009 — happy path with mocked LLM
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_analysis_submit_mock_llm_happy_path(auth_client):
    """POST /api/analysis/case with mocked LLM → 200 + correctly shaped response.

    Spec: documents-search.unit.009
    Patches llm_service.completion to avoid real API calls.
    Verifies the four required response fields: analysis, areas_identified,
    model_used, latency_ms.
    """
    with patch(_LLM_PATH, AsyncMock(return_value=_MOCK_COMPLETION)):
        res = await auth_client.post(
            "/api/analysis/case",
            json={"case_description": "Mi empleador me despidió sin causa justa después de 5 años de servicio."},
        )

    assert res.status_code == 200, f"Expected 200, got {res.status_code}. Body: {res.text[:400]}"

    data = res.json()
    assert "analysis" in data, f"Missing 'analysis' key. Keys: {list(data)}"
    assert "areas_identified" in data, f"Missing 'areas_identified' key. Keys: {list(data)}"
    assert "model_used" in data, f"Missing 'model_used' key. Keys: {list(data)}"
    assert "latency_ms" in data, f"Missing 'latency_ms' key. Keys: {list(data)}"

    assert isinstance(data["analysis"], str)
    assert len(data["analysis"]) > 0, "analysis field must not be empty"
    assert isinstance(data["areas_identified"], list)
    assert isinstance(data["model_used"], str)
    assert isinstance(data["latency_ms"], int)


# ---------------------------------------------------------------------------
# documents-search.unit.010 — cross-tenant isolation
# XFAIL: analysis route accepts case_description (free text) only — no document_id
# parameter exists. There is no per-user uploaded-document isolation surface
# on this endpoint. Wave-3 placeholder for T-E-15 route redesign.
# ---------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "POST /api/analysis/case accepts case_description (free text) only — "
        "no document_id parameter; uploaded-document cross-tenant isolation surface "
        "does not exist on this endpoint. Wave-3 placeholder; requires T-E-15 route change."
    ),
)
async def test_analysis_cross_tenant_isolation(tenant_pair):
    """User A's uploaded doc should not be accessible via User B's analysis call.

    Spec: documents-search.unit.010
    XFAIL: The analysis route has no document_id parameter. Any authenticated or
    anonymous user can call it with arbitrary text. The isolation concern (User B
    referencing User A's uploaded document) cannot be tested until the route accepts
    a document_id and applies user_id scoping.
    """
    # The route only accepts free-text — there is no document_id to reference.
    # This assertion will always fail, confirming the feature is absent.
    assert False, (
        "analysis route has no document_id parameter; "
        "cross-tenant uploaded-document isolation not implementable at this layer"
    )
