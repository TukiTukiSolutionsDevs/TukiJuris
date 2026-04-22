# fix-feedback-ownership

## Proposal

`POST /api/feedback/` runs `UPDATE Message SET feedback=? WHERE id=?` with no
ownership check. Any authenticated user can overwrite feedback on any message,
including messages from other users' conversations.

## Spec

- `POST /api/feedback/` MUST verify the message belongs to `current_user`
  before writing feedback.
- If the message does not exist OR belongs to another user → 404 "Message not
  found" (project-wide 404-on-foreign-resource convention, per
  `helpers/isolation.py::assert_isolated`).
- Invalid feedback type → keep existing 200+`status="error"` shape (no blast
  radius on existing tests).
- `GET /api/feedback/stats` is unchanged (public-by-design).

## Design

1. Replace the bare `UPDATE Message WHERE id=?` with:
   `SELECT Message JOIN Conversation WHERE Message.id=? AND Conversation.user_id=current_user.id`
2. If `scalar_one_or_none()` returns `None` → raise 404.
3. Set `msg.feedback = body.feedback` on the loaded ORM instance + `await db.flush()`.
   Avoids a second round-trip; atomic within the same session flush.
4. Imports added: `HTTPException`, `status` (fastapi); `select` (sqlalchemy);
   `Conversation` (app.models.conversation).

## Tasks

- [x] Write `openspec/changes/fix-feedback-ownership/change.md`
- [x] Update `apps/api/app/api/routes/feedback.py` — add ownership check
- [x] Update `apps/api/tests/test_feedback.py` — seed real messages for
      happy-path tests; flip xfail on cross-tenant isolation test
- [x] Verify: `pytest tests/test_feedback.py -v` → 12 passed
- [x] Verify: `pytest tests/ --tb=no -q` → 1232 passed, 10 xfailed, 0 failed
- [x] Commit + archive
