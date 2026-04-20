---
change: backend-saas-test-coverage
spec: byok
status: proposed
created: 2026-04-19
---

# Spec — BYOK and API Keys test coverage

## 1. Scope
Coverage for the Developer API key generation (`api_keys.py`) and upload validation (`upload.py`). This focuses on isolation, scoped access, and LLM key testing propagation.
Deliberately OUT:
- `byok-plan-gate` checks (already thoroughly tested in Sprint 2 C5).
- BYOK vitest tests (Sprint 3 Batch 3 frontend task).
- Ingestion decryption with v1: prefix centralization (Sprint 3 Batch 6 architectural fix).

## 2. Current state
- Existing tests: Good coverage for encryption/decryption, v1 migration, key isolation, and plan entitlement gates.
- Known gaps: Developer API key CRUD (`/api/keys/`) lacks route-level integration tests. Unknown scope validation rejection. LLM provider error propagation during key testing. Upload endpoint file type/size validation and ownership isolation for deletions.

## 3. Test catalog

1. ID: `byok.unit.001`
   - Name: `test_validate_scopes_unknown_scope_rejected`
   - Layer: unit
   - File: `apps/api/tests/unit/test_api_keys.py`
   - Intent: Ensure `_validate_scopes` function raises HTTP 400/422 if an unknown scope string is provided.
   - Setup: Call function directly with `["invalid_scope"]`.
   - Assertions: Raises HTTPException.
   - Expected runtime: fast
   - Dependency: NONE

2. ID: `byok.unit.002`
   - Name: `test_api_key_generate_unique`
   - Layer: unit
   - File: `apps/api/tests/unit/test_api_keys.py`
   - Intent: Ensure random generation creates structurally unique keys.
   - Setup: Generate two keys via service.
   - Assertions: `key1 != key2`.
   - Expected runtime: fast
   - Dependency: NONE

3. ID: `byok.int.001`
   - Name: `test_developer_api_key_crud`
   - Layer: integration
   - File: `apps/api/tests/integration/test_api_keys.py`
   - Intent: Full CRUD lifecycle for a Developer API Key (`POST /api/keys/` -> `GET` -> `PATCH` -> `DELETE`).
   - Setup: Standard user auth fixture.
   - Assertions: 201 Created -> 200 list includes key -> 200 update scope/name -> 204 Delete -> 200 list empty.
   - Expected runtime: med
   - Dependency: NONE

4. ID: `byok.int.002`
   - Name: `test_llm_key_test_provider_error_propagated`
   - Layer: integration
   - File: `apps/api/tests/integration/test_llm_keys.py`
   - Intent: Ensure `POST /api/keys/llm/{key_id}/test` gracefully bubbles up HTTP 401/400 provider errors to the user instead of 500s.
   - Setup: Mock OpenAI/provider API to return 401 Unauthorized.
   - Assertions: Response is HTTP 400 with a clean user-facing error message about invalid key.
   - Expected runtime: med
   - Dependency: NONE

5. ID: `byok.int.003`
   - Name: `test_upload_wrong_type_rejected`
   - Layer: integration
   - File: `apps/api/tests/integration/test_upload.py`
   - Intent: Verify `POST /api/upload/` rejects unsupported file types (e.g. `.exe`).
   - Setup: Standard user auth, mock file payload with `.exe` extension/mimetype.
   - Assertions: HTTP 422 Unprocessable Entity.
   - Expected runtime: med
   - Dependency: NONE

6. ID: `byok.int.004`
   - Name: `test_upload_ownership_isolation`
   - Layer: integration
   - File: `apps/api/tests/integration/test_upload.py`
   - Intent: Ensure user A cannot `GET` or `DELETE` user B's uploaded document.
   - Setup: User A uploads file. User B attempts `GET /api/upload/{doc_id}`.
   - Assertions: HTTP 403 or 404.
   - Expected runtime: med
   - Dependency: NONE

## 4. Code fixes likely required
- None major, but verify `_validate_scopes` strictly filters unknown scopes.
- Ensure `upload.py` enforces ownership in its DELETE route. 

## 5. Acceptance criteria
- Developer API Key CRUD is tested at the route level.
- Cross-tenant upload isolation (GET/DELETE) is explicitly tested and passing.
- LLM provider errors during testing propagate safely.
- Zero new skips/xfails.

## 6. Out of scope / deferred
- BYOK ingestion decryption centralization (Sprint 3 Batch 6).
- BYOK frontend vitest tasks (Sprint 3 Batch 3).

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
