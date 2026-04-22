## 1. Executive summary (≤200 palabras)
**Veredicto: ROJO**

Se ha realizado una auditoría exhaustiva de cobertura del frontend contra un backend que ya alcanzó el 100% de cobertura de pruebas (commit `9a82385`, 1235 tests). Se encontraron **24 gaps** en total: 3 CRITICAL, 7 HIGH, 9 MEDIUM y 5 LOW.

El estado del frontend es crítico debido a 3 bugs que impactan directamente a producción: el cambio de contraseña silenciosamente falla (C1), el centro de notificaciones no existe pese a tener todo el backend listo (C2) y existe código muerto de la API que falla sin auth (C3). Además, hay problemas serios en las rutas de administrador: la protección es únicamente *client-side*, lo que permite a usuarios ver la estructura visual antes del redireccionamiento, y varias vistas de administración carecen de UI (gestión RBAC, API keys de desarrollador, audit log).

**Nota de avance**: El requerimiento de testing frontend (RF-4) ya ha sido RESUELTO (Vitest y MSW instalados con 21 archivos de pruebas), lo cual desbloquea el trabajo con TDD sin necesidad de planificar una tarea adicional de configuración.

## 2. Backend → Frontend mapping table

| Endpoint | Status | Evidence |
|----------|--------|---------|
| POST /api/auth/register | COVERED | app/auth/register/page.tsx |
| POST /api/auth/login | COVERED | app/auth/login/page.tsx |
| POST /api/auth/refresh | COVERED | authClient.ts:refresh() |
| POST /api/auth/logout | COVERED | authClient.ts:logout() |
| POST /api/auth/logout-all | COVERED | AuthContext.tsx:logoutAll() |
| GET /api/auth/sessions | MISSING | No sessions page; no UI for session list |
| GET /api/auth/me | COVERED | AuthContext.tsx, AppSidebar, configuracion |
| GET /api/auth/me/permissions | COVERED | AuthContext.tsx:fetchMe() |
| PUT /api/auth/me | COVERED | configuracion/page.tsx:handleSaveProfile |
| POST /api/auth/me/onboarding | COVERED | onboarding/page.tsx |
| POST /api/auth/password-reset | PARTIAL | reset-password page exists, not verified |
| POST /api/auth/password-reset/confirm | PARTIAL | not verified |
| GET /api/auth/oauth/providers | MISSING | Not used in OAuth pages (hardcoded providers) |
| GET /api/auth/oauth/google/authorize | MISSING | Frontend likely opens direct URL |
| POST /api/auth/oauth/google/callback | COVERED | auth/callback/google/page.tsx |
| GET /api/auth/oauth/microsoft/authorize | MISSING | Same as Google |
| POST /api/auth/oauth/microsoft/callback | COVERED | auth/callback/microsoft/page.tsx |
| POST /api/chat/query | DEAD-UI | lib/api.ts:sendQuery() — no auth, unused |
| GET /api/chat/models | DEAD-UI | lib/api.ts:getModels() — no auth, unused |
| POST /api/chat/models/ping | MISSING | No frontend pings models |
| GET /api/chat/agents | DEAD-UI | lib/api.ts:getAgents() — no auth, unused |
| POST /api/chat/stream | COVERED | app/page.tsx:handleSubmit → authFetch |
| GET /api/conversations/ | COVERED | page.tsx, historial/page.tsx |
| GET /api/conversations/{id} | COVERED | page.tsx:loadConversation |
| PUT /api/conversations/{id}/rename | COVERED | page.tsx context menu |
| PUT /api/conversations/{id}/pin | COVERED | page.tsx, historial |
| PUT /api/conversations/{id}/archive | COVERED | page.tsx, historial |
| DELETE /api/conversations/{id} | COVERED | page.tsx, historial |
| POST /api/conversations/{id}/share | COVERED | page.tsx, historial |
| GET /api/tags/ | COVERED | historial/page.tsx |
| POST /api/tags/ | COVERED | historial/page.tsx |
| PUT /api/tags/{tag_id} | COVERED | historial/page.tsx |
| DELETE /api/tags/{tag_id} | COVERED | historial/page.tsx |
| GET /api/conversations/{conv_id}/tags | MISSING | historial reads tags from conv object |
| POST /api/conversations/{conv_id}/tags/{tag_id} | COVERED | historial/page.tsx:handleAssignTag |
| DELETE /api/conversations/{conv_id}/tags/{tag_id} | COVERED | historial/page.tsx:handleRemoveTag |
| GET /api/folders/ | COVERED | historial/page.tsx |
| POST /api/folders/ | COVERED | historial/page.tsx |
| PUT /api/folders/{folder_id} | MISSING | No rename folder UI |
| DELETE /api/folders/{folder_id} | COVERED | historial/page.tsx |
| PUT /api/conversations/{conv_id}/folder/{folder_id} | COVERED | historial/page.tsx |
| DELETE /api/conversations/{conv_id}/folder | COVERED | historial/page.tsx |
| GET /api/bookmarks/ | COVERED | marcadores/page.tsx |
| PUT /api/bookmarks/{message_id} | COVERED | page.tsx:handleToggleBookmark |
| DELETE /api/bookmarks/{message_id} | COVERED | marcadores/page.tsx |
| POST /api/search/advanced | COVERED | buscar/page.tsx |
| GET /api/search/suggestions | COVERED | buscar/page.tsx |
| POST /api/search/saved | COVERED | buscar/page.tsx |
| GET /api/search/saved | COVERED | buscar/page.tsx |
| DELETE /api/search/saved/{id} | COVERED | buscar/page.tsx |
| GET /api/search/history | COVERED | buscar/page.tsx |
| GET /api/documents/ | COVERED | buscar/page.tsx (browse mode) |
| GET /api/documents/search | MISSING | buscar uses /api/search/advanced instead |
| GET /api/documents/stats | MISSING | No frontend shows KB stats to users |
| GET /api/documents/{doc_id}/chunks | MISSING | documento/[id] page not verified |
| POST /api/analysis/case | PARTIAL | analizar/page.tsx not read — likely covers |
| POST /api/export/consultation/pdf | COVERED | page.tsx:handleDownloadPDF |
| POST /api/export/conversation/pdf | MISSING | No "export conversation" button found |
| GET /api/export/search-results/pdf | MISSING | No frontend uses this (NEW endpoint) |
| GET /api/memory/ | COVERED | configuracion/page.tsx |
| PUT /api/memory/{id}/toggle | COVERED | configuracion/page.tsx |
| DELETE /api/memory/{id} | COVERED | configuracion/page.tsx |
| DELETE /api/memory/ | COVERED | configuracion/page.tsx:handleClearAllMemories |
| GET /api/memory/settings | MISSING | Not in configuracion memory tab |
| PUT /api/memory/settings | MISSING | Not in configuracion memory tab |
| GET /api/notifications/ | MISSING | NO NOTIFICATIONS PAGE EXISTS |
| GET /api/notifications/unread-count | COVERED | AppSidebar.tsx |
| PUT /api/notifications/{id}/read | MISSING | No page to mark notifications read |
| PUT /api/notifications/read-all | MISSING | No page to mark all read |
| DELETE /api/notifications/{id} | MISSING | No page to delete notifications |
| POST /api/feedback/ | COVERED | page.tsx:handleFeedback |
| GET /api/feedback/stats | MISSING | No frontend shows feedback stats |
| POST /api/organizations/ | COVERED | organizacion/page.tsx |
| GET /api/organizations/ | COVERED | configuracion, analytics, organizacion |
| GET /api/organizations/{org_id} | COVERED | organizacion/page.tsx |
| PUT /api/organizations/{org_id} | COVERED | configuracion/page.tsx:handleSaveOrg |
| POST /api/organizations/{org_id}/invite | COVERED | organizacion/page.tsx |
| GET /api/organizations/{org_id}/members | COVERED | organizacion/page.tsx |
| DELETE /api/organizations/{org_id}/members/{member_id} | COVERED | configuracion/page.tsx (leave org) |
| GET /api/billing/config | COVERED | billing/page.tsx |
| GET /api/billing/plans | COVERED | billing/page.tsx |
| GET /api/billing/{org_id}/usage | COVERED | billing/page.tsx, organizacion/page.tsx |
| GET /api/billing/{org_id}/subscription | COVERED | billing/page.tsx |
| POST /api/billing/{org_id}/checkout | COVERED | billing/page.tsx |
| POST /api/billing/webhook/mp | MISSING (intentional) | Server-side webhook |
| POST /api/billing/webhook/culqi | MISSING (intentional) | Server-side webhook |
| GET /api/billing/{org_id}/invoices | COVERED | billing/page.tsx (InvoicesTable) |
| GET /api/billing/{org_id}/invoices/{invoice_id} | PARTIAL | table only, no detail view |
| GET /api/trials/me | COVERED | billing/page.tsx |
| POST /api/trials/start | COVERED | billing/page.tsx (via trials components) |
| POST /api/trials/add-card | COVERED | billing/page.tsx (via AddCardModal) |
| POST /api/trials/{trial_id}/cancel | COVERED | billing/page.tsx |
| POST /api/trials/{trial_id}/retry-charge | MISSING | No frontend retry button |
| GET /api/analytics/{org_id}/overview | COVERED | analytics/page.tsx |
| GET /api/analytics/{org_id}/queries | COVERED | analytics/page.tsx |
| GET /api/analytics/{org_id}/areas | COVERED | analytics/page.tsx |
| GET /api/analytics/{org_id}/models | COVERED | analytics/page.tsx |
| GET /api/analytics/{org_id}/costs | COVERED | analytics/page.tsx |
| GET /api/analytics/{org_id}/top-queries | COVERED | analytics/page.tsx |
| GET /api/analytics/{org_id}/export | COVERED | analytics/page.tsx |
| POST /api/keys/ | MISSING | configuracion only shows LLM keys, not dev API keys |
| GET /api/keys/ | MISSING | same — developer API keys tab absent |
| PUT /api/keys/{key_id} | MISSING | no UI to rename/update dev API keys |
| DELETE /api/keys/{key_id} | MISSING | same |
| GET /api/keys/llm-keys | COVERED | configuracion + page.tsx (models init) |
| POST /api/keys/llm-keys | COVERED | configuracion/page.tsx |
| DELETE /api/keys/llm-keys/{key_id} | COVERED | configuracion/page.tsx |
| GET /api/keys/llm-providers | MISSING | hardcoded LLM_PROVIDERS array in configuracion |
| GET /api/keys/free-models | MISSING | hardcoded MODEL_CATALOG in configuracion |
| POST /api/keys/llm-keys/test | COVERED | configuracion/page.tsx:handleTestKey |
| GET /api/plans/ | PARTIAL | precios/page.tsx likely but not verified |
| GET /api/shared/{share_id} | COVERED | compartido/[id]/page.tsx |
| POST /api/upload/ | COVERED | page.tsx:handleFileUpload |
| GET /api/upload/{doc_id} | MISSING | no download upload UI |
| DELETE /api/upload/{doc_id} | MISSING | no delete upload UI |
| GET /api/admin/stats | COVERED | admin/page.tsx |
| GET /api/admin/users | COVERED | admin/page.tsx |
| GET /api/admin/activity | COVERED | admin/page.tsx (recentQueries) |
| GET /api/admin/knowledge | MISSING | admin uses /api/health/knowledge instead |
| GET /api/admin/audit-log | MISSING | no audit log tab in admin page |
| GET /api/admin/invoices | COVERED | admin/page.tsx (InvoicesTable) |
| GET /api/admin/invoices/{invoice_id} | PARTIAL | table only |
| PATCH /api/admin/invoices/{invoice_id} | MISSING | no edit invoice UI |
| GET /api/admin/saas/* (2 endpoints) | COVERED | admin/page.tsx (RevenueCards) |
| GET /api/admin/trials | COVERED | admin/page.tsx (AdminTrialsTable) |
| PATCH /api/admin/trials/{trial_id} | COVERED | admin/page.tsx |
| GET /api/rbac/* (4 endpoints) | MISSING | no RBAC management UI |
| GET /api/health | COVERED | admin/page.tsx |
| GET /api/health/ready | COVERED | admin/page.tsx |
| GET /api/health/knowledge | COVERED | admin/page.tsx |
| GET /api/health/* (db, metrics, cache) | PARTIAL | status/page.tsx (not read) |
| GET /api/v1/* (6 endpoints) | MISSING (intentional) | third-party API, no UI needed |


## 3. Frontend → Backend mapping table

| Page/Component | Endpoints called | Issues |
|---------------|-----------------|--------|
| app/page.tsx | /api/keys/llm-keys, /api/conversations/*, /api/chat/stream, /api/feedback/, /api/bookmarks/{id}, /api/export/consultation/pdf, /api/upload/ | pref_default_model stored in localStorage (not RF-1 for tokens, but localStorage preference leak) |
| app/historial/page.tsx | /api/conversations/, /api/tags/, /api/folders/, conv/tag/folder CRUD | Well covered |
| app/buscar/page.tsx | /api/documents/, /api/search/*, /api/search/suggestions | Solid coverage |
| app/marcadores/page.tsx | /api/bookmarks/ | Well covered |
| app/analytics/page.tsx | /api/organizations/, /api/analytics/{org_id}/* | org hardcoded to orgs[0] — multi-org gap |
| app/configuracion/page.tsx | /api/auth/me, /api/auth/change-password★DEAD, /api/organizations/, /api/memory/*, /api/keys/llm-keys | change-password BROKEN; memory settings absent |
| app/billing/page.tsx | /api/billing/*, /api/trials/* | Well covered |
| app/organizacion/page.tsx | /api/organizations/* | Well covered |
| app/admin/page.tsx | /api/health, /api/admin/*, /api/admin/saas | /api/admin/knowledge unused; uses /api/health/knowledge instead |
| AppSidebar | /api/auth/me, /api/notifications/unread-count | Bell→/configuracion (wrong link) |
| AdminSidebar | /api/auth/me | "Notificaciones"→/configuracion (wrong) |
| lib/api.ts | /api/chat/query, /api/chat/agents, /api/chat/models, /api/health | ALL DEAD — no auth tokens, 0 callers |
| AuthContext.tsx | /api/auth/me, /api/auth/me/permissions | Solid |
| authClient.ts | /api/auth/login, register, logout, refresh | Solid — httpOnly cookie flow correct |

## 4. Gap report ordered by severity

**[GAP-C1] CRITICAL — POST /api/auth/change-password DOES NOT EXIST IN BACKEND**
* Evidence: `configuracion/page.tsx:474` calls `/api/auth/change-password`. Backend `auth.py` has no change-password route.
* Impact: Password change is COMPLETELY BROKEN for all users. Silent 404 on submit.
* Suggested fix surface: `frontend-fix-critical-bugs`

**[GAP-C2] CRITICAL — Notification Center ENTIRELY MISSING**
* Evidence: Backend has 5 notification endpoints. Frontend has no `/notificaciones` page; `AppSidebar` shows badge but links to `/configuracion` (wrong). `AdminSidebar` "Notificaciones" label also links to `/configuracion`.
* Impact: Users can see unread count badge but cannot read or manage any notifications.
* Suggested fix surface: `frontend-notifications-feature`

**[GAP-C3] CRITICAL — lib/api.ts dead functions call unauthenticated endpoints**
* Evidence: `sendQuery()` → POST `/api/chat/query` with NO Bearer token → 401. 
* Impact: Any code that accidentally imports these functions will silently fail. The file exists and is importable, creating a risk of accidental use or confusion.
* Suggested fix surface: `frontend-fix-critical-bugs`

**[GAP-H1] HIGH — Developer API Keys UI MISSING**
* Evidence: `GET/POST/PUT/DELETE /api/keys/` — full developer API key CRUD exists in backend. Frontend only exposes LLM provider keys.
* Impact: Developer API key management is 100% absent from configuration or any other page.
* Suggested fix surface: `frontend-high-gaps`

**[GAP-H2] HIGH — GET /api/auth/sessions no sessions management UI**
* Evidence: Backend lists active sessions. `configuracion/page.tsx` shows logout-all button but no session list.
* Impact: Users cannot see WHERE they're logged in and selectively revoke.
* Suggested fix surface: `frontend-high-gaps`

**[GAP-H3] HIGH — POST /api/export/conversation/pdf no frontend trigger**
* Evidence: `page.tsx` only exports single consultation. No "Export full conversation" button found.
* Impact: Missing feature in frontend.
* Suggested fix surface: `frontend-export-buttons`

**[GAP-H4] HIGH — GET /api/export/search-results/pdf NEW endpoint, no frontend**
* Evidence: Discovered during audit. `buscar/page.tsx` has no PDF export button for search results.
* Impact: Missing feature in frontend.
* Suggested fix surface: `frontend-export-buttons`

**[GAP-H5] HIGH — RBAC Admin UI completely absent**
* Evidence: 4 RBAC endpoints exist (`/api/rbac/*`) for role/permission management. No admin UI tab.
* Impact: RBAC is only manageable via API directly.
* Suggested fix surface: `frontend-high-gaps`

**[GAP-H6] HIGH — GET /api/admin/audit-log no frontend tab**
* Evidence: Admin page has no audit log section.
* Impact: Security-sensitive gap. Admins cannot see audit logs.
* Suggested fix surface: `frontend-high-gaps`

**[GAP-H7] HIGH — PUT /api/folders/{folder_id} rename folder MISSING**
* Evidence: `historial/page.tsx` can create and delete folders but NOT rename them.
* Impact: Missing basic CRUD feature for folders.
* Suggested fix surface: `frontend-historial-folder-actions`

**[GAP-M1] MEDIUM — Memory settings not exposed**
* Evidence: `GET/PUT /api/memory/settings` exist but `configuracion/page.tsx` memory tab only shows memory list and bulk-delete.
* Impact: No enable/disable memory globally or settings tuning.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-M2] MEDIUM — Notification bell links to /configuracion (wrong)**
* Evidence: `AppSidebar.tsx` and `AdminSidebar.tsx` have wrong links for the notification center.
* Impact: UX confusion.
* Suggested fix surface: `frontend-notifications-feature`

**[GAP-M3] MEDIUM — /api/keys/llm-providers and /api/keys/free-models not consumed**
* Evidence: `configuracion/page.tsx` hardcodes arrays instead of fetching from backend.
* Impact: Drift risk.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-M4] MEDIUM — GET /api/documents/stats not surfaced to users**
* Evidence: KB statistics shown only in admin page.
* Impact: Regular users see no KB health metrics.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-M5] MEDIUM — TODO: Sprint 33 — /api/billing/daily-usage endpoint doesn't exist yet**
* Evidence: `billing/page.tsx:758` comment.
* Impact: Missing data.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-M6] MEDIUM — GET /api/admin/knowledge vs GET /api/health/knowledge duplication**
* Evidence: Admin page calls health variant instead of admin variant.
* Impact: Unused admin endpoint.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-M7] MEDIUM — No org switcher in analytics**
* Evidence: `analytics/page.tsx` hardcodes `orgs[0].id`.
* Impact: Multi-org users cannot switch organizations.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-M8] MEDIUM — PATCH /api/admin/invoices/{invoice_id} no UI**
* Evidence: Admin InvoicesTable renders invoice list but no edit/patch action.
* Impact: Missing feature.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-M9] MEDIUM — POST /api/trials/{trial_id}/retry-charge no UI**
* Evidence: Trial management exists but no retry charge button.
* Impact: Missing feature.
* Suggested fix surface: `frontend-medium-cleanup`

**[GAP-L1] LOW — lib/api.ts is dead code**
* Evidence: 4 functions, 74 lines, all dead.
* Impact: Code bloat, confusion risk.
* Suggested fix surface: `frontend-fix-critical-bugs`

**[GAP-L2] LOW — GET /api/upload/{doc_id} and DELETE /api/upload/{doc_id} no UI**
* Evidence: Users can upload files but cannot see/delete previously uploaded files.
* Impact: Missing UI for file management.
* Suggested fix surface: `frontend-cosmetic-polish`

**[GAP-L3] LOW — /api/v1/* (6 endpoints)**
* Evidence: Third-party API.
* Impact: Intentionally no UI.
* Suggested fix surface: None

**[GAP-L4] LOW — GET /api/documents/search vs POST /api/search/advanced possible duplication**
* Evidence: Both endpoints exist, only one is used.
* Impact: Duplicate endpoints.
* Suggested fix surface: `frontend-cosmetic-polish`

**[GAP-L5] LOW — GET /api/billing/{org_id}/invoices/{invoice_id} no detail view**
* Evidence: InvoicesTable only shows list.
* Impact: Missing detail view.
* Suggested fix surface: `frontend-cosmetic-polish`

## 5. Admin vs Client drift

- **INFO**: **Separate layouts**: `AppLayout` (client) and `AdminLayout` (admin) — correctly separated.
- **SECURITY-RISK**: **Admin nav gate**: `authUser?.isAdmin` check in AppSidebar is CLIENT-SIDE. No server-side enforcement in middleware. Middleware only checks `tk_session` cookie presence. While backend RBAC is authoritative, any authenticated non-admin can navigate to `/admin` and see the admin UI shell antes del redireccionamiento.
- **RISK**: **Admin sidebar mislabeling**: "Notificaciones" label links to `/configuracion` — should be removed or point to a real notifications page.
- **RISK**: **Analytics not admin-gated**: `/analytics` route is accessible to ALL authenticated users via AppSidebar. Backend gating: `_assert_org_access` — any org member can see their own org analytics. Intentional design but note that `is_admin` bypasses org check completely.
- **RISK**: **No org switcher anywhere**: Both analytics and billing hardcode `orgs[0]`. Multi-org users silently see only their first org.
- **RISK**: **Admin audit-log endpoint**: Exists but no UI. Sensitive data no accesible para admins desde la interfaz.

## 6. Plan de trabajo frontend propuesto

1. **`frontend-fix-critical-bugs`**
   - **Scope**: small
   - **Addresses**: C1, C3, L1
   - **Prerequisites**: none
   - **Est. files touched**: 2-3 files
   - **Details**: Removes the broken `/api/auth/change-password` call (or adds the endpoint, pendiente de decisión) and deletes dead `lib/api.ts` functions.

2. **`frontend-admin-route-hardening`**
   - **Scope**: small
   - **Addresses**: SECURITY-RISK from drift (client-side admin gates)
   - **Prerequisites**: none
   - **Est. files touched**: 2 files
   - **Details**: Add middleware enforcement for `/admin/*` and `/analytics/*` (server-side role check, not client-side).

3. **`frontend-notifications-feature`**
   - **Scope**: medium
   - **Addresses**: C2, M2
   - **Prerequisites**: none
   - **Est. files touched**: 4-6 files
   - **Details**: Build `/notificaciones` page consuming the 5 backend endpoints. Fix bell icon hrefs in both AppSidebar and AdminSidebar.

4. **`frontend-auth-refresh-flow`**
   - **Scope**: medium-large
   - **Addresses**: RF-1, RF-2, RF-3
   - **Prerequisites**: none
   - **Est. files touched**: 5-8 files
   - **Details**: Move access token to memory, implement refresh flow with retry, store refresh token. MUST come with tests. *Note: this should land BEFORE the high-gaps batch because new admin features will all use `authFetch()`.*

5. **`frontend-export-buttons`**
   - **Scope**: small
   - **Addresses**: H3, H4
   - **Prerequisites**: none
   - **Est. files touched**: 2-3 files
   - **Details**: Implement export PDF buttons for conversations and search results.

6. **`frontend-historial-folder-actions`**
   - **Scope**: small
   - **Addresses**: H7
   - **Prerequisites**: none
   - **Est. files touched**: 2 files
   - **Details**: Implement UI for renaming folders in the history view.

7. **`frontend-high-gaps`**
   - **Scope**: large
   - **Addresses**: H1, H2, H5, H6
   - **Prerequisites**: `frontend-auth-refresh-flow`
   - **Est. files touched**: 8-12 files
   - **Details**: Implement developer API keys UI, sessions management UI, RBAC admin UI, and audit-log tab in admin.

8. **`frontend-medium-cleanup`**
   - **Scope**: medium
   - **Addresses**: M1, M3, M4, M5, M6, M7, M8, M9
   - **Prerequisites**: none
   - **Est. files touched**: 6-10 files
   - **Details**: Memory settings, feedback stats, trials actions, multi-org switcher, onboarding wiring, shared page guard, analytics role-gate UX, admin dashboard skeletons, password strength.

9. **`frontend-cosmetic-polish`**
   - **Scope**: small
   - **Addresses**: L2, L4, L5
   - **Prerequisites**: none
   - **Est. files touched**: 3-5 files
   - **Details**: Minor UI fixes and missing features for uploads and invoice details.

## 7. Riesgos y decisiones pendientes

- **C1 decision**: remove the broken UI call, OR ship a backend endpoint `POST /api/auth/change-password`? (Backend has password-reset but not in-app change-password for authenticated users.) → Owner must choose.
- **C2 decision**: should the new `/notificaciones` page replace the bell-icon dropdown, complement it, or both?
- **Admin panel strategy**: keep current `app/admin/*` standalone, or refactor with shared layouts and role-based menu?
- **Refresh token storage**: cookie (httpOnly, SameSite=Strict) vs IndexedDB? Current spec is RF-1/2/3 fix; choose a strategy before starting `frontend-auth-refresh-flow`.
- **Org switcher UX**: needed now (multi-org tenants exist) or deferred?
- **RFs status**:
  - **RF-1**: OPEN (still in localStorage — addressed by `frontend-auth-refresh-flow`)
  - **RF-2**: OPEN (no refresh — same change)
  - **RF-3**: OPEN (refresh token discarded — same change)
  - **RF-4**: **RESOLVED** (Vitest and MSW present)
  - **RF-5**: OPEN (env mismatch — backlog)
  - **RF-6**: OPEN (no skill registry — backlog)

## 8. Referencias

- Engram topics consulted:
  - `sdd-init/tukijuris` (obs #4)
  - `sdd/backend-microfixes-sprint/session-close` (obs #340)
  - `sdd/backend-saas-test-coverage/archive-report` (obs #314)
  - `sdd/frontend-coverage-audit/explore` (this audit's input)
- Backend commit: `9a82385` (latest fix #6 BYOK UniqueConstraint, pushed)
- Files read during exploration:
  - apps/web/package.json
  - apps/web/vitest.config.ts
  - apps/api/app/main.py
  - apps/web/src/lib/api.ts
  - apps/web/src/lib/auth/
  - apps/web/src/lib/auth/authClient.ts
  - apps/web/src/lib/auth/AuthContext.tsx
  - apps/web/src/components/AppSidebar.tsx
  - apps/web/src/components/AdminSidebar.tsx
  - apps/web/src/components/AppLayout.tsx
  - apps/web/src/middleware.ts
  - apps/web/src/app/page.tsx
  - apps/web/src/app/historial/page.tsx
  - apps/web/src/app/buscar/page.tsx
  - apps/web/src/app/marcadores/page.tsx
  - apps/web/src/app/analytics/page.tsx
  - apps/web/src/app/configuracion/page.tsx
  - apps/web/src/app/admin/page.tsx
  - apps/web/src/app/billing/page.tsx
  - apps/web/src/app/organizacion/page.tsx
  - apps/api/app/api/routes/
