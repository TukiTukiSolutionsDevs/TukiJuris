---
change: backend-saas-test-coverage
status: proposed
created: 2026-04-19
execution_mode: auto
batches:
  - A  # auth gaps + billing deferred warnings + test infra
  - B  # chat + stream + public-api-v1 + FIX-01
  - C  # admin 403 + byok CRUD + orgs isolation + FIX-02
  - D  # conversations write + analytics + notifications/emails
  - E  # bookmarks/tags/folders/memory/shared + documents/search/export/analysis
---

# Tasks — backend-saas-test-coverage

## Global pre-flight

- [ ] T-000  Verify backend test runtime is available
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: docker runtime state for `tukijuris-api-1`; optional `docker compose` startup from `/Users/soulkin/Documents/TukiJuris`
  - test_ids: NONE
  - depends_on: NONE
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: fast
  - notes: If the container is down, run `make up` and wait 15s before any pytest work.

- [ ] T-001  Pin W7 pre-existing webhook race as strict xfail
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/integration/test_webhook_idempotency.py`
  - test_ids: NONE
  - depends_on: [T-000]
  - code_fix: NONE
  - estimated_loc: 3 lines
  - estimated_runtime: fast
  - notes: Only add the marker if `test_concurrent_same_event_id_no_duplicate_processing` is not already strict-xfailed.

- [ ] T-002  Lock coverage baseline JSON
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `openspec/changes/backend-saas-test-coverage/baseline-coverage.json`
  - test_ids: NONE
  - depends_on: [T-000]
  - code_fix: NONE
  - estimated_loc: 1 lines
  - estimated_runtime: med
  - notes: Run `pytest --cov=app --cov-report=json:/tmp/cov-baseline.json` once and copy the JSON artifact into openspec.

- [ ] T-003  Confirm Makefile shells into Docker for tests
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `Makefile`
  - test_ids: NONE
  - depends_on: [T-000]
  - code_fix: NONE
  - estimated_loc: 2 lines
  - estimated_runtime: fast
  - notes: Replace host-Python test targets with `docker exec tukijuris-api-1 ...` only if the delta is still missing.

## Batch A — Foundations + auth + billing

**Scope summary**: front-load all reusable test primitives, baseline coverage enforcement, then land the low-risk auth and billing coverage gaps.

**Entry criteria**: T-000..T-003 complete; baseline JSON captured; W7 assumption pinned safely.

**Exit criteria**: Batch A infra primitives are available for later batches, auth+billing tests are green, and baseline+A delta passes inside Docker with coverage enforcement runnable.

- [ ] T-A-01  Create core factory package and user/org factories
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/factories/__init__.py`, `apps/api/tests/factories/user.py`, `apps/api/tests/factories/org.py`
  - test_ids: NONE
  - depends_on: [T-000]
  - code_fix: NONE
  - estimated_loc: 120 lines
  - estimated_runtime: fast
  - notes: Keep each module ≤50 LOC and HTTP-first, matching the design budget.

- [ ] T-A-02  Create conversation/invoice/api-key factories
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/factories/conversation.py`, `apps/api/tests/factories/invoice.py`, `apps/api/tests/factories/api_key.py`
  - test_ids: NONE
  - depends_on: [T-A-01]
  - code_fix: NONE
  - estimated_loc: 135 lines
  - estimated_runtime: fast
  - notes: These unblock Batch B/C/E route-level setup without in-test duplication.

- [ ] T-A-03  Create llm-key/notification/saved-search factories
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/factories/llm_key.py`, `apps/api/tests/factories/notification.py`, `apps/api/tests/factories/saved_search.py`
  - test_ids: NONE
  - depends_on: [T-A-01]
  - code_fix: NONE
  - estimated_loc: 135 lines
  - estimated_runtime: fast
  - notes: Service-backed factories only for states that are awkward to reach via HTTP.

- [ ] T-A-04  Create tenant-pair fixture module
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/fixtures/tenants.py`
  - test_ids: NONE
  - depends_on: [T-A-01]
  - code_fix: NONE
  - estimated_loc: 90 lines
  - estimated_runtime: fast
  - notes: Implement `two_orgs_two_users` exactly as the canonical cross-tenant harness entrypoint.

- [ ] T-A-05  Create isolation helper package
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/helpers/__init__.py`, `apps/api/tests/helpers/isolation.py`
  - test_ids: NONE
  - depends_on: [T-A-04]
  - code_fix: NONE
  - estimated_loc: 85 lines
  - estimated_runtime: fast
  - notes: Encode the project-wide 403-vs-404 rule so later tests stay consistent.

