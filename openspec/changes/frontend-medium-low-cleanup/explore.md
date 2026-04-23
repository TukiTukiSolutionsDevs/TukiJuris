# Explore: frontend-medium-low-cleanup (Sprint 8 + 9 unified)

**Date**: 2026-04-23  
**HEAD**: 13c6ceb  
**Status**: completed

---

## Verification Results

| Gap | Verdict |
|-----|---------|
| M2 — Bell → /notificaciones | ✅ CONFIRMED CLOSED — AppSidebar.tsx:384 `href="/notificaciones"`, AdminSidebar.tsx:55 same |
| L1 — lib/api.ts deleted | ✅ CONFIRMED CLOSED — file does not exist |
| L3 — /api/v1 no UI | ✅ OUT OF SCOPE — intentional third-party API, not a gap |
| M5 — /api/billing/daily-usage | ✅ OUT OF SCOPE — backend endpoint doesn't exist |
| L4 — documents/search vs search/advanced | ✅ NOOP — different purposes (chunk BM25 vs document semantic); document and close |

---

## Per-Gap Analysis

### M1 — Memory Settings (`GET/PUT /api/memory/settings`) — **REAL GAP**

**Backend shape** (`apps/api/app/api/routes/memory.py`):
- `GET /api/memory/settings` → `{ memory_enabled: bool, auto_extract: bool }`
- `PUT /api/memory/settings` → body `{ memory_enabled?: bool, auto_extract?: bool }`
- Persisted in `user.preferences` JSONB column

**Frontend gap** (`apps/web/src/app/configuracion/page.tsx`):
- `memoryEnabled` state exists (line 403) but is NEVER connected to the API
- No fetch on tab mount, no save on toggle
- UI shows memory list, toggle-per-item, bulk-delete — all working
- **Missing**: two global toggles (enable memory + auto-extract) at the top of the "Memoria" tab

**UI target**: `/configuracion` → "Memoria" tab → top of `DisclosureCard`  
**Approach**: `useEffect` when `activeTab === "memoria"` fetches settings; two `<Switch>`/`<input type="checkbox">` toggles; `PUT` on change  
**Effort**: **S** — ~50 lines + 2 Vitest tests  
**Risk**: none — independent of the memory list logic below it

---

### M3 — `/api/keys/llm-providers` + `/api/keys/free-models` — **REAL GAP**

**Backend shape** (`apps/api/app/api/routes/api_keys.py`):
- `GET /api/keys/llm-providers` → live list from `get_available_providers()`, no auth required
- `GET /api/keys/free-models` → `{ models: [...], daily_limit: N, enabled: bool }`, no auth required

**Frontend gap** (`apps/web/src/app/configuracion/page.tsx`):
- `LLM_PROVIDERS` const (lines 252–321): hardcoded 6 providers with model names like `"GPT-5.4 Nano ($0.20/M)"` — stale risk
- `MODEL_CATALOG` imported from `@/lib/models` — also static

**Decision**:
- Fetch `/api/keys/free-models` on mount to dynamically show which models are platform-provided
- Fetch `/api/keys/llm-providers` to ensure provider list is authoritative (not showing removed providers)
- **KEEP** local `LLM_PROVIDERS` as UI branding overlay (accent colors, docsUrl, description) and MERGE by `id` — the BE doesn't return UI-only fields
- **GOTCHA**: Local branding constants must stay; the live endpoint only adds/removes providers from the list — it doesn't supply visual metadata

**UI target**: `/configuracion` → "Preferencias" tab (provider selector) + "API Keys" tab (provider cards)  
**Effort**: **S** — ~60 lines + 2 tests  
**Risk**: low — purely additive; fallback to hardcoded list if fetch fails

---

### M4 — `/api/documents/stats` — **REAL GAP**

**Backend shape** (`apps/api/app/api/routes/documents.py` lines 100–106):
```python
GET /api/documents/stats → KBStats { total_documents: int, total_chunks: int, chunks_by_area: dict[str, int] }
```
No auth required.

**Frontend gap** (`apps/web/src/app/buscar/page.tsx`):
- Fetches full `GET /api/documents/` list to show `allDocs.length` (line 899–904)
- `/api/documents/stats` is NEVER called
- The browse-mode counter shows a raw count from the client-side array

**UI target**: Replace "X documentos en la base de conocimiento" with server-side stats strip: `"237 documentos · 4,891 chunks"`. Could also show top area breakdown.  
**Approach**: Single `useEffect` on mount; replace count display; optionally small stats pills per area  
**Effort**: **XS** — ~30 lines + 1 test  
**Risk**: none — additive display only

---

### M6 — `/api/admin/knowledge` swap — **REAL GAP (minor)**

**Backend**:
- Currently used: `GET /api/health/knowledge` (public endpoint, no auth)
- Available: `GET /api/admin/knowledge` — admin-only, "Detailed knowledge base stats: chunks by area, doc breakdown, embedding coverage"

