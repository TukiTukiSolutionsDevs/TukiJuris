"""
Codex Proxy — OpenAI-compatible HTTP shim for the codex-cli binary.

DEVELOPMENT ONLY. Bridges TukiJuris (which expects an OpenAI-style endpoint)
to the user's authenticated `codex` CLI session by shelling out to
`codex exec`. Replace with a real OpenAI key for production.

Endpoints:
  GET  /v1/models                  → static catalogue (codex-proxy/* models)
  POST /v1/chat/completions        → non-streaming OpenAI shape; calls `codex exec`
  GET  /health                     → returns codex binary version

Limitations:
  - Each request invokes `codex exec` fresh — no session reuse, ~14k tokens
    of overhead per call. Fine for dev, terrible for prod.
  - Embeddings NOT supported (codex doesn't expose them).
  - Streaming NOT implemented (always returns the final message).
"""

from __future__ import annotations

import asyncio
import logging
import os
import shlex
import shutil
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("codex-proxy")

CODEX_BIN = shutil.which("codex") or "/opt/homebrew/bin/codex"
DEFAULT_MODEL = os.environ.get("CODEX_PROXY_MODEL", "gpt-5.4")
TIMEOUT_SECONDS = int(os.environ.get("CODEX_PROXY_TIMEOUT", "300"))
WORKING_DIR = os.environ.get("CODEX_PROXY_CWD", str(Path.home()))
# Codex CLI defaults to xhigh, which makes every call 4-10s. We override to
# medium for the case-flow which fires 4-7 calls per turn. Switch via env if
# you need deeper reasoning (e.g. final synthesis). Valid: low|medium|high|xhigh.
REASONING_EFFORT = os.environ.get("CODEX_PROXY_REASONING_EFFORT", "medium")

app = FastAPI(title="Codex Proxy", version="0.1.0")


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: str
    content: str | list[dict[str, Any]]


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[ChatMessage]
    temperature: float | None = None
    max_tokens: int | None = None
    stream: bool | None = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _flatten_message(msg: ChatMessage) -> str:
    """Convert OpenAI message content (str or parts) to a single string."""
    if isinstance(msg.content, str):
        return msg.content
    parts: list[str] = []
    for p in msg.content:
        if isinstance(p, dict):
            text = p.get("text") or p.get("content") or ""
            parts.append(str(text))
        else:
            parts.append(str(p))
    return "\n".join(parts).strip()


def _build_prompt(messages: list[ChatMessage]) -> str:
    """Concatenate OpenAI messages into a single prompt for codex."""
    pieces: list[str] = []
    for m in messages:
        role = m.role.upper()
        body = _flatten_message(m)
        if not body:
            continue
        pieces.append(f"[{role}]\n{body}")
    return "\n\n".join(pieces)


async def _run_codex(prompt: str, model: str | None) -> str:
    """Run `codex exec` and return the final agent message."""
    if not Path(CODEX_BIN).exists():
        raise HTTPException(500, f"codex binary not found at {CODEX_BIN}")

    with tempfile.NamedTemporaryFile(mode="r+", suffix=".txt", delete=False) as f:
        out_path = f.name

    try:
        args = [
            CODEX_BIN,
            "exec",
            "--skip-git-repo-check",
            "--ephemeral",
            "--sandbox", "read-only",
            "--output-last-message", out_path,
            "-c", f"model_reasoning_effort={REASONING_EFFORT}",
        ]
        if model:
            args.extend(["-m", model])
        args.append("-")  # read prompt from stdin

        logger.info("codex args=%s", " ".join(shlex.quote(a) for a in args))
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKING_DIR,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(input=prompt.encode()),
                timeout=TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise HTTPException(504, f"codex exec timed out after {TIMEOUT_SECONDS}s")

        if proc.returncode != 0:
            err = (stderr or b"").decode(errors="replace").strip()
            logger.error("codex exec failed rc=%s err=%s", proc.returncode, err[:500])
            raise HTTPException(502, f"codex exec rc={proc.returncode}: {err[:400]}")

        try:
            content = Path(out_path).read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            content = ""

        if not content:
            # Fallback: take stdout
            content = (stdout or b"").decode(errors="replace").strip()

        return content or "(empty response)"
    finally:
        try:
            os.unlink(out_path)
        except FileNotFoundError:
            pass


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, Any]:
    if not Path(CODEX_BIN).exists():
        return {"ok": False, "error": f"codex binary missing at {CODEX_BIN}"}
    proc = await asyncio.create_subprocess_exec(
        CODEX_BIN, "--version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    return {
        "ok": proc.returncode == 0,
        "codex_version": (stdout or b"").decode().strip(),
        "default_model": DEFAULT_MODEL,
        "cwd": WORKING_DIR,
    }


@app.get("/v1/models")
async def list_models(authorization: str | None = Header(None)) -> dict[str, Any]:
    """Static catalog so OpenAI clients can discover us.

    The list mirrors what the local Codex CLI 0.142.0 actually answers — any
    other model name passed to ``codex exec -m`` returns rc=1 / HTTP 502.
    Verified against the proxy on 2026-06-25.
    """
    served = ["gpt-5.5", "gpt-5.4-mini", "gpt-5.4"]
    if DEFAULT_MODEL not in served:
        served.insert(0, DEFAULT_MODEL)
    return {
        "object": "list",
        "data": [
            {"id": m, "object": "model", "owned_by": "codex-proxy"}
            for m in served
        ],
    }


@app.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest) -> dict[str, Any]:
    if req.stream:
        raise HTTPException(400, "streaming not supported by codex-proxy (dev only)")

    prompt = _build_prompt(req.messages)
    if not prompt:
        raise HTTPException(400, "empty messages")

    started = time.monotonic()
    content = await _run_codex(prompt, req.model or DEFAULT_MODEL)
    elapsed = time.monotonic() - started
    logger.info("chat ok len=%d in %.2fs", len(content), elapsed)

    # Rough token estimate (4 chars ≈ 1 token)
    pt = max(1, len(prompt) // 4)
    ct = max(1, len(content) // 4)

    return {
        "id": f"chatcmpl-codexproxy-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model or DEFAULT_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": pt,
            "completion_tokens": ct,
            "total_tokens": pt + ct,
        },
    }


@app.post("/v1/embeddings")
async def embeddings(_: dict[str, Any]) -> dict[str, Any]:
    raise HTTPException(
        501,
        "codex-proxy does not provide embeddings; use a real Google or OpenAI key",
    )


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("CODEX_PROXY_HOST", "0.0.0.0")
    port = int(os.environ.get("CODEX_PROXY_PORT", "5050"))
    logger.info("starting codex-proxy on %s:%d (codex=%s, cwd=%s)", host, port, CODEX_BIN, WORKING_DIR)
    uvicorn.run(app, host=host, port=port, log_level="info")
