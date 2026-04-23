## Verification Report

**Change**: frontend-uploads-list  
**Mode**: Standard  
**Status**: FAIL  
**Skill resolution**: none

---

### Executive Summary

Backend verification passed: `GET /api/upload/` is authenticated, rate-limited with `RateLimitBucket.READ`, filtered to the current user, sorted by `created_at DESC`, and returns an explicit 7-field schema that excludes `storage_path` and `extracted_text`.

Frontend implementation is mostly present and the targeted uploads tests pass, but the change does **not** meet the spec gate yet for two reasons: the byte formatter returns `B` instead of the required `bytes`, and the changed frontend test file introduces new TypeScript errors on changed files. Test coverage is also partial for exact-string compliance and retry/in-flight behaviors.

---

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total | 6 |
| Tasks complete | 0 |
| Tasks incomplete | 6 |

**Notes**
- `openspec/changes/frontend-uploads-list/tasks.md` still has every task unchecked, even though the code changes exist. This is a tracking-artifact mismatch, not proof that implementation is absent.

---

### Build / Typecheck / Lint / Tests Execution

**Backend full suite**: ✅ Passed  
Command: `docker exec tukijuris-api-1 pytest tests/ -q`

```text
1258 passed, 7 xfailed, 48 warnings in 65.95s
```

**Backend targeted upload tests**: ✅ Passed  
Command: `docker exec tukijuris-api-1 pytest tests/integration/test_upload.py -q`

```text
4 passed in 1.35s
```

**Frontend full suite**: ❌ Failed (pre-existing unrelated failures remain)  
Command: `npm test`

```text
Test Files  4 failed | 46 passed (50)
Tests  15 failed | 450 passed (465)
```

**Frontend targeted uploads tests**: ✅ Passed  
Command: `npm test -- src/app/configuracion/__tests__/uploads-tab.test.tsx src/app/configuracion/__tests__/uploads-formatters.test.ts`

```text
Test Files  2 passed (2)
Tests  14 passed (14)
```

**Typecheck**: ❌ Failed  
Command: `npx tsc --noEmit --pretty false`

```text
Changed-file errors:
- src/app/configuracion/__tests__/uploads-tab.test.tsx(133,57): TS2769
- src/app/configuracion/__tests__/uploads-tab.test.tsx(197,28): TS2322
- src/app/configuracion/__tests__/uploads-tab.test.tsx(245,7): TS2769
- src/app/configuracion/__tests__/uploads-tab.test.tsx(289,7): TS2769

Pre-existing out-of-scope error:
- src/components/trials/AddCardModal.tsx(25,48): TS2554
```

**ESLint on changed files**: ✅ Passed  
Command: `npx eslint src/app/configuracion/page.tsx src/app/configuracion/uploads-formatters.ts src/app/configuracion/__tests__/uploads-tab.test.tsx src/app/configuracion/__tests__/uploads-formatters.test.ts`

**Coverage**: ➖ Not available as usable evidence

```text
Backend targeted coverage command produced no collected data for the requested module.
Frontend coverage command failed: Cannot find dependency '@vitest/coverage-v8'.
```

---

### Spec Compliance Matrix

| Requirement | Scenario | Evidence | Result |
|-------------|----------|----------|--------|
| BE-UPLOAD-LIST | Authenticated list endpoint exists with safe schema | `apps/api/app/api/routes/upload.py:46-70` + `tests/integration/test_upload.py::test_list_uploads_populated` | ✅ COMPLIANT |
| BE-UPLOAD-LIST | Empty list returns `[]` | `tests/integration/test_upload.py::test_list_uploads_empty` | ✅ COMPLIANT |
| BE-UPLOAD-LIST | Private fields are absent | `tests/integration/test_upload.py::test_list_uploads_excludes_private_fields` | ✅ COMPLIANT |
| FE-UPLOADS-TAB | Lazy fetch only on tab activation | `uploads-tab.test.tsx::AT-1` | ✅ COMPLIANT |
| FE-UPLOADS-TAB | Loading state renders on fetch | `uploads-tab.test.tsx::AT-2` + `page.tsx:1980-1983` | ⚠️ PARTIAL |
| FE-UPLOADS-TAB | Empty state exact copy | `uploads-tab.test.tsx::AT-3` | ✅ COMPLIANT |
| FE-UPLOADS-TAB | Error state exact copy + retry behavior | `page.tsx:1985-1996` + `uploads-tab.test.tsx::AT-4` | ⚠️ PARTIAL |
| FE-UPLOADS-TABLE | Table renders filename/type/size/date/actions | `uploads-tab.test.tsx::AT-5` + `page.tsx:2005-2054` | ✅ COMPLIANT |
| FE-UPLOADS-TABLE | File size bytes formatting uses `X bytes` | `uploads-formatters.ts:11-14` + `uploads-formatters.test.ts:17-22` | ❌ FAILING |
| FE-UPLOADS-DELETE | Confirmed delete removes row and calls DELETE | `uploads-tab.test.tsx::AT-6` | ✅ COMPLIANT |
| FE-UPLOADS-DELETE | Failed delete reverts + error toast | `uploads-tab.test.tsx::AT-7` | ✅ COMPLIANT |
| FE-UPLOADS-DELETE | Cancelled delete is no-op | `uploads-tab.test.tsx::AT-8` | ✅ COMPLIANT |
| FE-UPLOADS-DELETE | Exact confirm copy + in-flight disabled/`aria-busy` | `page.tsx:894-911`, `2034-2040` | ⚠️ PARTIAL |
| FE-UPLOADS-TESTS | New frontend tests exist and run | targeted Vitest run: 14/14 passed | ✅ COMPLIANT |
| FE-UPLOADS-NFR | No new TSC errors on changed files | `npx tsc --noEmit --pretty false` | ❌ FAILING |