**Frontend** (`apps/web/src/app/admin/page.tsx` line 191):
- Calls `authFetch("/api/health/knowledge")` — a **public** endpoint being called from a private admin view
- Sets `kbHealth` state with `chunks_by_area` and `embedding_coverage` — both work correctly

**Decision**: Swap to `/api/admin/knowledge`. The admin page already uses `require_admin`-gated endpoints for all other data. Using a public health endpoint in an admin view is architecturally inconsistent and may diverge from the richer admin endpoint over time.  
**Risk**: Response shapes should be compatible. May need to extend `KBHealthData` TS type if admin returns extra fields.  
**Effort**: **XS** — 1-line URL change + possibly 1 type update + 1 test  

---

### M7 — Org switcher in analytics — **REAL GAP**

**Backend**: `GET /api/organizations/` already called; returns list.

**Frontend gap** (`apps/web/src/app/analytics/page.tsx` lines 410–414):
```ts
if (orgs.length > 0) { setOrgId(orgs[0].id) }  // hardcoded first org
```
No multi-org switcher. If the user belongs to >1 org, analytics always shows org[0].

**Billing page** (`apps/web/src/app/billing/page.tsx` line 154): same pattern `const oid = orgs[0].id`.

**UI approach**:
- Add `useState<{id: string; name: string}[]>` for all orgs
- If `orgs.length > 1`: show a `<select>` or pill group above the tab bar
- Persist selection in `localStorage` key `pref_analytics_org_id`
- Flag billing page for same pattern (apply in same batch or follow-up)

**Effort**: **S** — ~65 lines in analytics + flag comment in billing. If billing included too: ~100 lines + 3 tests

---

### M8 — PATCH `/api/admin/invoices/{id}` — **REAL GAP**

**Backend shape** (`apps/api/app/api/routes/admin_invoices.py`):
- `GET /api/admin/invoices` → paginated list, filters: `status`, `org_id`
- `GET /api/admin/invoices/{id}` → single invoice
- `PATCH /api/admin/invoices/{id}` → `{ action: "refund" | "void", reason?: string }` → `InvoiceOut`
- Guards: `require_admin` + `billing:update` permission

**InvoiceOut fields** (`apps/api/app/schemas/invoice.py`):
`id, org_id, status, base_amount, seat_amount, subtotal_amount, tax_amount, total_amount, items[]`

**Frontend gap** (`apps/web/src/app/admin/page.tsx`):
- Admin page has tabs: "resumen" + "auditoria"
- `hasPermission("billing:read") && <RevenueCards />` exists but no invoice management table
- The PATCH endpoint is entirely unused

**UI approach**: Add new "Facturas" tab to admin page:
1. Paginated table: fecha | org | estado | total_amount
2. Status filter dropdown
3. Row action menu ("Reembolsar" / "Anular") → confirmation modal → `PATCH`
4. Gate entire tab behind `hasPermission("billing:update")`

**Effort**: **M** — ~150 lines + 4 tests  
**Risk**: Medium — involves confirmation modal, RBAC gating, pagination, error states

---

### M9 — POST `/api/trials/{trial_id}/retry-charge` — **REAL GAP**

**Backend shape** (`apps/api/app/api/routes/trials.py` lines 113–122):
- `POST /api/trials/{trial_id}/retry-charge` — user-initiated, 72-hour retry window
- Also: `GET /api/trials/me` → current trial or null
- `TrialResponse` shape includes `status` field

**Frontend gap**: No trial UI exists anywhere. `GET /api/trials/me` is never called.

**UI approach** in `/billing` page:
1. On mount: `GET /api/trials/me`
2. If `trial.status === "charge_failed"`: warning banner above plan cards:  
   _"Tu cobro de prueba falló. Podés reintentar dentro de las próximas 72 horas."_  
   + "Reintentar cobro" button → `POST /api/trials/{id}/retry-charge`
3. Success/error feedback via sonner toast
4. Conditionally rendered — invisible when no failed charge

**Effort**: **S** — ~70 lines + 2 tests  
**Risk**: Low — conditional UI, no impact on existing billing page when trials are off

---

### L2 — `/api/upload/{doc_id}` GET + DELETE — **DEFERRED**

**Backend** (`apps/api/app/api/routes/upload.py`):
- `POST /api/upload/` — upload for chat context ✓
- `GET /api/upload/{doc_id}` — get by ID ✓
- `DELETE /api/upload/{doc_id}` — delete by ID ✓
- **MISSING**: `GET /api/upload/` — list endpoint for user's uploaded docs → DOES NOT EXIST

**Frontend gap**: No "my files" UI exists anywhere.

**BLOCKER**: Without a BE list endpoint, the FE cannot render a file manager. You cannot reconstruct a list from per-ID fetches.

