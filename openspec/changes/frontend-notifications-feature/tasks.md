# Tasks — frontend-notifications-feature

## Batch A — API service layer
- [x] **A1** Create `apps/web/src/lib/api/notifications.ts`. Pattern: read `apps/web/src/lib/api/admin.ts` first to mirror its structure.
- [x] **A2** Implement `listNotifications({ page, per_page, unread_only })` — GET via authFetch with URLSearchParams. Returns `{ notifications, unread_count, total }`. Type the response. (NF-1)
- [x] **A3** Implement `getUnreadCount()` — GET. Returns `{ count }`. (NF-2)
- [x] **A4** Implement `markAsRead(id)` — PUT. Returns `{ status }`. (NF-3)
- [x] **A5** Implement `markAllAsRead()` — PUT. Returns `{ status, updated }`. (NF-4)
- [x] **A6** Implement `deleteNotification(id)` — DELETE. Returns `{ status }`. Throws on 404. (NF-5)
- [x] **A7** Add `Notification` (or `NotificationOut`) TypeScript type matching backend schema (id, user_id, type, title, message, is_read, action_url, extra_data, created_at). Export from same file.
- [x] **A8** Verify: `cd apps/web && npx tsc --noEmit src/lib/api/notifications.ts 2>&1 | tail -5` — no errors.

## Batch B — Page implementation
- [x] **B1** Create `apps/web/src/app/notificaciones/page.tsx`. Pattern: read `apps/web/src/app/historial/page.tsx` for list + filter + empty-state structure.
- [x] **B2** Add header: "Notificaciones" title + "Marcar todas como leídas" button (NF-14).
- [x] **B3** Add filters row: unread_only toggle + 5 type chips (NF-10/11/12). Localize labels per NF-NFR-4. Tooltip on chips per DR-8.
- [x] **B4** Add list rendering: each row with title, message (line-clamp), timeAgo, unread dot, action_url click, "Marcar leída" button (if !is_read), delete button (NF-7).
- [x] **B5** Add pagination: numbered prev/next + "Página N de M" indicator. Disabled at boundaries (NF-8).
- [x] **B6** Add empty states (NF-17, NF-18). Match historial pattern for all-empty (logo opacity-20).
- [x] **B7** Add 30s polling via setInterval, cleanup on unmount (NF-9, NF-NFR-5).
- [x] **B8** Wire mutations: per-item mark-read (NF-13), mark-all-read (NF-14), delete optimistic+rollback (NF-15). After each, refresh unread count (NF-16).
- [x] **B9** Verify: `cd apps/web && npx tsc --noEmit src/app/notificaciones/page.tsx 2>&1 | tail -5` — no errors.

## Batch C — Bell + sidebar fixes
- [x] **C1** `apps/web/src/components/NotificationBell.tsx`: add `<Link href="/notificaciones">Ver todas</Link>` in dropdown footer (NF-19). Style as subtle text link.
- [x] **C2** `apps/web/src/components/AppSidebar.tsx` line 384: change `href="/configuracion"` → `href="/notificaciones"` (NF-20).
- [x] **C3** `apps/web/src/components/AppSidebar.tsx` line 417: same change (collapsed state, NF-20).
- [x] **C4** `apps/web/src/components/AdminSidebar.tsx` line 55 (NAV_SISTEMA "Notificaciones"): change `href="/configuracion"` → `href="/notificaciones"` (NF-21).
- [x] **C5** Verify: `cd apps/web && npx tsc --noEmit 2>&1 | grep -v AddCardModal | tail -5` — 0 errors.

## Batch D — Tests
Test files:
- `apps/web/src/lib/api/__tests__/notifications.test.ts`
- `apps/web/src/app/notificaciones/__tests__/page.test.tsx`
- `apps/web/src/components/__tests__/NotificationBell.test.tsx` (extend, NOT replace)

Pattern: read Sprint 3 `NotificationBell.test.tsx` and Sprint 1 `change-password.test.tsx` for AuthContext mock + MSW setup.

- [x] **D1** NFT-1: listNotifications hits GET with params (MSW asserts URL).
- [x] **D2** NFT-2: markAsRead uses PUT.
- [x] **D3** NFT-3: markAllAsRead uses PUT.
- [x] **D4** NFT-4: deleteNotification handles 404.
- [x] **D5** NFT-5: getUnreadCount returns count.
- [x] **D6** NFT-6: Page renders 3 items + "Página 1 de 1".
- [x] **D7** NFT-7: Pagination next clicks fetch page=2.
- [x] **D8** NFT-8: unread_only toggle re-fetches with param.
- [x] **D9** NFT-9: Type chip filters list client-side.
- [x] **D10** NFT-10: Mark-read updates UI.
- [x] **D11** NFT-11: Mark-all-read updates UI.
- [x] **D12** NFT-12: Delete optimistic + rollback on error.
- [x] **D13** NFT-13: NotificationBell dropdown shows "Ver todas" link.

## Batch E — Validation + apply-progress
- [x] **E1** `cd apps/web && npm test -- notifications.test 2>&1 | tail -10` — service tests green (5/5).
- [x] **E2** `cd apps/web && npm test -- src/app/notificaciones 2>&1 | tail -10` — page tests green (7/7).
- [x] **E3** `cd apps/web && npm test -- NotificationBell.test 2>&1 | tail -10` — bell tests green (existing 6 + NFT-13 = 7).
- [x] **E4** `cd apps/web && npm test 2>&1 | tail -10` — full suite. Baseline 222 + 13 new = 235+. Zero NEW regressions.
- [x] **E5** `cd apps/web && npx eslint src/lib/api/notifications.ts src/app/notificaciones/page.tsx src/components/NotificationBell.tsx src/components/AppSidebar.tsx src/components/AdminSidebar.tsx src/lib/api/__tests__/notifications.test.ts src/app/notificaciones/__tests__/page.test.tsx src/components/__tests__/NotificationBell.test.tsx 2>&1 | tail -10` — 0 errors AND 0 warnings on changed files.
- [x] **E6** `cd apps/web && npx tsc --noEmit 2>&1 | grep -v AddCardModal | tail -5` — 0 errors excluding pre-existing.
- [x] **E7** `git status --short` — expect ONLY:
  - M apps/web/src/components/NotificationBell.tsx
  - M apps/web/src/components/__tests__/NotificationBell.test.tsx
  - M apps/web/src/components/AppSidebar.tsx
  - M apps/web/src/components/AdminSidebar.tsx
  - ?? apps/web/src/lib/api/notifications.ts
  - ?? apps/web/src/lib/api/__tests__/notifications.test.ts
  - ?? apps/web/src/app/notificaciones/
  - ?? openspec/changes/frontend-notifications-feature/
- [x] **E8** Save FINAL apply-progress to engram (topic_key sdd/frontend-notifications-feature/apply-progress) with checkbox state + suggested commit message.

<!-- Remediation pass 2026-04-22: NFT-14..17 added (NF-9, NF-16, NF-17, NF-18 coverage). NF-20/21 sidebar href tests declined per orchestrator (over-testing static change). -->
