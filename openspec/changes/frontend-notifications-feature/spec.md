# Spec — frontend-notifications-feature

## 1. Scope summary
8 files, ~708 LOC, 13 tests. Frontend-only — backend endpoints already exist.

Scope surfaces:
- API service: `apps/web/src/lib/api/notifications.ts` (new)
- Page: `apps/web/src/app/notificaciones/page.tsx` (new)
- Bell: `apps/web/src/components/NotificationBell.tsx` (modify)
- Sidebars: `AppSidebar.tsx` + `AdminSidebar.tsx` (href fixes)
- Tests: 3 test files

## 2. Behavioral requirements (NF-* — Notifications Feature)

### API service (NF-1..NF-5)
- **NF-1**: `listNotifications({ page, per_page, unread_only })` SHALL call `GET /api/notifications/?page=&per_page=&unread_only=` via authFetch. Returns `{ notifications: NotificationOut[], unread_count: number, total: number }`.
- **NF-2**: `getUnreadCount()` SHALL call `GET /api/notifications/unread-count` via authFetch. Returns `{ count: number }`.
- **NF-3**: `markAsRead(id: string)` SHALL call `PUT /api/notifications/{id}/read` via authFetch. Returns `{ status: "ok" }` or throws on 404.
- **NF-4**: `markAllAsRead()` SHALL call `PUT /api/notifications/read-all` via authFetch. Returns `{ status: "ok", updated: number }`.
- **NF-5**: `deleteNotification(id: string)` SHALL call `DELETE /api/notifications/{id}` via authFetch. Returns `{ status: "ok" }` or throws on 404.

### Page list rendering (NF-6..NF-9)
- **NF-6**: On mount, `/notificaciones/page.tsx` SHALL fetch page 1 with `per_page=20` (or `per_page=100` if any type chip is active) via `listNotifications`.
- **NF-7**: The page SHALL render each notification as a row with: title, message (line-clamp), timeAgo, unread dot (if !is_read), action_url click navigation, "Marcar leída" button (if !is_read), delete button (always).
- **NF-8**: The page SHALL render numbered pagination: prev button, "Página N de M" indicator, next button. Disabled at boundaries.
- **NF-9**: The page SHALL render a polling refresh every 30s (setInterval, cleanup on unmount).

### Filters (NF-10..NF-12)
- **NF-10**: An `unread_only` toggle SHALL re-fetch the list with the boolean param. Reset to page 1.
- **NF-11**: 5 type chips (`usage_alert`, `invite`, `system`, `billing`, `welcome`) SHALL filter the CURRENT PAGE client-side. Multiple chips: OR semantics (item passes if its type matches ANY active chip).
- **NF-12**: When ANY type chip is active, the next fetch SHALL use `per_page=100` (DR-8 mitigation). Tooltip on chips: "Filtros aplicados a las notificaciones cargadas."

### Mutations (NF-13..NF-16)
- **NF-13**: Per-item "Marcar leída" SHALL call `markAsRead`. On success: optimistically set `is_read=true` for that item.
- **NF-14**: "Marcar todas como leídas" header button SHALL call `markAllAsRead`. On success: optimistically set `is_read=true` for ALL items.
- **NF-15**: Per-item delete SHALL optimistically remove the item from local state, then call `deleteNotification`. On error: restore the item + show error toast "No se pudo eliminar la notificación."
- **NF-16**: After any mutation, the unread count badge SHALL be re-fetched (NF-2) to keep header counter accurate.

### Empty states (NF-17, NF-18)
- **NF-17**: All-empty (total === 0, no filters): logo opacity-20 + "No tenés notificaciones todavía." (matches `historial` page pattern).
- **NF-18**: Filter-empty (total > 0 but filtered list empty): "No hay notificaciones que coincidan con el filtro." + "Limpiar filtros" link that resets unread_only + chips.

### Bell dropdown (NF-19)
- **NF-19**: `NotificationBell.tsx` dropdown footer SHALL include a `<Link href="/notificaciones">Ver todas</Link>` element. Style: subtle text link, distinct from the per-item rows.

### Sidebar fixes (NF-20, NF-21)
- **NF-20**: `apps/web/src/components/AppSidebar.tsx` line 384 + line 417 (per explore) — bell href SHALL be `/notificaciones` (not `/configuracion`).
- **NF-21**: `apps/web/src/components/AdminSidebar.tsx` line 55 (NAV_SISTEMA "Notificaciones" item) — href SHALL be `/notificaciones`.

