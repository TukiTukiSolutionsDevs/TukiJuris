# Tasks: Frontend Config Quick Wins (Sprint 8a)

## Phase 1: Memory settings

- [x] 1.1 **FE-MEM-SETTINGS** — Add lazy `GET/PUT /api/memory/settings`, optimistic toggles, spinner, disabled notice, and revert flow in `apps/web/src/app/configuracion/page.tsx`; add MSW coverage in `apps/web/src/app/configuracion/__tests__/memory-settings.test.tsx`. **AC IDs:** FE-MEM-SETTINGS, FE-QW-TESTS. **DoD:** Memoria tab fetches once on activation, toggles toast/revert correctly, memory list stays visible. **Dependencies:** none.

## Phase 2: Dynamic providers and free models

- [x] 2.1 **FE-LLM-PROVIDERS** — Extract `PROVIDER_LABELS` to `apps/web/src/app/configuracion/provider-labels.ts`, merge backend providers/free models into `apps/web/src/app/configuracion/page.tsx`, and keep hardcoded fallback with dev-only warnings; test success, unknown provider, and fetch fallback in `apps/web/src/app/configuracion/__tests__/llm-providers.test.tsx`. **AC IDs:** FE-LLM-PROVIDERS, FE-QW-TESTS. **DoD:** backend data renders with label overlay, unknown IDs degrade safely, no error toast on fallback. **Dependencies:** none.

## Phase 3: Browse stats strip

- [x] 3.1 **FE-KB-STATS-STRIP** — Fetch `GET /api/documents/stats` in `apps/web/src/app/buscar/page.tsx`, render loading skeleton and compact stats pill only in browse mode, and hide silently on error; cover success, loading, and hidden-on-failure in `apps/web/src/app/buscar/__tests__/kb-stats-strip.test.tsx`. **AC IDs:** FE-KB-STATS-STRIP, FE-QW-TESTS. **DoD:** strip shows `documentos · fragmentos`, skeleton appears while pending, failures leave no visible error. **Dependencies:** none.

## Phase 4: Admin knowledge endpoint swap

- [x] 4.1 **FE-ADMIN-KB-SWAP** — Update `apps/web/src/app/admin/page.tsx` to call `/api/admin/knowledge`, map optional `KBHealthData` fields defensively, and fall back to `/api/health/knowledge` on non-ok/403 without toast; verify primary + fallback paths in `apps/web/src/app/admin/__tests__/knowledge-endpoint.test.tsx`. **AC IDs:** FE-ADMIN-KB-SWAP, FE-QW-TESTS. **DoD:** admin data loads from preferred endpoint, optional fields do not crash rendering, unauthorized fallback preserves prior behavior. **Dependencies:** none.

## Phase 5: Verification

- [x] 5.1 **Verification sweep** — Run the four new/updated Vitest suites plus related smoke coverage for `configuracion`, `buscar`, and `admin`, then run `tsc` and ESLint on changed frontend files. **AC IDs:** FE-QW-TESTS, FE-QW-NFR. **DoD:** all targeted tests pass and no new TypeScript/ESLint issues are introduced. **Dependencies:** 1.1, 2.1, 3.1, 4.1.

## Remediation batch (2026-04-23) — post-verify CRITICAL+WARN fixes

- [x] R1 **Memory settings contract drift** — Renamed `auto_extraction_enabled` → `auto_extract` throughout `configuracion/page.tsx` (interface, PUT body, all JSX refs). Changed success toast to "Configuración actualizada" and error toast to "No se pudo actualizar la configuración". Updated `memory-settings.test.tsx` to assert exact toast strings and `auto_extract` body key. Backend confirmed field is `auto_extract` (`apps/api/app/api/routes/memory.py`).
- [x] R2 **LLM providers + free models integration** — Replaced single `authFetch` with `Promise.all([/api/keys/llm-providers, /api/keys/free-models])`. Added `FreeModel` interface and `freeModels` state. Computed `renderedProviderIds` from `backendProviders` (fallback to `PROVIDER_ORDER`). Provider selector now iterates `renderedProviderIds` with `labelForProvider(id, backendName)` overlay. `allModels` merges `MODEL_CATALOG` + `freeModels`. Lint warning for `backendProviders unused` resolved. Updated `llm-providers.test.tsx`: LP-2 asserts both endpoints fetched + unknown backend provider renders; LP-3 asserts graceful fallback when both fail.
- [x] R3 **KB stats strip wording + legacy counter** — Removed legacy `allDocs.length` counter from browse-mode header. Changed strip copy from `" docs · "` to `" documentos · "`. Updated `kb-stats-strip.test.tsx` KB-1b to assert `"documentos"`.
- [x] R4 **tasks.md checkboxes** — All original tasks marked `[x]`. This remediation section appended.
- [x] R5 **backendProviders unused lint warning** — Resolved by R2 (variable now used in rendering).
- [x] R6 **Tests prove weaker behavior** — Addressed by R1/R2/R3 test updates: exact toast strings, `auto_extract` body key, both endpoints called, unknown backend provider renders, `"documentos"` copy.
