# Coverage Report — `backend-saas-test-coverage`

Status: **Batch A complete**. Batches B–E pending.

## Snapshot

| Phase | Tests passing | Tests xfailed | Tests failed | Wall time |
|---|---|---|---|---|
| Baseline (pre-change) | 1111 | 0 | 1 (W7) | — |
| After Batch A | **1145** | **3** | **0** | 30.84s |
| **Delta** | **+34** | +3 (W7 pinned + 2 new gaps) | −1 (W7 moved to xfail) | — |

## Line coverage

| Metric | Baseline | After Batch A | Delta |
|---|---|---|---|
| Total statements | 8004 | 8004 | 0 |
| Covered lines | 5161 | 5190 | **+29** |
| Overall % | 64.48% | 64.84% | **+0.36 pp** |

The small overall delta is expected: Batch A focused on edge cases in already-well-covered domains (auth, billing, admin-rbac). The larger gains come in Batch B (stream.py 0% → 75% target) and Batch D (notifications/analytics 0% → 75% target).

## Top domain gains (Batch A)

| Module | Before | After | Delta |
|---|---|---|---|
| `app/api/routes/billing.py` | 60.7% | 66.8% | **+6.1 pp** |
| `app/rbac/service.py` | 92.5% | 95.3% | +2.8 pp |

## Tests added (Batch A)

| Sub-batch | Domain | Files | Tests | Commit |
|---|---|---|---|---|
| A.1 (infra) | — | 9 factories + 3 helpers + 1 mock + 1 fixture | 0 | `3fdd7f7` |
| A.1 (unit) | auth | `test_auth_{helpers,me,sessions}.py` | 3 | `9887d95` |
| A.2 | auth | `test_auth_refresh_reuse.py`, `test_auth_logout_all.py`, `test_auth_oauth_state.py` | 11 (10 pass + 1 xfail) | `6957811`, `808b3b8`, `1673291` |
| A.3 | billing | `test_payment_webhooks.py`, `test_subscription_service.py` (appended), `test_me_invoices.py`, `test_trials_routes.py` (appended) | 17 (16 pass + 1 xfail) | `951ede9` |
| A.4 | admin-rbac | `test_admin_routes.py`, `test_rbac_admin.py` | 5 | `7dc01d5` |
| **Total** | | | **36 (34 pass + 2 xfail)** | 6 commits |

(W7 xfail was pinned separately in `de9ce83` — not counted in Batch A additions.)

## Bugs surfaced (documented, deferred)

Each xfail(strict=True) pins a real production bug found by the new coverage:

| ID | Severity | Area | Engram topic | Fix micro-change |
|---|---|---|---|---|
| FIX-REUSE | **HIGH** (security) | `RefreshTokenService.rotate()` | `tukijuris/refresh-family-kill-bug` | `fix-refresh-family-kill` |
| billing.unit.004 | MEDIUM (ops) | `_handle_payment_failed` missing owner notification | `tukijuris/payment-failed-notification-gap` | `fix-payment-failed-notification` |

**These are NOT in this change's scope.** They are surfaced; fixes ship in their own SDD changes.

## Remaining work (Batches B–E)

| Batch | Domains | Expected gains |
|---|---|---|
| B | chat + stream + public-api-v1 (+ FIX-01) | +15–20 tests, large coverage gain on stream.py |
| C | admin (FIX-02) + byok CRUD + orgs isolation (+ FIX-03a) | +20 tests, cross-tenant harness exercise |
| D | conversations write + analytics + notifications/emails (+ FIX-03b) | +25 tests, big coverage gain on analytics (0 → ~70) and notifications (0 → ~75) |
| E | bookmarks/tags/folders/memory/shared + documents/search/export/analysis (+ FIX-03c) | +30 tests, broad gain on product content domains |

## Test infrastructure installed

Reusable from Batch B onward:
- `apps/api/tests/factories/` — 9 model factories (user, org, conversation, invoice, llm_key, notification, api_key, saved_search)
- `apps/api/tests/helpers/isolation.py` — `two_orgs_two_users` + `assert_isolated`
- `apps/api/tests/helpers/sse.py` — SSE assertion helper for Batch B
- `apps/api/tests/helpers/llm.py` — mock LLM
- `apps/api/tests/mocks/email.py` — mock email provider with `last_sent` introspection
- `apps/api/tests/fixtures/tenants.py` — `TenantPair` context manager (wired to `tenant_pair` pytest fixture)
- `apps/api/coverage-targets.yaml` — per-domain coverage targets
- `apps/api/scripts/check_coverage.py` — enforcement script

## Pre-existing smells flagged (not in scope, not fixed)

- Welcome-notification FK violation during register flow — notification insert runs before user commit in the chain triggered by `refresh.issued`. Caught by `try/except`; currently emits a WARNING log. Separate micro-change candidate.

## Next

`sdd-apply` Batch B: chat + stream + public-api-v1. FIX-01 (stream quota alignment with chat.py) lands paired with stream tests per design §3.

---

## Batch B — closed

### Snapshot after Batch B

| Phase | Tests passing | Tests xfailed | Tests failed | Wall time |
|---|---|---|---|---|
| Baseline | 1111 | 0 | 1 (W7) | — |
| After Batch A | 1145 | 3 | 0 | 30.84s |
| **After Batch B** | **1165** | **4**–5 (W7 flaky) | 0–1 (W7 flaky race) | 137.59s |

