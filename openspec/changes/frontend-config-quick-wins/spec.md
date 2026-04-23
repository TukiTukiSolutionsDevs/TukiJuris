# Specification: Frontend Config Quick Wins (Sprint 8a)

## Intent
Connect existing backend endpoints to the UI to resolve four key gaps: enabling memory configuration toggles, dynamically fetching LLM providers and free models, displaying knowledge base statistics, and using the correct admin endpoint for system health.

## Domain: Configuration Management

### Requirement: FE-MEM-SETTINGS (Memory Settings Toggles)

The system MUST allow users to toggle memory and auto-extraction settings in the `/configuracion` Memoria tab.

#### Scenario: Lazy-load settings on tab activation
- GIVEN the user navigates to the Memoria tab
- WHEN the tab is activated
- THEN the system MUST fetch `GET /api/memory/settings` via `authFetch`
- AND display a spinner while the request is pending

#### Scenario: Successful setting update
- GIVEN the memory settings are loaded
- WHEN the user clicks the `memory_enabled` or `auto_extract` toggle
- THEN the system MUST trigger `PUT /api/memory/settings` with the updated body `{ memory_enabled, auto_extract }`
- AND show an optimistic UI update
- AND display a "Configuración actualizada" success toast

#### Scenario: Failed setting update
- GIVEN the memory settings are loaded
- WHEN the user toggles a setting and the PUT request fails
- THEN the system MUST revert the optimistic UI update
- AND display a "No se pudo actualizar la configuración" error toast

#### Scenario: Memory disabled state
- GIVEN the `memory_enabled` state is `false`
- WHEN the Memoria tab is displayed
- THEN the system MUST show a notice "La memoria está desactivada" above the memory list
- AND MUST continue to render the existing memory items allowing user deletion

### Requirement: FE-LLM-PROVIDERS (Dynamic LLM Providers)

The system MUST dynamically fetch and display LLM providers and free models in the `/configuracion` view.

#### Scenario: Successful providers and models fetch
- GIVEN the `/configuracion` view is mounted or API Keys/Preferencias tab is activated
- WHEN the system fetches `/api/keys/llm-providers` and `/api/keys/free-models`
- THEN the system MUST merge the backend provider data with the local `PROVIDER_LABELS` overlay map
- AND MUST replace the hardcoded `MODEL_CATALOG` free-tier section with `free-models.models`

#### Scenario: Unknown provider ID gracefully degrades
- GIVEN the backend returns a provider ID not found in `PROVIDER_LABELS`
- WHEN the providers list is rendered
- THEN the system MUST render it with a generic label (e.g., `backendProvider.name || backendProvider.id`)
- AND MUST NOT crash

#### Scenario: Provider fetch failure fallback
- GIVEN the fetch for providers or free models fails
- WHEN the system attempts to render the providers
- THEN the system MUST fall back silently to the hardcoded `LLM_PROVIDERS` constants
- AND MUST log a warning to the console in dev mode
- AND MUST NOT display an error toast

## Domain: Knowledge Discovery

### Requirement: FE-KB-STATS-STRIP (KB Stats Strip)

The system MUST display a compact stats strip at the top of the `/buscar` browse mode.

#### Scenario: Successful stats display
- GIVEN the user is on the `/buscar` browse mode
- WHEN the page mounts
- THEN the system MUST fetch `GET /api/documents/stats` via `authFetch`
- AND MUST format and display the stats as "{total_documents} documentos · {total_chunks} fragmentos"

#### Scenario: Loading state for stats strip
- GIVEN the `GET /api/documents/stats` request is pending
- WHEN the page is rendering
- THEN the system MUST display a skeleton pill (e.g., `animate-pulse bg-gray-200 rounded`)

#### Scenario: Graceful degradation on fetch error
- GIVEN the `GET /api/documents/stats` request fails
- WHEN the page renders
- THEN the system MUST completely hide the stats strip without throwing a user-visible error

## Domain: Admin Monitoring

### Requirement: FE-ADMIN-KB-SWAP (Admin Knowledge Endpoint Swap)

The system MUST use the admin-specific endpoint for knowledge base health in the `/admin` view.

#### Scenario: Successful admin endpoint load
- GIVEN the user navigates to `/admin`
- WHEN the `loadData()` function executes
- THEN the system MUST fetch `GET /api/admin/knowledge` instead of `GET /api/health/knowledge`
- AND MUST render additional fields if present in the extended `KBHealthData` payload

#### Scenario: Fallback on admin unauthorized
- GIVEN the user accesses `/admin` but lacks specific admin scopes
- WHEN `GET /api/admin/knowledge` returns a 403 or non-ok response
- THEN the system MUST silently fall back to `GET /api/health/knowledge`
- AND MUST render the health data as it did previously
- AND MUST NOT show an error toast

## Domain: Quality & Non-Functional

### Requirement: FE-QW-TESTS (Test Coverage)

The system MUST include MSW integration tests for all frontend features introduced.

#### Scenario: MSW Test Coverage
- GIVEN the existing test suites
- WHEN the new features are implemented
- THEN tests MUST cover successful toggle, fetch failures, skeleton rendering, error hiding, and endpoint fallback scenarios following the existing AuthContext wrapper patterns

### Requirement: FE-QW-NFR (Code Quality)

The system MUST NOT introduce any regressions or build warnings.

#### Scenario: Build and Linter
- GIVEN the modified source files
- WHEN the code is compiled and linted
- THEN there MUST NOT be any new TypeScript errors or ESLint warnings
- AND existing functionality MUST NOT break
