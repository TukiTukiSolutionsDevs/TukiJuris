# SDD Explore — frontend-export-buttons

**Date**: 2026-04-22  
**Change**: frontend-export-buttons  
**Scope**: H3 (chat page export) + H4 (buscar page export)

---

## 1. Backend Endpoint Verification

### H3 — POST /api/export/conversation/pdf ✅ EXISTS

| Field | Value |
|-------|-------|
| Method | POST |
| Path | `/api/export/conversation/pdf` |
| Auth | `get_current_user` (Bearer token required) |
| Rate-limit | WRITE bucket |
| Request body | `{ "conversation_id": "<UUID>" }` |
| Response | `StreamingResponse` — `application/pdf` |
| Content-Disposition | `attachment; filename="conversacion-tukijuris-YYYYMMDD.pdf"` (backend sets it) |
| Ownership guard | Filters by `user_id` — returns 404 for non-owners |
| File | `apps/api/app/api/routes/export.py` L110–188 |

### H4 — GET /api/export/search-results/pdf ✅ EXISTS

| Field | Value |
|-------|-------|
| Method | GET |
| Path | `/api/export/search-results/pdf` |
| Auth | `get_current_user` (Bearer token required) |
| Rate-limit | READ bucket |
| Query params | `q` (required, non-empty), `area` (optional, default "general"), `limit` (optional, default 20, max 50) |
| Response | `StreamingResponse` — `application/pdf` |
| Content-Disposition | `attachment; filename="busqueda-tukijuris-YYYYMMDD.pdf"` (backend sets it) |
| File | `apps/api/app/api/routes/export.py` L196–261 |

> ⚠️ **CRITICAL PARAM MISMATCH**: Audit scope specified `?query=...` — actual backend param is `?q=...`. Frontend MUST use `q`.

**No hard blockers — both endpoints exist and are fully functional.**

---

## 2. Frontend Page Inventory

### H3 — Chat page

| Item | Value |
|------|-------|
| Route | `/` (root — NOT `/chat`) |
| File | `apps/web/src/app/page.tsx` |
| Component | `ChatPage` (wrapped in `Suspense` → exported as `Home`) |
| Fetch helper | `authFetch` from `useAuth()` ✅ |
| Key state | `currentConversationId: string \| null`, `messages: Message[]`, `isLoading: boolean` |
| Feature gate | `hasPdfExport = useHasFeature("pdf_export")` — already in file (L81) |
| Upsell pattern | `setUpsellFeature("pdf_export")` → `<UpsellModal>` (L876) |
| Existing PDF export | `handleDownloadPDF` (L312–355) — per-message consultation export via `POST /api/export/consultation/pdf` — different endpoint |
| Header component | `ChatHeader` — receives `currentConversationId` prop, has right-side action area |
| Button location | `ChatHeader` right-side actions area, shown only when `currentConversationId !== null && messages.length > 0` |

### H4 — Buscar page

| Item | Value |
|------|-------|
| Route | `/buscar` |
| File | `apps/web/src/app/buscar/page.tsx` |
| Component | `BuscarPage` (wrapped in `Suspense` → exported as `BuscarPageWrapper`) |
| Fetch helper | `authFetch` from `useAuth()` ✅ |
| Key state | `query: string`, `results: SearchResult[]`, `searched: boolean`, `loading: boolean` |
| Button location | Results toolbar (L769–795) alongside sort dropdown — only when `searched && results.length > 0 && query.trim()` |

---

## 3. Existing Test Patterns

**No tests exist** for `/` (chat) or `/buscar` pages — full test infrastructure must be created.

Established pattern from `notificaciones/__tests__/page.test.tsx`:

```typescript
// 1. Hoist mock refs
const { mockAuthFetch } = vi.hoisted(() => ({ mockAuthFetch: vi.fn() }));

// 2. Module mocks before import
vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ authFetch: mockAuthFetch, user: { id: "user-1", ... }, ... }),
  useHasFeature: () => true, // or per-test
}));
vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }) => <div data-testid="app-layout">{children}</div>,
}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

// 3. beforeEach: reset + forward authFetch to native fetch → MSW intercepts
beforeEach(() => {
  mockAuthFetch.mockReset();
  mockAuthFetch.mockImplementation((url, init) => fetch(url, init));
  server.use(/* default handlers */);
});

// 4. MSW handler overrides per test
server.use(http.post("/api/export/conversation/pdf", () => new HttpResponse(...)));
```

