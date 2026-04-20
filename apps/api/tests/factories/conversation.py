"""Conversation factory — creates conversations via POST /api/chat/query.

IMPORTANT: The LLM adapter must be patched before calling make_conversation.
Use tests.helpers.llm.patch_llm_adapter in the calling test or fixture.
"""
from __future__ import annotations

import uuid
from collections.abc import Sequence

from httpx import AsyncClient


async def make_conversation(
    auth_client: AsyncClient,
    *,
    messages: Sequence[str] = ("Hola",),
) -> tuple[str, list[str]]:
    """Create a conversation via the chat endpoint.

    Conversations are created as a side effect of POST /api/chat/query — there
    is no standalone POST /api/conversations/ endpoint.

    Returns (conv_id, []) — individual message IDs are not in the chat response.
    Fetch via GET /api/conversations/{conv_id} if message IDs are needed.

    Requires LLM adapter to be patched to avoid real API calls.
    """
    conv_id: str | None = None
    for msg in messages:
        body: dict = {"message": msg}
        if conv_id is not None:
            body["conversation_id"] = conv_id  # str — httpx JSON-encodes it; Pydantic parses it
        res = await auth_client.post("/api/chat/query", json=body)
        assert res.status_code == 200, f"make_conversation failed: {res.status_code} {res.text}"
        if conv_id is None:
            conv_id = str(res.json()["conversation_id"])
    assert conv_id is not None
    return conv_id, []
