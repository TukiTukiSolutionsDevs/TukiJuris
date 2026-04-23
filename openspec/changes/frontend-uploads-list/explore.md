# Explore — frontend-uploads-list

**Change**: `frontend-uploads-list`
**Sprint**: L2 audit gap (final)
**Date**: 2026-04-23
**Status**: completed

---

## Executive Summary

Users can POST file uploads but have zero UI to see or manage them. The blocker is that `GET /api/upload/` (list) does not exist — only `GET /api/upload/{id}` and `DELETE /api/upload/{id}` exist. This change requires work on both stacks: one new backend endpoint + a new "Archivos" tab in `/configuracion`.

The `UploadedDocument` model has all needed columns. The list endpoint is a straightforward SELECT with user_id filter + created_at DESC order — consistent with all other GET list endpoints in the codebase. No migration needed.

A critical discovery: **there is no binary file streaming endpoint**. `GET /api/upload/{id}` returns JSON metadata, not the file bytes. A "Descargar" button is therefore deferred to post-MVP (would require a new `GET /api/upload/{id}/file` endpoint). MVP delivers: list + delete.

---

## Backend Findings

### Model: `UploadedDocument` (`apps/api/app/models/uploaded_document.py`)

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `user_id` | UUID FK | indexed, CASCADE on user delete |
| `conversation_id` | UUID FK nullable | SET NULL on conversation delete |
| `original_filename` | str(500) | |
| `file_type` | str(50) | extension string: "pdf", "docx", "jpg", "png" — NOT MIME |
| `file_size` | int | bytes |
| `storage_path` | str(1000) | local disk path — **MUST NEVER be sent to FE** |
| `extracted_text` | text nullable | |
| `page_count` | int nullable | PDFs only |
| `created_at` | datetime(tz) | |

⚠️ **No `status` column** — the model has no status/state field.

### Existing endpoint shapes

```
POST /api/upload/
→ { id, filename, file_type, file_size, page_count, text_preview, extracted_length }

GET /api/upload/{doc_id}
→ { id, filename, file_type, file_size, page_count, extracted_text, conversation_id, created_at }

DELETE /api/upload/{doc_id}
→ { status: "deleted" }
  HARD DELETE — os.remove(storage_path) + db.delete(doc)
  Non-owner → 404 (not 403, project convention: no existence leak)
```

### Proposed: GET /api/upload/ (new)

```python
@router.get("/", response_model=list[UploadedDocumentListItem])
async def list_uploaded_documents(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
) -> list[dict]:
    result = await db.execute(
        select(UploadedDocument)
        .where(UploadedDocument.user_id == current_user.id)
        .order_by(UploadedDocument.created_at.desc())
    )
    docs = result.scalars().all()
    return [...]
```

**Response shape** (flat list, consistent with `/folders/` pattern):

```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "filename": "contrato-arrendamiento.pdf",
    "file_type": "pdf",
    "file_size": 204800,
    "page_count": 12,
    "conversation_id": "uuid-or-null",
    "created_at": "2026-04-23T12:34:56+00:00"
  }
]
```

Fields explicitly **excluded**: `storage_path`, `extracted_text`.

### Test patterns to reuse

- `tenant_pair` fixture — `client_a` / `client_b` async HTTP clients
- Upload via `files={"file": (filename, bytes, content_type)}`
- Project convention: non-owner access → 404 (never 403)
- Existing test file: `apps/api/tests/integration/test_upload.py`

---

## Frontend Findings

### Target location

`/configuracion` — currently 5 tabs: `perfil | organizacion | preferencias | apikeys | memoria`

**Recommendation: add "Archivos" as 6th tab** (`ActiveTab` union + TABS array + TAB_DETAILS entry).

Rationale: file management is a distinct concern from profile identity. The perfil tab is already dense (profile form + password panel + sessions list + logout-all).

### Components & patterns available

| Component/Pattern | Location | Usage |
|-------------------|----------|-------|
| `DisclosureCard` | `configuracion/page.tsx` (local) | Collapsible sections — reuse for "Mis archivos" list |
| `SectionCard` + `SectionHeader` | same | Base layout |
| `confirm()` | all existing deletes | `if (!confirm("Eliminar este archivo?")) return;` |
| `toast` from sonner | all tabs | Success/error feedback |
| `showSuccess(msg)` | same page | Local state banner (3s auto-dismiss) |
| `authFetch` | `useAuth()` | Authenticated requests |

### Download strategy

- `downloadBlob` at `@/lib/export/downloadBlob` exists and is battle-tested.
- **BLOCKER**: `GET /api/upload/{id}` returns JSON metadata — no binary stream.
- **Decision**: skip "Descargar" for MVP. Post-MVP requires `GET /api/upload/{id}/file` streaming endpoint.

### Confirm/delete pattern (project convention)

```typescript
const handleDeleteUpload = async (docId: string) => {
  if (!confirm("Eliminar este archivo? Esta acción es irreversible.")) return;
  const res = await authFetch(`/api/upload/${docId}`, { method: "DELETE" });
  if (res.ok) {
    showSuccess("Archivo eliminado");
    await loadUploads();
  }
};
```

### Utility functions needed

```typescript
// No existing formatFileSize helper found — create new
function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// Date: toLocaleDateString("es-AR")
```

---

## OQ Resolutions

| OQ | Decision | Rationale |
|----|----------|-----------|
| OQ1 | New **"Archivos" tab** | Distinct concern; perfil tab already dense |
| OQ2 | **Eliminar only** (confirm required); Descargar deferred | No binary endpoint exists |
| OQ3 | Newest first (fixed) | `ORDER BY created_at DESC` |
| OQ4 | No pagination for MVP | Most users < 20 uploads |
| OQ5 | "Todavía no subiste ningún archivo." | Consistent Spanish tone |
| OQ6 | `formatFileSize` + `toLocaleDateString('es-AR')` | Create inline util |

---

## Risks & Gotchas

| # | Risk | Mitigation |
|---|------|-----------|
| R1 | `storage_path` must never reach FE | Create explicit `UploadedDocumentListItem` Pydantic schema — no `model.dict()` shortcuts |
| R2 | No binary download endpoint | Document as known gap; deferred to post-MVP; don't render broken download button |
| R3 | Hard delete is irreversible | `confirm()` required; test: DELETE → 404 on subsequent GET |
| R4 | `file_type` is extension, not MIME | Display as-is (uppercase badge); no MIME mapping needed |
| R5 | No `status` column on model | Don't include status in specs or response shape |

---

## Files Affected

### Backend (new/modified)
- `apps/api/app/api/routes/upload.py` — add `GET /` list endpoint
- `apps/api/tests/integration/test_upload.py` — add list + ownership tests

### Frontend (new/modified)
- `apps/web/src/app/configuracion/page.tsx` — add "archivos" tab, state, handler, render
- `apps/web/src/app/configuracion/__tests__/uploads-tab.test.tsx` — new test file (Vitest + MSW)

---

## Next Recommended Phase

`sdd-propose` — write the formal proposal with backend spec + FE component design.
