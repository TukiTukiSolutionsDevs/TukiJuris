---
change: backend-saas-test-coverage
spec: chat-stream
status: proposed
created: 2026-04-19
---

# Spec — Chat Stream test coverage

## 1. Scope
Coverage for the LLM interaction endpoints: `chat.py`, `stream.py`, and the SDK surface `v1.py`. This covers plan-quota enforcement, the complete SSE stream lifecycle (connect, yield tokens, disconnect), dual-auth handling for `v1.py` (JWT + API key), and scope enforcement. 

## 2. Current state
- Existing tests: `chat.py` has a few BYOK fallback tests and a daily quota integration test. `v1.py` has ~6 smoke tests. `stream.py` (640 lines) has 1 test.
- Known gaps: No happy-path integration tests for `POST /api/chat/` with mocked LLM. `stream.py` lacks tests for SSE frame structure, mid-stream error propagation, and explicitly lacks a test for plan-based quota enforcement. `v1.py` lacks scope verification and dual-auth tests.
- Pre-existing failures unrelated: `backend-tests` webhook race (Sprint 3 Batch 6 - out of scope).

## 3. Test catalog
1. `chat-stream.unit.001`
   - Name: `test_chat_post_happy_path_llm_mock`
   - Layer: integration
   - File: `apps/api/tests/integration/test_chat.py`
   - Intent: Ensure `/api/chat/` returns a successful response using a mocked LLM service.
   - Setup: User A, Mocked LLM Adapter
   - Assertions: 200 OK, returns correct JSON structure containing the LLM mock reply.
   - Expected runtime: fast
   - Dependency: NONE
2. `chat-stream.unit.002`
   - Name: `test_chat_quota_enforcement_free_user`
   - Layer: integration
   - File: `apps/api/tests/integration/test_chat.py`
   - Intent: Verify free users hitting their daily limit receive a 429.
   - Setup: Free User A, Usage at max limit
   - Assertions: Returns 429 Too Many Requests with specific quota-exhausted error payload.
   - Expected runtime: fast
   - Dependency: NONE
3. `chat-stream.unit.003`
   - Name: `test_chat_byok_fallback_platform_key`
   - Layer: integration
   - File: `apps/api/tests/integration/test_chat.py`
   - Intent: Verify if a user's BYOK plan gate fails, it correctly falls back to the platform key.
   - Setup: User without BYOK entitlements
   - Assertions: LLM adapter is initialized with platform configuration.
   - Expected runtime: fast
   - Dependency: NONE
4. `chat-stream.unit.004`
   - Name: `test_stream_sse_frame_format_connect`
   - Layer: unit
   - File: `apps/api/tests/unit/test_stream_sse.py`
   - Intent: Verify the SSE connection yields the required `data:` prefix and connection events.
   - Setup: Mocked SSE response generator
   - Assertions: First yielded frames contain valid Server-Sent Events formatting.
   - Expected runtime: fast
   - Dependency: NONE
5. `chat-stream.unit.005`
   - Name: `test_stream_sse_tokens_yield`
   - Layer: integration
   - File: `apps/api/tests/integration/test_stream.py`
   - Intent: Verify the stream yields text chunks from the mocked LLM stream.
   - Setup: User A, Mock LLM Async Generator
   - Assertions: Endpoint yields multiple frames matching the mock output.
   - Expected runtime: fast
   - Dependency: NONE
6. `chat-stream.unit.006`
   - Name: `test_stream_sse_done_event`
   - Layer: integration
   - File: `apps/api/tests/integration/test_stream.py`
   - Intent: Ensure the stream sends a terminating `[DONE]` event.
   - Setup: User A, Mock LLM Async Generator
   - Assertions: The final emitted frame is exactly `data: [DONE]`.
   - Expected runtime: fast
   - Dependency: NONE
7. `chat-stream.unit.007`
   - Name: `test_stream_quota_gate_free_user_exhausted`
   - Layer: integration
   - File: `apps/api/tests/integration/test_stream.py`
   - Intent: Verify that a quota-exhausted user attempting to stream gets rejected properly.
   - Setup: Free User A, Usage at max limit
   - Assertions: Stream connection is rejected, returning 429 or emitting a quota error frame.
   - Expected runtime: fast
   - Dependency: code-fix-needed
