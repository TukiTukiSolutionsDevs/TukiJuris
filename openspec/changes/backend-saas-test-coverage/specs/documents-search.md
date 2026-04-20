---
change: backend-saas-test-coverage
spec: documents-search
status: proposed
created: 2026-04-19
---

# Spec — Documents Search test coverage

## 1. Scope
Coverage for the `documents.py`, `search.py`, `analysis.py`, and `export.py` domains. This includes semantic search via pgvector, search filters, saved searches, search history, LLM-based document analysis flows, cross-tenant isolation on exports/uploads, and basic document metadata CRUD. 

## 2. Current state
- Existing tests: `documents.py` has 15 tests. `search.py` has 8 scattered tests. `export.py` has 6 basic shape tests.
- Known gaps: Analysis is completely untested. Exhaustive filter combination tests for search are missing. Saved searches and history pagination/auth lack tests. Export isolation (downloading a PDF that belongs to another user) is untested.
- Pre-existing failures unrelated: None.

## 3. Test catalog
1. `documents-search.unit.001`
   - Name: `test_search_filter_date_range_invalid`
   - Layer: unit
   - File: `apps/api/tests/unit/test_search_filters.py`
   - Intent: Ensure `_validate_filters` rejects an end date that precedes the start date.
   - Setup: Filters payload
   - Assertions: Raises HTTPException 422.
   - Expected runtime: fast
   - Dependency: NONE
2. `documents-search.unit.002`
   - Name: `test_search_filter_unknown_area_rejected`
   - Layer: unit
   - File: `apps/api/tests/unit/test_search_filters.py`
   - Intent: Ensure unknown legal areas are rejected by the validator.
   - Setup: Filters payload with `area="unknown"`
   - Assertions: Raises HTTPException 422.
   - Expected runtime: fast
   - Dependency: NONE
3. `documents-search.unit.003`
   - Name: `test_search_pagination_offset_limit`
   - Layer: unit
   - File: `apps/api/tests/unit/test_search_filters.py`
   - Intent: Verify `_build_search_query` correctly maps pagination parameters.
   - Setup: offset=20, limit=10
   - Assertions: SQL query generated contains correct offset/limit clauses.
   - Expected runtime: fast
   - Dependency: NONE
4. `documents-search.unit.004`
   - Name: `test_search_pgvector_semantic_happy_path`
   - Layer: integration
   - File: `apps/api/tests/integration/test_search.py`
   - Intent: Verify the main search route executes pgvector retrieval successfully.
   - Setup: DB with mocked document embeddings
   - Assertions: Returns 200 OK with relevance-ordered results.
   - Expected runtime: med
   - Dependency: NONE
5. `documents-search.unit.005`
   - Name: `test_search_saved_create_requires_auth`
   - Layer: integration
   - File: `apps/api/tests/integration/test_search.py`
   - Intent: Block unauthenticated users from creating saved searches.
   - Setup: No token
   - Assertions: POST to `/api/search/saved` returns 401.
   - Expected runtime: fast
   - Dependency: NONE
6. `documents-search.unit.006`
   - Name: `test_search_saved_list_isolation`
   - Layer: integration
   - File: `apps/api/tests/integration/test_search.py`
   - Intent: Prevent cross-tenant visibility of saved searches.
   - Setup: User A (saved search X), User B
   - Assertions: User B GET `/api/search/saved` returns 0 results.
   - Expected runtime: fast
   - Dependency: NONE
7. `documents-search.unit.007`
   - Name: `test_search_history_auth_pagination`
   - Layer: integration
   - File: `apps/api/tests/integration/test_search.py`
   - Intent: Validate auth gating and pagination for search history.
   - Setup: User A with 15 history records
   - Assertions: GET `limit=10` returns 10; unauthenticated GET returns 401.
   - Expected runtime: fast
   - Dependency: NONE