The 1-failed count in the post-B run was the W7 xfail flipping to XPASS (strict=True reports as FAIL). This is PRE-EXISTING flakiness, not a Batch B regression. Other xfails stable: FIX-REUSE, billing.unit.004, stream.008 anonymous, stream.009 disconnect.

### Line coverage — Batch B delta

| Metric | Post-A | Post-B | Δ (B-only) | Δ (baseline→B) |
|---|---|---|---|---|
| Covered lines | 5190 | 5377 | **+187** | +216 |
| Overall % | 64.84% | **67.15%** | **+2.31 pp** | **+2.67 pp** |

### Top Batch B gains

| Module | Post-A | Post-B | Δ |
|---|---|---|---|
| `app/api/routes/stream.py` | 22.9% | 65.3% | **+42.4 pp** |
| `app/agents/base_agent.py` | 48.9% | 64.4% | +15.6 pp |
| `app/api/routes/v1.py` | 53.5% | 68.2% | +14.7 pp |
| `app/api/deps.py` | 66.7% | 78.6% | +11.9 pp (FIX-06) |
| `app/api/routes/chat.py` | 52.7% | 62.2% | +9.5 pp |

### Tests added — Batch B

| Sub-batch | File | Tests | Commit |
|---|---|---|---|
| B.1 | `test_chat_routes.py` | 6 pass | `59eaf12` |
| B.2 | `test_stream_routes.py` | 6 (4 pass + 2 xfail policy) | `1f3f0e6` |
| B.3 | `test_v1_api.py` | 10 pass + FIX-06 | `ec46c9b` |

### FIX status (after Batch B)

| FIX | Predicted | Actual | Resolution |
|---|---|---|---|
| FIX-01 stream quota | missing | **confirmed non-issue** — stream.py already enforced it | Design §3 should be amended; no code change |
| FIX-06 v1 headers | missing | **confirmed real** — fixed in `deps.py` via Response dep | Committed as part of `ec46c9b` |

### Deferred to policy (new xfails from B.2)

- `stream.008` anonymous access — stream.py uses `get_optional_user`. Owner decides: enforce auth / IP-limit anonymous / dual-mode
- `stream.009` client disconnect cancellation — untested runaway LLM cost vector

Both documented in engram `tukijuris/stream-anonymous-abuse-vector`.

### Next

Batch C — admin FIX-02 (`_ensure_admin` consolidation) + byok CRUD + orgs cross-tenant isolation (first wave of FIX-03).

---

## Batch C — closed

### Snapshot after Batch C

| Phase | Tests passing | Tests xfailed | Tests failed | Wall time |
|---|---|---|---|---|
| After Batch A | 1145 | 3 | 0 | 30.84s |
| After Batch B | 1165 | 4–5 (W7 flaky) | 0–1 (W7 flaky) | 137.59s |
| **After Batch C** | **1181** | **5** | 0–1 (W7 flaky) | 47.76s |

### Line coverage — Batch C delta

| Metric | Post-B | Post-C | Δ (C-only) | Δ (baseline→C) |
|---|---|---|---|---|
| Covered lines | 5377 | 5370 | −7 (FIX-02 removed duplicated code) | +209 |
| Overall % | 67.15% | **67.18%** | **+0.03 pp** | **+2.70 pp** |

Coverage % rose only marginally because Batch C covered code paths already touched (byok/orgs) and FIX-02 shrank the denominator by removing duplicated `_ensure_admin` helpers.

### Top Batch C gains

| Module | Post-B | Post-C | Δ |
|---|---|---|---|
| `app/services/email_service.py` | 42.6% | 45.7% | +3.2 pp |
| `app/services/llm_key_service.py` | 43.3% | 46.3% | +3.0 pp |
| `app/api/routes/api_keys.py` | 54.4% | 56.2% | +1.9 pp |
| `app/api/routes/organizations.py` | 55.2% | 55.9% | +0.7 pp |
| `app/api/deps.py` | 78.6% | 79.1% | +0.5 pp (FIX-02) |

### Tests added — Batch C

| Sub-batch | File | Tests | Commit |
|---|---|---|---|
| C.1 FIX-02 | `test_admin_deps.py` + 4 route refactors | 2 pass | `015368d` |
| C.2 | `test_byok_crud.py` | 8 (7 pass + 1 xfail FIX-03b) | `4f90a2c` |
| C.3a | `factories/org.py` fix | — | `3f13fa8` |
| C.3b | `test_organizations_isolation.py` | 7 pass | `c2fd4c8` |

### FIX status (after Batch C)

| FIX | Status | Notes |
|---|---|---|
| FIX-02 | **Landed** | `_ensure_admin` → `require_admin` in `deps.py`, 7 routes refactored, −36/+15 LOC net |
| FIX-03a (orgs/conversations) | **Confirmed NON-ISSUE** | `_require_role()` + `user_id` filters already correct |
| FIX-03b (byok unique constraint) | **Surfaced, xfailed** | `UniqueConstraint(user_id, provider)` missing on `UserLLMKey`; duplicate POST returns 201 not 409 |

### New policy-decision xfails (Batch C)

- `FIX-03b` — low urgency; cosmetic DB noise, `get_user_key_for_provider` returns most recent. Engram: `tukijuris/byok-fix-03b-unique-constraint`.

### Next

Batch D — conversations write paths + analytics (848 LOC, 0 baseline tests) + notifications (377 LOC, 0 baseline tests). Expected largest coverage jump of the change.