## 3. Test matrix (NFT-* — Notifications Feature Tests)

Test files:
- `apps/web/src/lib/api/__tests__/notifications.test.ts` — 5 service tests
- `apps/web/src/app/notificaciones/__tests__/page.test.tsx` — 7 page tests
- `apps/web/src/components/__tests__/NotificationBell.test.tsx` — extend with +1 test

| ID    | Case                                                | Setup                                                  | Expected                                                                |
|-------|-----------------------------------------------------|--------------------------------------------------------|-------------------------------------------------------------------------|
| NFT-1 | listNotifications hits GET with params              | MSW handler asserts URL params; returns mock list      | Service returns parsed { notifications, unread_count, total }            |
| NFT-2 | markAsRead uses PUT                                 | MSW handler verifies method=PUT, path with id          | Service resolves with { status: "ok" }                                  |
| NFT-3 | markAllAsRead uses PUT                              | MSW handler verifies method=PUT, returns { updated: 3 }| Service returns { status: "ok", updated: 3 }                            |
| NFT-4 | deleteNotification uses DELETE + handles 404        | MSW returns 404                                        | Service throws (or rejects) — caller can catch                          |
| NFT-5 | getUnreadCount returns count                        | MSW returns { count: 7 }                               | Service returns { count: 7 }                                            |
| NFT-6 | Page renders list                                   | MSW returns 3 notifications, total=3                   | All 3 visible; "Página 1 de 1"                                          |
| NFT-7 | Pagination: click next                              | MSW returns total=50, render; click "Siguiente"        | Re-fetch with page=2; UI shows "Página 2 de 3"                          |
| NFT-8 | unread_only toggle                                  | Render; click toggle                                   | Re-fetch with unread_only=true; URL params asserted via MSW             |
| NFT-9 | Type chip filters client-side                       | MSW returns 3 items types billing/system/billing       | Click "billing" chip; only 2 items visible                              |
| NFT-10| Mark-read updates UI                                | Render with 1 unread; click "Marcar leída"             | Unread dot disappears; service called once                              |
| NFT-11| Mark-all-read updates UI                            | Render with 2 unread; click header button              | All dots disappear; service called once                                 |
| NFT-12| Delete optimistic + rollback                        | Render 2 items; mock delete to fail; click delete one  | Item disappears immediately; on error, restored + error toast visible    |
| NFT-13| Bell dropdown shows "Ver todas" link                | Render NotificationBell with token+empty list           | Link with text "Ver todas" + href="/notificaciones" present              |

## 4. Non-functional requirements
- **NF-NFR-1**: NO new dependencies.
- **NF-NFR-2**: NO backend changes.
- **NF-NFR-3**: All UI strings in Spanish (es-419 / Argentine).
- **NF-NFR-4**: Type chips localized labels: usage_alert→"Uso", invite→"Invitaciones", system→"Sistema", billing→"Facturación", welcome→"Bienvenida" (proposer/applier confirms exact copy from existing UI conventions; defaults shown).
- **NF-NFR-5**: Polling SHALL stop on unmount.
- **NF-NFR-6**: Lint+tsc clean on all changed files.
- **NF-NFR-7**: Frontend full suite still ≥222 passing, 0 NEW regressions.

## 5. Out of scope
- /preferences page (different change)
- WebSocket/SSE real-time
- AppSidebar/NotificationBell shared count state (known issue R2, deferred)
- Bulk delete (no backend endpoint)
- Server-side type filter (no backend support)
- Admin notification creation/management

## 6. References
- Proposal: `openspec/changes/frontend-notifications-feature/proposal.md` + engram topic
- Explore: engram obs #387 — endpoint shapes, current bell state, sidebar line numbers
- Backend route: `apps/api/app/api/routes/notifications.py`
- Backend model: `apps/api/app/models/notification.py`
- Pattern: `apps/web/src/lib/api/admin.ts` (service layer)
- Pattern: `apps/web/src/app/historial/page.tsx` (list + filter UI per audit)
- Sprint 1 test pattern: `apps/web/src/app/configuracion/__tests__/change-password.test.tsx`
- HTTP verbs: PUT for mark-read + read-all (NOT PATCH/POST as audit prompt mistakenly said)
