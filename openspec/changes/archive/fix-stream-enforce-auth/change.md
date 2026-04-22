# fix-stream-enforce-auth

**Status**: applied  
**Date**: 2026-04-22  
**Commit**: (see archive)  
**Artifact store**: openspec + engram

---

## Proposal

Anonymous access on `POST /chat/stream` is an abuse vector. The endpoint used
`get_optional_user` (returns `None` for unauthenticated requests), while the
sibling endpoint `chat.py` enforces auth via `get_current_user`. Two endpoints
implementing the same logical operation with divergent auth semantics is a bug,
not a feature.

**Decision**: Option A — enforce auth on `/chat/stream` to align with `chat.py`.

**Rationale**:
- `chat.py` enforces auth for the same logical operation; divergence is a bug.
- No rate-limit-by-IP or anonymous quota exists → plan+BYOK quotas bypassable.
- Default-secure principle.
- The existing xfail test already encoded the correct intent ("Expected 401 per spec.008").

---

## Spec

- `POST /chat/stream` MUST return `401` for unauthenticated requests.
- Behaviour for authenticated requests is unchanged.
- Test `test_stream_401_without_auth` (spec ref: chat-stream.unit.008) MUST pass.
- Test `test_stream_cancels_on_client_disconnect` (spec ref: chat-stream.unit.009)
  remains `xfail(strict=True)` — ASGITransport infrastructure limitation, NOT a
  code bug. Deferred to infra sprint (needs real-socket harness, e.g. pytest-anyio
  with live uvicorn).

---

## Design

Minimal blast-radius change: swap dependency only. Do NOT touch downstream
`if current_user is not None:` guards in the handler body — they become dead-but-
harmless. A follow-up cleanup change can remove them. Touching them expands blast
radius beyond this micro-change.

---

## Tasks

- [x] `stream.py` line 31: import `get_current_user` instead of `get_optional_user`
- [x] `stream.py` line 534: type annotation `User` (not `User | None`), dep `get_current_user`
- [x] `test_stream_routes.py`: remove `@pytest.mark.xfail` from `test_stream_401_without_auth`
- [x] Verify: 5 passed, 1 xfailed in stream suite
- [x] Verify: full suite counts 1234 passed, 8 xfailed, 0 failed
- [x] Commit + archive

---

## Out of scope

- `test_stream_cancels_on_client_disconnect` xfail — infra concern, not code bug.
  Needs a real-socket test harness. Tracked separately.
- Dead `if current_user is not None:` guards in handler body — cleanup candidate,
  separate commit.
