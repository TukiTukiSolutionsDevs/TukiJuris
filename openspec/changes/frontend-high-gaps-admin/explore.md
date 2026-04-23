# Explore — frontend-high-gaps-admin

**Date**: 2026-04-22  
**HEAD**: b9e4cba (Sprint 6)  
**Gaps**: H1 Dev API Keys · H2 Sessions · H5 RBAC Admin · H6 Audit Log

---

## 1. Backend Endpoint Inventory

### H1 — Dev API Keys (`/api/keys/`)

| Verb | Path | Auth | Scope |
|------|------|------|-------|
| `POST` | `/api/keys/` | `get_current_user` | User-scoped |
| `GET` | `/api/keys/` | `get_current_user` | User-scoped |
| `PUT` | `/api/keys/{key_id}` | `get_current_user` (owner check) | User-scoped |
| `DELETE` | `/api/keys/{key_id}` | `get_current_user` (owner check) | User-scoped |

**Request — create** (`APIKeyCreate`):
```json
{ "name": "string", "scopes": ["query","search"], "expires_in_days": null }
```
Valid scopes: `query`, `search`, `analyze`, `documents`.

**Response — create** (`APIKeyCreated` — **full_key returned ONCE only**):
```json
{
  "id": "uuid", "name": "string", "key_prefix": "ak_xxxxx",
  "scopes": ["query"], "is_active": true,
  "last_used_at": null, "expires_at": null,
  "rate_limit_per_minute": 60, "created_at": "iso8601",
  "full_key": "ak_<40hex>"   // ← ONE TIME ONLY, not stored in DB
}
```

**Response — list** (`APIKeyResponse[]`): same shape minus `full_key`.  
**No entitlement gate** — available to all authenticated users (unlike BYOK which requires `pro` plan).  
Soft-delete: `DELETE` sets `is_active=False`, row is kept.

---

### H2 — Sessions (`/api/auth/sessions`)

| Verb | Path | Auth | Scope |
|------|------|------|-------|
| `GET` | `/api/auth/sessions` | `get_current_user` | User-scoped |
| `POST` | `/api/auth/logout` | cookie-based | User-scoped (current session) |
| `POST` | `/api/auth/logout-all` | `get_current_user` | User-scoped (all sessions) |

**Response — list** (`SessionResponse[]`):
```json
[{ "jti": "uuid", "family_id": "uuid", "created_at": "iso8601", "expires_at": "iso8601" }]
```

**⚠️ CRITICAL GAP**: No `user_agent` or `ip_address` in `SessionResponse` — only timestamps and token IDs.  
**⚠️ CRITICAL GAP**: No per-session revoke by `jti` endpoint exists. `POST /logout` only revokes the *current* session via the refresh cookie. Only option to revoke a specific OTHER session is `logout-all`.

---

### H5 — RBAC Admin (`/api/admin/`)

| Verb | Path | Permission | Scope |
|------|------|------------|-------|
| `GET` | `/api/admin/roles` | `roles:read` | Admin-scoped |
| `GET` | `/api/admin/roles/{role_id}/permissions` | `roles:read` | Admin-scoped |
| `POST` | `/api/admin/users/{user_id}/roles` | `roles:write` | Admin-scoped |
| `DELETE` | `/api/admin/users/{user_id}/roles/{role_id}` | `roles:write` | Admin-scoped |

**Request — assign** (`UserRoleAssign`): `{ "role_id": "uuid" }`  
**Response — assign** (`UserRoleResponse`):
```json
{ "role_id": "uuid", "role_name": "admin", "assigned_at": "iso8601", "assigned_by": "uuid", "expires_at": null }
```

**Self-demotion protection**: `DELETE` returns `409 CANNOT_REVOKE_OWN_ADMIN` if caller would lose their last admin role.  
**Backend service method exists**: `RBACService.get_user_roles(user_id)` — but **NO HTTP route** exposes it.  
**⚠️ BACKEND GAP**: Missing `GET /api/admin/users/{user_id}/roles` endpoint. Required for showing current roles per user in the UI.

---

### H6 — Audit Log (`/api/admin/audit-log`)

| Verb | Path | Permission | Scope |
|------|------|------------|-------|
| `GET` | `/api/admin/audit-log` | `audit_log:read` | Admin-scoped |

**Query params**: `page` (default 1), `page_size` (1-100, default 20), `user_id` (UUID), `action` (str), `resource_type` (str), `date_from` (datetime), `date_to` (datetime).