**Compliance summary**: 10 compliant / 3 partial / 2 failing

---

### Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| BE-UPLOAD-LIST | ✅ Implemented | `UploadedDocumentListItem` has exactly 7 fields and omits `storage_path` / `extracted_text`; route uses bearer dependency + `RateLimitBucket.READ`; query filters by `current_user.id` and orders DESC. |
| FE-UPLOADS-TAB | ✅ Implemented | `ActiveTab` includes `archivos`; `TABS` adds `Archivos` in 6th position; lazy fetch guarded by `activeTab === "archivos" && !uploadsLoaded`; loading/error/empty states exist inside `DisclosureCard`. |
| FE-UPLOADS-TABLE | ⚠️ Partial | Table structure, truncate, uppercase badge, date formatting, and no download action are implemented; byte-unit copy does not match spec (`B` vs `bytes`). |
| FE-UPLOADS-DELETE | ✅ Implemented | Exact confirm dialog, optimistic removal, revert-on-failure, toasts, and in-flight button state are present in source. |
| FE-UPLOADS-TESTS | ⚠️ Partial | Tests exist and pass, but they do not fully prove exact-string/error/retry/in-flight requirements. |
| FE-UPLOADS-NFR | ❌ Failing | Changed frontend test file introduces TypeScript errors. |

---

### Coherence (Design / Proposal)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Explicit backend whitelist schema to avoid leaks | ✅ Yes | Implemented via `UploadedDocumentListItem` mapping in `upload.py`. |
| Frontend Archivos tab inside configuration with DisclosureCard | ✅ Yes | Implemented in `page.tsx`. |
| Native confirm + optimistic delete + toast feedback | ✅ Yes | Implemented in `handleDeleteUpload`. |
| Design document alignment | ➖ Skipped by override | No `design.md`; not flagged per verifier override for small changes. |

---

### Issues Found

#### CRITICAL

1. **Byte formatter violates the spec string contract**  
   - File: `apps/web/src/app/configuracion/uploads-formatters.ts:11-14`  
   - Evidence: values under 1024 render as `${bytes} B`, but the spec requires `X bytes`.  
   - Reinforced by tests: `apps/web/src/app/configuracion/__tests__/uploads-formatters.test.ts:17-22` asserts `0 B`, `1 B`, `512 B`, `1023 B`, encoding the wrong contract.

2. **Changed frontend test file introduces new TypeScript errors**  
   - File: `apps/web/src/app/configuracion/__tests__/uploads-tab.test.tsx:133,197,245,289`  
   - Evidence: `npx tsc --noEmit --pretty false` fails with `TS2769` and `TS2322` in the changed file.  
   - This breaks the explicit NFR: no new TypeScript errors on changed files.

#### WARNING

1. **Exact-string coverage is incomplete in frontend integration tests**  
   - File: `apps/web/src/app/configuracion/__tests__/uploads-tab.test.tsx:175-194,223-299`  
   - The tests do not assert the exact error copy `No se pudieron cargar los archivos.`, the retry label text, or the exact confirm message `¿Eliminar "{filename}"? Esta acción no se puede deshacer.`

2. **Retry behavior and in-flight accessibility state are not behaviorally proven**  
   - File: `apps/web/src/app/configuracion/__tests__/uploads-tab.test.tsx:175-194,223-272`  
   - Source implements retry and `aria-busy`/disabled state, but tests do not click retry or assert disabled/`aria-busy` while the delete request is in flight.

3. **Task artifact was not updated**  
   - File: `openspec/changes/frontend-uploads-list/tasks.md:5-55`  
   - All six tasks remain unchecked, so completeness tracking is stale.

4. **Apply-progress test counts are inaccurate**  
   - Evidence: targeted frontend run shows **14** passing uploads tests total, not 18. Current file counts are 8 integration tests in `uploads-tab.test.tsx` and 6 unit tests in `uploads-formatters.test.ts`.

#### SUGGESTION

1. Add explicit assertions for the retry button text, exact error copy, exact confirm copy, and delete-button in-flight state so the tests prove the user-facing contract, not just DOM presence.

---

### Verdict

**FAIL**

The backend portion is ready, but the overall change cannot pass verification yet because the frontend violates the specified byte-format contract and the changed test file introduces new TypeScript errors.

---

### Requested Deliverables Snapshot

- **status**: fail
- **next_recommended**: sdd-apply
- **artifacts**:
  - Engram: `sdd/frontend-uploads-list/verify-report`
  - OpenSpec: `openspec/changes/frontend-uploads-list/verify-report.md`
