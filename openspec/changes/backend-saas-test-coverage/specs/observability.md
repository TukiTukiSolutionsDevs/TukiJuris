---
change: backend-saas-test-coverage
spec: observability
status: proposed
created: 2026-04-19
---

# Spec — Observability test coverage

## 1. Scope
Coverage for the `analytics.py` and `health.py` domains. This includes system health probes (liveness, readiness, metrics, cache), analytics event aggregations (usage per plan/org), org-admin access gates, cost estimations, date logic, and CSV exports.

## 2. Current state
- Existing tests: `health.py` has 8 basic tests. `analytics.py` (848 lines) is completely dark.
- Known gaps: Zero tests for analytics. Org-admin gating logic `_assert_org_access` is completely untested. Analytics CSV export, models cost calculation, date range boundary math, and health metrics/cache data shape lack coverage.
- Pre-existing failures unrelated: None.

## 3. Test catalog
1. `observability.unit.001`
   - Name: `test_analytics_overview_requires_org_admin`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analytics.py`
   - Intent: Ensure standard org members cannot view analytics data.
   - Setup: User A (member role), Org A
   - Assertions: GET `/api/analytics/{org_id}/overview` returns 403.
   - Expected runtime: fast
   - Dependency: NONE
2. `observability.unit.002`
   - Name: `test_analytics_system_admin_sees_all`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analytics.py`
   - Intent: Verify global system admins can view any org's analytics.
   - Setup: User Admin (`is_admin=True`), Org A
   - Assertions: GET to Org A analytics returns 200, bypassing org_role check.
   - Expected runtime: fast
   - Dependency: NONE
3. `observability.unit.003`
   - Name: `test_analytics_free_user_access_own_data_only`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analytics.py`
   - Intent: Ensure free users (no org) can access their personal analytics if supported, or receive 403.
   - Setup: Free User A
   - Assertions: Gated properly depending on plan-logic (200 for self, 403 for others).
   - Expected runtime: fast
   - Dependency: NONE
4. `observability.unit.004`
   - Name: `test_analytics_queries_org_admin_only`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analytics.py`
   - Intent: Ensure the `/queries` time-series endpoint is properly auth-gated.
   - Setup: Org Admin, Org Member
   - Assertions: Member gets 403, Admin gets 200.
   - Expected runtime: fast
   - Dependency: NONE
5. `observability.unit.005`
   - Name: `test_analytics_areas_breakdown`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analytics.py`
   - Intent: Verify the `/areas` aggregation returns correct groupings.
   - Setup: Org Admin, mock DB with 5 labor queries, 2 civil queries
   - Assertions: Response matches expected grouped counts.
   - Expected runtime: fast
   - Dependency: NONE
6. `observability.unit.006`
   - Name: `test_analytics_top_queries_isolation`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analytics.py`
   - Intent: Verify that top queries list strictly scopes to the requested org.
   - Setup: Org A, Org B
   - Assertions: Org A top queries response does not contain Org B's queries.
   - Expected runtime: fast
   - Dependency: NONE
7. `observability.unit.007`
   - Name: `test_analytics_export_csv_generation`
   - Layer: integration
   - File: `apps/api/tests/integration/test_analytics.py`
   - Intent: Validate CSV file generation and headers.
   - Setup: Org Admin
   - Assertions: Returns `text/csv` with proper header rows and data points.
   - Expected runtime: fast
   - Dependency: NONE
8. `observability.unit.008`
   - Name: `test_analytics_models_cost_calculation`
   - Layer: unit
   - File: `apps/api/tests/unit/test_analytics_costs.py`
   - Intent: Validate `_estimate_cost` function maths.
   - Setup: Call `_estimate_cost("gpt-4o", 1000)`
   - Assertions: Returns expected float value.
   - Expected runtime: fast
   - Dependency: NONE
9. `observability.unit.009`
   - Name: `test_analytics_date_range_logic`
   - Layer: unit
   - File: `apps/api/tests/unit/test_analytics_dates.py`
   - Intent: Validate `_date_range(30)` boundary calculations to prevent off-by-one errors.
   - Setup: Call date range for 30 days.
   - Assertions: Start date is exactly 30 days prior; end date is today.
   - Expected runtime: fast
   - Dependency: code-fix-needed (if off-by-one found)
10. `observability.unit.010`
    - Name: `test_health_liveness_probe`
    - Layer: integration
    - File: `apps/api/tests/integration/test_health.py`
    - Intent: Validate the `/health` liveness endpoint.
    - Setup: Running app
    - Assertions: Returns 200 with `status: ok`.
    - Expected runtime: fast
    - Dependency: NONE
11. `observability.unit.011`
    - Name: `test_health_readiness_probe`
    - Layer: integration
    - File: `apps/api/tests/integration/test_health.py`
    - Intent: Validate the `/health/ready` and `/health/db` endpoint probes Postgres.
    - Setup: Running app
    - Assertions: Returns 200 with active DB connection status.
    - Expected runtime: fast
    - Dependency: NONE
12. `observability.unit.012`
    - Name: `test_health_metrics_endpoint_shape`
    - Layer: integration
    - File: `apps/api/tests/integration/test_health.py`
    - Intent: Ensure `/health/metrics` returns system CPU/RAM usage.
    - Setup: Running app
    - Assertions: Payload includes psutil/resource metrics without crashing.
    - Expected runtime: fast
    - Dependency: NONE
13. `observability.unit.013`
    - Name: `test_health_cache_redis_stats`
    - Layer: integration
    - File: `apps/api/tests/integration/test_health.py`
    - Intent: Ensure `/health/cache` returns Redis connection info.
    - Setup: Running app, Mock Redis
    - Assertions: Payload includes Redis PING success.
    - Expected runtime: fast
    - Dependency: NONE
14. `observability.unit.014`
    - Name: `test_health_rate_limit_bucket_observation`
    - Layer: integration
    - File: `apps/api/tests/integration/test_health.py`
    - Intent: Verify health endpoints are exempt from rate limiting buckets.
    - Setup: Hammer `/health` 100 times.
    - Assertions: Never returns 429 Too Many Requests.
    - Expected runtime: fast
    - Dependency: NONE

## 4. Code fixes likely required
- Verify the off-by-one error in `_date_range` mentioned during exploration. Fix it if `test_analytics_date_range_logic` fails.

## 5. Acceptance criteria
- All 14 tests pass.
- Zero new unjustified skips.
- Coverage delta target ≥ 85% for `analytics.py` and `health.py`.
- No regression in the 1111 currently-passing tests.

## 6. Out of scope / deferred
- Items in Sprint 3 Batch 3.
- Advanced load testing on analytics.

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
- Prior relevant archives (cite engram topic keys)