**Response** (`AuditLogPage`):
```json
{
  "items": [{
    "id": "uuid", "user_id": "uuid", "action": "role.assign",
    "resource_type": "user", "resource_id": "uuid",
    "before_state": {}, "after_state": {},
    "ip_address": "1.2.3.4", "created_at": "iso8601"
  }],
  "total": 100, "page": 1, "page_size": 20
}
```

Fully featured — filters by actor/action/resource_type/date range. No export endpoint.

---

## 2. Frontend Existing Admin Surface

### `/admin` page (`apps/web/src/app/admin/page.tsx`)
Single monolithic `"use client"` page. Sections:
- System stats (users, orgs, queries, conversations)
- KB health (embedding coverage, chunks by area)
- **Users table** — paginated, shows email/plan/org/queries/byok_count, NO role column, NO role actions
- BYOKTable (admin BYOK keys view)
- InvoicesTable
- Recent queries activity

No tabs, no sub-routes under `/admin/`.

### `/admin/layout.tsx`
Client-side guard: `user.isAdmin === true` → renders children, else redirect.  
Pattern: `useAuth()` → `{ isLoading, user }`.

### `/configuracion` page (`apps/web/src/app/configuracion/page.tsx`)
Tabbed layout (sidebar desktop / horizontal scroll mobile). Tabs:
- `perfil` — profile info + change password + **logout-all button** (exists, tested)
- `organizacion`
- `preferencias`
- `memoria`
- `apikeys` — **manages BYOK LLM keys** (`/api/keys/llm-keys`), NOT dev API keys

**Dev API keys** (`/api/keys/`) have **zero frontend UI** anywhere.  
**Sessions list** (`GET /api/auth/sessions`) has **zero frontend UI** anywhere.

---

## 3. Per-Gap UI Target Pages

| Gap | Target page | Placement | New sub-page? |
|-----|-------------|-----------|---------------|
| H1 Dev API Keys | `/configuracion` | New tab `devkeys` OR sub-section inside `apikeys` tab | No |
| H2 Sessions | `/configuracion` | New section in `perfil` tab (below logout-all) OR new `sesiones` tab | No |
| H5 RBAC Admin | `/admin` | Inline role dropdown per user row (expand on click) | No |
| H6 Audit Log | `/admin` | New tabbed nav on admin page, `audit-log` tab | No (unless admin gets full tab nav) |

---

## 4. Existing Test Coverage (Admin)

```
apps/web/src/app/admin/__tests__/layout.test.tsx         — 5 tests (layout guard)
apps/web/src/app/admin/_components/__tests__/
  BYOKTable.test.tsx        — 8 tests (list/empty/403-silent/pagination)
  BYOKBadge.test.tsx        — exists
  InvoicesTable.test.tsx    — exists
  RevenueCards.test.tsx     — exists
  UsersPagination.test.tsx  — exists
  AdminTrialsTable.test.tsx — exists
apps/web/src/app/configuracion/__tests__/
  logout-all.test.tsx       — 3 tests (button render, click, no accidental call)
  change-password.test.tsx  — exists
```

**Admin test render pattern** (from `layout.test.tsx`):
```tsx
vi.mock("@/lib/auth/AuthContext", () => ({
  useAuth: () => ({ user: { isAdmin: true }, isLoading: false }),
}));
// No tk_admin cookie mock needed — layout uses in-memory user.isAdmin from JWT
```

**Component test pattern** (from `BYOKTable.test.tsx`):
```tsx
vi.mock("@/lib/api/admin", () => ({ fetchBYOK: vi.fn() }));
// Self-fetching components mock their fetch helper, not authFetch directly
// 403 → silent null render
// 500 → error message
// loading state → spinner text
```

---

## 5. Precedents to Reuse

| Need | Existing precedent | File |
|------|--------------------|------|
| List + create + delete table | `BYOKTable.tsx` | `admin/_components/BYOKTable.tsx` |
| Paginated table | `UsersPagination.tsx` | `admin/_components/UsersPagination.tsx` |
| Tab navigation | `configuracion/page.tsx` (`activeTab` state pattern) | full page |
| Confirm for destructive actions | `window.confirm()` — used throughout | `configuracion/page.tsx` |
| Copy-to-clipboard | **NONE** — not in codebase, must implement | — |
| Permission gate | `hasPermission("roles:write")` from `useAuth()` | `admin/page.tsx:171` |
| 403-silent-unmount | `BYOKTable.tsx` pattern | `admin/_components/BYOKTable.tsx` |
| Error/success toast | `sonner` toasts (check usage) + inline alert pattern | configuracion |

