---
change: backend-saas-test-coverage
status: proposed
created: 2026-04-19
depends_on:
  - sdd/backend-saas-test-coverage/proposal
  - sdd/backend-saas-test-coverage/spec/auth
  - sdd/backend-saas-test-coverage/spec/billing
  - sdd/backend-saas-test-coverage/spec/admin-rbac
  - sdd/backend-saas-test-coverage/spec/byok
  - sdd/backend-saas-test-coverage/spec/organizations
  - sdd/backend-saas-test-coverage/spec/conversations
  - sdd/backend-saas-test-coverage/spec/chat-stream
  - sdd/backend-saas-test-coverage/spec/documents-search
  - sdd/backend-saas-test-coverage/spec/notifications
  - sdd/backend-saas-test-coverage/spec/observability
---

# Design — Backend SaaS Test Coverage

## 1. Executive summary

This is the single, cross-cutting technical design that bridges the 10 per-domain
specs (~130 new tests) into one coherent implementation plan. We write ONE document
instead of ten because 80% of the work is shared infrastructure — a cross-tenant
isolation harness, fixture factories, mock providers, an SSE assertion helper,
and a coverage-enforcement strategy — that every spec reuses verbatim. The design
also pins down six code fixes (`FIX-01` … `FIX-06`) that testing will necessarily
expose (divergent quota gate in `stream.py`, triplicated `_ensure_admin`, missing
`user_id`/`org_id` filters, fail-unsafe search logging, off-by-one in analytics
date math, missing rate-limit headers in v1). Every decision prefers the minimum
delta over the existing conftest and the current Python-3.12 async/httpx stack.
No new production dependencies are introduced; `factory-boy` and `pytest-xdist`
are explicitly rejected below with tradeoffs. All execution runs inside the
`tukijuris-api-1` Docker container — the host Python 3.9 is incompatible with
the app runtime (per engram obs #280).

## 2. Test infrastructure patterns (canonical, reused across specs)

These patterns are authored ONCE in this change and every spec's test catalog
consumes them by name. No spec duplicates fixture code inline.

### 2.1 Cross-tenant isolation harness

#### 2.1.1 Motivation

The app has **no global Row-Level Security**. Tenant scoping is manual per-route
via `.where(Model.user_id == current_user.id)` or `.where(Model.org_id == …)`.
Every org- or user-scoped route is therefore a single typo away from a data-leak
bug. The specs list 25+ places where this must be covered; writing it ad-hoc 25
times would drift. We centralize.

#### 2.1.2 `two_orgs_two_users` fixture

Location: `apps/api/tests/fixtures/tenants.py` (new module; imported by conftest).

Contract (plain async factory — no factory-boy — matching the existing
`auth_client` pattern in `conftest.py`):

```
async def two_orgs_two_users(
    client: AsyncClient,
    *,
    plan_a: str = "pro",
    plan_b: str = "pro",
    seed_a: Callable | None = None,
    seed_b: Callable | None = None,
) -> TenantPair
```

Returns a dataclass:

```
@dataclass
class TenantPair:
    org_a: Organization
    owner_a: User
    token_a: str        # access token, Bearer-ready
    org_b: Organization
    owner_b: User
    token_b: str
    client_a: AsyncClient   # already has Authorization header for token_a
    client_b: AsyncClient   # already has Authorization header for token_b
```

Implementation notes:

- Registers two distinct users with unique `uuid4()` emails, mirroring the
  existing `auth_client` fixture style (lines 81–106 of current `conftest.py`).
- Creates one org per user via `POST /api/organizations/`, making each user the
  sole owner.
- Optional `seed_a`/`seed_b` callbacks receive `(client, user, org)` and let
  callers preload conversations, bookmarks, etc. before assertions start.
- DOES NOT wrap `auth_client` — it builds its own clients from two fresh
  `AsyncClient` instances so header cross-pollution is impossible.
- Exposes raw tokens so tests can issue unauthenticated cross-tenant probes
  (e.g. passing `token_b` via an explicit header against a route owned by A).

#### 2.1.3 `assert_isolated` helper

Location: `apps/api/tests/helpers/isolation.py` (new module).

Contract:

```
async def assert_isolated(
    *,
    victim_client: AsyncClient,     # user A — the OWNER
    attacker_client: AsyncClient,   # user B — attempts access
    method: str,                    # "GET" | "PATCH" | "DELETE" | "POST"
    path: str,                      # full path, e.g. /api/bookmarks/{id}
    attacker_status: int,           # 403 OR 404 depending on convention (§2.1.4)
    json: dict | None = None,       # optional body for write methods
    owner_status: int = 200,        # sanity check: A really does have access
) -> None
```

Behaviour:

1. Issues the same request first as the owner — asserts `owner_status` (defaults
   to 200). This guards against false-green isolation tests where the route is
   simply broken for everyone.
2. Issues the request as the attacker — asserts `attacker_status`.
3. For write methods, also asserts the owner's resource is UNMODIFIED afterwards
   via a follow-up `GET` (when a stable GET path is derivable). This catches the
   nasty class of bug where 403 is returned BUT the write already happened.

#### 2.1.4 403 vs 404 — project-wide convention (RESOLVED)

The specs are mixed. We pin this down now to avoid drift:

| Scenario                                                         | Status | Rationale                                                                 |
|------------------------------------------------------------------|--------|---------------------------------------------------------------------------|
| Authenticated user accesses a user-owned resource (not their own)| `404`  | Do NOT leak existence. Matches `bookmark.009`, `upload_ownership`, `shared.007`. |
| Authenticated user accesses an org they are NOT a member of      | `403`  | Org membership is a first-class concept users reason about. Matches `orgs.int.004`, `billing.int.001`. |
| Non-admin hits `/api/admin/*`                                    | `403`  | Admin is a role, not a hidden resource. Matches `admin-rbac.int.001..003`. |
| Org member (not admin) mutates org-level settings                | `403`  | Role gate inside a known resource. Matches `orgs.int.002`.                |
| Unauthenticated access to protected route                        | `401`  | Standard.                                                                 |
| Scope-restricted API key hits an out-of-scope endpoint           | `403`  | Matches `chat-stream.unit.012`.                                           |

Specs that wrote `403 OR 404` (e.g. `notifications.unit.006`, `feedback.015`,
`export.012/013`) are adjudicated here: **404 for user-owned resources, 403 for
org/role gates**. Tests land with `attacker_status=404` for those cases. If a
route currently returns 403 for user-owned, that is a **testing-surfaced fix**
(tracked as `FIX-03`) — align it to 404 silently.

Exception: `analysis.010` (cross-tenant document reference inside an analysis
body) is allowed to return `403` OR `404`; we pick `404` consistent with
"document not visible to you" semantics.

#### 2.1.5 Catalog of routes that MUST consume the harness

Every entry in Appendix B §B.1 consumes `assert_isolated` with no exception.
The harness is the single enforcement point — if the catalog changes, the
harness is the only file that needs to update shared setup code.

### 2.2 Fixture factories

We explicitly **reject `factory-boy`**: it is not in `apps/api/pyproject.toml`
and adding it buys little over plain async functions while costing one more dep
to pin. Every factory is a plain `async def` that takes an `AsyncSession` (or
`AsyncClient` for endpoint-driven creation) and returns the persisted model.

All factories live under `apps/api/tests/factories/` (new package with
`__init__.py`). Each module is ≤ 50 LOC (hard budget — see §8).

| File                                | Builds                                                         | Used by specs                          |
|-------------------------------------|----------------------------------------------------------------|----------------------------------------|
| `factories/user.py`                 | User via `POST /api/auth/register`; optional plan, is_admin    | auth, admin-rbac, chat-stream, all     |
| `factories/org.py`                  | Organization with owner via `POST /api/organizations/`; optional members with roles | organizations, billing, admin-rbac, observability |
| `factories/conversation.py`         | Conversation + N messages via auth_client; returns (conv_id, message_ids[]) | conversations, chat-stream, documents-search |
| `factories/invoice.py`              | Invoice row in state={paid,pending,refunded} via `invoice_service` (NOT HTTP — state manipulation only) | billing |
| `factories/llm_key.py`              | Encrypted BYOK LLM key via `llm_key_service`                   | byok, chat-stream                      |
| `factories/notification.py`         | Notification in read/unread state via `notification_service`   | notifications, billing (downgrade hook)|
| `factories/api_key.py`              | Developer API key via `POST /api/keys/`; returns (key_id, raw_token, scopes) | byok, chat-stream (v1 dual-auth)  |
| `factories/saved_search.py`         | Saved search row for documents-search spec                     | documents-search                       |

Factory style (canonical example, `factories/conversation.py`):

```
async def make_conversation(
    auth_client: AsyncClient,
    *,
    title: str = "Test conv",
    messages: Sequence[str] = ("Hola",),
) -> tuple[str, list[str]]:
    res = await auth_client.post("/api/conversations/", json={"title": title})
    conv_id = res.json()["id"]
    message_ids: list[str] = []
    for m in messages:
        mres = await auth_client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": m},
        )
        message_ids.append(mres.json()["id"])
    return conv_id, message_ids
```

Rule: factories call the **HTTP surface** whenever possible, not raw SA models.
Rationale: (a) they exercise the real pipeline the test is supposed to validate,
(b) they sidestep the SA 2.0 `mapped_column(default=…)` gotcha (engram obs #156
gotcha #1), (c) they eliminate the same-session duplicate-path gotcha (obs #156
gotcha #3). Only `invoice.py`, `llm_key.py`, `notification.py` and
`saved_search.py` go through services directly because they need specific DB
states (e.g. `paid` invoice) that cannot be reached via HTTP without touching
webhooks.

### 2.3 Mock providers

#### 2.3.1 Email — NEW

Location: `apps/api/tests/mocks/email.py` (new module; `mocks/` package created).

Interface parity with whatever `email_service.py` currently uses. The real
service accepts a `send_email(to, subject, html, text)` contract — we mirror it:

```
class MockEmailProvider:
    def __init__(self) -> None:
        self.sent: list[SentEmail] = []

    async def send_email(
        self, *, to: str, subject: str, html: str, text: str | None = None
    ) -> SentEmailResult:
        sent = SentEmail(to=to, subject=subject, html=html, text=text)
        self.sent.append(sent)
        return SentEmailResult(id=f"mock_{len(self.sent)}", ok=True)

    @property
    def last_sent(self) -> SentEmail | None:
        return self.sent[-1] if self.sent else None
```

Wiring: a `mock_email_provider` pytest fixture uses FastAPI dependency override
(`app.dependency_overrides`) to replace the real provider for the duration of
one test. Fixture yields the instance so tests can assert on `last_sent` and
`sent`. Revert is automatic via `dependency_overrides.clear()` on teardown.

Failure-path variant: `mock_email_provider_failing` that raises `HTTPException`
on every send (for `notifications.unit.012` bounce fallback test).

#### 2.3.2 LLM — EXTEND existing pattern

Audit first: the existing `apps/api/tests/unit/test_byok_plan_gate.py` and
`apps/api/tests/integration/test_chat_quota.py` already mock LLM calls via
`unittest.mock.AsyncMock` on the adapter factory. We **do not create a new
`tests/mocks/llm.py` module**; we factor the existing mock into a shared
helper only if two or more new tests would duplicate > 20 LOC.

Shared helper (added to `apps/api/tests/helpers/llm.py`):

```
def patch_llm_adapter(
    *,
    reply: str = "mocked reply",
    tokens_in: int = 10,
    tokens_out: int = 5,
    stream_chunks: Sequence[str] | None = None,
) -> AsyncMock
```

Returns an `AsyncMock` pre-wired to return the canned reply for non-streaming
calls, and an async generator over `stream_chunks` for streaming. Tests use it
via `monkeypatch.setattr("app.services.llm_adapter.get_adapter", lambda _: mock)`.

#### 2.3.3 Payments — REUSE

Culqi and MP adapters are already mock-able per engram obs #213 (Culqi stored
token API) and obs #223 (MP preapproval API). The existing
`tests/test_payment_providers.py` shows the pattern. Billing spec (§3 rows
`billing.unit.001/002/003/004`) consumes these unchanged. No design work needed
here — specs reference existing fixtures.

### 2.4 SSE (stream.py) test harness

#### 2.4.1 Why a dedicated helper

`httpx.AsyncClient.stream()` is the only correct way to test SSE with
`ASGITransport` — `post()` buffers the entire response and breaks streaming
contracts. Writing the iteration loop by hand in every stream test (specs list
5 such tests: `stream.004..009`) invites flaky timeouts and missed-disconnect
bugs. We centralize.

#### 2.4.2 `assert_sse_yields` helper

Location: `apps/api/tests/helpers/sse.py` (new module).

Contract:

```
async def assert_sse_yields(
    client: AsyncClient,
    *,
    method: str = "POST",
    path: str,
    json: dict | None = None,
    expected_events: Sequence[SSEEvent | Pattern[str]],
    timeout_s: float = 10.0,
    client_disconnect_after: int | None = None,
) -> list[SSEEvent]
```

Where `SSEEvent` is a small dataclass `{data: str, event: str | None, id: str | None}`.
`expected_events` supports literal dataclass equality OR regex patterns to
match the `data:` payload. Returns the full list of captured events for any
further bespoke assertions.

Behaviour:

1. Opens `client.stream(method, path, json=...)` inside `asyncio.wait_for` with
   `timeout_s`.
2. Parses frames line-by-line honouring the SSE spec: `data:` continuation,
   blank line = event boundary, optional `event:` and `id:` lines.
3. If `client_disconnect_after` is set, breaks the loop after capturing N events
   and verifies the server-side task is cancelled (no runaway charges — this
   covers `chat-stream.unit.009`).
4. Asserts the captured sequence matches `expected_events` one-to-one. Length
   mismatch is a hard fail with a diff-style message.

#### 2.4.3 SSE frame format convention

We ratify what `stream.py` currently emits (verified during FIX-01 below) and
bake it into the helper's default expectations:

- Token frames: `data: {"type":"token","content":"<chunk>"}\n\n`
- Error frames: `data: {"type":"error","code":<int>,"message":"<msg>"}\n\n`
- Terminator: `data: [DONE]\n\n`

Tests write `expected_events=[..., SSEEvent(data="[DONE]")]` and the helper
handles the rest.

### 2.5 Coverage strategy

#### 2.5.1 Command matrix

Authoritative command (inside the container):

```
docker exec tukijuris-api-1 \
  pytest tests \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=json:/tmp/coverage.json \
  --cov-report=xml:/tmp/coverage.xml
```

The XML report is for future GH Actions upload (codecov/artifact). The JSON is
for the per-module enforcement script below.

#### 2.5.2 Per-domain targets

We publish both a MUST (CI-blocking) and a STRETCH (warning-only) target per
module. Current numbers are estimates from the proposal/exploration notes —
actual measurements land in Batch A and anchor the thresholds in Batch B.

| Module                          | Current % (est) | MUST % | STRETCH % | Spec owning it              |
|---------------------------------|-----------------|--------|-----------|-----------------------------|
| `app/api/routes/auth.py`        | ~90%            | 95%    | 100%      | auth                        |
| `app/api/routes/oauth.py`       | ~75%            | 85%    | 95%       | auth                        |
| `app/api/routes/billing.py`     | ~80%            | 85%    | 95%       | billing                     |
| `app/services/webhook_idempotency_service.py` | ~90% | 95% | 100%      | billing                     |
| `app/api/routes/admin.py`       | ~60%            | 80%    | 90%       | admin-rbac                  |
| `app/api/routes/admin_saas.py`  | ~70%            | 85%    | 95%       | admin-rbac                  |
| `app/api/routes/rbac_admin.py`  | ~65%            | 80%    | 90%       | admin-rbac                  |
| `app/api/routes/api_keys.py`    | ~40%            | 80%    | 90%       | byok                        |
| `app/api/routes/upload.py`      | ~35%            | 75%    | 85%       | byok                        |
| `app/api/routes/organizations.py`| ~60%           | 85%    | 95%       | organizations               |
| `app/api/routes/conversations.py`| ~30%           | 80%    | 90%       | conversations               |
| `app/api/routes/bookmarks.py`   | ~0%             | 75%    | 85%       | conversations               |
| `app/api/routes/tags.py`        | ~0%             | 75%    | 85%       | conversations               |
| `app/api/routes/folders.py`     | ~0%             | 75%    | 85%       | conversations               |
| `app/api/routes/memory.py`      | ~0%             | 75%    | 85%       | conversations               |
| `app/api/routes/shared.py`      | ~0%             | 75%    | 85%       | conversations               |
| `app/api/routes/chat.py`        | ~30%            | 85%    | 95%       | chat-stream                 |
| `app/api/routes/stream.py`      | ~5%             | 75%    | 85%       | chat-stream                 |
| `app/api/routes/v1.py`          | ~25%            | 80%    | 90%       | chat-stream                 |
| `app/api/routes/documents.py`   | ~50%            | 80%    | 90%       | documents-search            |
| `app/api/routes/search.py`      | ~40%            | 85%    | 95%       | documents-search            |
| `app/api/routes/analysis.py`    | ~0%             | 75%    | 85%       | documents-search            |
| `app/api/routes/export.py`      | ~50%            | 80%    | 90%       | documents-search            |
| `app/api/routes/notifications.py`| ~0%            | 85%    | 95%       | notifications               |
| `app/api/routes/emails.py`      | ~0%             | 75%    | 85%       | notifications               |
| `app/api/routes/analytics.py`   | ~0%             | 75%    | 85%       | observability               |
| `app/api/routes/health.py`      | ~70%            | 85%    | 95%       | observability               |
| **Global (project-wide)**       | ~55%            | 75%    | 82%       | all                         |

#### 2.5.3 Enforcement mechanism

Option A (rejected) — `--cov-fail-under=N` global: too blunt, silences per-module regressions.

Option B (rejected) — `pytest-cov`'s `[coverage:report] fail_under` in `setup.cfg`: global
only, same problem.

Option C (**chosen**) — A 60-LOC script `apps/api/scripts/check_coverage.py`
that reads `/tmp/coverage.json`, loads the MUST thresholds from a YAML
companion `apps/api/coverage-targets.yaml` (the table above), and exits 1 on
any MUST violation. STRETCH misses print a warning but exit 0. Makefile target
`make test-cov` runs pytest then the script.

Rationale: simple, self-contained, zero new deps, and the thresholds live in
one file the sdd-tasks phase can codify line-by-line.

#### 2.5.4 No coverage regressions

Pragma policy:
- Existing `# pragma: no cover` markers stay untouched.
- No new `pragma: no cover` added in this change unless the line is genuinely
  unreachable (e.g. a `raise NotImplementedError` placeholder that must remain).
  Any new pragma requires a comment `# pragma: no cover — <reason>`.

## 3. Code fixes — design decisions

Each fix is surfaced by a spec test. Tests are written failing first, then the
fix lands in the SAME commit (TDD-lite — not strict TDD because the proposal
has `strict_tdd: false`, but discipline-wise we keep test + fix paired).

### 3.1 FIX-01 — `stream.py` quota gate alignment

- **Surface**: `chat-stream.unit.007` (`test_stream_quota_gate_free_user_exhausted`).
- **Current behaviour**: `stream.py` may dispatch to LLM without the same
  `usage.check_and_consume(user_id, plan)` gate that `chat.py` performs. A free
  user at their daily cap can bypass via the streaming endpoint.
- **Target behaviour**: `stream.py` invokes the same gate BEFORE the first LLM
  token is yielded. Over-quota returns HTTP 429 during the initial response
  (NOT mid-stream as an error frame). Matches `chat.py` exactly.
- **Approach**: Extract the shared logic into `app/services/usage.py::ensure_quota`
  (the service file already exists). Both `chat.py` and `stream.py` call it via:
  ```
  await ensure_quota(user=current_user, plan=plan, db=db)
  ```
  `ensure_quota` raises `HTTPException(429, detail={"error":"quota_exhausted", ...})`
  which both routes already know how to serialize. No behavioural change for
  `chat.py` — same error payload shape.
- **Test strategy**: `chat-stream.unit.007` + a new regression assertion in
  `chat-stream.unit.002` (existing-style chat quota test) that the payload shape
  is identical across both endpoints.
- **Risk**: Medium. The frontend's streaming consumer may not handle 429 on
  connection open. Documented as an out-of-scope follow-up (§9 non-goals).

### 3.2 FIX-02 — `_ensure_admin` consolidation

- **Surface**: `admin-rbac.unit.001` (`test_admin_ensure_admin_non_admin_raises`)
  and `admin-rbac.int.001..003` (403 probes).
- **Current behaviour**: `_ensure_admin` is textually duplicated in
  `app/api/routes/admin_saas.py:37`, `admin_invoices.py:34`, `admin_trials.py:37`.
  `admin.py` imports the one from `admin_saas`, which is the least-terrible
  version — but three independent copies means a bug fix in one silently skips
  the others.
- **Target behaviour**: A single `require_admin` FastAPI dependency in
  `app/api/deps.py`:
  ```
  async def require_admin(current_user: User = Depends(get_current_user)) -> User:
      if not current_user.is_admin:
          raise HTTPException(status_code=403, detail="Admin access required")
      return current_user
  ```
  Every admin route replaces `_ensure_admin(user)` call-sites with
  `Depends(require_admin)` in the signature. The three local `_ensure_admin`
  copies are DELETED.
- **Approach**: Mechanical grep-and-replace per file (three files only). The
  import in `admin.py` (`from app.api.routes.admin_saas import _ensure_admin`)
  also gets replaced with `from app.api.deps import require_admin`. Audit pass:
  `rg "_ensure_admin"` after the edit must return 0 hits.
- **Test strategy**: `admin-rbac.unit.001` unit-tests the dependency in
  isolation (calling it with a non-admin user raises 403). The three
  integration 403 probes verify every admin route still rejects non-admins end-to-end.
- **Risk**: Low. Mechanical.

### 3.3 FIX-03 — Missing `user_id` / `org_id` filters (generic pattern)

- **Surface**: Every cross-tenant isolation test that currently returns 200
  where it should return 404/403 (`conversations.unit.001/003/008/010/012/014/015`,
  `notifications.unit.006`, `byok.int.004`, `documents-search.012/013/014`).
- **Current behaviour**: One or more repository queries return rows regardless
  of `user_id`. Expected offenders (to be confirmed during Batch D–E):
  `bookmarks`, `tags`, `folders`, `memory` (all completely untested per spec).
- **Target behaviour**: Every `db.execute(select(Model))` for a user-owned or
  org-owned model has an explicit `.where(Model.user_id == current_user.id)` or
  `.where(Model.org_id == current_org.id)`.
- **Approach — generic fix pattern**:
  1. When an isolation test fails with 200 instead of 404, locate the route
     handler.
  2. Inspect the repository call — likely missing `.where(<owner_field> == …)`.
  3. Add the filter. If the model has `user_id` AND `org_id`, use `user_id`
     unless the resource is explicitly an org-level resource
     (e.g. `Organization`, `Invoice.org_id`).
  4. Confirm the test now returns 404.
- **Test strategy**: Every route touched by FIX-03 gets an
  `assert_isolated(...)` invocation in its spec. Future regressions will fail
  the single isolation helper call.
- **Risk**: Medium — unknown unknowns. Budget: up to 8 touched files. If more,
  escalate (scope creep signal for sdd-verify).

### 3.4 FIX-04 — `search.py` fail-unsafe history logging

- **Surface**: `documents-search.unit.008` (`test_search_history_db_write_failure_safe`).
- **Current behaviour**: `_log_search_history` in `search.py` likely raises on
  DB error and tanks the entire search request.
- **Target behaviour**: `_log_search_history` wraps its insert in
  `try/except Exception as exc: logger.warning(...)`. Search results return
  successfully even if history logging fails.
- **Approach**: 3-line change. No schema migration. Add a `caplog` assertion in
  the test to verify the warning fired.
- **Risk**: Trivial.

### 3.5 FIX-05 — `analytics._date_range` off-by-one

- **Surface**: `observability.unit.009` (`test_analytics_date_range_logic`).
- **Current behaviour**: `_date_range(30)` may return an end date of `today -
  1day` or a start date that includes today, producing off-by-one windows in
  daily aggregations.
- **Target behaviour**: Canonical contract:
  - `start = date.today() - timedelta(days=days_back)` (inclusive)
  - `end = date.today() + timedelta(days=1)` (exclusive, or `today` inclusive,
    pick one and lock it)
- **Approach**: Fix in place; add a docstring specifying the contract
  (inclusive/exclusive); the test asserts both boundaries.
- **Risk**: Low, but may shift numbers in existing dashboards. Acceptable —
  dashboards are admin-only and eventually-consistent.

### 3.6 FIX-06 — `v1.py` missing rate-limit headers

- **Surface**: `chat-stream.unit.014` (`test_v1_rate_limit_headers_injected`).
- **Current behaviour**: `/api/v1/*` endpoints do not emit `X-RateLimit-Limit`,
  `X-RateLimit-Remaining`, `X-RateLimit-Reset`.
- **Target behaviour**: Middleware or per-endpoint dependency injects the three
  headers on every response.
- **Approach**: Two options:
  - (A) Extend the existing rate-limit middleware (`apps/api/app/api/middleware.py`)
    to inject headers for paths matching `^/api/v1/`. Preferred.
  - (B) Inject via a dependency on the v1 router. Secondary — duplicates
    middleware concerns per-route.
- **Decision**: Option A. Middleware already knows the bucket state; it just
  doesn't write response headers today.
- **Risk**: Medium — middleware touches the global request pipeline. Mitigated
  by scoping the header injection to the `/api/v1/` prefix only.

### 3.7 Summary table

| ID     | Spec surfacing it        | Area                    | Risk   | Paired test(s)                 |
|--------|--------------------------|-------------------------|--------|--------------------------------|
| FIX-01 | chat-stream              | `stream.py` quota gate  | Medium | chat-stream.unit.007, .002     |
| FIX-02 | admin-rbac               | `_ensure_admin` unify   | Low    | admin-rbac.unit.001, .int.001..003 |
| FIX-03 | conversations + byok + docs + notifications | Query `user_id`/`org_id` filters | Medium | ~10 isolation tests |
| FIX-04 | documents-search         | `_log_search_history`   | Trivial| documents-search.unit.008      |
| FIX-05 | observability            | `_date_range` math      | Low    | observability.unit.009         |
| FIX-06 | chat-stream              | v1 rate-limit headers   | Medium | chat-stream.unit.014           |

## 4. Execution strategy

Five batches matching the proposal. Each batch is one or more commits; every
commit passes the full suite before the next lands. The test-infrastructure
patterns of §2 are front-loaded into Batch A so every later batch consumes
ready-made fixtures.

### Batch A — foundations + auth + billing

- **Infra delivered**:
  - `apps/api/tests/fixtures/tenants.py` (two_orgs_two_users)
  - `apps/api/tests/helpers/isolation.py` (assert_isolated)
  - `apps/api/tests/helpers/sse.py` (assert_sse_yields)
  - `apps/api/tests/helpers/llm.py` (patch_llm_adapter)
  - `apps/api/tests/mocks/email.py` (MockEmailProvider + fixture)
  - `apps/api/tests/factories/` (skeleton + user.py + org.py)
  - `apps/api/scripts/check_coverage.py`
  - `apps/api/coverage-targets.yaml`
  - Makefile delta: `make test-cov` runs pytest then the coverage script.
- **Specs covered**: `auth` (6 tests) + `billing` (6 tests).
- **Code fixes landing**: NONE. Auth and billing are well-hardened; tests are
  confirmatory.
- **Dependencies**: None.
- **Commits (est)**: 4 — infra / factories / auth tests / billing tests.
- **Exit criteria**: 12 new tests green; `make test-cov` runs; coverage
  baseline JSON captured; no regressions in the 1111 existing tests.

### Batch B — chat + stream + public-api-v1 (+ FIX-01 + FIX-06)

- **Specs covered**: `chat-stream` (14 tests).
- **Code fixes landing**: **FIX-01** (stream.py quota gate) and **FIX-06** (v1
  rate-limit headers) alongside their failing tests.
- **Dependencies**: Batch A (SSE helper + LLM helper + factories).
- **Commits (est)**: 4 — chat tests / stream tests + FIX-01 / v1 tests + FIX-06
  / cleanup.
- **Exit criteria**: 14 new tests green; `stream.py` quota semantics match
  `chat.py` exactly; v1 endpoints emit all three rate-limit headers.

### Batch C — admin + byok + organizations (+ FIX-02)

- **Specs covered**: `admin-rbac` (6 tests) + `byok` (6 tests) +
  `organizations` (6 tests).
- **Code fixes landing**: **FIX-02** (`_ensure_admin` consolidation). First
  commit in the batch — deletes duplicates, all three route files + the
  dependency land together. Grep audit at the end of the commit: zero hits.
- **Dependencies**: Batch B (full infra; two_orgs_two_users is heavily used).
- **Commits (est)**: 4 — FIX-02 + admin tests / byok tests / org tests / cleanup.
- **Exit criteria**: 18 new tests green; `rg _ensure_admin` = 0 hits;
  organization cross-tenant harness validated live.

### Batch D — conversations + analytics + notifications (+ FIX-03 first wave + FIX-04 + FIX-05)

- **Specs covered**: `conversations` (15 tests) + `observability` (14 tests,
  analytics slice primarily) + `notifications` (12 tests).
- **Code fixes landing**: **FIX-03 first wave** (bookmarks, tags, folders,
  memory, shared — expected to surface missing `user_id` filters), **FIX-04**
  (search history fail-safe — lands here because the analytics tests touch
  adjacent search paths), **FIX-05** (date range math).
- **Dependencies**: Batch C (admin-level fixtures needed for analytics
  `test_analytics_system_admin_sees_all`).
- **Commits (est)**: 5 — conversations writes + FIX-03 wave 1 / shared + memory
  tests / analytics + FIX-05 / notifications + FIX-04 / cleanup.
- **Exit criteria**: 41 new tests green; no missing-filter leaks remaining in
  touched modules (verified via new isolation tests).

### Batch E — documents + search + export + analysis (+ FIX-03 second wave)

- **Specs covered**: `documents-search` remaining items (15 tests).
- **Code fixes landing**: **FIX-03 second wave** (upload isolation, export
  isolation, analysis cross-tenant — if the tests surface leaks). Expected
  lower-volume than Batch D wave.
- **Dependencies**: Batch D.
- **Commits (est)**: 3 — documents/search tests / analysis + export tests
  (+ FIX-03 wave 2 as needed) / final cleanup + full coverage audit.
- **Exit criteria**: ~130 total new tests green across the full change;
  coverage targets in §2.5.2 met; `apps/api/scripts/check_coverage.py` exits
  zero.

### Cross-batch conventions

- Each batch's first commit ONLY touches infrastructure or fix code, never both.
- Each test commit title follows conventional commits: `test(<domain>): <what>`.
- Each fix commit follows: `fix(<area>): <what>` referencing the spec test ID
  in the body.
- Any commit that adds a new file under `tests/factories/` or `tests/helpers/`
  re-runs `make test` locally before landing.

## 5. CI / local dev flow

### 5.1 Container mandate

All tests execute inside the `tukijuris-api-1` container. The host is Python
3.9; the app runtime requires Python 3.12 per `sdd-init/tukijuris`. Running
pytest on the host produces import errors (engram obs #280). This is non-optional.

### 5.2 Command matrix (local dev)

| Purpose                         | Command                                                                                          |
|---------------------------------|--------------------------------------------------------------------------------------------------|
| Unit-only (fast, mocked infra)  | `docker exec tukijuris-api-1 pytest tests/unit -v`                                               |
| Integration (DB + Redis req'd)  | `docker exec tukijuris-api-1 pytest tests/integration -v`                                        |
| Full + coverage                 | `docker exec tukijuris-api-1 pytest tests --cov=app --cov-report=term-missing --cov-report=json:/tmp/coverage.json` |
| Full + coverage + enforcement   | `docker exec tukijuris-api-1 make test-cov`                                                      |
| Single file (debug loop)        | `docker exec tukijuris-api-1 pytest tests/integration/test_chat.py -v -x`                        |
| Single test (debug loop)        | `docker exec tukijuris-api-1 pytest tests/integration/test_chat.py::test_chat_quota_enforcement_free_user -v` |

### 5.3 Makefile deltas

Current (inferred): `make test` and `make test-cov` exist and invoke pytest on
the host. We **update** both to shell into the container:

```
test:
	docker exec tukijuris-api-1 pytest tests -v

test-cov:
	docker exec tukijuris-api-1 pytest tests \
	    --cov=app \
	    --cov-report=term-missing \
	    --cov-report=json:/tmp/coverage.json
	docker exec tukijuris-api-1 python scripts/check_coverage.py
```

If the current Makefile already shells in (to be confirmed during Batch A), no
change. If not, the delta is 2 lines.

### 5.4 GitHub Actions pre-spec (for Sprint 3 Item 8 — not in scope here)

Item 8 (github-setup) is explicitly NOT implemented in this change, but this
design pre-specs what that future workflow should run, so Item 8 is a
mechanical translation:

```yaml
jobs:
  backend-tests:
    services:
      postgres: { image: postgres:15-alpine, ... }
      redis:   { image: redis:7-alpine,    ... }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e apps/api
      - run: alembic upgrade head
        working-directory: apps/api
      - run: pytest apps/api/tests --cov=app --cov-report=xml:/tmp/coverage.xml
      - run: python apps/api/scripts/check_coverage.py
      - uses: codecov/codecov-action@v4
        with: { files: /tmp/coverage.xml }
```

When Item 8 lands, this workflow is the seed; no design iteration needed.

## 6. Performance budget

### 6.1 Test runtime budget

Current baseline (estimate from existing 1111 tests): ~90–120s inside the
container on a developer laptop. Each batch's test delta MUST NOT increase the
full-suite runtime by more than **45 seconds per batch** (≤ 3 minutes absolute
worst case across all five batches).

Guardrails:

- Prefer `tests/unit/` (no DB, no Redis) for anything that doesn't NEED
  integration. Unit tests run in ~5ms each; integration tests in ~200ms each.
- Shared factories reuse `auth_client` and the autouse `_reset_rate_limit_buckets`
  fixture, both of which are fast (Redis SCAN + DELETE, microseconds).
- New helpers (`assert_isolated`, `assert_sse_yields`) add one extra request per
  invocation for the owner sanity check. Negligible in aggregate.

### 6.2 `pytest-xdist` — DECIDED NO

Tradeoff evaluated:

| Pros                                                      | Cons                                                                                           |
|-----------------------------------------------------------|------------------------------------------------------------------------------------------------|
| 4× wall-clock speedup on 4-core laptops                   | Autouse `_reset_rate_limit_buckets` fixture would collide across workers — Redis key namespace is shared |
| Parallelizes independent domains well                     | Integration tests share a single DB — workers would race on row creation; would need per-worker schemas |
| Industry-standard                                         | Adds a dep and a CI setup concern                                                              |
| —                                                         | Current 90s baseline is not painful enough to justify the complexity                           |

**Decision**: defer. Revisit if full-suite runtime exceeds 5 minutes.

## 7. Quality gates (DoD — executable)

The change is DONE when all of the following are mechanically verifiable:

1. `docker exec tukijuris-api-1 pytest tests` exits 0.
2. All 10 spec test catalogs are implemented; all tests are green.
3. `docker exec tukijuris-api-1 python apps/api/scripts/check_coverage.py`
   exits 0 — every MUST threshold in §2.5.2 is met.
4. `rg "skip\(" apps/api/tests | wc -l` — no increase over the baseline
   captured in Batch A's first commit.
5. `rg "xfail\(" apps/api/tests` — any new xfail has a `strict=True` flag AND a
   non-empty `reason=` string referencing a spec ID or engram topic key.
6. `rg "_ensure_admin" apps/api/app` returns 0 hits (FIX-02 audit).
7. `rg "TODO|FIXME" apps/api/tests` — no new occurrences introduced by this change.
8. No regression in the pre-existing 1111 passing tests (delta measured against
   Batch A baseline).
9. Every route in Appendix B §B.1 is covered by at least one `assert_isolated`
   call in the new tests.
10. Every fix from §3 has a paired test whose failure would have caught the bug.

## 8. Risks & mitigations

| Risk                                                                          | Likelihood | Impact | Mitigation                                                                                                       |
|-------------------------------------------------------------------------------|------------|--------|------------------------------------------------------------------------------------------------------------------|
| Cross-tenant tests expose bugs beyond the 6 listed fixes (i.e. FIX-03 balloons) | Medium     | Medium | Proposal explicitly budgets code fixes. Cap at 8 files touched per batch. If exceeded, pause and re-verify scope with sdd-verify. |
| `stream.py` quota 429 on connection-open breaks the frontend consumer         | Medium     | Low    | Document as FE follow-up. Do NOT change FE here.                                                                 |
| Coverage thresholds too aggressive, block CI                                  | Medium     | Medium | Tiered MUST vs STRETCH. STRETCH is warning-only. Anchor MUST thresholds against Batch A's measured baseline (not estimates). |
| Fixture complexity explosion (one factory pulls in five services)             | Low        | Medium | Hard budget: ≤ 50 LOC per factory module. If a factory exceeds, refactor the logic into a service helper (which would also benefit production code) or split the factory into two. |
| Async event-loop fixture (`event_loop` in conftest) conflicts with new SSE helper | Low    | High   | `assert_sse_yields` re-enters the same session loop via `asyncio.wait_for`. No new loop created. Verified in Batch A.         |
| Two tenants' autouse Redis reset step double-deletes rate-limit keys between test pairs | Low | Low | Fixture is idempotent (SCAN + DELETE). No ordering guarantee needed.                                              |
| `MockEmailProvider` dependency override leaks across tests                    | Low        | Medium | Fixture teardown calls `app.dependency_overrides.clear()` for the specific key, not globally.                    |
| `two_orgs_two_users` seeds hitting rate limits on auth registration           | Low        | Low    | Autouse Redis reset runs BEFORE the fixture. If the fixture itself registers 2 users and rate limit is 10/min per IP, we're 5× under the cap. |
| SA 2.0 savepoint gotcha in any new factory that inserts under UNIQUE constraints (obs #156) | Low | High | Factories go through HTTP when possible. The 4 service-layer factories (invoice, llm_key, notification, saved_search) already follow the "check first, then insert" pattern per obs #156. |
| FIX-06 middleware change breaks unrelated endpoints                           | Low        | High   | Scope header injection to `^/api/v1/` prefix only. Full-suite run after the middleware change validates no regressions. |
| github-setup (Item 8) blocks adoption of this workflow                        | Low        | Low    | Commands run locally inside container today. CI is additive, not blocking.                                       |

## 9. Non-goals

Explicitly OUT of this design (and therefore out of sdd-tasks / sdd-apply):

1. Frontend tests — `apps/web/` is at 212 passing tests already; untouched.
2. `redirect_slashes=True` cross-origin bug — separate proposal after this
   change archives.
3. Email real-provider integration — blocked on Sprint 3 Item 3b.
4. W7 webhook concurrency race bug — tracked in engram obs #276, Sprint 3
   Batch 6. Our billing tests assume the CURRENT behaviour (the one pre-existing
   test failure is allowed to stay red as an `xfail(strict=True, reason="W7")`).
5. Global RLS (Row-Level Security) via Postgres policies — architectural
   change; this design relies on application-layer filtering reinforced by
   tests.
6. `pytest-xdist` adoption — deferred until suite runtime > 5 minutes (§6.2).
7. `factory-boy` adoption — rejected (§2.2).
8. Migrating root-level tests (`tests/test_*.py`) into `tests/integration/`.
   The existing 17 root-level files are legacy-but-passing; we only enforce the
   new `tests/unit/` vs `tests/integration/` split for NEW files (§C).
9. Item 8 (github-setup) itself — we pre-spec the workflow but do not create it.

## 10. Appendices

### Appendix A — Canonical fixture/helper file paths and shapes

```
apps/api/tests/
├── conftest.py                  # UNCHANGED (197 LOC) — existing fixtures preserved
├── helpers/                     # NEW package
│   ├── __init__.py
│   ├── isolation.py             # assert_isolated(...)
│   ├── sse.py                   # assert_sse_yields(...), SSEEvent dataclass
│   └── llm.py                   # patch_llm_adapter(...)
├── factories/                   # NEW package
│   ├── __init__.py
│   ├── user.py                  # make_user(client, *, plan, is_admin)
│   ├── org.py                   # make_org(client, owner, *, plan), add_member(client, org, user, role)
│   ├── conversation.py          # make_conversation(auth_client, *, title, messages)
│   ├── invoice.py               # make_invoice(db, *, org, status)
│   ├── llm_key.py               # make_llm_key(db, *, user, provider, encrypted_value)
│   ├── notification.py          # make_notification(db, *, user, is_read)
│   ├── api_key.py               # make_api_key(auth_client, *, scopes)
│   └── saved_search.py          # make_saved_search(db, *, user, filters)
├── fixtures/
│   ├── tenants.py               # NEW — two_orgs_two_users(...)
│   └── webhooks/                # UNCHANGED — existing Culqi/MP payload fixtures
├── mocks/                       # NEW package
│   ├── __init__.py
│   └── email.py                 # MockEmailProvider, mock_email_provider fixture
├── unit/                        # existing — 41 files; new files added per spec
├── integration/                 # existing — 10 files; new files added per spec
└── test_*.py                    # legacy root-level — untouched
```

Pytest discovery: adding directories under `apps/api/tests/` requires no
`pyproject.toml` change — pytest already auto-discovers nested test files.
`helpers/`, `factories/`, `fixtures/`, `mocks/` are NON-test packages (no
`test_*.py` files); they are imported by tests via their fully-qualified path,
e.g. `from tests.factories.user import make_user`.

### Appendix B — Cross-tenant route catalog

Every entry here MUST be covered by at least one `assert_isolated(...)` call
in the new tests. This is the authoritative list; the quality gate §7 #9
checks each entry.

#### B.1 User-owned resources — 404 isolation expected

| Route                                             | Method     | Owning model      | Spec test ID              |
|---------------------------------------------------|------------|-------------------|---------------------------|
| `/api/conversations/{id}`                         | GET        | Conversation      | conversations.unit.001    |
| `/api/conversations/{id}`                         | PATCH      | Conversation      | conversations.unit.001    |
| `/api/conversations/{id}`                         | DELETE     | Conversation      | conversations.unit.004    |
| `/api/conversations/{id}/pin`                     | PATCH      | Conversation      | conversations.unit.002    |
| `/api/conversations/{id}/archive`                 | PATCH      | Conversation      | conversations.unit.003    |
| `/api/shared/{share_id}` (revoked)                | GET        | Conversation.share| conversations.unit.007    |
| `/api/bookmarks/`                                 | GET        | Bookmark          | conversations.unit.009    |
| `/api/bookmarks/{id}`                             | DELETE     | Bookmark          | conversations.unit.009    |
| `/api/tags/{id}`                                  | PATCH/DELETE| Tag              | conversations.unit.010/011|
| `/api/folders/{id}`                               | GET/PATCH/DELETE | Folder      | conversations.unit.012    |
| `/api/memory/{id}`                                | GET/DELETE | MemoryFact       | conversations.unit.014    |
| `/api/feedback/{message_id}`                      | POST       | Message          | conversations.unit.015    |
| `/api/notifications/{id}/read`                    | PATCH      | Notification     | notifications.unit.006    |
| `/api/upload/{id}`                                | GET        | UploadedDocument | byok.int.004 / docs-search.014 |
| `/api/upload/{id}`                                | DELETE     | UploadedDocument | byok.int.004              |
| `/api/export/consultation/{message_id}`           | GET        | Message          | documents-search.012      |
| `/api/export/conversation/{id}`                   | GET        | Conversation     | documents-search.013      |
| `/api/analysis/` (with foreign doc_id in body)    | POST       | UploadedDocument | documents-search.010      |
| `/api/search/saved/{id}`                          | GET/DELETE | SavedSearch      | documents-search.006      |
| `/api/keys/{id}` (developer api key)              | PATCH/DELETE| ApiKey          | byok.int.001              |
| `/api/keys/llm/{id}` (BYOK llm key)               | PATCH/DELETE| LlmKey          | byok existing tests       |

#### B.2 Org-membership gates — 403 isolation expected

| Route                                             | Method     | Spec test ID              |
|---------------------------------------------------|------------|---------------------------|
| `/api/organizations/{org_id}`                     | GET        | orgs.int.004              |
| `/api/organizations/{org_id}`                     | PATCH      | orgs.int.002 (member role)|
| `/api/organizations/{org_id}/members/{uid}`       | DELETE     | orgs.int.001/003          |
| `/api/billing/{org_id}/invoices`                  | GET        | billing.int.001           |
| `/api/analytics/{org_id}/overview`                | GET        | observability.unit.001    |
| `/api/analytics/{org_id}/queries`                 | GET        | observability.unit.004    |
| `/api/analytics/{org_id}/areas`                   | GET        | observability.unit.005    |
| `/api/analytics/{org_id}/top-queries`             | GET        | observability.unit.006    |
| `/api/analytics/{org_id}/export`                  | GET        | observability.unit.007    |

#### B.3 Role gates — 403 expected

| Route                                   | Method | Gate type    | Spec test ID                     |
|-----------------------------------------|--------|--------------|----------------------------------|
| `/api/admin/users`                      | GET    | is_admin     | admin-rbac.int.001               |
| `/api/admin/activity`                   | GET    | is_admin     | admin-rbac.int.002               |
| `/api/admin/knowledge`                  | GET    | is_admin     | admin-rbac.int.003               |
| `/api/admin/rbac/users/{id}/roles`      | POST   | is_admin     | admin-rbac.int.004 (positive)    |
| `/api/admin/rbac/users/{id}/roles/{rid}`| DELETE | is_admin     | admin-rbac.int.005 (positive)    |
| `/api/v1/query` (wrong scope)           | POST   | API-key scope| chat-stream.unit.012             |
| `/api/documents/…` (admin mutations)    | POST/PATCH/DELETE | is_admin | documents-search.015         |

### Appendix C — Test-file placement convention

Going forward, NEW test files MUST land under the appropriate subdirectory.
Existing root-level files are legacy (§9 non-goal #8) and untouched.

| Convention                                            | Location                              | Purpose                             |
|-------------------------------------------------------|---------------------------------------|-------------------------------------|
| Pure logic, fully mocked, no DB, no Redis             | `apps/api/tests/unit/`                | <100ms per test; parallelizable later |
| httpx + FastAPI + DB/Redis live                       | `apps/api/tests/integration/`         | 100–500ms per test                  |
| Multi-step end-to-end flow (new category — OPTIONAL)  | `apps/api/tests/e2e/`                 | Only if a flow truly spans 3+ domains. At time of writing no spec requires e2e — the directory is CONDITIONALLY created only if Batch D or E needs it. |

Naming rules:

- Files: `test_<domain>_<aspect>.py`. Examples: `test_auth_sessions.py`,
  `test_conversations_write.py`.
- Tests: `test_<subject>_<condition>_<expected>` in snake_case. Example:
  `test_stream_quota_gate_free_user_exhausted`.

Import rules:

- Helpers and factories are imported via their package path:
  `from tests.helpers.isolation import assert_isolated`.
- Fixtures that should be auto-discovered go in `conftest.py` (root).
  Factories and helpers do NOT auto-register; tests import them explicitly.
  This keeps the root `conftest.py` lean and searchable.

### Appendix D — Canonical pattern references

These observations are already in engram and govern how the new test code is
written. Contributors MUST read them before editing the relevant areas; this
design does NOT re-describe them.

| Engram topic key                              | Obs ID | When to read                                                                 |
|-----------------------------------------------|--------|------------------------------------------------------------------------------|
| `tukijuris/webhook-two-phase-commit`          | #159   | Before touching any billing webhook test (canonical commit pattern).         |
| `tukijuris/sqlalchemy-async-gotchas`          | #156   | Before writing any factory that inserts under UNIQUE constraints.            |
| `tukijuris/vitest-gotchas`                    | #186   | Frontend-only. NOT applicable to this change (FE tests out of scope).        |
| `tukijuris/culqi-stored-token-api`            | #213   | Before writing Culqi-related billing tests.                                  |
| `tukijuris/mp-stored-token-api`               | #223   | Before writing MP-related billing tests.                                     |
| `tukijuris/webhook-concurrency-race-bug` (#276) | #276 | External dependency; informs why billing W7 stays as `xfail(strict=True)`.   |

### Appendix E — Decision log (resolved vs unresolved for sdd-tasks)

| # | Decision                                        | Status    | Notes                                                                    |
|---|-------------------------------------------------|-----------|--------------------------------------------------------------------------|
| 1 | 403 vs 404 on cross-tenant                      | RESOLVED  | §2.1.4 — user-owned → 404; org/role → 403.                               |
| 2 | factory-boy vs plain async factories            | RESOLVED  | Plain async. §2.2.                                                       |
| 3 | pytest-xdist                                    | RESOLVED  | Rejected. §6.2.                                                          |
| 4 | Coverage enforcement mechanism                  | RESOLVED  | Script + YAML thresholds (Option C). §2.5.3.                             |
| 5 | Test placement (new files)                      | RESOLVED  | §C.                                                                      |
| 6 | Legacy root-level test migration                | RESOLVED  | Non-goal. §9 #8.                                                         |
| 7 | `_ensure_admin` home                            | RESOLVED  | `app/api/deps.py::require_admin`. §3.2.                                  |
| 8 | `ensure_quota` home                             | RESOLVED  | `app/services/usage.py`. §3.1.                                           |
| 9 | Shared LLM mock — new module vs helper          | RESOLVED  | Helper in `tests/helpers/llm.py`; no new `tests/mocks/llm.py`. §2.3.2.    |
| 10| SSE frame contract                              | RESOLVED  | `{type:"token"}`, `{type:"error"}`, `[DONE]`. §2.4.3.                   |
| 11| W7 xfail vs skip                                | RESOLVED  | `xfail(strict=True, reason="W7 — see engram #276")`. §9 #4.              |
| 12| Coverage MUST numbers per module                | **UNRESOLVED (sdd-tasks)** | Table anchored on estimates in §2.5.2; final numbers land after Batch A baseline measurement. |
| 13| Whether `tests/e2e/` gets created this change   | **UNRESOLVED (sdd-tasks)** | Conditional on Batch D/E needs. Default: no.                  |
| 14| Exact `ensure_quota` error payload shape        | **UNRESOLVED (sdd-tasks)** | Must match `chat.py` current shape byte-for-byte. Captured during Batch B. |
| 15| Whether Makefile currently shells into container | **UNRESOLVED (sdd-tasks)** | Quick inspection in Batch A. 2-line delta if not.            |
