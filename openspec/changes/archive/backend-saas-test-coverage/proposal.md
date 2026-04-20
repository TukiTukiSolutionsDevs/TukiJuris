---
change: backend-saas-test-coverage
status: proposed
owner: orchestrator
created: 2026-04-19
execution_mode: auto
artifact_store: openspec
strict_tdd: false
---

# Proposal: Backend SaaS Test Coverage

## 1. Why
The current TukiJuris backend has uneven test coverage. While auth, billing, and RBAC are well-hardened, 7 core domains (analytics, notifications, api_keys, chat streaming, memory, bookmarks, tags/folders, and shared) are completely dark despite housing production traffic. There is no global Row Level Security (RLS), and the SDK surface (public API v1) only has smoke tests. Additionally, a recent auth bug was reported on `/api/conversations/` (currently parked). Hardening these areas is critical to prevent silent regressions and data leaks.

## 2. Scope
**What's IN:**
- Add/harden unit and integration tests across the 10 domains identified in the exploration (auth, billing, conversations/chat/stream, byok/admin, documents/search, notifications/analytics/v1).
- Code fixes necessary to make the added tests pass.
- Cross-tenant ownership isolation tests as a cross-cutting addition.

**What's OUT:**
- Frontend changes.
- The `redirect_slashes=True` + cross-origin bug (parked for a separate change after this).
- Sprint 3 Batch 3 items already underway (role-consistency 8.2 integration coverage, middleware stale cleanup, BYOK vitest tests).
- Prior settled SDD work (`fix-auth-tokens`, `byok-plan-gate`, `fix-role-model-consistency`, `fix-usage-limit-schema`, `admin-saas-panel`, `payment-webhook-idempotency`) are already done and not in scope.

## Capabilities
### New Capabilities
None.

### Modified Capabilities
- `auth`: Add missing test coverage for sessions and profile update.
- `billing`: Add missing test coverage for HMAC tamper detection and downgrade handler.
- `conversations`: Add missing test coverage for write paths, streaming, and content organization.
- `byok`: Add missing test coverage for API key CRUD and upload validation.
- `admin`: Add missing test coverage for RBAC integration and 403 enforcement.
- `documents`: Add missing test coverage for advanced search and analysis flow.
- `notifications`: Add missing test coverage for CRUD and auth gates.
- `observability`: Add missing test coverage for analytics and health metrics.
- `public-api-v1`: Add missing test coverage for SDK surface auth and quota.
- `organizations`: Add missing test coverage for seat sync and member removal.

## 3. Per-domain Breakdown

| Domain | Current Coverage | Target Additions | Acceptance Criteria | Risk |
|--------|------------------|------------------|---------------------|------|
| **auth / oauth** | Excellent | `GET /api/auth/sessions`, `PUT /api/auth/me` validation, OAuth MS errors, internal helper mock. | All auth endpoints have 401/403 tests. Sessions and OAuth errors tested. No skipped tests. | Priority 1 |
| **billing / trials** | Excellent | HMAC tamper detection, downgrade handler, `me_invoices` org membership gate, trials retry. | HMAC verification has tamper unit test. 7 deferred webhook warnings addressed. me_invoices gated. | Priority 2 |
| **conversations / chat / stream** | Minimal / Dark | SSE stream quota gate, frame format, BYOK fallback, ownership isolation for writes, bookmarks/tags/memory CRUD. | All write paths have owner-only test. Stream has SSE quota test. Sub-resources have CRUD smoke tests. | Priority 3 & 7 |
| **public-api-v1** | Minimal | Scope check, dual-auth, usage quota, `POST /api/v1/query` happy-path. | Each restricted endpoint has scope-check test. | Priority 4 |
| **byok / api_keys** | Partial | Developer API key CRUD, scope validation, provider failure, upload isolation. | API key CRUD integration tested. Upload ownership explicitly tested. | Priority 5 |
| **admin / rbac** | Partial | `GET /api/admin/*` 403 enforcement on non-admins, RBAC assign/revoke integration. | All admin routes have non-admin 403 test. | Priority 6 |
| **organizations** | Good | Member removal, role enforcement, seat sync. | Owner-only ops tested, seat sync tested. | Priority 8 |
| **analytics** | Dark | Entire file coverage, org-admin gates, cost calculation, date range logic. | Every analytics endpoint has org-admin gate test. | Priority 9 |
| **notifications / emails** | Dark | Notifications CRUD, ownership isolation, auth gates. | CRUD has auth + ownership tests. | Priority 10 |
| **documents / search / analysis** | Partial | Advanced search filter combos, saved searches, LLM mock analysis, export ownership. | Filter unit tests exhaustive. Saved search + history auth gated. Analysis mocked. | Priority 11 |

## 4. Batches
The implementation will be divided into 5 batches:

- **Batch A**: `auth` / `oauth` gaps + `billing` deferred warnings.
  - *Count*: ~10 tests.
  - *Dependencies*: None.
- **Batch B**: `chat` + `stream` + `public-api-v1`.
  - *Count*: ~15 tests.
  - *Dependencies*: Batch A.
- **Batch C**: `admin` 403 guards + `byok` CRUD + `organizations` isolation.
  - *Count*: ~15 tests.
  - *Dependencies*: Batch B.
- **Batch D**: `conversations` write paths + `analytics` + `notifications`/`emails`.
  - *Count*: ~20 tests.
  - *Dependencies*: Batch C.
- **Batch E**: `bookmarks`/`tags`/`folders`/`memory`/`shared` + `documents`/`search`/`export`/`analysis`.
  - *Count*: ~20 tests.
  - *Dependencies*: Batch D.

## 5. Quality Bar / DoD
- All new tests pass in CI.
- Zero `skip("TODO")` remaining in the suite. Existing ones must be fixed or promoted to `xfail(strict=True)` with explicit reasons.
- Coverage delta reported per domain.
- Cross-tenant isolation test suite covers every org-scoped route (catch-all).
- No collection errors.

## 6. Risks & Mitigations
- **Sprint 3 overlap**: Certain items like role-consistency 8.2 and BYOK vitest are already covered in Sprint 3 Batch 3 (obs #267). We will diff against Batch 3 to avoid double-booking and merge cleanly.
- **`stream.py` quota gate divergence**: Might not be wired identically to `chat.py`. Expecting code fixes; treat as a bug.
- **`_ensure_admin` duplication**: Currently duplicated across admin_saas, admin_invoices, admin_trials. Will consolidate during Batch C to avoid inconsistent checks.
- **No global RLS**: Ownership isolation tests may expose real cross-tenant bugs since scoping is manual per route. Code fix scope creep is allowed and budgeted.

## 7. Non-goals
- No refactors unrelated to testability.
- No new features.
- No frontend work.

## 8. Rollout / Rollback
- **Rollout**: Land per-batch. Each batch will be committed in its own series and followed by a dedicated verify pass.
- **Rollback**: If a batch causes CI failures or uncovers deep regressions, the commit series for that batch will be reverted without blocking the verified prior batches.