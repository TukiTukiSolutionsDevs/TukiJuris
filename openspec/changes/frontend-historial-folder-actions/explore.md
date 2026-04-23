# Explore — frontend-historial-folder-actions

**Phase**: explore  
**Date**: 2026-04-22  
**Change**: frontend-historial-folder-actions  
**Audit bucket**: H7

---

## 1. Backend Endpoint Inventory

All folder-scoped routes live in `apps/api/app/api/routes/folders.py`.  
All endpoints require Bearer auth (`get_current_user` dependency).

| Method | Path | Schema | Business rules |
|--------|------|--------|----------------|
| `GET` | `/api/folders/` | → `list[FolderOut]` | Ordered by position, then name. Returns conversation_count per folder. |
| `POST` | `/api/folders/` | `FolderCreate { name: 1-200, icon: ≤50, default="folder" }` → `FolderOut 201` | Max 10 folders/user. 409 on duplicate name. |
| `PUT` | `/api/folders/{folder_id}` | `FolderUpdate { name?, icon?, position? }` → `FolderOut` | 404 if not found/not owned. 409 on duplicate name (excluding self). |
| `DELETE` | `/api/folders/{folder_id}` | → 204 | Conversations set to folder_id=NULL (explicit UPDATE, not cascade). |
| `PUT` | `/api/conversations/{id}/folder/{folder_id}` | → `{ detail }` | Verifies ownership of both conversation and folder. |
| `DELETE` | `/api/conversations/{id}/folder` | → 204 | Sets conversation.folder_id = NULL. |

**Key schemas:**

```python
class FolderOut:
    id: uuid.UUID
    name: str
    icon: str
    position: int
    conversation_count: int
    created_at: str  # ISO string

class FolderUpdate:
    name: str | None  # 1-200 chars
    icon: str | None  # ≤50 chars
    position: int | None
```

---

## 2. Frontend Historial Inventory

**File**: `apps/web/src/app/historial/page.tsx` (1139 lines, monolith — no sub-components)

### What EXISTS in the UI

| Action | Handler | API call | UX pattern |
|--------|---------|----------|------------|
| List folders | `fetchFolders()` | `GET /api/folders/` | Sidebar section, collapsible |
| Create folder | `handleCreateFolder()` | `POST /api/folders/` | Inline form in sidebar (+ button → input → Enter/Crear) |
| Delete folder | `handleDeleteFolder()` | `DELETE /api/folders/{id}` | X icon on hover, `window.confirm()` guard |
| Move conversation to folder | `handleMoveToFolder(convId, folderId)` | `PUT /api/conversations/{id}/folder/{folderId}` | Per-conversation dropdown (FolderInput icon on hover) |
| Remove conversation from folder | `handleMoveToFolder(convId, null)` | `DELETE /api/conversations/{id}/folder` | Same dropdown, "Quitar de carpeta" option |
| Filter by folder | `setActiveFolderFilter()` | — (client-side) | Sidebar folder click |

### What is MISSING — H7 Gap

| Action | Backend endpoint | Frontend | Gap |
|--------|-----------------|----------|-----|
| **Rename folder** | `PUT /api/folders/{id}` with `{ name }` | ❌ No handler, no UI | **THE H7 GAP** |
| Update icon | `PUT /api/folders/{id}` with `{ icon }` | ❌ No UI | Minor (low priority) |
| Reorder folders | `PUT /api/folders/{id}` with `{ position }` | ❌ No UI | Out of scope |

**Conclusion**: H7 is NARROWLY scoped — the ONLY missing folder action is **rename**. Create, delete, move, list are all implemented and functional.

---

## 3. Existing Tests for Historial

**Zero tests.** The directory `apps/web/src/app/historial/` contains only `page.tsx`.  
No MSW handlers for `/api/folders/` have been found in the test setup (needs verification during propose phase).

---

## 4. Precedents to Reuse

### Inline Edit (Tags — identical pattern)

Tags in the same page implement a complete inline-edit flow:

```tsx
// State
const [editingTag, setEditingTag] = useState<TagItem | null>(null);

// Trigger: Edit2 icon appears on group-hover
<button onClick={() => setEditingTag({ ...t })}>
  <Edit2 className="w-3 h-3" />
</button>

// Edit mode: replaces the row
<input
  autoFocus
  value={editingTag.name}
  onChange={(e) => setEditingTag({ ...editingTag, name: e.target.value })}
  onKeyDown={(e) => {
    if (e.key === "Enter") handleUpdateTag(editingTag);
    if (e.key === "Escape") setEditingTag(null);
  }}
/>
// + Save / Cancel buttons
```

