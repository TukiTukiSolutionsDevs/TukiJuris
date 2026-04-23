# Delta Specification: frontend-export-buttons

## Goal
Add UI buttons to export the current chat conversation and semantic search results to PDF. This provides a way to extract value for offline usage, securely downloading documents via existing backend endpoints while gating access with the `pdf_export` feature flag.

## Scope

### In Scope
- Chat page header export button (`/` route).
- Search results toolbar export button (`/buscar` route).
- A reusable blob download primitive.
- Vitest/MSW integration tests for the export behavior on both pages.
- Unit tests for the blob download primitive.

### Out of Scope
- Backend changes.
- Formats other than PDF.
- Modifying the existing per-message PDF export.
- Fixing pre-existing TS errors or ESLint warnings in unrelated parts of the codebase.
- Modifying `/historial`.

## ADDED Requirements

### Requirement: FE-EXP-CHAT — Conversation export button
The system MUST provide a feature-gated button to export the current active chat conversation to a PDF file.

#### Scenario: Active conversation exported successfully
- GIVEN a user has an active conversation with `messages.length > 0`
- AND the user has the `pdf_export` feature entitlement
- WHEN the user clicks "Exportar conversación" in the `ChatHeader`
- THEN the button state changes to pending (`aria-busy="true"`, label changes to "Exportando...", spinner visible)
- AND a POST request is made to `/api/export/conversation/pdf` with `{ conversation_id }` via `authFetch`
- AND on success, the blob is downloaded as a file (filename from `Content-Disposition` or fallback `conversacion-{id}.pdf`)
- AND a success toast "Conversación exportada" is shown.

#### Scenario: Active conversation export fails
- GIVEN a user has an active conversation with `messages.length > 0`
- AND the user has the `pdf_export` feature entitlement
- WHEN the user clicks "Exportar conversación"
- AND the backend returns a non-OK status
- THEN a toast error "No se pudo exportar. Intentá nuevamente." is shown
- AND the error is logged to `console.error` in development
- AND the button returns to its default state.

#### Scenario: No active conversation or empty conversation
- GIVEN the current conversation is null OR `messages.length === 0`
- THEN the export button is disabled or not rendered.

#### Scenario: User lacks PDF export feature entitlement
- GIVEN the user does NOT have the `pdf_export` feature entitlement
- WHEN the user clicks the "Exportar conversación" button
- THEN the `UpsellModal` is displayed
- AND no request is sent to the backend.

### Requirement: FE-EXP-BUSCAR — Search results export button
The system MUST provide a feature-gated button to export search results to a PDF file.

#### Scenario: Search results exported successfully
- GIVEN the user is on `/buscar` with a valid search query and `results.length > 0`
- AND the user has the `pdf_export` feature entitlement
- WHEN the user clicks "Exportar resultados"
- THEN the button state changes to pending (`aria-busy="true"`, spinner visible)
- AND a GET request is made to `/api/export/search-results/pdf?q={query}` via `authFetch`
- AND on success, the blob is downloaded (filename from `Content-Disposition` or fallback `busqueda-{slugified-query}.pdf`)
- AND a success toast is shown.

#### Scenario: Empty search results
- GIVEN the user has no search results (`results.length === 0`) AND no query is in progress
- THEN the export button MUST be hidden.

#### Scenario: Search results export fails
- GIVEN the user clicks "Exportar resultados"
- WHEN the backend returns a non-OK status
- THEN a toast error is shown and logged to console in development.

#### Scenario: User lacks PDF export feature entitlement for search
- GIVEN the user does NOT have the `pdf_export` feature entitlement
- WHEN the user clicks "Exportar resultados"
- THEN the `UpsellModal` is displayed and no request is sent.

### Requirement: FE-EXP-HELPER — Blob download primitive
The system MUST use a centralized primitive for downloading blobs.

#### Scenario: Download blob using helper
- GIVEN a valid `Blob` object
- WHEN `downloadBlob(blob, fallbackFilename, contentDisposition)` is called
- THEN it parses the `Content-Disposition` header for `filename=...` or `filename*=UTF-8''...`
- AND triggers an anchor click using `URL.createObjectURL`
- AND invokes `URL.revokeObjectURL` after triggering the download.

### Requirement: FE-EXP-TESTS — Test coverage
The system MUST include automated tests for the export capabilities.

#### Scenario: Blob helper unit tested
- GIVEN the `downloadBlob` helper
- THEN it MUST be unit-tested to ensure `Content-Disposition` parsing, fallback usage, and `revokeObjectURL` execution.

#### Scenario: Chat export integration tested
- GIVEN the chat page test suite
- THEN it MUST mock `POST /api/export/conversation/pdf` via MSW
- AND assert the success path (anchor click), error path (toast visible), empty state (disabled), and feature-gate path (UpsellModal shown).

#### Scenario: Buscar export integration tested
- GIVEN the search page test suite wrapping `BuscarPageWrapper` with Suspense
- THEN it MUST mock `GET /api/export/search-results/pdf` via MSW
- AND assert the success path, error path, hidden state on empty results, and correct URL param (`q` instead of `query`).

### Requirement: FE-EXP-NFR — Non-functional Requirements
The system MUST maintain code quality and not break existing behaviors.

#### Scenario: Code quality maintained
- GIVEN the changes introduced
- THEN no new TypeScript errors are introduced (ignoring pre-existing `AddCardModal` error)
- AND no new ESLint warnings are introduced in the modified files
- AND no breaking changes are made to the existing per-message PDF export
- AND no public types/exports of unrelated modules are changed.

## Definition of Done
- [ ] `downloadBlob` helper implemented and unit-tested.
- [ ] "Exportar conversación" button added to `/` and tested via MSW.
- [ ] "Exportar resultados" button added to `/buscar` and tested via MSW.
- [ ] Feature gate `pdf_export` and `UpsellModal` consistently applied to both buttons.
- [ ] Loading and error states handled via ARIA attributes, inline spinners, and Sonner toasts.
- [ ] Query parameter strictly uses `?q=` in search export.
- [ ] No new TS/ESLint issues.

## Test Matrix
| Test File | AC IDs Covered |
|-----------|----------------|
| `apps/web/src/lib/export/__tests__/downloadBlob.test.ts` | FE-EXP-HELPER, FE-EXP-TESTS |
| `apps/web/src/app/__tests__/export-conversation.test.tsx` | FE-EXP-CHAT, FE-EXP-TESTS |
| `apps/web/src/app/buscar/__tests__/export-search.test.tsx`| FE-EXP-BUSCAR, FE-EXP-TESTS |

## Dependencies
- **Files to touch**: 
  - `apps/web/src/app/page.tsx`
  - `apps/web/src/app/chat/components/ChatHeader.tsx`
  - `apps/web/src/app/buscar/page.tsx`
  - `apps/web/src/lib/export/downloadBlob.ts` (create)
  - Test files
- **Files to read**: 
  - `notificaciones/__tests__/page.test.tsx` (for MSW+Auth pattern)
  - `analytics/page.tsx` (for blob download and loading state precedent)

## Rollout/Rollback
- **Rollout**: Deploy frontend normally. No data migration.
- **Rollback**: Revert the commit that adds the buttons and helpers.