8. `documents-search.unit.008`
   - Name: `test_search_history_db_write_failure_safe`
   - Layer: unit
   - File: `apps/api/tests/unit/test_search_logging.py`
   - Intent: Ensure that `_log_search_history` failing does not crash the search request.
   - Setup: Mock DB to raise exception on insert
   - Assertions: Search still returns results successfully (fail-safe).
   - Expected runtime: fast
   - Dependency: code-fix-needed
9. `documents-search.unit.009`
   - Name: `test_analysis_submit_mock_llm_happy_path`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analysis.py`
   - Intent: Verify `/api/analysis/` successfully coordinates with LLM and returns data.
   - Setup: User A, Mocked LLM Adapter
   - Assertions: Returns 200 with correctly shaped analysis response.
   - Expected runtime: fast
   - Dependency: NONE
10. `documents-search.unit.010`
    - Name: `test_analysis_cross_tenant_isolation`
    - Layer: integration
    - File: `apps/api/tests/integration/test_analysis.py`
    - Intent: Ensure analysis logic respects tenant boundaries for provided documents.
    - Setup: User A provides Doc B (owned by User B)
    - Assertions: API rejects the analysis or filters out unauthorized documents (403/404).
    - Expected runtime: fast
    - Dependency: NONE
11. `documents-search.unit.011`
    - Name: `test_export_pdf_bytes_shape`
    - Layer: integration
    - File: `apps/api/tests/integration/test_export.py`
    - Intent: Ensure PDF generation returns a valid file shape.
    - Setup: User A, Valid Conv ID
    - Assertions: Response has `application/pdf` content-type and bytes.
    - Expected runtime: fast
    - Dependency: NONE
12. `documents-search.unit.012`
    - Name: `test_export_consultation_ownership_403`
    - Layer: integration
    - File: `apps/api/tests/integration/test_export.py`
    - Intent: Block User B from exporting User A's consultation.
    - Setup: User A (Message A), User B
    - Assertions: User B GET `/api/export/consultation/{message_a_id}` returns 403/404.
    - Expected runtime: fast
    - Dependency: NONE
13. `documents-search.unit.013`
    - Name: `test_export_conversation_ownership_404`
    - Layer: integration
    - File: `apps/api/tests/integration/test_export.py`
    - Intent: Block User B from exporting User A's entire conversation.
    - Setup: User A (Conv A), User B
    - Assertions: User B GET `/api/export/conversation/{conv_a_id}` returns 403/404.
    - Expected runtime: fast
    - Dependency: NONE
14. `documents-search.unit.014`
    - Name: `test_upload_ownership_isolation`
    - Layer: integration
    - File: `apps/api/tests/integration/test_upload.py`
    - Intent: Block cross-tenant access to uploaded document files.
    - Setup: User A (Doc A), User B
    - Assertions: User B GET `/api/upload/{doc_a_id}` returns 404.
    - Expected runtime: fast
    - Dependency: NONE
15. `documents-search.unit.015`
    - Name: `test_document_metadata_crud_admin_only`
    - Layer: integration
    - File: `apps/api/tests/integration/test_documents.py`
    - Intent: Validate any mutating document metadata endpoints enforce admin roles.
    - Setup: User A (non-admin)
    - Assertions: Write endpoints reject with 403.
    - Expected runtime: fast
    - Dependency: NONE

## 4. Code fixes likely required
- Verify `_log_search_history` in `search.py` uses proper exception handling to act fail-safe. If an exception cascades and fails the search request, budget a fix.

## 5. Acceptance criteria
- All 15 tests pass.
- Zero new unjustified skips.
- Coverage delta target ≥ 85% for `documents.py`, `search.py`, `analysis.py`, `export.py`.
- No regression in the 1111 currently-passing tests.

## 6. Out of scope / deferred
- Items in Sprint 3 Batch 3.
- Frontend tests.

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
- Prior relevant archives (cite engram topic keys)