**Exact same pattern applies to folder rename** — state `editingFolderId + editingFolderName`, Edit2 icon on hover, input inline in sidebar, Enter/Escape handling.

### Confirm Dialog (Destructive actions)
`window.confirm()` is used consistently for delete folder and delete conversation. Pattern is established (not ideal, but consistent — do not introduce a different dialog pattern in H7 unless explicitly requested).

### Action Loading State
`folderActionLoading: string | null` already exists. Extend with rename loading: use `folderActionLoading === folder.id + "rename"` or a separate `renamingFolderId` state.

### Toast (Sonner — NOT used in historial)
`sonner` is installed. The historial page has ZERO toast calls — all API errors are silently swallowed (`if (!res.ok) return`). The rename flow should introduce toasts for success + 409 conflict error (first usage of sonner on this page).

---

## 5. Open Questions with Recommended Defaults

| # | Question | Recommended Default | Rationale |
|---|----------|-------------------|-----------|
| OQ1 | Which folder actions are in scope? | **Rename only** | All others (create, delete, move) are already implemented. Backend also supports icon/position but those are out of scope. |
| OQ2 | Rename UX — inline edit vs. modal | **Inline edit in sidebar** | Tags already use this exact pattern in the same file. Zero new components needed. |
| OQ3 | Delete UX | **Keep window.confirm()** | Already implemented. Don't change it in H7. |
| OQ4 | Move UX | **Already done** (dropdown picker) | No work needed. |
| OQ5 | Empty-folder delete behavior | **SET NULL (backend handles)** | Confirmed in code: `UPDATE conversations SET folder_id=NULL WHERE folder_id=?` before delete. Frontend already confirms "Las conversaciones no se eliminaran." |
| OQ6 | Test coverage depth | **Integration test per action with MSW** | historial has 0 tests — any new feature needs MSW handlers for folders + test for rename (happy path + 409 conflict). |

---

## 6. Risks and Gotchas

| Risk | Severity | Detail |
|------|----------|--------|
| **409 not surfaced to user** | HIGH | `handleCreateFolder` and all other folder handlers do `if (!res.ok) return` silently. The 409 "Ya existe una carpeta con ese nombre" error from the server is never shown. Rename MUST handle this or users see nothing on duplicate name. |
| **No toasts on this page** | MEDIUM | Historial is the only page that uses zero sonner toasts. Rename is the right moment to introduce them. First call establishes the pattern for the page. |
| **Monolith page.tsx** | MEDIUM | 1139 lines, all inline. Rename adds ~40 lines of state + JSX. Consider extracting `FolderSidebarItem` component as part of implementation to keep it manageable. |
| **authFetch missing from useCallback deps** | LOW | Pre-existing: `fetchConversations` deps array is `[tab]` but uses `authFetch`. Do NOT touch — this is a pre-existing lint issue. |
| **MAX_FOLDERS_PER_USER=10 not surfaced** | LOW | Backend returns 400 when limit hit. Frontend silently ignores. Not H7 but worth a follow-up. |
| **position/icon fields ignored by frontend** | LOW | Backend accepts them; frontend never sends them on update. Rename should only send `{ name }` — confirmed safe (all FolderUpdate fields are optional). |
| **Optimistic vs. pessimistic UI** | LOW | Current pattern is pessimistic (refetch after every action). Keep consistent — rename calls `PUT`, then `fetchFolders()`. No optimistic update needed. |

---

## 7. Implementation Sketch (for propose phase)

**New state needed:**
```tsx
const [editingFolderId, setEditingFolderId] = useState<string | null>(null);
const [editingFolderName, setEditingFolderName] = useState("");
```

**New handler:**
```tsx
const handleRenameFolder = async (folderId: string) => {
  const trimmed = editingFolderName.trim();
  if (!trimmed) return;
  setFolderActionLoading(folderId + "rename");
  try {
    const res = await authFetch(`/api/folders/${folderId}`, {
      method: "PUT",
      body: JSON.stringify({ name: trimmed }),
    });
    if (res.status === 409) {
      toast.error("Ya existe una carpeta con ese nombre");
      return;
    }
    if (!res.ok) { toast.error("Error al renombrar carpeta"); return; }
    setEditingFolderId(null);
    toast.success("Carpeta renombrada");
    fetchFolders();
  } finally {
    setFolderActionLoading(null);
  }
};
```

**UX placement:** Edit2 icon appears on the folder row on hover (same as tags), replacing the delete X temporarily with an input field while editing.

---

## Artifact Metadata

- **topic_key**: `sdd/frontend-historial-folder-actions/explore`
- **next_recommended**: sdd-propose
- **skill_resolution**: none (RF-6)
