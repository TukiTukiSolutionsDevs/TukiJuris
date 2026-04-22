# fix-byok-unique-constraint

## Proposal
Reject duplicate LLM provider keys per (user, provider) with a DB-level UniqueConstraint and a 409 HTTP response.

## Spec
- `UserLLMKey` must enforce uniqueness on `(user_id, provider)` at the DB level.
- POST `/api/keys/llm-keys` with a duplicate (user, provider) must return 409.
- Migration must dedup existing rows (keep most-recent per pair) before adding constraint.
- Test `test_llm_key_duplicate_provider_rejected` must pass (xfail removed).

## Design
- Part 1: Add `__table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_llm_keys_user_provider"),)` to `UserLLMKey`.
- Part 2: Migration `017_unique_user_llm_keys` — dedup via ROW_NUMBER(), then `create_unique_constraint`.
- Part 3: Wrap `await db.flush()` in `add_llm_key` with `try/except IntegrityError` → raise 409.

## Tasks
- [x] Model: add UniqueConstraint + import
- [x] Migration: 017_unique_user_llm_keys.py
- [x] Route: IntegrityError → 409 in add_llm_key
- [x] Test: flip xfail → pass
- [x] Verify: alembic upgrade + pytest
- [x] Commit + archive
