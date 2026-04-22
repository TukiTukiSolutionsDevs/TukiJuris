# Tasks — frontend-auth-refresh-flow

## Batch A — NotificationBell (Gap 1)
- [x] **A1** Read `apps/web/src/components/NotificationBell.tsx`. Locate every raw `fetch('/api/notifications/...')` call. (FAR-1)
- [x] **A2** Replace raw `fetch()` with `authFetch` (imported from `@/lib/auth/authClient`). Preserve query params + body shape. (FAR-1)
- [x] **A3** In the catch block, set `bellCount` (or whichever local state holds the count) to `0`. Keep any existing logging. (FAR-2, FAR-3)
- [x] **A4** Verify NotificationBell still type-checks: `cd apps/web && npx tsc --noEmit src/components/NotificationBell.tsx 2>&1 | tail -5`.

## Batch B — Cross-tab logout (Gap 2)
- [x] **B1** Read `apps/web/src/lib/auth/authClient.ts`. Locate logout/logoutAll exports. (FAR-4, FAR-5)
- [x] **B2** Add a lazy-initialized `BroadcastChannel('tukijuris:auth')` accessor:
  ```ts
  let _bc: BroadcastChannel | null = null;
  function getAuthChannel(): BroadcastChannel | null {
    if (typeof BroadcastChannel === 'undefined') return null;
    if (!_bc) _bc = new BroadcastChannel('tukijuris:auth');
    return _bc;
  }
  ```
  (FAR-4, AR-NFR-1)
- [x] **B3** In `logout()` and `logoutAll()`: BEFORE returning, call `getAuthChannel()?.postMessage({ type: 'LOGOUT' })`. Place AFTER the server-side logout API call (so the message reflects committed state). (FAR-5)
- [x] **B4** Read `apps/web/src/lib/auth/AuthContext.tsx`. Locate AuthProvider's mount useEffect.
- [x] **B5** In that useEffect: register a listener:
  ```ts
  const bc = getAuthChannel();
  const onMessage = (e: MessageEvent) => {
    if (e.data?.type === 'LOGOUT') {
      // clear in-memory state + redirect to public path (same as onRefreshFailure)
    }
  };
  bc?.addEventListener('message', onMessage);
  return () => { bc?.removeEventListener('message', onMessage); /* + existing cleanups */ };
  ```
  (FAR-6, FAR-7, FAR-8)
- [x] **B6** Verify type-check passes: `cd apps/web && npx tsc --noEmit 2>&1 | grep -v AddCardModal | tail -5`.

## Batch C — Tests
Test files: 
- `apps/web/src/lib/auth/__tests__/AuthContext.test.tsx` (new or extend existing)
- `apps/web/src/components/__tests__/NotificationBell.test.tsx` (new)

Pattern: read Sprint 1 `change-password.test.tsx` and Sprint 2 `analytics.admin.test.tsx` for AuthContext mock + Vitest patterns.

- [x] **C1** FRT-1: NotificationBell uses authFetch. Mock authFetch via `vi.mock('@/lib/auth/authClient', () => ({ authFetch: vi.fn().mockResolvedValue(new Response(JSON.stringify({ count: 5 }))) }))`. Render component. Wait for fetch. Assert badge shows 5 + authFetch called with the notifications endpoint.
- [x] **C2** FRT-2: NotificationBell catch resets count. Mock authFetch to throw. Render. Wait for catch. Assert bellCount === 0 in DOM (e.g., badge hidden or shows 0).
- [x] **C3** FRT-3: AuthContext onRefreshFailure clears + redirects. Mount AuthProvider with mocked router. Trigger the onRefreshFailure callback (find it via the registered listener). Assert: user state becomes null + router.push to login path called.
- [x] **C4** FRT-4: AuthContext BroadcastChannel LOGOUT clears state. Mount AuthProvider. Get the BroadcastChannel instance. Post `{ type: 'LOGOUT' }`. Assert: user state becomes null.
- [x] **C5** (Optional, recommended) FRT-5: authClient.logout posts BroadcastChannel message. Spy on `BroadcastChannel.prototype.postMessage` (or the lazy bc instance). Call logout. Assert: postMessage called with `{ type: 'LOGOUT' }`.
- [x] **C6** (Optional) FRT-6: same for logoutAll.

## Batch D — Documentation + validation
- [x] **D1** `apps/api/AGENTS.md`: locate "POST /api/auth/refresh" section. Update its description to read: refresh_token is read from the **Cookie header** (FastAPI `Cookie(default=None)` parameter), NOT from the request body. Add a sentence pointing to `apps/web/AGENTS.md` as the source of truth for the cookie contract. (FAR-12)
- [x] **D2** `cd apps/web && npm test -- AuthContext.test 2>&1 | tail -10` — expect FRT-3 + FRT-4 (+ FRT-5/6 if added) green.
- [x] **D3** `cd apps/web && npm test -- NotificationBell.test 2>&1 | tail -10` — expect FRT-1 + FRT-2 green.
- [x] **D4** `cd apps/web && npm test 2>&1 | tail -10` — full suite. Baseline 216 + new ~6 = 222+. Zero NEW regressions vs baseline.
- [x] **D5** `cd apps/web && npx eslint src/components/NotificationBell.tsx src/lib/auth/authClient.ts src/lib/auth/AuthContext.tsx src/lib/auth/__tests__/AuthContext.test.tsx src/components/__tests__/NotificationBell.test.tsx 2>&1 | tail -10` — 0 errors AND 0 warnings on changed files.
- [x] **D6** `cd apps/web && npx tsc --noEmit 2>&1 | grep -v AddCardModal | tail -5` — 0 errors excluding pre-existing.
- [x] **D7** `git status --short` — expect ONLY these files (+ openspec change folder):
  - M apps/web/src/components/NotificationBell.tsx
  - M apps/web/src/lib/auth/authClient.ts
  - M apps/web/src/lib/auth/AuthContext.tsx
  - M or ?? apps/web/src/lib/auth/__tests__/AuthContext.test.tsx
  - ?? apps/web/src/components/__tests__/NotificationBell.test.tsx
  - M apps/api/AGENTS.md
  - ?? openspec/changes/frontend-auth-refresh-flow/
- [x] **D8** Save FINAL apply-progress to engram (topic_key sdd/frontend-auth-refresh-flow/apply-progress) with checkbox state + suggested commit message.