**No dedicated `ConfirmDialog` component** — uses browser `confirm()`. For revoke-key and revoke-role, this is acceptable (matches existing pattern).

---

## 6. Effort Estimation

| Gap | UI Lines (est.) | Test Lines (est.) | Difficulty | Notes |
|-----|-----------------|-------------------|------------|-------|
| H1 Dev API Keys | ~280 | ~120 | **M** | Show-once modal + copy-button (new component) |
| H2 Sessions | ~120 | ~70 | **S** | Read-only list; no per-session revoke available |
| H5 RBAC Admin | ~200 + backend route | ~130 | **M** | Backend gap: need GET /admin/users/{id}/roles |
| H6 Audit Log | ~350 | ~160 | **L** | Filters + date range + JSON expansion + pagination |

---

## 7. Open Questions (OQ)

### H1 — Dev API Keys
- **OQ-H1-1**: Available to all plans or plan-gated? Backend has no gate — is this intentional?
- **OQ-H1-2**: Should `apikeys` tab be split into "Dev Keys" + "BYOK LLM Keys" sub-sections, or a new separate tab `devkeys`?
- **OQ-H1-3**: Scopes UI — checkboxes (4 options) or multi-select?
- **OQ-H1-4**: Show revoked keys in the list or hide them? (Backend returns all including `is_active=false`)

### H2 — Sessions
- **OQ-H2-1**: No `user_agent`/`ip_address` in `SessionResponse`. Show generic "Session" rows with only dates?
- **OQ-H2-2**: No per-session revoke endpoint. UI should clarify: can only revoke ALL. Acceptable?
- **OQ-H2-3**: New `sesiones` tab or inline section in `perfil` tab?

### H5 — RBAC Admin
- **OQ-H5-1**: Backend needs `GET /api/admin/users/{user_id}/roles` — add in same sprint or pre-req?
- **OQ-H5-2**: Inline dropdown per user row vs. expandable role panel per user?
- **OQ-H5-3**: Should assigning `super_admin` require an extra confirmation?

### H6 — Audit Log
- **OQ-H6-1**: PII redaction — `resource_id`/`before_state`/`after_state` may contain email/personal data. Mask for non-super_admin?
- **OQ-H6-2**: Export to CSV? Backend has no export endpoint.
- **OQ-H6-3**: Date pickers — native `<input type="date">` or custom component?
- **OQ-H6-4**: Admin page gets a proper tab nav (H5 + H6 each a tab), or audit log is a new `/admin/audit-log` sub-page?

---

## 8. Risks

| Risk | Gap | Severity |
|------|-----|----------|
| Secret exposure: `full_key` returned once — if user closes modal before copying, key is lost forever | H1 | CRITICAL |
| No plan gate on dev API keys backend — inconsistent with BYOK (which requires `pro`) | H1 | MEDIUM |
| No per-session revoke by `jti` — only logout-all available. UI must communicate this limitation | H2 | MEDIUM |
| Missing `GET /api/admin/users/{user_id}/roles` route — backend blocker for H5 UI | H5 | HIGH |
| Self-escalation: backend protects self-demotion but not assigning `super_admin` to arbitrary users | H5 | HIGH |
| PII in audit log `before_state`/`after_state` JSON — no redaction, admin-only but compliance concern | H6 | MEDIUM |
| Admin page is a 846-line monolith — adding tabs + audit log + RBAC may require a refactor first | H5+H6 | MEDIUM |

---

## 9. Recommended Batching

**SPLIT into Sprint 7a + Sprint 7b.**

**Sprint 7a** — `/configuracion` changes (H1 + H2):
- H1: Dev API keys tab/section — create/list/revoke + show-once modal + copy button
- H2: Sessions list section in `perfil` tab
- Natural grouping: same page, user-scoped, no admin permission needed
- Estimated: ~400 UI lines + ~190 test lines

**Sprint 7b** — `/admin` changes (H5 + H6) + 1 backend route:
- Pre-req: `GET /api/admin/users/{user_id}/roles` backend route (small, ~15 lines using existing `RBACService.get_user_roles`)
- H5: Role assignment UI in users table
- H6: Audit log tab (requires admin page tab nav refactor first)
- Estimated: ~550 UI lines + ~290 test lines

**Why not single sprint?** Audit log alone is L-difficulty and the admin page refactor (adding tab nav) is risky on a 846-line component. Better to de-risk each group separately.

---

## Artifacts
- **engram**: `sdd/frontend-high-gaps-admin/explore`
- **openspec**: `openspec/changes/frontend-high-gaps-admin/explore.md`
