---
change: backend-saas-test-coverage
phase: explore
artifact_store: openspec
project: tukijuris
date: 2026-04-19
status: completed
author: sdd-explore
---

# Exploration: Backend SaaS Test Coverage

## Executive Summary

TukiJuris has ~1,099 test functions across 60+ test files, but coverage is deeply
uneven. Auth, billing, and RBAC are well-hardened (hundreds of focused unit +
integration tests from Sprints 1–3). Seven domains — analytics, notifications,
api_keys (CRUD), chat streaming, memory, bookmarks, tags/folders, and shared — have
**zero or near-zero** test coverage despite housing production traffic paths.
The public API v1 (671 lines, 3 billable endpoints) has 6 smoke tests.
The stream endpoint (640 lines) has 1 test. This creates an asymmetric risk profile
where core SaaS money/auth flows are solid but the user-facing product surface
(conversations, content organization, observability) is completely dark.

---

## 1. Domain Inventory

### 1.1 `auth`

**Purpose**: Registration, login, JWT issuance and rotation, logout, session management,
user profile, permissions, onboarding. The foundational security layer for the entire API.

**Routers + key routes**:
| Method | Path |
|--------|------|
| POST | `/api/auth/register` |
| POST | `/api/auth/login` |
| POST | `/api/auth/refresh` |
| POST | `/api/auth/logout` |
| POST | `/api/auth/logout-all` |
| GET | `/api/auth/sessions` |
| GET | `/api/auth/me` |
| GET | `/api/auth/me/permissions` |
| PUT | `/api/auth/me` |
| POST | `/api/auth/me/onboarding` |

**OAuth sub-domain** (`oauth.py`):
| Method | Path |
|--------|------|
| GET | `/api/auth/oauth/providers` |
| GET | `/api/auth/oauth/google/authorize` |
| GET | `/api/auth/oauth/google/callback` |
| GET | `/api/auth/oauth/microsoft/authorize` |
| GET | `/api/auth/oauth/microsoft/callback` |

**Services consumed**: `auth_service.py`, `refresh_token_service.py`, `entitlement_service.py`,
`email_service.py`

**Models / tables**: `users`, `refresh_tokens`, `rbac_user_roles`, `rbac_roles`

**Upstream deps**: Redis (denylist `tukijuris:denylist:<jti>`, refresh rate-limit bucket
`ratelimit:rl:write:ip:<ip>`)

**Current tests**:
- `tests/test_auth.py` — 11 smoke tests (register, login, 401 paths)
- `tests/unit/test_refresh_*.py` — 7 files, ~1,500 lines: service, repo, routes, security,
  observability, rate-limit, denylist integration, settings
- `tests/unit/test_access_token_claims.py` — JWT claim assertions
- `tests/unit/test_auth_cookies.py` — cookie shape (304 lines)
- `tests/unit/test_cookie_domain.py` — domain scoping (259 lines)
- `tests/unit/test_oauth_*.py` — 4 files: returnto validation, integration, state JWT, refresh
- `tests/unit/test_sso_enforcement.py` — SSO-only org enforcement (279 lines)
- `tests/integration/test_logout.py`, `test_logout_all.py` — (243/246 lines each)
- `tests/integration/test_onboarding_flow.py` — (234 lines)
- `tests/integration/test_me_endpoint.py` — (190 lines)

**Obvious gaps**:
- No test for `GET /api/auth/sessions` list (session enumeration)
- No test for expired refresh token edge case at the route level
- No test for `PUT /api/auth/me` (profile update) request validation
- `_has_privileged_role` internal helper untested in isolation
- OAuth: no test for Microsoft callback error paths (code exchange failure)
- No test for `complete_onboarding` with invalid body

