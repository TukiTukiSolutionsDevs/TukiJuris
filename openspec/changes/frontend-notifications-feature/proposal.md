# Proposal: frontend-notifications-feature

## Why
- Closes audit gap C2 — notifications backend has 5 endpoints (incl. DELETE discovered during audit) with 0% UI coverage.
- Sprint 3 already wired the bell dropdown to authFetch but didn't add the full management page.
- Bell href bug in BOTH AppSidebar (2 locations) and AdminSidebar (1 location) misroutes users to `/configuracion`.

## What changes (~708 LOC across 8 files)

### Frontend modify (3 files)
1. `apps/web/src/components/NotificationBell.tsx` — add "Ver todas" link to dropdown footer.
2. `apps/web/src/components/AppSidebar.tsx` — fix 2 bell hrefs (lines 384 + 417 per explore) from `/configuracion` to `/notificaciones`.
3. `apps/web/src/components/AdminSidebar.tsx` — fix NAV_SISTEMA "Notificaciones" item (line 55) from `/configuracion` to `/notificaciones`.

### Frontend add (2 files)
4. `apps/web/src/lib/api/notifications.ts` — service layer with 5 fetcher functions:
   - `listNotifications({ page, per_page, unread_only })`
   - `getUnreadCount()`
   - `markAsRead(id)` — PUT
   - `markAllAsRead()` — PUT
   - `deleteNotification(id)` — DELETE
   Each returns typed response. Pattern: follow `apps/web/src/lib/api/admin.ts` (per explore note).
5. `apps/web/src/app/notificaciones/page.tsx` — full page:
   - Header: "Notificaciones" + "Marcar todas como leídas" button
   - Filters: unread_only toggle + 5 type chips (`usage_alert | invite | system | billing | welcome`). Localized labels (es-419).
   - List: pagination (numbered prev/next), per-item rows with title, message, timeAgo, unread dot, action_url click, mark-read button (if unread), delete button
   - Empty state per DR-7
   - Polling per DR-6

### Frontend tests (3 files)
6. `apps/web/src/lib/api/__tests__/notifications.test.ts` — 5 service tests (one per function), MSW-backed.
7. `apps/web/src/app/notificaciones/__tests__/page.test.tsx` — 7 page tests:
   - Renders list from MSW
   - Pagination clicks fetch next page
   - unread_only toggle re-fetches with param
   - Type chip filters list client-side
   - Mark-read button hits service, updates UI
   - Mark-all-read button updates UI
   - Delete button optimistic, restores on error
8. `apps/web/src/components/__tests__/NotificationBell.test.tsx` — extend with +1 test asserting "Ver todas" link present + correct href.

## Non-changes
- NO new dependencies.
- NO backend changes — endpoints already exist.
- NO touching `lib/auth/*` (Sprint 3 territory).
- NO middleware changes.
- NO `/preferences` endpoint UI (separate change — backend endpoint missing per audit).
- NO admin notifications-management UI (separate change).

## UX contract

| Scenario                                         | Behavior                                                                |
|--------------------------------------------------|-------------------------------------------------------------------------|
| User clicks bell                                 | Existing dropdown shows latest 10 + new "Ver todas" link in footer       |
| User clicks "Ver todas"                          | Navigates to `/notificaciones`                                           |
| `/notificaciones` loads                          | Lists page 1 (per_page=20), shows total + page indicator                 |
| User toggles unread_only                         | Re-fetches with `?unread_only=true`                                      |
| User clicks "billing" chip                       | Filters CURRENT PAGE client-side; if active, fetch uses per_page=100 (DR-8) |
| User clicks per-item "Marcar leída"              | PUT `/read`; row's unread dot disappears                                 |
| User clicks "Marcar todas como leídas"           | PUT `/read-all`; all unread dots clear                                   |
| User clicks delete on item                       | Item disappears immediately; on 4xx/5xx, restored + error toast          |
| All-empty                                        | Logo opacity-20 + "No tenés notificaciones todavía."                     |
| Filter-empty                                     | "No hay notificaciones que coincidan con el filtro." + "Limpiar filtros" link |
| Page mounted >30s                                | Auto re-fetch (background polling)                                       |

## Acceptance criteria
- [ ] `lib/api/notifications.ts` exports 5 typed functions, all using PUT (not PATCH/POST) where required
- [ ] `/notificaciones/page.tsx` lists notifications with numbered pagination
- [ ] unread_only toggle works (verify query param sent)
- [ ] Type chips filter client-side
- [ ] Type chip activation triggers per_page=100 fetch (DR-8)
- [ ] Mark-read updates UI (optimistic)
- [ ] Mark-all-read updates UI (optimistic)
- [ ] Delete optimistic + rollback on error
- [ ] Empty states (both variants) render correctly
- [ ] Polling refreshes every 30s
- [ ] NotificationBell dropdown shows "Ver todas" link → /notificaciones
- [ ] AppSidebar bell hrefs (2x) point to /notificaciones
- [ ] AdminSidebar NAV_SISTEMA Notificaciones href points to /notificaciones
- [ ] 13 Vitest tests pass (5 service + 7 page + 1 bell extension)
- [ ] Frontend full suite still 222+ passing, 0 NEW regressions
- [ ] Lint+tsc clean on changed files

## Risks
- **R1** — type chip filters only the current page (DR-8 mitigation: per_page=100 when active). For users with >100 notifications + active type filter, result is incomplete. Acceptable MVP trade-off, document in user-facing tooltip.
- **R2** — AppSidebar unread-count lag (up to 30s post-mark-all-read). Known issue, deferred (would require shared context).
- **R3** — Hard delete with no undo. Optimistic UI restored on error, but successful delete is permanent. Acceptable per backend contract.
- **R4** — Type filter is client-side; backend doesn't support `type=` param. If product needs server-side type filtering later, backend extension required.

## Architecture Decisions (DR-1..DR-8)
- **DR-1**: Bell dropdown UI - Keep existing Sprint-3 dropdown, add "Ver todas" footer link to `/notificaciones`. No per-item delete here.
- **DR-2**: Pagination - Numbered pages (prev/next + page indicator). Backend provides `total`.
- **DR-3**: Filters - `unread_only` toggle (server-side query param), type chips applied client-side on current page (localized labels for `usage_alert | invite | system | billing | welcome`).
- **DR-4**: DELETE UX - Optimistic immediate hard delete. No modal. Restore + error toast on 4xx/5xx failure.
- **DR-5**: Bulk operations - "Mark all read" only (PUT `/read-all`). No bulk delete.
- **DR-6**: Real-time updates - Poll every 30s while page mounted. Refresh list after mutations.
- **DR-7**: Empty state - Two variants: All-empty (logo opacity-20 + "No tenés notificaciones todavía.") and Filter-empty ("No hay notificaciones que coincidan con el filtro." + "Limpiar filtros" link).
- **DR-8**: Type filter UX - Active type chip fetches with `per_page=100` to mitigate client-side filtering limits. Add tooltip: "Filtros aplicados a las notificaciones cargadas."
- **HTTP verb correction**: Use PUT for `read` and `read-all` (not PATCH/POST) per backend exploration.
