# Deploy Checklist — plan-model-refactor

## Pre-deploy

- [ ] All unit tests pass: `docker exec tukijuris-api-1 python -m pytest tests/unit/ -v --tb=short`
- [ ] TypeScript check passes: `cd apps/web && npx tsc --noEmit`
- [ ] No legacy plan strings in codebase (grep guard):
  ```bash
  grep -rn '"base"\|"enterprise"' apps/api/app/ apps/web/src/ \
    --include="*.py" --include="*.ts" --include="*.tsx" \
    | grep -v "__pycache__\|.pyc\|test_\|#\|comment\|deploy"
  ```
  Expected: zero hits for plan-value context (billing page email subject "Estudio" is OK).

- [ ] `.env.example` has `BETA_MODE=true` documented
- [ ] Production `.env` has `BETA_MODE` explicitly set (true or false — startup validation will hard-fail if missing in production)

## Deploy Order (MANDATORY — do not reverse)

1. **Build & push** new image
2. **Stop API** (`docker compose stop api` or equivalent)
3. **Run migrations**: `docker exec tukijuris-api-1 alembic upgrade head`
   - Applies 007_rename_plan_values (UPDATE plan columns)
   - Applies 008_org_seat_pricing (ADD COLUMN)
4. **Start API** (`docker compose start api`)
5. **Verify startup** — check logs for startup validation passing (no BETA_MODE fail-fast error)

> ⚠️ Migration 007 is forward-only. There is no downgrade path. If rollback is needed, restore from DB snapshot.

## Post-deploy Verification

Run against production (or staging) DB:

```sql
-- Must return 0
SELECT COUNT(*) FROM users WHERE plan IN ('base', 'enterprise');
SELECT COUNT(*) FROM organizations WHERE plan IN ('base', 'enterprise');
SELECT COUNT(*) FROM subscriptions WHERE plan IN ('base', 'enterprise');

-- Must return the revision
SELECT version_num FROM alembic_version
  WHERE version_num IN ('007_rename_plan_values', '008_org_seat_pricing');

-- Must show new columns
SELECT column_name FROM information_schema.columns
  WHERE table_name = 'organizations'
    AND column_name IN ('base_seats_included', 'seat_price_cents', 'base_price_cents');

SELECT column_name FROM information_schema.columns
  WHERE table_name = 'subscriptions' AND column_name = 'price_cents';
```

Manual smoke test:
- [ ] `GET /api/auth/me` returns `"entitlements": [...]` array
- [ ] Free user: entitlements = `["chat_enabled"]` (if BETA_MODE=false)
- [ ] Pro user: `byok_enabled` in entitlements, `team_seats` NOT in entitlements
- [ ] Studio user: all 6 features present

## Sibling Change Coordination

### fix-rate-limit-architecture

- **Shared file**: `apps/api/app/core/rate_limiter.py`
- **This change**: renamed `RATE_LIMIT_TIERS` keys `"base"` → `"pro"`, `"enterprise"` → `"studio"`
- **Coordination**: `fix-rate-limit-architecture` must be rebased onto this change AFTER merge.
  Any reference to `"base"` or `"enterprise"` keys in that branch's rate limiter changes will conflict.
- **Owner action**: reviewer of fix-rate-limit-architecture must verify `RATE_LIMIT_TIERS` uses `pro`/`studio` keys.

### byok-plan-gate

- **Shared files**: `apps/web/src/app/configuracion/page.tsx`, `apps/web/src/lib/auth/AuthContext.tsx`
- **This change**: added `FeatureGate` wrapping BYOK/apikeys tab; added `useHasFeature` hook to AuthContext
- **Coordination**: byok-plan-gate should NOT re-implement FeatureGate or useHasFeature — use what was shipped here.
  If byok-plan-gate landed first, merge carefully: keep this change's `FeatureGate` implementation.
- **Owner action**: reviewer must confirm no duplicate feature-gating logic.
