# Verification Report

**Change**: frontend-export-buttons  
**Mode**: Standard  
**Date**: 2026-04-22

---

## Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 6 |
| Tasks complete | 6 |
| Tasks incomplete | 0 |

All tasks in `openspec/changes/frontend-export-buttons/tasks.md` are checked off.

---

## Build & Tests Execution

**Targeted tests**: ✅ 23 passed / 0 failed  
Command: `npm test -- src/lib/export/__tests__/downloadBlob.test.ts src/app/__tests__/export-conversation.test.tsx src/app/buscar/__tests__/export-search.test.tsx`

Breakdown:
- `downloadBlob.test.ts`: 15 passed
- `export-conversation.test.tsx`: 4 passed
- `export-search.test.tsx`: 4 passed

**Full web suite**: ✅ Baseline preserved  
Command: `npm test`
- Result: 262 passed / 15 failed / 0 skipped
- The 15 failures are the same pre-existing auth/onboarding redirect failures described in the verification brief.

**TypeScript**: ✅ No new changed-file errors  
Command: `npm exec tsc -- --noEmit`
- Output only reports the pre-existing excluded error:
  - `src/components/trials/AddCardModal.tsx(25,48): error TS2554: Expected 2 arguments, but got 3.`

**ESLint**: ✅ No new warnings in changed export code  
Command: `npm run lint -- src/lib/export/downloadBlob.ts src/lib/export/__tests__/downloadBlob.test.ts src/app/chat/components/ChatHeader.tsx src/app/page.tsx src/app/buscar/page.tsx src/app/__tests__/export-conversation.test.tsx src/app/buscar/__tests__/export-search.test.tsx`
- 10 warnings reported, all pre-existing hook/unused-var warnings in `src/app/page.tsx` and `src/app/buscar/page.tsx`
- No lint errors
- No warnings on the new helper/tests or on the new export handler lines

**Coverage**: ➖ Not run (no threshold/config required for this change)

---

## Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| FE-EXP-CHAT | Active conversation exported successfully | `src/app/__tests__/export-conversation.test.tsx > shows export button after conversation loads and calls downloadBlob on success` | ⚠️ PARTIAL |
| FE-EXP-CHAT | Active conversation export fails | `src/app/__tests__/export-conversation.test.tsx > shows error toast when backend returns non-OK status` | ⚠️ PARTIAL |
| FE-EXP-CHAT | No active conversation or empty conversation | `src/app/__tests__/export-conversation.test.tsx > does not show export button when there are no messages` | ❌ FAILING |
| FE-EXP-CHAT | User lacks PDF export feature entitlement | `src/app/__tests__/export-conversation.test.tsx > shows UpsellModal and sends no request when pdf_export entitlement is missing` | ✅ COMPLIANT |
| FE-EXP-BUSCAR | Search results exported successfully | `src/app/buscar/__tests__/export-search.test.tsx > shows export button after search and calls downloadBlob with correct ?q= param` | ✅ COMPLIANT |
| FE-EXP-BUSCAR | Empty search results | `src/app/buscar/__tests__/export-search.test.tsx > does not show export button when there are no search results` | ✅ COMPLIANT |
| FE-EXP-BUSCAR | Search results export fails | `src/app/buscar/__tests__/export-search.test.tsx > shows error toast when backend returns non-OK status` | ⚠️ PARTIAL |
| FE-EXP-BUSCAR | User lacks PDF export entitlement | `src/app/buscar/__tests__/export-search.test.tsx > shows UpsellModal and sends no export request when pdf_export entitlement is missing` | ✅ COMPLIANT |
| FE-EXP-HELPER | Download blob using helper | `src/lib/export/__tests__/downloadBlob.test.ts` | ✅ COMPLIANT |
| FE-EXP-TESTS | Blob helper unit tested | `src/lib/export/__tests__/downloadBlob.test.ts` | ✅ COMPLIANT |
| FE-EXP-TESTS | Chat export integration tested | `src/app/__tests__/export-conversation.test.tsx` | ✅ COMPLIANT |
| FE-EXP-TESTS | Buscar export integration tested | `src/app/buscar/__tests__/export-search.test.tsx` | ✅ COMPLIANT |
| FE-EXP-NFR | Code quality maintained | test + tsc + eslint evidence | ✅ COMPLIANT |

**Compliance summary**: 9 compliant / 3 partial / 1 failing

---

## Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| FE-EXP-CHAT | ❌ Partial implementation | Request, helper, toast, spinner, and entitlement gate exist, but the button is rendered from `hasMessages` only and stays enabled when `currentConversationId` is null. Visible label is also `Exportar`, not `Exportar conversación`. |
| FE-EXP-BUSCAR | ✅ Implemented | Uses `authFetch` with `GET /api/export/search-results/pdf?q=...`, reuses helper, gates with `useHasFeature("pdf_export")` + `UpsellModal`, and hides button when results are empty. |
| FE-EXP-HELPER | ✅ Implemented | `downloadBlob.ts` documents the signature, parses `filename*` + `filename`, and performs create/click/remove/revoke flow. |
| FE-EXP-TESTS | ✅ Implemented | 15 helper tests and 8 integration tests exist and pass. Buscar tests render `BuscarPageWrapper`, preserving the Suspense wrapper. |
| FE-EXP-NFR | ✅ Implemented with caveat | Per-message PDF export path remains wired through `handleDownloadPDF` → `ChatBubble onDownloadPDF`; no new TS errors on changed files; lint warnings observed are pre-existing. |

---

## Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Reuse centralized blob helper | ✅ Yes | Both new export flows call `downloadBlob`. |
| Keep per-message PDF export intact | ✅ Yes | Existing `handleDownloadPDF` and `onDownloadPDF` wiring remain present. |
| Separate design artifact | ➖ N/A | No standalone design artifact was present for this change; verification used spec + tasks + apply-progress. |

---

## Issues Found

### CRITICAL

1. **Chat export button does not satisfy the “no active conversation” requirement**  
   Evidence: `apps/web/src/app/chat/components/ChatHeader.tsx:56-60` renders the button whenever `hasMessages` is true and only disables it while exporting; `currentConversationId` is not part of the render/disable condition. `apps/web/src/app/page.tsx:747-749` passes `currentConversationId`, but `ChatHeader` never uses it. This violates the spec scenario requiring the button to be disabled or absent when the active conversation is null.

2. **Chat export control is hidden on small screens, so the feature is not available across the chat UI**  
   Evidence: `apps/web/src/app/chat/components/ChatHeader.tsx:67` uses `className="hidden sm:flex ..."`, which suppresses the button on mobile viewports. The spec requires the chat export button to be provided in `ChatHeader`; no responsive exclusion is defined.

### WARNING

1. **Visible chat button label does not match the specified label**  
   Evidence: `apps/web/src/app/chat/components/ChatHeader.tsx:75` renders visible text `Exportar`, while the acceptance checklist requires label `Exportar conversación`. The accessible name is corrected only through `aria-label` at `:62-66`.

2. **Chat/search tests do not fully prove all runtime details of the success/error scenarios**  
   Evidence: the passing integration tests assert request/upsell/toast/download behavior, but they do not explicitly assert pending `aria-busy` + spinner states or the development `console.error` path. This leaves those scenario parts validated statically, not behaviorally.

### SUGGESTION

1. Add one chat integration test covering `messages.length > 0` with `currentConversationId === null` to prevent regressions on the missing gate.

---

## Verdict

**FAIL**

The search export flow and helper are in good shape, and all new tests pass, BUT the chat export button still misses a required guard for `currentConversationId === null` and is hidden on mobile. Remediate those gaps before shipping.