MSW server import: `import { server } from "@/test/msw/server"`  
DOM blob mocking: `URL.createObjectURL` and `URL.revokeObjectURL` must be mocked in tests.

---

## 4. Design Precedents

### Blob download pattern (project-standard)

Established in both `analytics/page.tsx` and `page.tsx` (chat):

```typescript
const blob = await res.blob();
const url = URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = "fallback-filename.pdf"; // browser prefers Content-Disposition
document.body.appendChild(a);
a.click();
a.remove();
URL.revokeObjectURL(url);
```

### Toast system: **sonner**

```typescript
import { toast } from "sonner";
toast.error("Error al generar el PDF. Intenta nuevamente.");
toast.success("PDF descargado.");
```
`<Toaster>` already mounted in root `apps/web/src/app/layout.tsx` L73.

### Loading state pattern

From `analytics/page.tsx`:
```typescript
const [exporting, setExporting] = useState(false);
// button: disabled={exporting}
// label: {exporting ? "Exportando..." : "Exportar PDF"}
```
No spinner component used — text change only.

---

## 5. Open Questions — Resolved Defaults

| # | Question | Recommended Default |
|---|----------|---------------------|
| OQ1 | Button location in `/` (chat) | Right side of `ChatHeader`, after `#conv-id` chip. Only rendered when `currentConversationId !== null && messages.length > 0`. Passes through `hasPdfExport` gate + UpsellModal. |
| OQ2 | Button location in `/buscar` | Results toolbar (same row as sort dropdown), right-aligned. Only rendered when `searched && !loading && results.length > 0`. |
| OQ3 | Download method | blob + `URL.createObjectURL` + anchor click — already the project standard. |
| OQ4 | Error UX | `toast.error()` from sonner — project-standard toast system. **Upgrade from existing silent-fail** in chat's per-message export. |
| OQ5 | Loading state | `disabled={exporting} aria-busy={exporting}` + label change to "Exportando..." — no spinner needed (follows existing pattern). |
| OQ6 | Filename | Backend sets `Content-Disposition` header with correct filename — frontend sets matching `a.download` as fallback. |

---

## 6. Risks

| Severity | Risk | Mitigation |
|----------|------|------------|
| 🔴 CRITICAL | **Param name mismatch**: spec says `?query=`, backend expects `?q=` | Use `q` in frontend. Tests should assert correct param. |
| 🟡 MEDIUM | **Feature gate scope**: `hasPdfExport` already guards per-message PDF — conversation export must check same flag or it creates a gap | Use same `useHasFeature("pdf_export")` + `UpsellModal` pattern for H3. |
| 🟡 MEDIUM | **Empty conversation edge case**: `currentConversationId` set but `messages.length === 0` — backend returns valid (empty) PDF or 404? | Disable button when `messages.length === 0`. |
| 🟡 MEDIUM | **No existing tests for chat or buscar pages** — full mock+MSW infrastructure from scratch | Follow notificaciones pattern exactly. Mock `URL.createObjectURL`. |
| 🟡 MEDIUM | **`BuscarPage` uses `useSearchParams`** — must wrap in `Suspense` in tests or render outer `BuscarPageWrapper` | Render `BuscarPageWrapper` directly in tests (already has Suspense). |
| 🟢 LOW | Large conversation timeout | No streaming on frontend; single blob fetch — add no special handling for now. |
| 🟢 LOW | Auth guard on both endpoints | `authFetch` handles 401 automatically via refresh flow. |
| 🟢 LOW | Buscar button shows in browse mode (no search, all docs listed) | Condition on `searched` flag — already tracked. |

---

## 7. Files to Create / Modify

### H3 — Chat export button

| Action | File |
|--------|------|
| Modify | `apps/web/src/app/page.tsx` — add `handleExportConversation`, pass prop to `ChatHeader` |
| Modify | `apps/web/src/app/chat/components/ChatHeader.tsx` — add `onExportConversation` prop + button |
| Create | `apps/web/src/app/__tests__/export-conversation.test.tsx` |

### H4 — Buscar export button

| Action | File |
|--------|------|
| Modify | `apps/web/src/app/buscar/page.tsx` — add `handleExportSearchResults` + export button in toolbar |
| Create | `apps/web/src/app/buscar/__tests__/export-search.test.tsx` |

---

## 8. Artifact References

- **Engram topic**: `sdd/frontend-export-buttons/explore`
- **OpenSpec file**: `openspec/changes/frontend-export-buttons/explore.md`
- **Backend source**: `apps/api/app/api/routes/export.py`
- **Backend tests**: `apps/api/tests/integration/test_export.py`