**Known red flags from engram**:
- RF-1 (obs #4): access_token stored in localStorage — frontend XSS exposure. Backend
  cannot fix this alone but test should assert cookie-only response shape.
- RF-2/#3 (obs #4): frontend never stores/uses refresh_token — backend auth flow is correct
  but frontend ignores it. Auth integration tests should prove backend contract is solid.

**Interactions**: feeds EVERY protected domain; OAuth threads through `returnTo` → billing redirect.

---

### 1.2 `conversations`

**Purpose**: Conversation history management, real-time chat (query + SSE stream), user
content organization (bookmarks, tags, folders, memory, shared links). The core user-facing
product surface.

**Routers + key routes**:

`conversations.py`:
| Method | Path |
|--------|------|
| GET | `/api/conversations/` |
| GET | `/api/conversations/{id}` |
| PATCH | `/api/conversations/{id}` (rename) |
| PATCH | `/api/conversations/{id}/pin` |
| PATCH | `/api/conversations/{id}/archive` |
| DELETE | `/api/conversations/{id}` |
| POST | `/api/conversations/{id}/share` |

`chat.py`:
| Method | Path |
|--------|------|
| POST | `/api/chat/` |
| GET | `/api/chat/models` |
| POST | `/api/chat/models/{model_id}/ping` |
| GET | `/api/chat/agents` |

`stream.py`:
| Method | Path |
|--------|------|
| GET | `/api/stream/` |

`feedback.py`:
| Method | Path |
|--------|------|
| POST | `/api/feedback/` |
| GET | `/api/feedback/stats` |

`bookmarks.py`, `memory.py`, `tags.py`, `folders.py`, `shared.py` — each with
full CRUD (list/get/create/update/delete).

**Services consumed**: `conversations.py` service, `llm_adapter.py`, `rag.py`,
`reranker.py`, `memory_service.py`, `usage.py`, `entitlement_service.py`

**Models / tables**: `conversations`, `messages`, `feedback`, `bookmarks`, `tags`,
`folders`, `memory`, `uploaded_documents`

**Upstream deps**: LiteLLM / LangGraph (LLM calls), Redis (BYOK model fallback cache,
rate-limit buckets), pgvector (RAG retrieval)

**Current tests**:
- `tests/test_conversations.py` — 6 tests (list 401, list empty, list shape, get 401,
  get 404, invalid UUID 422). **No write-path, no share, no pin/archive/delete.**
- `tests/integration/test_chat_quota.py` — 187 lines, covers daily quota enforcement.
- `tests/test_feedback.py` — 11 tests (submit, stats, validation). Good.
- `tests/test_byok_plan_gate.py` — 247 lines, covers BYOK plan check in chat.
- Stream: **1 test** (likely auth check only)
- Bookmarks: **0 tests**
- Memory: **0 tests**
- Tags: **0 tests**
- Folders: **0 tests**
- Shared: **0 tests**

**Obvious gaps**:
- `POST /api/chat/` — no happy-path integration test (LLM mocked), no quota-exhausted
  response shape test
- `GET /api/stream/` — no SSE frame structure test, no quota-gate test, no mid-stream
  error handling test
- All of bookmarks, tags, folders, memory, shared = zero coverage
- Conversation CRUD write paths (rename, pin, archive, delete, share) = zero coverage
- Cross-conversation ownership isolation (user A cannot access user B's conversation)
  = untested
- `chat.py` BYOK model fallback logging path tested in byok_plan_gate but not at
  route level with full request lifecycle

**Interactions**: consumes `auth` (get_current_user), `billing` (usage.py quota check),
`byok` (model selection), `documents` (RAG retrieval), `upload` (in-chat file context).

---

### 1.3 `billing`

**Purpose**: Subscription lifecycle, payment provider webhooks (MercadoPago + Culqi),
checkout, usage metering, invoicing, trials. Money domain — highest criticality.

**Routers + key routes**:

`billing.py`:
| Method | Path |
|--------|------|
| GET | `/api/billing/config` |
| GET | `/api/billing/plans` (legacy) |
| GET | `/api/billing/{org_id}/usage` |
| GET | `/api/billing/{org_id}/subscription` |
| POST | `/api/billing/{org_id}/subscribe` |
| POST | `/api/billing/webhooks/mercadopago` |
| POST | `/api/billing/webhooks/culqi` |

`plans.py`:
| Method | Path |
|--------|------|
| GET | `/api/plans` |

`trials.py`:
| Method | Path |
|--------|------|
| GET | `/api/trials/current` |
| POST | `/api/trials/start` |
| POST | `/api/trials/add-card` |
| POST | `/api/trials/cancel` |
| POST | `/api/trials/retry-charge` |

`internal_trials.py` — scheduler-facing internal tick endpoints
`me_invoices.py` — `GET/GET /api/billing/{org_id}/invoices/{id}`
`admin_invoices.py` — admin invoice list/get/patch
`admin_trials.py` — admin trial list/patch

**Services consumed**: `subscription_service.py`, `plan_service.py`, `usage.py`,
`entitlement_service.py`, `invoice_service.py`, `invoice_pricing.py`,
`webhook_idempotency_service.py`, `trial_service.py`, `payment_providers/`

**Models / tables**: `subscriptions`, `invoices`, `trials`, `usage_records`, `organizations`

**Upstream deps**: MercadoPago API, Culqi API, Redis (idempotency cache), Scheduler

**Current tests**:
- `tests/test_billing.py` — 12 tests (plans list, usage, webhook bad body, subscribe)
- `tests/test_plans_route.py` — 83 tests (full plans catalog). Excellent.
- `tests/integration/test_webhook_idempotency.py` — 454 lines. Excellent.
- `tests/test_billing_webhook_invoice_creation.py` — 275 lines
- `tests/test_billing_trial_integration.py` — 382 lines
- `tests/test_invoice_batch_e.py` — 333 lines
- `tests/test_invoice_model.py` — 186 lines
- `tests/test_invoice_routes_admin.py` — 303 lines
- `tests/test_invoice_routes_user.py` — 227 lines
- `tests/test_invoice_service.py` — 534 lines
- `tests/test_payment_providers.py` — 402 lines
- `tests/test_trial_service.py` — 857 lines. Excellent.
- `tests/test_trials_routes.py` — 333 lines
- `tests/test_internal_trials_routes.py` — 328 lines
- `tests/test_admin_trials_routes.py` — 250 lines
- `tests/unit/test_subscription_service.py` — present
- `tests/unit/test_invoice_pricing.py` — present
- `tests/unit/test_webhook_idempotency_service.py` — present
- `tests/unit/test_usage_limits.py` — 314 lines

**Obvious gaps**:
- Webhook HMAC verification (`_verify_culqi_hmac`, `_verify_mp_hmac`) — no dedicated
  unit test for tampered signatures
- `POST /api/billing/{org_id}/subscribe` happy-path with mock payment provider —
  existing test uses a real org but may not cover the full checkout flow
- `_handle_subscription_deleted` and `_handle_payment_failed` webhook handlers
  need dedicated tests for downgrade retention logic
- `me_invoices.py` non-member access should return 403 — untested
- Trial `retry_charge` flow under `TRIALS_ENABLED=False` guard

**Known red flags from engram**:
- payment-webhook-idempotency archived (obs #143) — PASS WITH WARNINGS. 7 deferred
  warnings not yet addressed.
- invoices-model archived (obs #166) — 0 CRITICALs, 5 deferred WARNINGs.
- trials-lifecycle archived (obs #261) — 0 CRITICALs, 7 deferred WARNINGs.

**Interactions**: Billing enforces plan state read by `entitlement_service` (used by
byok, chat, api_keys). Trial state affects org plan. Invoice lifecycle runs through scheduler.

---

### 1.4 `admin`

**Purpose**: Internal operations — system stats, user management, activity logs, knowledge
base management, audit trail, SaaS metrics, RBAC role assignment.

**Routers + key routes**:

`admin.py`:
| Method | Path |
|--------|------|
| GET | `/api/admin/stats` |
| GET | `/api/admin/users` |
| GET | `/api/admin/activity` |
| GET | `/api/admin/knowledge` |
| GET | `/api/admin/audit-log` |

`admin_saas.py`:
| Method | Path |
|--------|------|
| GET | `/api/admin/saas/revenue` |
| GET | `/api/admin/saas/byok` |

`rbac_admin.py`:
| Method | Path |
|--------|------|
| GET | `/api/admin/rbac/roles` |
| GET | `/api/admin/rbac/roles/{id}/permissions` |
| POST | `/api/admin/rbac/users/{user_id}/roles` |
| DELETE | `/api/admin/rbac/users/{user_id}/roles/{role_id}` |

**Services consumed**: `admin_metrics_service.py`, `subscription_service.py`,
`rbac/service.py`, `rbac/audit.py`

**Models / tables**: `users`, `conversations`, `documents`, `subscriptions`,
`rbac_roles`, `rbac_permissions`, `rbac_user_roles`, `rbac_audit_log`

**Upstream deps**: None external (DB + Redis for RBAC cache)

**Current tests**:
- `tests/integration/test_admin_saas_panel.py` — 353 lines (revenue, BYOK list, auth guard)
- `tests/unit/test_admin_metrics_service.py` — 256 lines
- `tests/unit/test_admin_audit_log.py` — 208 lines
- `tests/unit/test_rbac_*.py` — 9 files: audit, cache, constants, dependencies, migration,
  models, routes, schemas, seed, service (~500+ lines each on average)
- `tests/test_admin_trials_routes.py` — admin trials (250 lines)
- `tests/test_invoice_routes_admin.py` — admin invoice (303 lines)

**Obvious gaps**:
- `GET /api/admin/users` — no test for filtering, pagination, or non-admin 403
- `GET /api/admin/activity` — zero coverage
- `GET /api/admin/knowledge` — zero coverage
- `GET /api/admin/audit-log` — service tested in unit but route-level 403 guard untested
- `admin_saas.py` `_ensure_admin` is a local function (not the deps.py guard) —
  divergence from RBAC pattern, not tested for edge case where `is_admin=False`
- RBAC assign/revoke role routes missing happy-path integration test

**Known red flags from engram**:
- obs #79: Sprint 2 C11 — admin.py routes use WRITE guards (applied but test-validation
  pending Docker run)
- admin-saas-panel SDD change referenced but no archive obs found — likely completed
  within Sprint 3 item 2

**Interactions**: RBAC role assignment affects `entitlement_service` and `get_current_user`
token claim validation across all domains.

---

### 1.5 `byok`

**Purpose**: Developer API keys (external integrations) and BYOK LLM key management
(user-owned API keys for OpenAI/Anthropic/Gemini). Plan-gated (pro/studio only for BYOK).

**Routers + key routes**:

`api_keys.py`:
| Method | Path |
|--------|------|
| POST | `/api/keys/` |
| GET | `/api/keys/` |
| PATCH | `/api/keys/{key_id}` |
| DELETE | `/api/keys/{key_id}` |
| GET | `/api/keys/llm` |
| POST | `/api/keys/llm` |
| DELETE | `/api/keys/llm/{key_id}` |
| GET | `/api/keys/llm/providers` |
| GET | `/api/keys/llm/free-models` |
| POST | `/api/keys/llm/{key_id}/test` |

`upload.py`:
| Method | Path |
|--------|------|
| POST | `/api/upload/` |
| GET | `/api/upload/{doc_id}` |
| DELETE | `/api/upload/{doc_id}` |

**Services consumed**: `llm_key_service.py`, `llm_key_encryption.py`,
`entitlement_service.py`, `upload_service.py`

**Models / tables**: `api_keys`, `llm_keys`, `uploaded_documents`

**Upstream deps**: LLM provider APIs (for key testing), Redis (rate-limit)

**Current tests**:
- `tests/test_byok_plan_gate.py` — 247 lines (entitlement check for BYOK access)
- `tests/unit/test_llm_key_encryption.py` — encryption/decryption unit tests
- `tests/unit/test_llm_key_encryption_migration.py` — v1: prefix migration
- `tests/test_llm_key_isolation.py` — cross-user key isolation

**Obvious gaps**:
- Developer API key CRUD (`POST/GET/PATCH/DELETE /api/keys/`) = **zero** route-level tests
- `_validate_scopes` — no test for unknown scope rejection
- `POST /api/keys/llm/{key_id}/test` — no test for LLM provider failure propagation
- `GET /api/keys/llm/free-models` — no test
- Upload: file type rejection, max size enforcement = untested
- `DELETE /api/upload/{doc_id}` ownership check = untested

**Known red flags from engram**:
- byok-plan-gate archived (obs #70) — PASS WITH WARNINGS. Sprint 2 C5 applied.
- Sprint 2 C8: ingestion/generate_embeddings.py BYOK decryption with v1: prefix —
  deferred Batch 6 item (obs #267).

**Interactions**: api_keys feeds `get_authenticated_user` dual-auth; llm_keys feed
`chat.py` and `stream.py` model selection; upload feeds in-chat file context.

---

### 1.6 `organizations`

**Purpose**: Multi-tenant organization creation, membership management, and seat-based
billing for Studio plan. Foundational for org-scoped data isolation.

**Routers + key routes**:
| Method | Path |
|--------|------|
| POST | `/api/organizations/` |
| GET | `/api/organizations/` |
| GET | `/api/organizations/{org_id}` |
| PATCH | `/api/organizations/{org_id}` |
| POST | `/api/organizations/{org_id}/members` |
| GET | `/api/organizations/{org_id}/members` |
| DELETE | `/api/organizations/{org_id}/members/{user_id}` |

**Services consumed**: `subscription_service.py` (seat sync on member change),
`entitlement_service.py`

**Models / tables**: `organizations`, `org_memberships`

**Upstream deps**: None external

**Current tests**:
- `tests/test_organizations.py` — 202 lines, 13 tests (create, list, get, update,
  invite, list members — basic happy-path + auth/404 guards)

**Obvious gaps**:
- `DELETE /api/organizations/{org_id}/members/{user_id}` — not tested (remove member)
- Role enforcement: member cannot update org (403) — untested
- Owner self-removal edge case — untested
- Seat count sync (`_sync_member_plans`) when member is added/removed — untested
- Non-member attempt to GET org — should be 403, not tested
- Org with SSO-only enforcement + non-SSO member invite = untested

**Interactions**: org_id scoping used across billing (subscription), analytics (overview),
conversations (if org_id attached), and admin (user management by org).

---

### 1.7 `documents`

**Purpose**: Legal knowledge base navigation (El Peruano, TC, INDECOPI), semantic
search, case analysis, PDF/report export, file upload for in-chat context.

**Routers + key routes**:

`documents.py`:
| Method | Path |
|--------|------|
| GET | `/api/documents/` |
| GET | `/api/documents/search` |
| GET | `/api/documents/stats` |
| GET | `/api/documents/{id}/chunks` |

`search.py` (advanced):
| Method | Path |
|--------|------|
| GET | `/api/search/` |
| GET | `/api/search/suggestions` |
| POST | `/api/search/saved` |
| GET | `/api/search/saved` |
| DELETE | `/api/search/saved/{id}` |
| GET | `/api/search/history` |

`analysis.py`:
| Method | Path |
|--------|------|
| POST | `/api/analysis/` |

`export.py`:
| Method | Path |
|--------|------|
| GET | `/api/export/consultation/{message_id}` |
| GET | `/api/export/conversation/{conv_id}` |
| GET | `/api/export/search` |

**Services consumed**: `rag.py`, `reranker.py`, `pdf_service.py`, `upload_service.py`

**Models / tables**: `documents`, `document_chunks`, `search_history`, `saved_searches`,
`uploaded_documents`

**Upstream deps**: pgvector (semantic search), tiktoken (embedding), LLM (analysis)

**Current tests**:
- `tests/test_documents.py` — 15 tests (list, search, stats, chunks — validation
  focused, no auth-guard since documents are public-ish)
- Search: 8 scattered test references (not a dedicated `test_search.py`)
- Analysis: **0 tests**
- Export: 6 tests (basic PDF generation, probably shape only)
- Upload: 5 tests (basic)

**Obvious gaps**:
- `GET /api/search/` advanced search with filters — no test for each filter combination
- `POST /api/search/saved` — create saved search = untested
- `GET /api/search/history` — pagination, auth guard = untested
- `POST /api/analysis/` — no mock LLM test for full analysis lifecycle
- `GET /api/export/consultation/{message_id}` — 403 when message_id belongs to other user
- `GET /api/export/conversation/{conv_id}` — PDF bytes response shape = untested
- `_validate_filters` unit tests for edge cases (date range, area codes)
- Search `_log_search_history` DB write failure = untested (fail-safe?)

**Interactions**: RAG retrieval feeds `chat.py` and `stream.py`; analysis uses same
LLM adapter as chat; export depends on conversations + messages + documents.

---

### 1.8 `notifications`

**Purpose**: In-app notification center (legal alerts, billing events, system messages)
and transactional email (password reset, onboarding, billing receipts).

**Routers + key routes**:

`notifications.py`:
| Method | Path |
|--------|------|
| GET | `/api/notifications/` |
| GET | `/api/notifications/unread-count` |
| PATCH | `/api/notifications/read-all` |
| PATCH | `/api/notifications/{id}/read` |
| DELETE | `/api/notifications/{id}` |

`emails.py`:
| Method | Path |
|--------|------|
| POST | `/api/auth/password-reset/request` |
| POST | `/api/auth/password-reset/confirm` |
| POST | `/api/auth/verify-email` (presumed) |

**Services consumed**: `notification_service.py`, `email_service.py`

**Models / tables**: `notifications`

**Upstream deps**: SMTP / email provider (email_service)

**Current tests**:
- Notifications: **0 tests**
- Emails: **0 tests**

**Obvious gaps**:
- Entire notifications domain is dark — list, unread count, mark-read, delete all untested
- 401 guard on all notifications endpoints = untested
- Ownership isolation (user A cannot mark user B's notification read) = untested
- `email_service.py` — password reset token generation/validation = untested
- Email template rendering = untested

**Interactions**: `notification_service.py` is called by billing (invoice events),
trials (state machine transitions), and auth (onboarding).

---

### 1.9 `observability`

**Purpose**: System health probes (liveness, readiness, DB/Redis/pgvector), operational
metrics (memory, CPU, document stats), and org-scoped analytics (query trends, area
breakdowns, model costs, top queries, CSV export).

**Routers + key routes**:

`health.py`:
| Method | Path |
|--------|------|
| GET | `/api/health` |
| GET | `/api/health/db` |
| GET | `/api/health/ready` |
| GET | `/api/health/metrics` |
| GET | `/api/health/knowledge` |
| GET | `/api/health/cache` |

`analytics.py` (848 lines):
| Method | Path |
|--------|------|
| GET | `/api/analytics/{org_id}/overview` |
| GET | `/api/analytics/{org_id}/queries` |
| GET | `/api/analytics/{org_id}/areas` |
| GET | `/api/analytics/{org_id}/models` |
| GET | `/api/analytics/{org_id}/costs` |
| GET | `/api/analytics/{org_id}/top-queries` |
| GET | `/api/analytics/{org_id}/export` |

**Services consumed**: `admin_metrics_service.py` (indirectly via inline DB queries)

**Models / tables**: `conversations`, `messages`, `usage_records`, `documents`

**Upstream deps**: None (DB queries only)

**Current tests**:
- `tests/test_health.py` — 8 tests (basic, db, ready, knowledge). Good.
- Analytics: **0 tests**

**Obvious gaps**:
- Analytics: entire 848-line route file is dark — all 7 endpoints untested
- `_assert_org_access` guard (requires org admin role) = untested
- `GET /api/analytics/{org_id}/export` CSV generation = untested
- `_estimate_cost` model cost calculation = untested unit function
- `GET /api/health/cache` — Redis cache stats = untested
- `GET /api/health/metrics` — system metrics (psutil?) = untested
- Analytics date range calculations — off-by-one in `_date_range` = untested

**Interactions**: analytics feeds admin dashboard; health is called by load balancer
(exempt from rate limiting); analytics queries same `usage_records` table as billing.

---

### 1.10 `public-api-v1`

**Purpose**: Versioned external API for third-party integrations (SDK consumers).
Accepts JWT or API key. Exposes query, search, analyze, areas, documents, usage.

**Routers + key routes**:
| Method | Path |
|--------|------|
| POST | `/api/v1/query` |
| GET | `/api/v1/search` |
| POST | `/api/v1/analyze` |
| GET | `/api/v1/areas` |
| GET | `/api/v1/documents` |
| GET | `/api/v1/usage` |

**Services consumed**: `llm_adapter.py`, `rag.py`, `usage.py`, `entitlement_service.py`

**Models / tables**: `usage_records`, `documents`, `api_keys`

**Upstream deps**: LLM (query/analyze), pgvector (search), Redis (rate-limit)

**Current tests**:
- 6 test references across the codebase (no dedicated `test_v1.py` found)

**Obvious gaps**:
- `_check_scope` — API key scope validation per-endpoint = untested
- `_rate_limit_headers` — custom rate-limit header injection = untested
- Dual-auth (JWT + API key) at v1 layer = untested
- `POST /api/v1/query` happy-path with mocked LLM = untested
- `GET /api/v1/usage` quota calculation = untested
- 403 when API key lacks required scope = untested
- This is the SDK surface — any regression here breaks external integrations silently

**Interactions**: mirrors chat/search/analysis internally; metering goes to same
`usage_records` table as billing quota checks.

---

## 2. Cross-Cutting Concerns

### 2.1 Auth/RBAC Middleware Chain

**Execution order** (last registered = outermost):
```
Request → GZipMiddleware → RateLimitMiddleware → SecurityHeadersMiddleware → CORSMiddleware → Route
```

`RateLimitMiddleware` (`middleware.py`) handles IP-level abuse prevention globally.
Per-route rate limiting is handled by `RateLimitGuard(bucket)` dependency.

**Auth dependency tree**:
```
get_current_user          → JWT only (Bearer, type=access enforced)
get_optional_user         → JWT or None (used by RateLimitGuard)
get_api_key_user          → X-API-Key or Bearer ak_... → owner User
get_authenticated_user    → JWT first, then API key (dual-auth for v1 + api_keys)
require_org_role(role)    → org membership + role hierarchy (member < admin < owner)
RateLimitGuard(bucket)    → plan-aware per-route, admin bypass, fail-open
```

**Token type enforcement**: `deps.py` line 65 — `payload.get("type") != "access"` →
401. Prevents refresh tokens from being used as access tokens.

**Admin check**: `is_admin` field on `User` model; admin routes use local `_ensure_admin`
helper (admin_saas, admin_invoices, admin_trials) — NOT the RBAC dependency. This
divergence means RBAC roles and `is_admin` are separate trust surfaces.

### 2.2 Rate Limit Buckets

Two buckets, applied by `RateLimitGuard`:

| Bucket | Limit | Key pattern | Notes |
|--------|-------|-------------|-------|
| `READ` | 600 req/min (flat) | `rl:read:user:<uuid>` or `rl:read:ip:<ip>` | Same for all plans |
| `WRITE` | plan-based | `rl:write:user:<uuid>` or `rl:write:ip:<ip>` | free=30, pro=120, studio=600 |

Global middleware also runs a separate IP-level abuse bucket (see `middleware.py`).
Admin users (`is_admin=True`) bypass all limits unconditionally.

Redis implementation: sliding window via sorted set (`ZADD` / `ZCARD` / `ZREMRANGEBYSCORE`).
Key: `ratelimit:<bucket_key>` (not prefixed with `tukijuris:`).

### 2.3 Redis Key Patterns (Complete Inventory)

| Key pattern | Owner | TTL |
|------------|-------|-----|
| `tukijuris:denylist:<jti>` | `token_denylist.py` | token remaining lifetime |
| `ratelimit:rl:read:user:<uuid>` | `rate_limiter.py` | sliding 60s window |
| `ratelimit:rl:write:user:<uuid>` | `rate_limiter.py` | sliding 60s window |
| `ratelimit:rl:read:ip:<ip>` | `rate_limiter.py` | sliding 60s window |
| `ratelimit:rl:write:ip:<ip>` | `rate_limiter.py` | sliding 60s window |
| `ratelimit:<middleware-bucket>` | `middleware.py` | sliding 60s window |
| `cache:<md5(prefix:args)[:16]>` | `cache.py` | configurable (default 300s) |

**Note**: The global middleware rate-limit key pattern may differ from the RateLimitGuard
pattern — verify `middleware.py` for the exact key format.
**Note**: Webhook idempotency uses DB table (`webhook_events`), NOT Redis.

### 2.4 Plan Gates

`EntitlementService.has_feature(user, feature_key, db)` is the primary gate.
It honours `BETA_MODE=True` for most features EXCEPT:
- `free` plan stays capped at 10 queries/day regardless of BETA_MODE
- `byok` feature is HARD-EXCLUDED for free plan (no BETA_MODE bypass)

**Where plan gates are enforced**:
| Feature | Enforcer | File |
|---------|----------|------|
| BYOK access | `_byok_allowed()` → `EntitlementService.has_feature` | `api_keys.py:40` |
| Entitlements list (JWT claim) | `EntitlementService.list_user_features` | `auth.py:613` |
| Daily quota | `usage.py` via `check_daily_limit` | `chat.py` + `stream.py` |
| Model fallback (BYOK gate) | inline in `chat.py:134` | `chat.py` |

**Gap**: No plan gate test at the `stream.py` level — quota check is tested for `chat.py`
but SSE stream goes through a separate handler.

### 2.5 Multi-Tenancy

**Approach**: Manual per-route `org_id` scoping — NO global Row Level Security (RLS)
in PostgreSQL. Each route individually checks membership via `require_org_role` or
`_require_org_member`.

**Risk**: Any new route that forgets to call `require_org_role` leaks cross-tenant data.
There is no middleware-level enforcement. This is the highest-impact structural gap for
a test strategy — every org-scoped endpoint needs an explicit cross-tenant isolation test.

**Affected domains**: billing (org subscription/usage), analytics (org overview), me_invoices,
organizations (members).

---

## 3. Test Strategy Gap Matrix

| Domain | Unit | Integration | E2E-critical | Observed gap |
|--------|------|-------------|-------------|--------------|
| auth | ✅ Excellent (7 unit files) | ✅ Good (logout, me, onboarding) | ✅ Covered | Sessions list, profile update, OAuth MS errors |
| oauth | ✅ Good (4 unit files) | ✅ Good | 🟡 Partial | MS callback error path |
| conversations | ❌ None | 🟡 Minimal (6 tests) | ❌ Missing | All write paths, ownership isolation |
| chat | 🟡 Partial (BYOK unit) | 🟡 Partial (quota) | ❌ Missing | Happy-path LLM mock, BYOK fallback |
| stream | ❌ None | ❌ None (1 test) | ❌ Missing | SSE frames, quota gate, mid-stream error |
| feedback | ❌ None | ✅ Good (11 tests) | ✅ Covered | — |
| bookmarks | ❌ None | ❌ None | ❌ Missing | Entire domain dark |
| memory | ❌ None | ❌ None | ❌ Missing | Entire domain dark |
| tags | ❌ None | ❌ None | ❌ Missing | Entire domain dark |
| folders | ❌ None | ❌ None | ❌ Missing | Entire domain dark |
| shared | ❌ None | ❌ None | ❌ Missing | Public endpoint, no rate-limit test |
| billing | ✅ Excellent | ✅ Excellent | ✅ Covered | HMAC tamper test, downgrade handler |
| plans | ✅ Excellent | ✅ Excellent | ✅ Covered | — |
| trials | ✅ Excellent | ✅ Good | ✅ Covered | retry_charge w/ TRIALS_ENABLED=False |
| invoices | ✅ Excellent | ✅ Good | ✅ Covered | 409 vs 422 PATCH reconcile |
| admin | 🟡 Partial (metrics, audit) | 🟡 Partial (saas panel) | ❌ Missing | Activity, knowledge, audit route 403 |
| rbac | ✅ Excellent (9 unit files) | 🟡 Partial | 🟡 Partial | Assign/revoke integration test |
| byok/api_keys | 🟡 Partial (encryption) | 🟡 Partial (plan gate) | ❌ Missing | API key CRUD route-level tests |
| upload | ❌ None | 🟡 Minimal (5 tests) | ❌ Missing | Type rejection, ownership |
| organizations | ❌ None | ✅ Good (13 tests) | 🟡 Partial | Remove member, role enforcement, seat sync |
| documents | ❌ None | ✅ Good (15 tests) | 🟡 Partial | Auth gates (public endpoints OK) |
| search | ❌ None | 🟡 Minimal (8 refs) | ❌ Missing | Saved searches, history, filter combos |
| analysis | ❌ None | ❌ None | ❌ Missing | Entire domain dark |
| export | ❌ None | 🟡 Minimal (6 tests) | ❌ Missing | Ownership 403, PDF bytes shape |
| notifications | ❌ None | ❌ None | ❌ Missing | Entire domain dark |
| emails | ❌ None | ❌ None | ❌ Missing | Entire domain dark |
| analytics | ❌ None | ❌ None | ❌ Missing | Entire 848-line file dark |
| health | ❌ None | ✅ Good (8 tests) | ✅ Covered | Cache stats, metrics |
| public-api-v1 | ❌ None | 🟡 Minimal (6 refs) | ❌ Missing | Scope check, dual-auth, all endpoints |

**Legend**: ✅ Good coverage | 🟡 Partial/minimal | ❌ Dark

---

## 4. Risk Ranking

Domains ordered by combined risk score (criticality × coverage gap × bugfix history):

### Priority 1 — `auth` + `oauth` (maintain + fill gaps)
- **Rationale**: Highest business criticality. Already well-covered but 3 deferred
  SDD warnings (obs #30 fix-auth-tokens verify) plus sessions list + profile update
  are completely untested. Auth bugs = total platform outage.
- **Engram refs**: obs #30 (fix-auth-tokens verify report), obs #32 (session summary)
- **Gap score**: LOW coverage gap, CRITICAL impact → maintain + targeted additions

### Priority 2 — `billing` + `trials` (fill deferred warnings)
- **Rationale**: Money domain. Already heavily tested but 7+5+7 deferred warnings across
  3 archived changes. HMAC tamper detection and downgrade handler are untested.
  Any regression = silent revenue loss or ghost subscriptions.
- **Engram refs**: obs #143 (payment-webhook-idempotency archive), obs #166 (invoices-model),
  obs #261 (trials-lifecycle)
- **Gap score**: LOW-MEDIUM coverage gap, CRITICAL impact

### Priority 3 — `chat` + `stream` (core product, nearly dark for SSE)
- **Rationale**: The primary revenue-generating surface. `stream.py` is 640 lines with
  1 test. LLM quota gate is tested for `chat.py` but NOT for `stream.py`. SSE frame
  structure, mid-stream error propagation, BYOK fallback at stream level = all dark.
- **Engram refs**: Sprint 2 byok-plan-gate (chat.py BYOK denial)
- **Gap score**: HIGH coverage gap, HIGH impact

### Priority 4 — `public-api-v1` (SDK surface, silent regressions)
- **Rationale**: External SDK consumers have no fallback. A scope-check regression or
  quota calculation error breaks paying API customers silently. 671 lines, 6 tests.
- **Gap score**: HIGH coverage gap, HIGH impact (external API contract)

### Priority 5 — `byok` / `api_keys` CRUD (plan-gated feature, untested routes)
- **Rationale**: Developer API key creation/revocation routes have zero test coverage.
  LLM key test endpoint could expose provider credentials if error handling fails.
- **Engram refs**: obs #70 (byok-plan-gate verify — PASS WITH WARNINGS)
- **Gap score**: HIGH coverage gap, MEDIUM-HIGH impact

### Priority 6 — `admin` fill (ops surface, 403 enforcement)
- **Rationale**: `admin.py` has no route-level tests for 403 rejection on non-admin
  users. Admin access to user data with wrong auth = data breach.
- **Gap score**: MEDIUM coverage gap, HIGH impact (privilege escalation risk)

### Priority 7 — `conversations` write paths + isolation
- **Rationale**: rename/pin/archive/delete/share have zero tests. Cross-user ownership
  isolation = untested. These are the most commonly used UI operations.
- **Gap score**: HIGH coverage gap, MEDIUM impact

### Priority 8 — `organizations` (seat sync, remove member)
- **Rationale**: Studio plan seat billing depends on member count sync. Seat sync bug =
  revenue leak. `_sync_member_plans` in billing.py has no test.
- **Gap score**: MEDIUM coverage gap, HIGH impact for Studio customers

### Priority 9 — `analytics` (entire 848-line file dark)
- **Rationale**: Org admin–only. Not user-facing revenue path but `_assert_org_access`
  is the only gate — untested privilege check.
- **Gap score**: HIGH coverage gap, MEDIUM impact

### Priority 10 — `notifications` + `emails`
- **Rationale**: Notification delivery is side-effect-only for now (no webhooks to
  external systems). Email password-reset is a security-sensitive flow.
- **Gap score**: HIGH coverage gap, LOW-MEDIUM impact

### Priority 11 — `documents` / `search` / `analysis` / `export`
- **Rationale**: Read-mostly, mostly public. Low risk of data leak. Filter validation
  and ownership checks are the main concerns.
- **Gap score**: MEDIUM coverage gap, LOW-MEDIUM impact

### Priority 12 — `bookmarks` / `tags` / `folders` / `memory` / `shared`
- **Rationale**: Convenience features. Zero tests. Low revenue impact but high UX
  regression risk if queries silently break.
- **Gap score**: HIGH coverage gap, LOW impact

---

## 5. Proposal Seeds

### 5.1 `auth` — seed for proposal

- **Unit tests to add**:
  - `test_auth_sessions_list` — GET `/api/auth/sessions` returns list of active sessions with correct shape
  - `test_profile_update_validation` — PUT `/api/auth/me` with missing/invalid fields → 422
  - `test_has_privileged_role_helper` — unit test internal helper with mock DB
  - `test_oauth_microsoft_code_exchange_failure` — httpx mock returns 400 from MS
- **Integration tests**:
  - `test_onboarding_complete_invalid_body` — POST `/api/auth/me/onboarding` bad payload → 422
  - `test_refresh_token_wrong_type_rejected` — presenting access token to /refresh → 401
- **Code fixes likely needed**: none (auth is solid — tests will likely pass)
- **Acceptance criteria**:
  - All auth endpoints have at least one 401/403 rejection test
  - Sessions list tested with known fixture
  - OAuth error paths tested with mocked httpx

### 5.2 `billing` — seed for proposal

- **Unit tests to add**:
  - `test_verify_culqi_hmac_tampered` — wrong signature returns False
  - `test_verify_mp_hmac_tampered` — idem
  - `test_handle_subscription_deleted_downgrade` — service call with mock DB
  - `test_handle_payment_failed_notification_triggered` — notification_service called
- **Integration tests**:
  - `test_me_invoices_non_member_403` — user not in org gets 403
  - `test_retry_charge_trials_disabled` — 503/404 when TRIALS_ENABLED=False
- **Code fixes likely needed**: None anticipated — these are additive tests for deferred warnings
- **Acceptance criteria**:
  - HMAC verification has dedicated tamper-detection unit test
  - All 7 deferred payment-webhook-idempotency warnings addressed
  - me_invoices org membership gate explicitly tested

### 5.3 `conversations` + `chat` + `stream` — seed for proposal

- **Unit tests to add**:
  - `test_chat_byok_fallback_uses_platform_key` — mock EntitlementService returns False → platform key used
  - `test_stream_quota_gate_free_user_exhausted` — mock usage at limit → SSE error frame
  - `test_stream_sse_frame_format` — single SSE frame has correct `data:` prefix
- **Integration tests**:
  - `test_conversation_rename_owner_only` — user A cannot rename user B's conversation → 403/404
  - `test_conversation_delete_cascades_messages` — deletion returns 204, GET 404
  - `test_conversation_pin_toggle` — pin → unpin → check state
  - `test_conversation_share_creates_public_link` — share → GET shared (no auth) returns 200
  - `test_bookmarks_crud` — create/list/delete bookmark
  - `test_tags_crud` — create/list/delete tag, assign to conversation
  - `test_folders_crud` — create/list/delete folder
  - `test_memory_crud` — create/list/delete memory item
  - `test_chat_quota_stream_path` — quota check fires on stream endpoint (not just chat)
- **Code fixes likely needed**:
  - `stream.py` may not have usage check wired identically to `chat.py` — verify and align
  - Confirm ownership isolation in `conversations.py` GET uses `user_id` filter
- **Acceptance criteria**:
  - All conversation write paths have owner-only test
  - Stream has SSE quota gate test
  - All content-org sub-resources (bookmarks/tags/folders/memory) have CRUD smoke tests

### 5.4 `byok` + `admin` — seed for proposal

- **Unit tests to add**:
  - `test_validate_scopes_unknown_scope_rejected` — `_validate_scopes(["unknown"]) → HTTPException`
  - `test_api_key_generate_unique` — two calls produce different keys
  - `test_admin_ensure_admin_non_admin_raises` — `_ensure_admin` with `is_admin=False`
- **Integration tests**:
  - `test_api_key_crud` — create → list → patch → revoke lifecycle
  - `test_llm_key_test_provider_error_propagated` — provider returns 401 → 400 to user
  - `test_admin_users_non_admin_403` — GET /api/admin/users without is_admin → 403
  - `test_admin_activity_non_admin_403` — GET /api/admin/activity → 403
  - `test_rbac_assign_role_integration` — assign role → GET permissions → confirm
  - `test_upload_wrong_type_rejected` — upload .exe → 422
  - `test_upload_ownership_isolation` — GET /api/upload/{doc_id} belonging to other user → 404
- **Code fixes likely needed**:
  - `admin_saas.py`, `admin_invoices.py`, `admin_trials.py` all have local `_ensure_admin`
    instead of RBAC dependency — consider unifying. May surface bugs in inconsistent checks.
- **Acceptance criteria**:
  - All admin routes have non-admin 403 test
  - API key CRUD lifecycle has one integration test
  - Upload ownership isolation is explicitly tested

### 5.5 `documents` + `search` — seed for proposal

- **Unit tests to add**:
  - `test_validate_filters_invalid_date_range` — end before start → HTTPException
  - `test_validate_filters_unknown_area` — unknown legal area → reject
  - `test_build_search_query_pagination` — offset/limit parameter mapping
- **Integration tests**:
  - `test_advanced_search_with_area_filter` — search with area=laboral returns relevant results
  - `test_save_search_requires_auth` — POST /api/search/saved → 401 without token
  - `test_search_history_requires_auth` — GET /api/search/history → 401
  - `test_export_conversation_ownership` — GET /api/export/conversation/{id} for other user → 403/404
  - `test_analysis_mocked_llm` — POST /api/analysis/ with mock LLM → 200 with result shape
- **Code fixes likely needed**: Verify `search.py` `_log_search_history` failure is truly silenced
- **Acceptance criteria**:
  - Filter validation has exhaustive unit tests
  - Saved search + history auth gates tested
  - Analysis has at least one mocked-LLM happy-path test

### 5.6 `notifications` + `analytics` + `public-api-v1` — seed for proposal

- **Unit tests to add**:
  - `test_estimate_cost_known_model` — `_estimate_cost("gpt-4o", 1000)` returns expected value
  - `test_date_range_30_days` — `_date_range(30)` returns correct range
  - `test_v1_check_scope_missing_scope_raises` — `_check_scope(...)` with wrong scope → 403
- **Integration tests**:
  - `test_notifications_list_requires_auth` — GET /api/notifications/ → 401
  - `test_notifications_mark_read_ownership` — PATCH /api/notifications/{id}/read for other user → 404
  - `test_analytics_overview_requires_org_admin` — member role → 403
  - `test_analytics_export_returns_csv` — GET /api/analytics/{org_id}/export content-type
  - `test_v1_query_api_key_wrong_scope_403` — API key without query scope → 403
  - `test_v1_query_jwt_happy_path` — JWT auth → 200 with mock LLM
  - `test_v1_usage_returns_quota_info` — GET /api/v1/usage returns correct shape
- **Code fixes likely needed**:
  - Emails: verify password-reset token flow is consistent (may have been partially done in fix-auth-session-flow SDD — check engram)
- **Acceptance criteria**:
  - Every analytics endpoint has org-admin gate test
  - v1 has scope-check test for each restricted endpoint
  - Notifications CRUD has auth + ownership isolation tests

---

## Appendix: File Index

### Route files
| File | Lines | Domain |
|------|-------|--------|
| `billing.py` | 1,149 | billing |
| `analytics.py` | 848 | observability |
| `auth.py` | 704 | auth |
| `v1.py` | 671 | public-api-v1 |
| `stream.py` | 640 | conversations |
| `search.py` | 616 | documents |
| `api_keys.py` | 454 | byok |
| `oauth.py` | 434 | auth |
| `chat.py` | 374 | conversations |
| `admin.py` | 365 | admin |
| `organizations.py` | 360 | organizations |
| `conversations.py` | 325 | conversations |
| `tags.py` | 304 | conversations |
| `folders.py` | 278 | conversations |
| `export.py` | 261 | documents |
| `notifications.py` | 221 | notifications |
| `memory.py` | 219 | conversations |
| `documents.py` | 158 | documents |
| `emails.py` | 156 | notifications |
| `health.py` | 151 | observability |
| `admin_saas.py` | 148 | admin |
| `admin_invoices.py` | 145 | billing |
| `bookmarks.py` | 135 | conversations |
| `upload.py` | 129 | byok |
| `rbac_admin.py` | 126 | admin |
| `trials.py` | 122 | billing |
| `plans.py` | 110 | billing |
| `me_invoices.py` | 104 | billing |
| `analysis.py` | 101 | documents |
| `admin_trials.py` | 84 | billing |
| `feedback.py` | 82 | conversations |
| `internal_trials.py` | 63 | billing |
| `shared.py` | 56 | conversations |

### Test files (by coverage quality)
| File | Lines | Domain | Quality |
|------|-------|--------|---------|
| `test_trial_service.py` | 857 | billing | ✅ |
| `test_invoice_service.py` | 534 | billing | ✅ |
| `unit/test_oauth_refresh.py` | 521 | auth | ✅ |
| `unit/test_rbac_service.py` | 505 | admin | ✅ |
| `unit/test_refresh_service.py` | 500 | auth | ✅ |
| `integration/test_webhook_idempotency.py` | 454 | billing | ✅ |
| `test_payment_providers.py` | 402 | billing | ✅ |
| `unit/test_rbac_routes.py` | 385 | admin | ✅ |
| `test_billing_trial_integration.py` | 382 | billing | ✅ |
| `test_plans_route.py` | 315 | billing | ✅ |
| `unit/test_usage_limits.py` | 314 | billing | ✅ |
| `test_conversations.py` | ~80 est | conversations | ❌ |
| `test_notifications` | — | notifications | ❌ MISSING |
| `test_analytics` | — | observability | ❌ MISSING |
| `test_api_keys` | — | byok | ❌ MISSING |