**Decision**: **DEFER** — requires BE work first:
1. BE: Add `GET /api/upload/` → paginated list of `UploadedDocument` for current user (~20 BE lines)
2. FE: Add "Mis archivos subidos" `DisclosureCard` in `/configuracion` (~80 FE lines)

Tag as: BE backlog first → FE sprint 9+ follows.

---

### L4 — `/api/documents/search` vs `/api/search/advanced` — **NOOP**

These serve different purposes:
- `GET /api/documents/search?q=&area=&limit=` — chunk-level BM25 keyword search, returns article-granularity fragments, used by RAG/agent pipeline
- `POST /api/search/advanced` — document-level semantic search, rich filters, paginated, used by `/buscar` user-facing page

**Decision**: Not a duplicate. Close without action. Document for future reference.

---

### L5 — `/api/billing/{org_id}/invoices/{invoice_id}` detail — **REAL GAP**

**Backend shape** (`apps/api/app/api/routes/me_invoices.py`):
- `GET /billing/{org_id}/invoices` → `InvoiceListResponse { items, total, page, per_page }`
- `GET /billing/{org_id}/invoices/{id}` → `InvoiceOut`
- Member-only (org membership check)

**Frontend gap** (`apps/web/src/app/billing/page.tsx`):
- NO invoice list exists. `usage` state is fetched but suppressed with `void usage`
- No "payment history" section at all

**UI approach**: Add "Historial de pagos" section below the plan comparison:
1. Fetch `GET /api/billing/{orgId}/invoices` on mount (after orgId resolves)
2. Table: fecha | estado | total_amount
3. Click row → expand inline OR open modal → shows full `InvoiceOut` fields (subtotals, tax, line items)
4. Empty state if no invoices yet

**Effort**: **S** — ~90 lines + 2 tests  
**Risk**: Low — read-only, no mutations

---

## Effort Summary

| Gap | Page | Effort | Notes |
|-----|------|--------|-------|
| M1 | /configuracion (memoria) | S | 2 toggles, fetch settings |
| M3 | /configuracion (preferencias + apikeys) | S | merge live + local branding |
| M4 | /buscar | XS | stats strip, additive |
| M6 | /admin | XS | 1-line URL swap |
| M7 | /analytics (+ /billing flag) | S | org switcher dropdown |
| M8 | /admin (new tab) | M | invoices tab + PATCH modal |
| M9 | /billing | S | trial retry banner |
| L2 | DEFERRED | — | needs BE list endpoint |
| L4 | NOOP | — | document + close |
| L5 | /billing | S | invoice history + detail |

---

## Page Clustering

```
/configuracion  →  M1, M3
/buscar         →  M4
/admin          →  M6, M8
/analytics      →  M7
/billing        →  M9, L5  (+ M7 flag)
```

---

## Recommended Batching

### Sprint 8a — Config + Quick Wins (XS–S, all low-risk)
- **M1**: Memory settings toggles → `/configuracion` memoria tab
- **M3**: Dynamic provider/free-models fetch → `/configuracion` preferencias + apikeys tabs
- **M4**: KB stats strip → `/buscar`
- **M6**: Admin knowledge endpoint swap → `/admin` (1-line + type check)

**Rationale**: All config-page or additive display work. Zero billing risk. Shippable independently. Estimated: 1 session.

### Sprint 8b — Billing + Admin Features (S–M)
- **M7**: Org switcher → `/analytics` (+ flag in `/billing`)
- **M9**: Trial retry-charge banner → `/billing`
- **L5**: Invoice list + detail → `/billing`
- **M8**: Admin invoices tab + PATCH → `/admin` (largest item, schedule last)

**Rationale**: Clusters all billing/admin page work together — same reviewer context, easier E2E testing. Estimated: 1–2 sessions.

### Deferred
- **L2**: Needs BE `GET /api/upload/` list endpoint first — separate BE+FE sprint

---

## Risks

1. **M3 branding merge**: If `GET /api/keys/llm-providers` returns a provider ID not in `PROVIDER_LABELS`, the UI must handle unknown providers gracefully (skip or show generic card).
2. **M6 type mismatch**: `/api/admin/knowledge` may return extra fields not covered by the TS `KBHealthData` type — extend carefully.
3. **M8 RBAC**: Admin invoices tab must respect `hasPermission("billing:update")` — missing this gate is a security issue.
4. **M9 trials disabled**: `TRIALS_ENABLED=false` means `GET /api/trials/me` still works (it's not guarded) but retry-charge returns 503. Handle gracefully.
5. **L5 empty state**: Most users in beta won't have invoices yet — the empty state must not look like an error.
6. **M7 single-org users**: The org switcher must be hidden (not just empty) when the user has exactly 1 org — don't add UI noise for the common case.
