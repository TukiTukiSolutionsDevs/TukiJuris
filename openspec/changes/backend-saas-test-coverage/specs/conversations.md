---
change: backend-saas-test-coverage
spec: conversations
status: proposed
created: 2026-04-19
---

# Spec — Conversations test coverage

## 1. Scope
Coverage for the `conversations` domain and user content organization sub-resources, specifically focusing on `conversations.py`, `bookmarks.py`, `tags.py`, `folders.py`, `memory.py`, `shared.py`, and `feedback.py`. The focus is on write paths, cross-tenant ownership isolation, and the complete CRUD lifecycle for user-generated organization mechanisms. Streaming and chat execution are OUT of scope for this spec (handled in `chat-stream.md`).

## 2. Current state
- Existing tests: `tests/test_conversations.py` has 6 tests (mainly list/get validation). `tests/test_feedback.py` has 11 tests. Total ~17 tests.
- Known gaps: Zero tests for any of the conversation write paths (rename, pin, archive, delete, share). Zero coverage for bookmarks, memory, tags, folders, and shared conversations. No tests assert cross-tenant ownership isolation (User A accessing User B's content).
- Pre-existing failures unrelated: None.

## 3. Test catalog
1. `conversations.unit.001`
   - Name: `test_conversation_rename_owner_only`
   - Layer: integration
   - File: `apps/api/tests/integration/test_conversations_write.py`
   - Intent: Ensure only the creator can rename a conversation.
   - Setup: User A, User B, Conv A
   - Assertions: User B PATCH returns 403/404; User A PATCH returns 200 and updates name.
   - Expected runtime: fast
   - Dependency: NONE
2. `conversations.unit.002`
   - Name: `test_conversation_pin_toggle`
   - Layer: integration
   - File: `apps/api/tests/integration/test_conversations_write.py`
   - Intent: Verify the pin and unpin state machine works.
   - Setup: User A, Conv A
   - Assertions: PATCH pin sets `is_pinned=True`; second PATCH unpins.
   - Expected runtime: fast
   - Dependency: NONE
3. `conversations.unit.003`
   - Name: `test_conversation_archive_owner_only`
   - Layer: integration
   - File: `apps/api/tests/integration/test_conversations_write.py`
   - Intent: Verify archiving is restricted to the owner.
   - Setup: User A, User B, Conv A
   - Assertions: User B PATCH returns 403/404; User A returns 200 and sets `is_archived=True`.
   - Expected runtime: fast
   - Dependency: NONE
4. `conversations.unit.004`
   - Name: `test_conversation_delete_cascades`
   - Layer: integration
   - File: `apps/api/tests/integration/test_conversations_write.py`
   - Intent: Verify deleting a conversation cascades to messages and removes it from GET.
   - Setup: User A, Conv A with 2 messages
   - Assertions: DELETE returns 204; subsequent GET returns 404; DB count drops.
   - Expected runtime: med
   - Dependency: NONE
5. `conversations.unit.005`
   - Name: `test_conversation_share_creates_link`
   - Layer: integration
   - File: `apps/api/tests/integration/test_shared.py`
   - Intent: Verify the share endpoint generates a public link identifier.
   - Setup: User A, Conv A
   - Assertions: POST to `/share` returns a share UUID; DB marks `is_shared=True`.
   - Expected runtime: fast
   - Dependency: NONE
6. `conversations.unit.006`
   - Name: `test_shared_conversation_public_access`
   - Layer: integration
   - File: `apps/api/tests/integration/test_shared.py`
   - Intent: Verify unauthenticated users can view a shared conversation.
   - Setup: Conv A (shared)
   - Assertions: GET with no auth returns 200 and message history.
   - Expected runtime: fast
   - Dependency: NONE
7. `conversations.unit.007`
   - Name: `test_shared_conversation_revocation`
   - Layer: integration
   - File: `apps/api/tests/integration/test_shared.py`
   - Intent: Verify un-sharing immediately blocks public access.
   - Setup: Conv A (shared)
   - Assertions: Revoke share; subsequent public GET returns 404.
   - Expected runtime: fast
   - Dependency: NONE
8. `conversations.unit.008`
   - Name: `test_bookmark_crud_happy_path`
   - Layer: integration
   - File: `apps/api/tests/integration/test_bookmarks.py`
   - Intent: Validate create, read, and delete flow for bookmarks.
   - Setup: User A, Message A
   - Assertions: POST creates bookmark; GET lists it; DELETE removes it.
   - Expected runtime: fast
   - Dependency: NONE
9. `conversations.unit.009`
   - Name: `test_bookmark_isolation`
   - Layer: integration
   - File: `apps/api/tests/integration/test_bookmarks.py`
   - Intent: Validate User B cannot see or delete User A's bookmarks.
   - Setup: User A, User B, Bookmark A
   - Assertions: User B GET lists 0; User B DELETE returns 404.
   - Expected runtime: fast
   - Dependency: NONE
10. `conversations.unit.010`
    - Name: `test_tag_crud_happy_path`
    - Layer: integration
    - File: `apps/api/tests/integration/test_tags.py`
    - Intent: Validate create, list, and delete for tags.
    - Setup: User A
    - Assertions: POST creates tag; list includes it.
    - Expected runtime: fast
    - Dependency: NONE
11. `conversations.unit.011`
    - Name: `test_tag_assign_unassign`
    - Layer: integration
    - File: `apps/api/tests/integration/test_tags.py`
    - Intent: Validate assigning a tag to a conversation.
    - Setup: User A, Conv A, Tag A
    - Assertions: Assigning tag links it; unassigning breaks link.
    - Expected runtime: fast
    - Dependency: NONE
12. `conversations.unit.012`
    - Name: `test_folder_crud_isolation`
    - Layer: integration
    - File: `apps/api/tests/integration/test_folders.py`
    - Intent: Create/list folders and verify cross-tenant isolation.
    - Setup: User A, User B
    - Assertions: User A creates folder; User B cannot list or modify it.
    - Expected runtime: fast
    - Dependency: NONE
13. `conversations.unit.013`
    - Name: `test_memory_crud_happy_path`
    - Layer: integration
    - File: `apps/api/tests/integration/test_memory.py`
    - Intent: Validate reading and writing memory facts for a user.
    - Setup: User A
    - Assertions: POST saves fact; GET lists fact.
    - Expected runtime: fast
    - Dependency: NONE
14. `conversations.unit.014`
    - Name: `test_memory_isolation`
    - Layer: integration
    - File: `apps/api/tests/integration/test_memory.py`
    - Intent: Validate User B cannot access User A's AI memory.
    - Setup: User A, User B, Memory Fact A
    - Assertions: User B GET returns 0 items for User A's memory.
    - Expected runtime: fast
    - Dependency: NONE
15. `conversations.unit.015`
    - Name: `test_feedback_submit_cross_tenant_isolation`
    - Layer: integration
    - File: `apps/api/tests/integration/test_feedback.py`
    - Intent: Ensure User B cannot submit feedback for User A's message.
    - Setup: User A (Message A), User B
    - Assertions: User B POST to feedback for Message A returns 403/404.
    - Expected runtime: fast
    - Dependency: NONE

## 4. Code fixes likely required
- Verify `conversations.py` uses explicit `user_id` filters in DB queries. No global RLS means cross-tenant isolation tests might surface actual bugs. Budget `FIX-01` for missing `user_id` query filters across tags/folders/bookmarks if tests fail.

## 5. Acceptance criteria
- All 15 tests pass.
- Zero new unjustified skips.
- Coverage delta target ≥ 80% for `conversations.py`, `bookmarks.py`, `tags.py`, `folders.py`, `memory.py`, `shared.py`.
- No regression in the 1111 currently-passing tests.

## 6. Out of scope / deferred
- Chat and Streaming functionalities (these belong to `chat-stream`).
- Frontend tests.
- Real-time websocket notification on feedback.

## 7. References
- Proposal: sdd/backend-saas-test-coverage/proposal
- Exploration: sdd/backend-saas-test-coverage/explore
- Prior relevant archives (cite engram topic keys)
