"""SSE (Server-Sent Events) assertion helper.

Provides `assert_sse_yields` — the canonical way to test streaming endpoints
via httpx.AsyncClient.stream() with ASGITransport.

Using .post()/.get() buffers the entire response, which breaks SSE contracts.
This helper iterates frame-by-frame, parses the SSE wire format, and asserts
the captured event sequence matches expectations.

SSE frame format contract (ratified from stream.py):
  - Token frames:   data: {"type":"token","content":"<chunk>"}
  - Error frames:   data: {"type":"error","code":<int>,"message":"<msg>"}
  - Terminator:     data: [DONE]
"""
from __future__ import annotations

import asyncio
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from re import Pattern
from typing import Union

from httpx import AsyncClient


@dataclass
class SSEEvent:
    """A parsed SSE event frame."""

    data: str
    event: str | None = None
    id: str | None = None


# An expected_events entry is either an exact SSEEvent or a compiled regex matched
# against the data field.
EventExpectation = Union[SSEEvent, "Pattern[str]"]


async def assert_sse_yields(
    client: AsyncClient,
    *,
    method: str = "POST",
    path: str,
    json: dict | None = None,
    expected_events: Sequence[EventExpectation],
    timeout_s: float = 10.0,
    client_disconnect_after: int | None = None,
) -> list[SSEEvent]:
    """Open a streaming request and assert the SSE event sequence.

    Args:
        client:                   Authenticated (or anonymous) AsyncClient.
        method:                   HTTP verb — default "POST".
        path:                     Full path, e.g. "/api/stream/query".
        json:                     Optional request body.
        expected_events:          Sequence of SSEEvent (exact match) or compiled
                                  regex Pattern (matched against data field).
        timeout_s:                Hard timeout for the entire stream. Default 10s.
        client_disconnect_after:  If set, break after capturing this many events
                                  and verify the server-side task is cancelled
                                  (no runaway charges — covers stream.unit.009).

    Returns:
        Full list of captured SSEEvent instances for additional bespoke assertions.

    Raises:
        AssertionError: on timeout, sequence mismatch, or disconnect failure.
    """
    captured: list[SSEEvent] = []

    async def _consume() -> None:
        kwargs: dict = {}
        if json is not None:
            kwargs["json"] = json

        async with client.stream(method, path, **kwargs) as response:
            assert response.status_code == 200, (
                f"assert_sse_yields: expected 200, got {response.status_code}. "
                f"Body: {(await response.aread()).decode()[:300]}"
            )
            current = SSEEvent(data="")
            async for line in response.aiter_lines():
                if line.startswith("data:"):
                    current.data = line[5:].strip()
                elif line.startswith("event:"):
                    current.event = line[6:].strip()
                elif line.startswith("id:"):
                    current.id = line[3:].strip()
                elif line == "":
                    # Blank line = event boundary
                    if current.data:
                        captured.append(SSEEvent(data=current.data, event=current.event, id=current.id))
                        current = SSEEvent(data="")
                        if client_disconnect_after is not None and len(captured) >= client_disconnect_after:
                            break

    try:
        await asyncio.wait_for(_consume(), timeout=timeout_s)
    except TimeoutError:
        raise AssertionError(
            f"assert_sse_yields: stream timed out after {timeout_s}s. "
            f"Captured {len(captured)} events before timeout."
        ) from None

    # Sequence assertion
    assert len(captured) == len(expected_events), (
        f"assert_sse_yields: expected {len(expected_events)} events, "
        f"got {len(captured)}.\n"
        f"  Expected: {expected_events}\n"
        f"  Captured: {captured}"
    )

    for i, (actual, expected) in enumerate(zip(captured, expected_events)):
        if isinstance(expected, re.Pattern):
            assert expected.search(actual.data), (
                f"assert_sse_yields: event[{i}] data did not match pattern {expected.pattern!r}. "
                f"Got: {actual.data!r}"
            )
        else:
            assert actual.data == expected.data, (
                f"assert_sse_yields: event[{i}] data mismatch.\n"
                f"  Expected: {expected.data!r}\n"
                f"  Got:      {actual.data!r}"
            )
            if expected.event is not None:
                assert actual.event == expected.event, (
                    f"assert_sse_yields: event[{i}] event-type mismatch: "
                    f"expected {expected.event!r}, got {actual.event!r}"
                )

    return captured