- [ ] T-A-06  Create SSE assertion helper
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/helpers/sse.py`
  - test_ids: NONE
  - depends_on: [T-000]
  - code_fix: NONE
  - estimated_loc: 95 lines
  - estimated_runtime: fast
  - notes: Build `assert_sse_yields` around `httpx.AsyncClient.stream()` and the documented frame contract.

- [ ] T-A-07  Create shared LLM patch helper
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/helpers/llm.py`
  - test_ids: NONE
  - depends_on: [T-000]
  - code_fix: NONE
  - estimated_loc: 45 lines
  - estimated_runtime: fast
  - notes: Reuse the existing AsyncMock pattern instead of introducing a new mocks module.

- [ ] T-A-08  Create email mock provider package
  - spec: sdd/backend-saas-test-coverage/spec/notifications
  - deliverable: `apps/api/tests/mocks/__init__.py`, `apps/api/tests/mocks/email.py`
  - test_ids: notifications.unit.009, notifications.unit.010, notifications.unit.011, notifications.unit.012
  - depends_on: [T-000]
  - code_fix: NONE
  - estimated_loc: 70 lines
  - estimated_runtime: fast
  - notes: Include success and failing provider variants for Batch D consumers.

- [ ] T-A-09  Wire new fixtures into pytest discovery safely
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/tests/conftest.py`
  - test_ids: NONE
  - depends_on: [T-A-04, T-A-05, T-A-08]
  - code_fix: NONE
  - estimated_loc: 30 lines
  - estimated_runtime: fast
  - notes: Import only what should be globally discoverable; keep helpers/factories explicit imports.

- [ ] T-A-10  Add coverage enforcement artifacts
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `apps/api/scripts/check_coverage.py`, `apps/api/coverage-targets.yaml`
  - test_ids: NONE
  - depends_on: [T-002, T-003]
  - code_fix: NONE
  - estimated_loc: 95 lines
  - estimated_runtime: fast
  - notes: MUST targets stay script-enforced; STRETCH targets warn only.

- [ ] T-A-11  Add auth unit coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/auth
  - deliverable: `apps/api/tests/unit/test_auth_sessions.py`, `apps/api/tests/unit/test_auth_me.py`, `apps/api/tests/unit/test_auth_helpers.py`, `apps/api/tests/unit/test_oauth_microsoft.py`
  - test_ids: auth.unit.001, auth.unit.002, auth.unit.003, auth.unit.004
  - depends_on: [T-A-01, T-A-09]
  - code_fix: NONE
  - estimated_loc: 120 lines
  - estimated_runtime: fast
  - notes: Keep this batch confirmatory; no production code changes are expected.

- [ ] T-A-12  Add auth integration coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/auth
  - deliverable: `apps/api/tests/integration/test_onboarding_flow.py`, `apps/api/tests/integration/test_refresh_token.py`
  - test_ids: auth.int.001, auth.int.002
  - depends_on: [T-A-09]
  - code_fix: NONE
  - estimated_loc: 55 lines
  - estimated_runtime: med
  - notes: Reuse existing auth fixtures rather than inventing alternate token setup.

- [ ] T-A-13  Add billing unit coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/billing
  - deliverable: `apps/api/tests/unit/test_payment_webhooks.py`, `apps/api/tests/unit/test_subscription_service.py`
  - test_ids: billing.unit.001, billing.unit.002, billing.unit.003, billing.unit.004
  - depends_on: [T-A-03, T-A-08]
  - code_fix: NONE
  - estimated_loc: 110 lines
  - estimated_runtime: fast
  - notes: Stay within the deferred boundary; do not absorb Sprint 3 Batch 6 webhook fixes here.

- [ ] T-A-14  Add billing integration coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/billing
  - deliverable: `apps/api/tests/integration/test_me_invoices.py`, `apps/api/tests/test_trials_routes.py`
  - test_ids: billing.int.001, billing.int.002
  - depends_on: [T-A-04, T-A-05]
  - code_fix: NONE
  - estimated_loc: 60 lines
  - estimated_runtime: med
  - notes: Use the tenant harness for org-membership 403 and settings override for `TRIALS_ENABLED=False`.

- [ ] T-A-99  Verify Batch A and commit
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `openspec/changes/backend-saas-test-coverage/baseline-coverage.json`, `apps/api/coverage-targets.yaml`, Batch A test files, git commit
  - test_ids: auth.unit.001, auth.unit.002, auth.unit.003, auth.unit.004, auth.int.001, auth.int.002, billing.unit.001, billing.unit.002, billing.unit.003, billing.unit.004, billing.int.001, billing.int.002
  - depends_on: [T-A-01, T-A-02, T-A-03, T-A-04, T-A-05, T-A-06, T-A-07, T-A-08, T-A-09, T-A-10, T-A-11, T-A-12, T-A-13, T-A-14]
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: slow
  - notes: Run full pytest + coverage in Docker and commit as `test(backend): batch A — infra + auth/billing coverage`.

## Batch B — Chat + stream + public API v1

**Scope summary**: consume the new SSE/LLM helpers to harden chat, streaming, and the public API surface, landing the two known behavior fixes.

**Entry criteria**: Batch A complete; SSE helper, LLM helper, API-key factory, and coverage enforcement are available.

**Exit criteria**: chat, stream, and v1 tests are green; `stream.py` matches `chat.py` quota semantics; `/api/v1/*` responses emit rate-limit headers.

- [ ] T-B-01  Add chat route coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/chat-stream
  - deliverable: `apps/api/tests/integration/test_chat.py`
  - test_ids: chat-stream.unit.001, chat-stream.unit.002, chat-stream.unit.003
  - depends_on: [T-A-02, T-A-07, T-A-99]
  - code_fix: NONE
  - estimated_loc: 95 lines
  - estimated_runtime: med
  - notes: Establish the current `chat.py` quota payload as the reference contract for FIX-01.

- [ ] T-B-02  Add stream SSE contract coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/chat-stream
  - deliverable: `apps/api/tests/unit/test_stream_sse.py`, `apps/api/tests/integration/test_stream.py`
  - test_ids: chat-stream.unit.004, chat-stream.unit.005, chat-stream.unit.006
  - depends_on: [T-A-06, T-A-07, T-A-99]
  - code_fix: NONE
  - estimated_loc: 110 lines
  - estimated_runtime: med
  - notes: Use `assert_sse_yields` rather than hand-rolled frame parsing.

- [ ] T-B-03  Land FIX-01 stream quota alignment
  - spec: sdd/backend-saas-test-coverage/spec/chat-stream
  - deliverable: `apps/api/app/services/usage.py`, `apps/api/app/api/routes/chat.py`, `apps/api/app/api/routes/stream.py`, `apps/api/tests/integration/test_stream.py`
  - test_ids: chat-stream.unit.002, chat-stream.unit.007
  - depends_on: [T-B-01, T-B-02]
  - code_fix: FIX-01
  - estimated_loc: 55 lines
  - estimated_runtime: med
  - notes: Extract a shared `ensure_quota` helper and reject over-quota streams before first token emission.

- [ ] T-B-04  Add stream auth and disconnect coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/chat-stream
  - deliverable: `apps/api/tests/integration/test_stream.py`
  - test_ids: chat-stream.unit.008, chat-stream.unit.009
  - depends_on: [T-B-02, T-B-03]
  - code_fix: NONE
  - estimated_loc: 65 lines
  - estimated_runtime: med
  - notes: Reuse the SSE helper's disconnect support to assert server-side cancellation.

- [ ] T-B-05  Add public API dual-auth happy-path tests
  - spec: sdd/backend-saas-test-coverage/spec/chat-stream
  - deliverable: `apps/api/tests/integration/test_v1_public.py`
  - test_ids: chat-stream.unit.010, chat-stream.unit.011
  - depends_on: [T-A-02, T-A-07, T-A-99]
  - code_fix: NONE
  - estimated_loc: 70 lines
  - estimated_runtime: med
  - notes: Cover both JWT and developer API key auth using the shared API-key factory.

- [ ] T-B-06  Add public API scope and usage coverage
  - spec: sdd/backend-saas-test-coverage/spec/chat-stream
  - deliverable: `apps/api/tests/unit/test_v1_scopes.py`, `apps/api/tests/integration/test_v1_public.py`
  - test_ids: chat-stream.unit.012, chat-stream.unit.013
  - depends_on: [T-B-05]
  - code_fix: NONE
  - estimated_loc: 70 lines
  - estimated_runtime: fast
  - notes: Keep scope validation unit-level and quota state integration-level.

- [ ] T-B-07  Land FIX-06 v1 rate-limit headers
  - spec: sdd/backend-saas-test-coverage/spec/chat-stream
  - deliverable: `apps/api/app/api/middleware.py`, `apps/api/app/api/routes/v1.py`, `apps/api/tests/integration/test_v1_public.py`
  - test_ids: chat-stream.unit.014
  - depends_on: [T-B-05, T-B-06]
  - code_fix: FIX-06
  - estimated_loc: 45 lines
  - estimated_runtime: med
  - notes: Prefer middleware-scoped injection for `/api/v1/` only, exactly as the design resolved.

- [ ] T-B-99  Verify Batch B and commit
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: Batch B route/test files, coverage output, git commit
  - test_ids: chat-stream.unit.001, chat-stream.unit.002, chat-stream.unit.003, chat-stream.unit.004, chat-stream.unit.005, chat-stream.unit.006, chat-stream.unit.007, chat-stream.unit.008, chat-stream.unit.009, chat-stream.unit.010, chat-stream.unit.011, chat-stream.unit.012, chat-stream.unit.013, chat-stream.unit.014
  - depends_on: [T-B-01, T-B-02, T-B-03, T-B-04, T-B-05, T-B-06, T-B-07]
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: slow
  - notes: Run full pytest + coverage and commit as `test(backend): batch B — chat/stream/v1 coverage`.

## Batch C — Admin + BYOK + organizations

**Scope summary**: consolidate admin authorization, harden BYOK CRUD/isolation, and prove organization role + tenant boundaries before conversation writes fan out.

**Entry criteria**: Batch B complete; tenant harness and API-key factory are stable; `_ensure_admin` grep audit still shows the legacy copies.

**Exit criteria**: admin routes reject non-admins end-to-end, BYOK CRUD/isolation passes, organization access is airtight, and wave 1 cross-tenant audits are complete.

- [ ] T-C-01  Land FIX-02 centralized admin dependency
  - spec: sdd/backend-saas-test-coverage/spec/admin-rbac
  - deliverable: `apps/api/app/api/deps.py`, `apps/api/app/api/routes/admin.py`, `apps/api/app/api/routes/admin_saas.py`, `apps/api/app/api/routes/admin_invoices.py`, `apps/api/app/api/routes/admin_trials.py`
  - test_ids: admin-rbac.unit.001, admin-rbac.int.001, admin-rbac.int.002, admin-rbac.int.003
  - depends_on: [T-B-99]
  - code_fix: FIX-02
  - estimated_loc: 65 lines
  - estimated_runtime: fast
  - notes: Delete all local `_ensure_admin` copies and move to `require_admin` in deps.

- [ ] T-C-02  Add admin guard coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/admin-rbac
  - deliverable: `apps/api/tests/unit/test_admin_helpers.py`, `apps/api/tests/integration/test_admin_routes.py`
  - test_ids: admin-rbac.unit.001, admin-rbac.int.001, admin-rbac.int.002, admin-rbac.int.003
  - depends_on: [T-C-01]
  - code_fix: NONE
  - estimated_loc: 95 lines
  - estimated_runtime: med
  - notes: The unit test proves the dependency contract; integration tests prove every route still enforces it.

- [ ] T-C-03  Add admin RBAC lifecycle coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/admin-rbac
  - deliverable: `apps/api/tests/integration/test_rbac_admin.py`
  - test_ids: admin-rbac.int.004, admin-rbac.int.005
  - depends_on: [T-C-01]
  - code_fix: NONE
  - estimated_loc: 75 lines
  - estimated_runtime: med
  - notes: Keep the flow end-to-end: assign, inspect permissions, revoke, then verify loss of access.

- [ ] T-C-04  Add BYOK unit coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/byok
  - deliverable: `apps/api/tests/unit/test_api_keys.py`
  - test_ids: byok.unit.001, byok.unit.002
  - depends_on: [T-B-99]
  - code_fix: NONE
  - estimated_loc: 45 lines
  - estimated_runtime: fast
  - notes: Keep unknown-scope rejection and key-uniqueness checks fast and isolated.

- [ ] T-C-05  Add developer API key CRUD coverage
  - spec: sdd/backend-saas-test-coverage/spec/byok
  - deliverable: `apps/api/tests/integration/test_api_keys.py`
  - test_ids: byok.int.001
  - depends_on: [T-A-02, T-C-04]
  - code_fix: NONE
  - estimated_loc: 60 lines
  - estimated_runtime: med
  - notes: Cover POST→GET→PATCH→DELETE in one cohesive route-level cluster.

- [ ] T-C-06  Add LLM key provider-error coverage
  - spec: sdd/backend-saas-test-coverage/spec/byok
  - deliverable: `apps/api/tests/integration/test_llm_keys.py`
  - test_ids: byok.int.002
  - depends_on: [T-A-03, T-A-07]
  - code_fix: NONE
  - estimated_loc: 40 lines
  - estimated_runtime: med
  - notes: Ensure provider 401/400 responses stay user-facing instead of bubbling to 500.

- [ ] T-C-07  Add upload validation and isolation coverage
  - spec: sdd/backend-saas-test-coverage/spec/byok
  - deliverable: `apps/api/tests/integration/test_upload.py`, `apps/api/app/api/routes/upload.py`
  - test_ids: byok.int.003, byok.int.004
  - depends_on: [T-A-04, T-A-05]
  - code_fix: NONE
  - estimated_loc: 65 lines
  - estimated_runtime: med
  - notes: Land test-first; if DELETE/GET isolation leaks, let FIX-03a absorb the route patch.

- [ ] T-C-08  Add organization membership mutation coverage
  - spec: sdd/backend-saas-test-coverage/spec/organizations
  - deliverable: `apps/api/tests/integration/test_organizations.py`
  - test_ids: orgs.int.001, orgs.int.003
  - depends_on: [T-A-04]
  - code_fix: NONE
  - estimated_loc: 70 lines
  - estimated_runtime: med
  - notes: Keep owner-removal rejection explicit so sole-owner semantics never regress silently.

- [ ] T-C-09  Add organization role and read-isolation coverage
  - spec: sdd/backend-saas-test-coverage/spec/organizations
  - deliverable: `apps/api/tests/integration/test_organizations.py`
  - test_ids: orgs.int.002, orgs.int.004
  - depends_on: [T-A-04, T-A-05]
  - code_fix: NONE
  - estimated_loc: 55 lines
  - estimated_runtime: med
  - notes: Use the tenant harness to lock the 403 org-membership convention.

- [ ] T-C-10  Add organization seat-sync coverage
  - spec: sdd/backend-saas-test-coverage/spec/organizations
  - deliverable: `apps/api/tests/integration/test_organizations.py`
  - test_ids: orgs.int.005, orgs.int.006
  - depends_on: [T-C-08]
  - code_fix: NONE
  - estimated_loc: 60 lines
  - estimated_runtime: med
  - notes: Spy on `subscription_service` rather than duplicating billing internals in the test.

- [ ] T-C-11  FIX-03a cross-tenant filter audit wave 1
  - spec: sdd/backend-saas-test-coverage/spec/organizations
  - deliverable: `apps/api/app/api/routes/organizations.py`, `apps/api/app/api/routes/conversations.py`, `apps/api/app/api/routes/feedback.py`, `apps/api/app/api/routes/upload.py`
  - test_ids: orgs.int.004, byok.int.004, conversations.unit.001, conversations.unit.003, conversations.unit.004, conversations.unit.015
  - depends_on: [T-C-07, T-C-09]
  - code_fix: FIX-03
  - estimated_loc: 70 lines
  - estimated_runtime: med
  - notes: Cap this audit to ≤8 touched files and prepare conversation-write/user-owned filters for Batch D.

- [ ] T-C-99  Verify Batch C and commit
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: Batch C route/test files, grep audit output, git commit
  - test_ids: admin-rbac.unit.001, admin-rbac.int.001, admin-rbac.int.002, admin-rbac.int.003, admin-rbac.int.004, admin-rbac.int.005, byok.unit.001, byok.unit.002, byok.int.001, byok.int.002, byok.int.003, byok.int.004, orgs.int.001, orgs.int.002, orgs.int.003, orgs.int.004, orgs.int.005, orgs.int.006
  - depends_on: [T-C-01, T-C-02, T-C-03, T-C-04, T-C-05, T-C-06, T-C-07, T-C-08, T-C-09, T-C-10, T-C-11]
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: slow
  - notes: Run full pytest + coverage, confirm `rg "_ensure_admin" apps/api/app` returns 0 hits, then commit as `test(backend): batch C — admin/byok/org coverage`.

## Batch D — Conversations write + analytics + notifications/emails

**Scope summary**: cover conversation write-paths and feedback, fully open the dark analytics surface, then light up notifications/email behavior with the shared mocks.

**Entry criteria**: Batch C complete; wave 1 filter audit done; admin dependency and email mock are available.

**Exit criteria**: conversation write paths are owner-safe, analytics endpoints and health probes are covered, notifications/email tests are green, and wave 2 isolation fixes are contained.

- [x] T-D-01  Add conversation write-path owner coverage
  - spec: sdd/backend-saas-test-coverage/spec/conversations
  - deliverable: `apps/api/tests/integration/test_conversations_write.py`
  - test_ids: conversations.unit.001, conversations.unit.002, conversations.unit.003
  - depends_on: [T-A-02, T-A-04, T-A-05, T-C-11]
  - code_fix: NONE
  - estimated_loc: 90 lines
  - estimated_runtime: med
  - notes: Group rename/pin/archive together because they share the same conversation fixture setup.

- [x] T-D-02  Add conversation delete and feedback isolation coverage
  - spec: sdd/backend-saas-test-coverage/spec/conversations
  - deliverable: `apps/api/tests/integration/test_conversations_write.py`, `apps/api/tests/test_feedback.py`
  - test_ids: conversations.unit.004, conversations.unit.015
  - depends_on: [T-D-01, T-C-11]
  - code_fix: NONE
  - estimated_loc: 65 lines
  - estimated_runtime: med
  - notes: Keep delete cascade and cross-tenant feedback coupled to the same ownership model. conversations.unit.015 is XFAIL(strict=True) — feedback route has no ownership check, bug deferred to T-D-11. Factory bug fixed: uuid.UUID(conv_id) → conv_id (str) in factories/conversation.py.

- [x] T-D-03  Add analytics access-gate coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/observability
  - deliverable: `apps/api/tests/integration/test_analytics.py`
  - test_ids: observability.unit.001, observability.unit.002, observability.unit.003, observability.unit.004
  - depends_on: [T-A-04, T-C-99]
  - code_fix: NONE
  - estimated_loc: 95 lines
  - estimated_runtime: med
  - notes: Exercise member, org-admin, free-user, and system-admin access paths explicitly.

- [x] T-D-04  Add analytics aggregation/export coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/observability
  - deliverable: `apps/api/tests/integration/test_analytics.py`
  - test_ids: observability.unit.005, observability.unit.006, observability.unit.007
  - depends_on: [T-D-03]
  - code_fix: NONE
  - estimated_loc: 80 lines
  - estimated_runtime: med
  - notes: Group areas, top-queries isolation, and CSV export around one seeded analytics dataset.

- [x] T-D-05  Add health probe coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/observability
  - deliverable: `apps/api/tests/integration/test_health.py`
  - test_ids: observability.unit.010, observability.unit.011, observability.unit.012, observability.unit.013, observability.unit.014
  - depends_on: [T-C-99]
  - code_fix: NONE
  - estimated_loc: 95 lines
  - estimated_runtime: med
  - notes: Keep health routes rate-limit-exempt and shape-validated without overfitting to host metrics.

- [x] T-D-06  Land FIX-05 analytics date-range correction
  - spec: sdd/backend-saas-test-coverage/spec/observability
  - deliverable: `apps/api/app/api/routes/analytics.py`, `apps/api/tests/unit/test_analytics_dates.py`
  - test_ids: observability.unit.009
  - depends_on: [T-D-03]
  - code_fix: FIX-05
  - estimated_loc: 25 lines
  - estimated_runtime: fast
  - notes: Lock the inclusive/exclusive contract in code comments and in the unit test.

- [x] T-D-07  Add notifications service + list/count coverage
  - spec: sdd/backend-saas-test-coverage/spec/notifications
  - deliverable: `apps/api/tests/unit/test_notification_service.py`, `apps/api/tests/integration/test_notifications.py`
  - test_ids: notifications.unit.001, notifications.unit.002, notifications.unit.003, notifications.unit.004
  - depends_on: [T-A-03, T-A-08]
  - code_fix: NONE
  - estimated_loc: 95 lines
  - estimated_runtime: med
  - notes: Cover auth, creation, pagination, and unread count before mutation tests.

- [x] T-D-08  Add notifications mutation/preference coverage
  - spec: sdd/backend-saas-test-coverage/spec/notifications
  - deliverable: `apps/api/tests/integration/test_notifications.py`
  - test_ids: notifications.unit.005, notifications.unit.006, notifications.unit.007, notifications.unit.008
  - depends_on: [T-D-07, T-A-05]
  - code_fix: NONE
  - estimated_loc: 85 lines
  - estimated_runtime: med
  - notes: Reuse `assert_isolated` for mark-read ownership protection.

- [x] T-D-09  Add password-reset email flow coverage
  - spec: sdd/backend-saas-test-coverage/spec/notifications
  - deliverable: `apps/api/tests/integration/test_emails.py`
  - test_ids: notifications.unit.009, notifications.unit.010
  - depends_on: [T-A-08]
  - code_fix: NONE
  - estimated_loc: 60 lines
  - estimated_runtime: med
  - notes: Use the mock provider to verify outbound email intent without touching a real vendor.

- [x] T-D-10  Add email service resilience coverage
  - spec: sdd/backend-saas-test-coverage/spec/notifications
  - deliverable: `apps/api/tests/unit/test_email_service.py`
  - test_ids: notifications.unit.011, notifications.unit.012
  - depends_on: [T-A-08]
  - code_fix: NONE
  - estimated_loc: 45 lines
  - estimated_runtime: fast
  - notes: Assert graceful handling when the provider raises, especially on non-critical paths.

- [x] T-D-11  FIX-03b cross-tenant filter audit wave 2
  - spec: sdd/backend-saas-test-coverage/spec/notifications
  - deliverable: `apps/api/app/api/routes/analytics.py`, `apps/api/app/api/routes/notifications.py`, `apps/api/app/api/routes/emails.py`
  - test_ids: observability.unit.006, notifications.unit.006
  - depends_on: [T-D-04, T-D-08]
  - code_fix: FIX-03
  - estimated_loc: 45 lines
  - estimated_runtime: med
  - notes: Keep this wave surgical: org scoping in analytics, user scoping in notifications/email side paths.

- [x] T-D-99  Verify Batch D and commit
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: Batch D route/test files, coverage output, git commit
  - test_ids: conversations.unit.001, conversations.unit.002, conversations.unit.003, conversations.unit.004, conversations.unit.015, observability.unit.001, observability.unit.002, observability.unit.003, observability.unit.004, observability.unit.005, observability.unit.006, observability.unit.007, observability.unit.009, observability.unit.010, observability.unit.011, observability.unit.012, observability.unit.013, observability.unit.014, notifications.unit.001, notifications.unit.002, notifications.unit.003, notifications.unit.004, notifications.unit.005, notifications.unit.006, notifications.unit.007, notifications.unit.008, notifications.unit.009, notifications.unit.010, notifications.unit.011, notifications.unit.012
  - depends_on: [T-D-01, T-D-02, T-D-03, T-D-04, T-D-05, T-D-06, T-D-07, T-D-08, T-D-09, T-D-10, T-D-11]
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: slow
  - notes: Run full pytest + coverage and commit as `test(backend): batch D — conversations/analytics/notifications coverage`.

## Batch E — Shared content + documents/search/export/analysis

**Scope summary**: finish the dark user-content organization routes, then close the documents/search/export/analysis surface with fail-safe logging and the last isolation audit wave.

**Entry criteria**: Batch D complete; shared factories/helpers are already proven; analytics/notifications fixes are settled.

**Exit criteria**: all shared subresources and documents/search/export/analysis specs are green, FIX-04 is landed, and wave 3 isolation audits are closed.

- [x] T-E-01  Add shared conversation lifecycle coverage
  - spec: sdd/backend-saas-test-coverage/spec/conversations
  - deliverable: `apps/api/tests/integration/test_shared.py`
  - test_ids: conversations.unit.005, conversations.unit.006, conversations.unit.007
  - depends_on: [T-A-02, T-D-01]
  - code_fix: NONE
  - estimated_loc: 85 lines
  - estimated_runtime: med
  - notes: Cover share creation, public read, and revocation in one file because they share the same link lifecycle.

- [x] T-E-02  Add bookmark coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/conversations
  - deliverable: `apps/api/tests/integration/test_bookmarks.py`
  - test_ids: conversations.unit.008, conversations.unit.009
  - depends_on: [T-A-02, T-A-05, T-C-11]
  - code_fix: NONE
  - estimated_loc: 60 lines
  - estimated_runtime: med
  - notes: Use message/conversation factories so the tests stay focused on bookmark semantics.

- [ ] T-E-03  Add tag coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/conversations
  - deliverable: `apps/api/tests/integration/test_tags.py`
  - test_ids: conversations.unit.010, conversations.unit.011
  - depends_on: [T-A-02, T-C-11]
  - code_fix: NONE
  - estimated_loc: 65 lines
  - estimated_runtime: med
  - notes: Group CRUD and assign/unassign because both consume the same tag fixture state.

- [ ] T-E-04  Add folder coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/conversations
  - deliverable: `apps/api/tests/integration/test_folders.py`
  - test_ids: conversations.unit.012
  - depends_on: [T-A-04, T-A-05, T-C-11]
  - code_fix: NONE
  - estimated_loc: 45 lines
  - estimated_runtime: med
  - notes: One focused file is enough because CRUD and isolation share the same route family.

- [ ] T-E-05  Add memory coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/conversations
  - deliverable: `apps/api/tests/integration/test_memory.py`
  - test_ids: conversations.unit.013, conversations.unit.014
  - depends_on: [T-A-05, T-C-11]
  - code_fix: NONE
  - estimated_loc: 55 lines
  - estimated_runtime: med
  - notes: Keep the list/read ownership expectations aligned with the user-owned 404 convention.

- [ ] T-E-06  Add search filter validator unit cluster
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/unit/test_search_filters.py`
  - test_ids: documents-search.unit.001, documents-search.unit.002, documents-search.unit.003
  - depends_on: [T-D-99]
  - code_fix: NONE
  - estimated_loc: 65 lines
  - estimated_runtime: fast
  - notes: Keep pure filter validation/unit query construction out of the DB path.

- [ ] T-E-07  Add search happy-path and auth coverage
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/integration/test_search.py`
  - test_ids: documents-search.unit.004, documents-search.unit.005
  - depends_on: [T-A-03, T-A-07]
  - code_fix: NONE
  - estimated_loc: 65 lines
  - estimated_runtime: med
  - notes: Seed embeddings once per test cluster and keep auth coverage cheap.

- [ ] T-E-08  Add saved-search and history coverage cluster
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/integration/test_search.py`
  - test_ids: documents-search.unit.006, documents-search.unit.007
  - depends_on: [T-A-03, T-A-05, T-E-07]
  - code_fix: NONE
  - estimated_loc: 60 lines
  - estimated_runtime: med
  - notes: Reuse the saved-search factory and assert pagination/auth together.

- [ ] T-E-09  Land FIX-04 search history fail-safe
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/app/api/routes/search.py`, `apps/api/tests/unit/test_search_logging.py`
  - test_ids: documents-search.unit.008
  - depends_on: [T-E-07, T-E-08]
  - code_fix: FIX-04
  - estimated_loc: 20 lines
  - estimated_runtime: fast
  - notes: Wrap history logging with warning-level fail-safe behavior instead of failing the request.

- [ ] T-E-10  Add analysis happy-path coverage
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/integration/test_analysis.py`
  - test_ids: documents-search.unit.009
  - depends_on: [T-A-07, T-E-07]
  - code_fix: NONE
  - estimated_loc: 45 lines
  - estimated_runtime: med
  - notes: Use the shared LLM helper so analysis stays deterministic.

- [ ] T-E-11  Add analysis isolation coverage
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/integration/test_analysis.py`
  - test_ids: documents-search.unit.010
  - depends_on: [T-A-05, T-E-10]
  - code_fix: NONE
  - estimated_loc: 40 lines
  - estimated_runtime: med
  - notes: Assert foreign document IDs are rejected or filtered without leaking data.

- [ ] T-E-12  Add export shape and consultation ownership coverage
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/integration/test_export.py`
  - test_ids: documents-search.unit.011, documents-search.unit.012
  - depends_on: [T-A-02, T-A-05, T-D-01]
  - code_fix: NONE
  - estimated_loc: 55 lines
  - estimated_runtime: med
  - notes: Pair happy-path PDF bytes assertions with consultation ownership checks.

- [ ] T-E-13  Add export conversation and upload isolation coverage
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/integration/test_export.py`, `apps/api/tests/integration/test_upload.py`
  - test_ids: documents-search.unit.013, documents-search.unit.014
  - depends_on: [T-C-07, T-E-12]
  - code_fix: NONE
  - estimated_loc: 50 lines
  - estimated_runtime: med
  - notes: Reuse the upload fixtures from Batch C so document ownership stays consistent.

- [ ] T-E-14  Add documents admin-mutation guard coverage
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/tests/integration/test_documents.py`
  - test_ids: documents-search.unit.015
  - depends_on: [T-C-01, T-C-99]
  - code_fix: NONE
  - estimated_loc: 35 lines
  - estimated_runtime: med
  - notes: Keep admin-only document writes aligned with the centralized `require_admin` dependency.

- [ ] T-E-15  FIX-03c cross-tenant filter audit wave 3
  - spec: sdd/backend-saas-test-coverage/spec/documents-search
  - deliverable: `apps/api/app/api/routes/search.py`, `apps/api/app/api/routes/analysis.py`, `apps/api/app/api/routes/export.py`, `apps/api/app/api/routes/upload.py`, `apps/api/app/api/routes/bookmarks.py`, `apps/api/app/api/routes/tags.py`, `apps/api/app/api/routes/folders.py`, `apps/api/app/api/routes/memory.py`, `apps/api/app/api/routes/shared.py`
  - test_ids: conversations.unit.005, conversations.unit.007, conversations.unit.008, conversations.unit.009, conversations.unit.010, conversations.unit.011, conversations.unit.012, conversations.unit.013, conversations.unit.014, documents-search.unit.006, documents-search.unit.010, documents-search.unit.012, documents-search.unit.013, documents-search.unit.014
  - depends_on: [T-E-01, T-E-02, T-E-03, T-E-04, T-E-05, T-E-08, T-E-11, T-E-12, T-E-13]
  - code_fix: FIX-03
  - estimated_loc: 85 lines
  - estimated_runtime: med
  - notes: Final ownership-filter sweep; stop and re-verify scope if the audit exceeds the 8-file budget materially.

- [ ] T-E-99  Verify Batch E and commit
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: Batch E route/test files, coverage output, git commit
  - test_ids: conversations.unit.005, conversations.unit.006, conversations.unit.007, conversations.unit.008, conversations.unit.009, conversations.unit.010, conversations.unit.011, conversations.unit.012, conversations.unit.013, conversations.unit.014, documents-search.unit.001, documents-search.unit.002, documents-search.unit.003, documents-search.unit.004, documents-search.unit.005, documents-search.unit.006, documents-search.unit.007, documents-search.unit.008, documents-search.unit.009, documents-search.unit.010, documents-search.unit.011, documents-search.unit.012, documents-search.unit.013, documents-search.unit.014, documents-search.unit.015
  - depends_on: [T-E-01, T-E-02, T-E-03, T-E-04, T-E-05, T-E-06, T-E-07, T-E-08, T-E-09, T-E-10, T-E-11, T-E-12, T-E-13, T-E-14, T-E-15]
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: slow
  - notes: Run full pytest + coverage and commit as `test(backend): batch E — shared/docs/search/export/analysis coverage`.

## Tail tasks

- [ ] T-900  Run full regression pass
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: full-suite pytest output for `apps/api/tests/`
  - test_ids: NONE
  - depends_on: [T-E-99]
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: slow
  - notes: `docker exec tukijuris-api-1 pytest tests/ -v --tb=short` must be green except the explicitly pinned W7 strict xfail.

- [ ] T-901  Write post-change coverage diff report
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: `openspec/changes/backend-saas-test-coverage/coverage-report.md`
  - test_ids: NONE
  - depends_on: [T-900]
  - code_fix: NONE
  - estimated_loc: 40 lines
  - estimated_runtime: med
  - notes: Compare final coverage against `baseline-coverage.json` and summarize MUST/STRETCH outcomes by module.

- [ ] T-902  Confirm archive readiness for sdd-verify
  - spec: sdd/backend-saas-test-coverage/design
  - deliverable: readiness checklist confirmation inside `openspec/changes/backend-saas-test-coverage/tasks.md` context and clean test tree state
  - test_ids: NONE
  - depends_on: [T-901]
  - code_fix: NONE
  - estimated_loc: 0 lines
  - estimated_runtime: fast
  - notes: Confirm all tasks are checked, all spec acceptance criteria are met, and no stray xfails/skips were introduced.