8. `chat-stream.unit.008`
   - Name: `test_stream_401_missing_auth`
   - Layer: integration
   - File: `apps/api/tests/integration/test_stream.py`
   - Intent: Verify stream endpoints block unauthenticated requests.
   - Setup: No token
   - Assertions: Returns 401 Unauthorized.
   - Expected runtime: fast
   - Dependency: NONE
9. `chat-stream.unit.009`
   - Name: `test_stream_client_disconnect_cancellation`
   - Layer: integration
   - File: `apps/api/tests/integration/test_stream.py`
   - Intent: Verify that if the client disconnects, the server halts generation.
   - Setup: User A, Async client drops connection mid-stream
   - Assertions: Server-side task is cancelled, avoiding runaway LLM usage.
   - Expected runtime: med
   - Dependency: NONE
10. `chat-stream.unit.010`
    - Name: `test_v1_query_jwt_happy_path`
    - Layer: integration
    - File: `apps/api/tests/integration/test_v1_public.py`
    - Intent: Validate v1 accepts JWT authentication.
    - Setup: User A (JWT Bearer), Mock LLM
    - Assertions: Returns 200 with result payload.
    - Expected runtime: fast
    - Dependency: NONE
11. `chat-stream.unit.011`
    - Name: `test_v1_query_api_key_happy_path`
    - Layer: integration
    - File: `apps/api/tests/integration/test_v1_public.py`
    - Intent: Validate v1 accepts API Key dual-auth.
    - Setup: User API Key, Mock LLM
    - Assertions: Returns 200 with result payload.
    - Expected runtime: fast
    - Dependency: NONE
12. `chat-stream.unit.012`
    - Name: `test_v1_check_scope_missing_scope_raises`
    - Layer: unit
    - File: `apps/api/tests/unit/test_v1_scopes.py`
    - Intent: Verify `_check_scope` blocks keys lacking the required permission.
    - Setup: API Key with `["search"]` scope only
    - Assertions: Calling a `query` endpoint raises HTTP 403.
    - Expected runtime: fast
    - Dependency: NONE
13. `chat-stream.unit.013`
    - Name: `test_v1_usage_quota_calculation`
    - Layer: integration
    - File: `apps/api/tests/integration/test_v1_public.py`
    - Intent: Verify `/api/v1/usage` returns accurate quota state.
    - Setup: User API Key
    - Assertions: Payload matches structure: limits, used, remaining.
    - Expected runtime: fast
    - Dependency: NONE
14. `chat-stream.unit.014`
    - Name: `test_v1_rate_limit_headers_injected`
    - Layer: integration
    - File: `apps/api/tests/integration/test_v1_public.py`
    - Intent: Validate that `X-RateLimit-Limit` headers are returned on v1 endpoints.
    - Setup: API Key
    - Assertions: Response headers include standard rate limiting data.
    - Expected runtime: fast
    - Dependency: code-fix-needed

## 4. Code fixes likely required
- **FIX-01**: `stream.py` missing/divergent usage quota check. Exploration §4 noted `stream.py` may NOT call `usage.py` the same way `chat.py` does. Writing `test_stream_quota_gate_free_user_exhausted` will likely expose this bug. Expecting a fix to align both files.
- **FIX-02**: Rate limit headers in `v1.py` may need adjustments to ensure they are properly injected via middleware or custom dependencies.

## 5. Acceptance criteria
- All 14 tests pass.
- Zero new unjustified skips.
- Coverage delta target ≥ 85% for `chat.py`, `stream.py`, and `v1.py`.
- No regression in the 1111 currently-passing tests.

## 6. Out of scope / deferred
- Items in Sprint 3 Batch 3.
- Frontend test coverage for SSE.
- Real LLM calls (tests must use mocks).
- The `redirect_slashes` cross-origin bug.

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
- Prior relevant archives (cite engram topic keys)
