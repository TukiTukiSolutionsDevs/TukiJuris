# Tasks: frontend-export-buttons

## Phase 1: Helper + unit tests

| Task | Description | Files | AC IDs | DoD | Depends |
|---|---|---|---|---|---|
| [x] 1.1 Implement `downloadBlob` helper | Create centralized blob download primitive with `Content-Disposition` parsing (`filename` / `filename*`) and fallback filename support. | `apps/web/src/lib/export/downloadBlob.ts` | FE-EXP-HELPER | Creates object URL, clicks anchor, removes anchor, revokes URL, exports reusable helper. | None |
| [x] 1.2 Unit test helper | Add focused tests for parsed filename, fallback usage, and `URL.revokeObjectURL`. | `apps/web/src/lib/export/__tests__/downloadBlob.test.ts` | FE-EXP-HELPER, FE-EXP-TESTS | Vitest covers `filename`, UTF-8 `filename*`, fallback, and revoke side effect. | 1.1 |

## Phase 2: Chat page export button

| Task | Description | Files | AC IDs | DoD | Depends |
|---|---|---|---|---|---|
| [x] 2.1 Wire chat export action | Add conversation export handler in `/`, reuse helper, gate with `useHasFeature("pdf_export")`, keep empty conversation disabled, and surface toast/error states. | `apps/web/src/app/page.tsx` | FE-EXP-CHAT, FE-EXP-NFR | `POST /api/export/conversation/pdf` sends `{ conversation_id }`, pending UI uses `aria-busy`, success downloads file, failure resets state and shows error toast. | 1.1 |
| [x] 2.2 Add header button UI | Extend `ChatHeader` action area with the export trigger and loading/disabled presentation without breaking current orchestrator actions. | `apps/web/src/app/chat/components/ChatHeader.tsx` | FE-EXP-CHAT, FE-EXP-NFR | Button label switches to `Exportando...`, is hidden/disabled per conversation state, and opens `UpsellModal` path when entitlement is missing. | 2.1 |
| [x] 2.3 Integration test chat export | Add MSW-backed page test for success, backend error, empty conversation, and feature-gated flow. | `apps/web/src/app/__tests__/export-conversation.test.tsx` | FE-EXP-CHAT, FE-EXP-TESTS | Test asserts anchor download, toast error, no-request gate path, and disabled/absent state for empty chat. | 2.1, 2.2 |

## Phase 3: Buscar page export button

| Task | Description | Files | AC IDs | DoD | Depends |
|---|---|---|---|---|---|
| [x] 3.1 Wire buscar export action | Add search-results export handler in `/buscar`, reuse helper, feature-gate with `UpsellModal`, and request `GET /api/export/search-results/pdf?q=...`. | `apps/web/src/app/buscar/page.tsx` | FE-EXP-BUSCAR, FE-EXP-NFR | Button only appears for searched non-empty results, pending state uses `aria-busy`, success downloads, error shows toast, request uses `q` param only. | 1.1 |
| [x] 3.2 Integration test buscar export | Add Suspense-safe MSW test for success, error, hidden empty state, and exact `q` query parameter. | `apps/web/src/app/buscar/__tests__/export-search.test.tsx` | FE-EXP-BUSCAR, FE-EXP-TESTS | Renders `BuscarPageWrapper`, mocks blob APIs, verifies no button when empty and correct backend URL when exporting. | 3.1 |

## Phase 4: Verification

| Task | Description | Files | AC IDs | DoD | Depends |
|---|---|---|---|---|---|
| [x] 4.1 Run targeted verification | Execute web tests for new coverage plus `tsc` and `eslint` on touched files; confirm no regressions to existing per-message PDF export. | Changed files + test suites | FE-EXP-TESTS, FE-EXP-NFR | New tests pass, known pre-existing failures remain unchanged, changed files are TS/ESLint clean. | 1.2, 2.3, 3.2 |

## DAG Summary

- Batch 1 → Batch 2, Batch 3
- Batch 2 → Batch 4
- Batch 3 → Batch 4
- Batch 4 has no downstream dependencies
