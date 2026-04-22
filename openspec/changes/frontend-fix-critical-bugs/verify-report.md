## Verification Report

**Change**: frontend-fix-critical-bugs  
**Project**: tukijuris  
**Mode**: Standard  
**Scope**: Focused post-remediation re-verify for FIX-1..FIX-4 only

---

### Completeness

| Metric | Value |
|---|---:|
| Tasks total | 28 |
| Tasks complete (`- [x]`) | 28 |
| Tasks incomplete (`- [ ]`) | 0 |

- ✅ Remediation footer comment present in `openspec/changes/frontend-fix-critical-bugs/tasks.md`

---

### Fix-by-fix Verification

| Fix | Evidence | Verdict |
|---|---|---|
| FIX-1 (FCB-6 + FCT-9) | `page.tsx:535-543` now uses `setTimeout(async () => { try { await logout() } finally { router.push("/login") } }, 1500)` for the 401 session-expiry path. `change-password.test.tsx:310-334` adds FCT-9 with `changePasswordError(null, 401)`, asserts `"Tu sesión expiró..."`, then verifies logout + redirect after the 1500 ms callback. | PASS |
| FIX-2 (FCT-1 form-reset) | `change-password.test.tsx:255-265` asserts the success toast first, then all 3 inputs are `""`, before the 1500 ms callback is invoked at `267-274`. | PASS |
| FIX-3 (tasks.md ticked) | `tasks.md` contains 28 completed checklist items and the remediation footer comment at line 52. | PASS |
| FIX-4 (lint warnings cleared) | ESLint JSON for the 3 changed files reports `errorCount: 0` and `warningCount: 0` for each file. | PASS |

---

### Validation Execution

**Changed-file lint** — `cd apps/web && npx eslint src/app/configuracion/page.tsx src/test/msw/handlers.ts src/app/configuracion/__tests__/change-password.test.tsx`

- ✅ `page.tsx`: 0 errors / 0 warnings
- ✅ `handlers.ts`: 0 errors / 0 warnings
- ✅ `change-password.test.tsx`: 0 errors / 0 warnings

**Targeted suite** — `cd apps/web && npm test -- src/app/configuracion/__tests__/change-password.test.tsx`

- ✅ 9 passed / 0 failed

**Full suite** — `cd apps/web && npm test`

- ✅/⚠️ 206 passed / 15 failed / 221 total
- ✅ Matches applier baseline for this remediation pass: 206 / 15
- ✅ Regressions introduced by this change: 0

**Type-check (filtered)** — `cd apps/web && npx tsc --noEmit | grep -v AddCardModal`

- ✅ No changed-file TypeScript errors after excluding the known pre-existing `AddCardModal.tsx` issue

**Scope integrity** — `git status --short apps/web/ openspec/changes/frontend-fix-critical-bugs/`

- ✅ `M apps/web/src/app/configuracion/page.tsx`
- ✅ `M apps/web/src/test/msw/handlers.ts`
- ✅ `D apps/web/src/lib/api.ts`
- ✅ `?? apps/web/src/app/configuracion/__tests__/change-password.test.tsx`
- ✅ `?? openspec/changes/frontend-fix-critical-bugs/`

---

### authFetch Dependency Risk Review

**Verdict**: ACCEPT

**Evidence**:

- `apps/web/src/lib/auth/AuthContext.tsx:33-41` imports a module-level function: `authFetch as clientAuthFetch`
- `apps/web/src/lib/auth/AuthContext.tsx:241` exposes `authFetch: clientAuthFetch`

This means the context value reuses a stable module reference, not a freshly created inline function each render. Adding `authFetch` to `useCallback` dependencies in `page.tsx` is therefore correct and does **not** create the re-run risk described by the applier note.

---

### Issues Found

**CRITICAL**

None.

**WARNING**

None for the focused remediation scope.

**SUGGESTION**

1. File backlog: `AddCardModal.tsx` tsc error + 51 pre-existing lint problems.

---

### Verdict

**READY-TO-COMMIT**

All four remediation fixes are verified with source evidence plus runtime validation. The targeted suite is now 9/9, changed-file lint is clean, filtered type-check is clean, scope matches expectations, and the `authFetch` dependency risk is acceptable because the reference is stable in `AuthContext`.
