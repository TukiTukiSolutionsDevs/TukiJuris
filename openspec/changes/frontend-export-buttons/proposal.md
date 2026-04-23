# Proposal: frontend-export-buttons

## Intent

Add UI controls to allow users to export their current chat conversation and search results to PDF. This provides a way to extract value from the platform for offline usage, leveraging existing backend export endpoints.

## Scope

### In Scope
- Add an "Export" button to the chat page header.
- Add an "Export" button to the search results page toolbar.
- Implement file download using `blob()` and `URL.createObjectURL()`.
- Add loading states (inline spinner) and error handling (`sonner` toast).
- Enforce feature gating (`pdf_export` entitlement) via `UpsellModal` for both buttons.
- Create tests for both page components using MSW.

### Out of Scope
- Modifying backend endpoints.
- Exporting formats other than PDF (e.g., HTML, DOCX).
- Modifying the existing per-message PDF export functionality.
- Touching pre-existing failing tests or ESLint warnings.
- Any actions in the `/historial` folder.

## Capabilities

### New Capabilities
- `pdf-export`: Defines the UI behavior, feature gating, and API integration for exporting chat conversations and search results to PDF format.

### Modified Capabilities
- None

## Approach

We will add the "Export" buttons directly within their respective page components (`apps/web/src/app/page.tsx` for chat and `apps/web/src/app/buscar/page.tsx` for search). Both buttons will use a standard blob download method (`URL.createObjectURL`), feature gate checks (`useHasFeature("pdf_export")` + `UpsellModal`), and `sonner` toasts for error handling. State management for loading will be local to the pages. The search endpoint will explicitly use the `?q=` parameter instead of `?query=`. The feature gate will be applied to the search export as well for consistency.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `apps/web/src/app/page.tsx` | Modified | Add `handleExportConversation` and pass to header |
| `apps/web/src/app/chat/components/ChatHeader.tsx` | Modified | Add Export button to header actions |
| `apps/web/src/app/buscar/page.tsx` | Modified | Add `handleExportSearchResults` and toolbar Export button |
| `apps/web/src/app/__tests__/` | New | Add tests for conversation export |
| `apps/web/src/app/buscar/__tests__/` | New | Add tests for search export |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Parameter mismatch for search endpoint | High | Hardcode explicitly `?q=` in the fetch call, enforce with tests. |
| Feature gate inconsistency | Medium | Apply the same `useHasFeature("pdf_export")` gate and `UpsellModal` to both export functions. |
| Empty states causing errors | Medium | Disable the chat export button when `messages.length === 0`. Hide the search export button when `results.length === 0`. |

## Rollback Plan

Revert the commits modifying `apps/web/src/app/page.tsx`, `ChatHeader.tsx`, and `apps/web/src/app/buscar/page.tsx`, and delete the newly created test files.

## Dependencies

- Existing backend endpoints (`POST /api/export/conversation/pdf` and `GET /api/export/search-results/pdf`).
- `sonner` for toast notifications.
- `useHasFeature` and `UpsellModal` for feature gating.

## Success Criteria

- [ ] Users can click an export button in the chat header to download the conversation as a PDF.
- [ ] Users can click an export button above search results to download the results as a PDF.
- [ ] Both buttons display an inline spinner and are disabled while exporting.
- [ ] Both features correctly require the `pdf_export` entitlement and show the UpsellModal if missing.
- [ ] Error toasts appear if the export fails.
- [ ] Both features are covered by Vitest/MSW tests.