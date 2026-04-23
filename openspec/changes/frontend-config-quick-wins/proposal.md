# Proposal: Frontend Config Quick Wins (Sprint 8a)

## Intent
Connect existing backend endpoints to the UI to resolve four key gaps: enabling memory configuration toggles, dynamically fetching LLM providers and free models, displaying knowledge base statistics, and using the correct admin endpoint for system health.

## Scope

### In Scope
- M1: Two toggle checkboxes at the top of the Memoria tab in `/configuracion` (`memory_enabled`, `auto_extract`).
- M3: Dynamically fetch `GET /api/keys/llm-providers` and `GET /api/keys/free-models` in `/configuracion`, merging them with the local `PROVIDER_LABELS` branding overlay.
- M4: A stats strip at the top of `/buscar` browse-mode (`{total_documents} documentos · {total_chunks} fragmentos`), replacing the client-side counter.
- M6: Swap `/api/health/knowledge` to `/api/admin/knowledge` in `admin/page.tsx`'s data loader.

### Out of Scope
- Sprint 8b tasks: billing, org switcher, admin invoices, trial retry banner (M7, M8, M9, L5).
- File upload list endpoint or UI (L2).
- Structural refactors of the configuration page beyond these 4 touches.
- Fixing `AddCardModal.tsx` pre-existing failing tests or ESLint warnings.

## Capabilities

### New Capabilities
- `configuration-management`: Interface for managing user preferences including AI providers and memory settings.
- `knowledge-discovery`: Interface for browsing and viewing statistics of the user's knowledge base.
- `admin-monitoring`: Administrative tools for viewing system health and metrics.

### Modified Capabilities
None

## Approach
- **M1**: Use optimistic UI with `PUT /api/memory/settings` triggered on toggle changes within the Memoria tab. Show `sonner` toasts on success/error and revert state on failure. Leave memory list visible even if `memory_enabled` is false (add notice).
- **M3**: Fetch providers and free-models on config page mount. Merge with `PROVIDER_LABELS` to retain UI aesthetics. Fall back gracefully (no toasts) to hardcoded lists if fetches fail or providers are unmapped.
- **M4**: Fetch `GET /api/documents/stats` on `/buscar` mount. Show a skeleton pill during loading and hide the strip gracefully on failure.
- **M6**: Direct URL string replacement in the admin page's fetch call. Extend `KBHealthData` type if extra fields are detected. Silent fallback to the health endpoint if unauthorized.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/web/src/app/configuracion/page.tsx` | Modified | Adds memory toggles and dynamic AI provider/model fetching. |
| `apps/web/src/app/buscar/page.tsx` | Modified | Replaces static document count with fetched backend KB stats. |
| `apps/web/src/app/admin/page.tsx` | Modified | Swaps the knowledge endpoint URL. |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Unmapped LLM Provider | Med | Render unknown provider IDs with a generic label fallback to avoid UI crashes. |
| Admin Knowledge Endpoint Unauthorized | Low | Silent fallback to `/api/health/knowledge` if the admin fetch fails (e.g., missing specific admin perm). |
| API downtime during config load | Low | Fallback to hardcoded `LLM_PROVIDERS` on fetch failure, without blocking rendering. |

## Rollback Plan
Revert the modifications in `page.tsx` files via `git revert`. Because no backend schemas are modified, restoring the frontend directly rolls back these visual features without data loss or corruption.

## Dependencies
- Backend endpoints must be accessible (`/api/memory/settings`, `/api/keys/llm-providers`, `/api/keys/free-models`, `/api/documents/stats`, `/api/admin/knowledge`).

## Success Criteria
- [ ] Users can toggle `memory_enabled` and `auto_extract` successfully via the UI.
- [ ] The configuration UI displays LLM providers and free models accurately fetched from the API.
- [ ] The `/buscar` page accurately shows dynamic counts of documents and chunks without crashing.
- [ ] The admin dashboard successfully fetches from `/api/admin/knowledge` without breaking existing health visualizations.