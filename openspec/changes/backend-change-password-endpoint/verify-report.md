# Verification Report — backend-change-password-endpoint (post-remediation)

**Change**: backend-change-password-endpoint  
**Project**: tukijuris  
**Mode**: Standard  
**Date**: 2026-04-22

## Overall Verdict

**READY-TO-COMMIT**

Post-remediation re-verification confirms the four flagged items are fixed:

- **FIX-1 PASS** — CP-3 guard now uses `if not current_user.hashed_password:`.
- **FIX-2 PASS** — success path contains exactly one `await db.commit()` and Redis denylist writes occur after commit, with an explicit best-effort audit comment.
- **FIX-3 PASS** — T-04 is split into two tests: a mocked branch-coverage test and a real DB OAuth-user test using `hashed_password=""`.
- **FIX-4 PASS** — `tasks.md` now shows **25/25** checked tasks and includes the remediation footer comment.

Validation also re-passed independently:

- change-password suite: **10 passed**
- auth subset: **149 passed, 1103 deselected, 0 regressions**
- OAuth spot-check: **2 passed**
- Ruff lint: **pass**
- Ruff format: **pass**

## Fix-by-fix Verification

### FIX-1 — CP-3 guard

**Verdict: PASS**

Quoted handler line:

```python
763:     if not current_user.hashed_password:
```

This correctly covers both `None` and `""`.

### FIX-2 — Single transaction + post-commit Redis

**Verdict: PASS**

Relevant lines:

```python
807:     # CP-9 (DB part): Emit audit event — NO password material
808:     # Audit is best-effort: do not abort password change on audit failure (conscious trade-off).
819:     # Single commit — atomic: password update + session revoke + audit (NFR-2)
820:     await db.commit()
822:     # CP-8 (Redis part): Post-commit denylist writes (per AGENTS.md: DB first, Redis post-commit)
830:                 await denylist.add(jti, ttl_seconds=ttl)
```

Findings:

- exactly **one** `await db.commit()` appears in the handler success path
- `denylist.add()` happens **after** line 820 commit
- the audit trade-off comment exists at lines **807-808**

### FIX-3 — T-04 split

**Verdict: PASS**

Confirmed test names:

- `test_change_password_oauth_user_branch_coverage`
- `test_change_password_oauth_user_real_db`

Behavioral checks:

- mocked branch test uses `MagicMock` + `hashed_password = None`
- real DB test creates `User(... hashed_password="", auth_provider="microsoft")`
- both assert **400** and `detail["code"] == "oauth_password_unsupported"`

Quoted assertions:

```python
112:         assert res.status_code == 400
114:         assert detail["code"] == "oauth_password_unsupported"
153:     assert res.status_code == 400
155:     assert detail["code"] == "oauth_password_unsupported"
```

### FIX-4 — tasks.md

**Verdict: PASS**

Task counts from `tasks.md`:

- `- [x]`: **25**
- `- [ ]`: **0**

Footer present:

```md
<!-- Remediation pass 2026-04-22: FIX-1 (CP-3 guard) + FIX-2 (single transaction) + FIX-3 (T-04 real DB user). See apply-progress + verify-report-2 in engram. -->
```

## Validation Commands

### Runtime note

The requested host-shell commands were NOT executable as-is because this shell exposes `/usr/bin/python3` = **Python 3.9.6**, while `apps/api/pyproject.toml` requires **Python >= 3.12** and `tests/conftest.py` imports `datetime.UTC`.

Independent verification therefore used the already running `docker compose` **api** service (`Python 3.12.13`), which is the correct project runtime.

### 1) New suite

Command executed:

```bash
docker compose exec -T api sh -lc 'cd /app && python -m pytest tests/test_auth_change_password.py -v --tb=short'
```

Result:

```text
10 passed, 1 warning in 3.30s
```

### 2) Auth subset

Command executed:

```bash
docker compose exec -T api sh -lc 'cd /app && python -m pytest tests/ -k "auth" -v --tb=short 2>&1 | tail -10'
```

Result:

```text
149 passed, 1103 deselected, 16 warnings in 8.01s
```

### 3) Lint

Command executed:

```bash
docker compose exec -T api sh -lc 'cd /app && python -m ruff check app/api/routes/auth.py tests/test_auth_change_password.py'
```

Result:

```text
All checks passed!
```

### 4) Format

Command executed:

```bash
docker compose exec -T api sh -lc 'cd /app && python -m ruff format --check app/api/routes/auth.py tests/test_auth_change_password.py'
```

Result:

```text
2 files already formatted
```

### 5) Scope integrity

Command executed:

```bash
git status --short --untracked-files=all apps/api/ openspec/changes/backend-change-password-endpoint/
```

Result:

```text
 M apps/api/app/api/routes/auth.py
?? apps/api/tests/test_auth_change_password.py
?? openspec/changes/backend-change-password-endpoint/proposal.md
?? openspec/changes/backend-change-password-endpoint/spec.md
?? openspec/changes/backend-change-password-endpoint/tasks.md
?? openspec/changes/backend-change-password-endpoint/verify-report.md
```

This matches the expected scope exactly.

### 6) Pre-existing drift check

Command executed:

```bash
git status --short apps/web/ docker-compose.yml 2>&1 | head
```

Result: **no output**

Interpretation: no new drift was introduced in `apps/web/` or `docker-compose.yml` by this change.

## CP-3 Spot-check

The empty-string OAuth path is covered by:

- `test_change_password_oauth_user_real_db`

It asserts:

```python
153:     assert res.status_code == 400
155:     assert detail["code"] == "oauth_password_unsupported"
```

Standalone OAuth command:

```bash
docker compose exec -T api sh -lc 'cd /app && python -m pytest tests/test_auth_change_password.py -v -k "oauth" --tb=short'
```

Result:

```text
2 passed, 8 deselected in 0.07s
```

## Issues Found

**CRITICAL**: None

**WARNING**: None blocking. Existing pytest warnings remain, but no new failures or regressions were introduced by this change.

**CONCERN**: Host shell runtime mismatch (`python` absent, `python3` = 3.9) means backend verification must use the container/runtime aligned with `requires-python >= 3.12`.

## Carry-forward Note

This report supersedes the original verify report stored as **Engram observation #353** and UPSERTS topic key:

`sdd/backend-change-password-endpoint/verify-report`

## Final Verdict

**READY-TO-COMMIT**

The remediation is VERIFIED. The previously flagged behavioral gap, transaction-ordering issue, test-coverage gap, and tasks-artifact drift are all resolved with independent runtime evidence.
