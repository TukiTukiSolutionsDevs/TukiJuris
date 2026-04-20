"""Shared LLM adapter patch helper.

Reuses the AsyncMock pattern already established in test_byok_plan_gate.py and
test_chat_quota.py — no new mocks module for LLM. This helper factors the
common ≥20-LOC setup into one place so multiple test files share it.

Usage:
    with patch_llm_adapter(reply="mocked answer") as mock:
        res = await auth_client.post("/api/chat/query", json={"message": "Hi"})
    assert mock.called
"""
from __future__ import annotations

from collections.abc import AsyncIterator, Iterator, Sequence
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch


def _make_async_gen(chunks: Sequence[str]) -> AsyncMock:
    """Return an AsyncMock that iterates over chunks as an async generator."""

    async def _gen() -> AsyncIterator[str]:
        for chunk in chunks:
            yield chunk

    mock = MagicMock()
    mock.return_value = _gen()
    return mock


@contextmanager
def patch_llm_adapter(
    *,
    reply: str = "mocked reply",
    tokens_in: int = 10,
    tokens_out: int = 5,
    stream_chunks: Sequence[str] | None = None,
) -> Iterator[AsyncMock]:
    """Context manager that patches the LLM adapter factory with a canned mock.

    Non-streaming calls return `reply` wrapped in the adapter response shape.
    Streaming calls yield `stream_chunks` (defaults to splitting `reply` into words).

    Args:
        reply:          Canned text reply for non-streaming calls.
        tokens_in:      Reported input token count.
        tokens_out:     Reported output token count.
        stream_chunks:  Sequence of text chunks for streaming; defaults to
                        `reply.split()` for a simple word-by-word stream.

    Yields:
        The AsyncMock representing the patched adapter instance.
    """
    if stream_chunks is None:
        stream_chunks = reply.split() or ["mocked"]

    adapter_mock = AsyncMock()
    # Non-streaming call — returns a dict matching the expected adapter contract
    adapter_mock.generate.return_value = {
        "content": reply,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "model": "mock-model",
    }
    # Streaming call — returns an async generator
    adapter_mock.stream = _make_async_gen(stream_chunks)

    with patch("app.services.llm_adapter.get_adapter", return_value=adapter_mock):
        yield adapter_mock
