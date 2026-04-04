"""Streaming chat endpoint — Server-Sent Events (SSE) with deliberative orchestration."""

import json
import logging
import time
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.domain_agents import get_agent
from app.agents.orchestrator import (
    classify_query,
    evaluate_response,
    retrieve_context,
    synthesize_response,
)
from app.api.deps import get_optional_user
from app.config import settings
from app.core.database import get_db
from app.models.user import User
from app.services.conversations import (
    add_message,
    create_conversation,
    get_conversation_with_messages,
)
from app.services.llm_adapter import llm_service
from app.services.llm_key_service import get_user_keys_for_model
from app.services.memory_service import memory_service
from app.services.rag import rag_service
from app.services.usage import usage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat-stream"])


class StreamRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    model: str | None = None
    legal_area: str | None = None


async def _generate_stream(
    body: StreamRequest,
    current_user: User | None,
    db: AsyncSession,
    user_api_key: str | None = None,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for a legal query — full deliberative orchestration loop."""
    start = time.time()
    model = body.model or settings.default_llm_model

    # ── Step 1: Load conversation history (ORM) ───────────────────────────────
    conversation_history: list[dict] = []
    if body.conversation_id and current_user:
        try:
            conv_uuid = uuid.UUID(body.conversation_id)
            existing_conv = await get_conversation_with_messages(db, conv_uuid, current_user.id)
            if existing_conv and existing_conv.messages:
                sorted_msgs = sorted(existing_conv.messages, key=lambda m: m.created_at)
                conversation_history = [
                    {"role": m.role, "content": m.content}
                    for m in sorted_msgs[-20:]  # Last 20 messages max
                ]
        except Exception:
            # History load failure must not block streaming
            pass

    # ── Step 2: Classify WITH history ────────────────────────────────────────
    yield _sse({"type": "status", "content": "Analizando tu consulta..."})

    classify_state = {
        "query": body.message,
        "model": model,
        "legal_area_hint": body.legal_area,
        "primary_area": "",
        "secondary_areas": [],
        "classification_confidence": 0.0,
        "conversation_history": conversation_history,  # ← NOW includes history
    }
    classification = await classify_query(classify_state)
    area = classification["primary_area"]
    yield _sse({
        "type": "classification",
        "legal_area": area,
        "confidence": classification["classification_confidence"],
    })

    # ── Step 3: RAG Retrieve ──────────────────────────────────────────────────
    yield _sse({"type": "status", "content": f"Consultando normativa de {area}..."})

    retrieve_state = {**classify_state, **classification}
    retrieval = await retrieve_context(retrieve_state)
    context = retrieval.get("retrieved_context", "")

    # ── Step 4: Resolve agent ─────────────────────────────────────────────────
    agent = get_agent(area)
    if not agent:
        yield _sse({"type": "error", "message": f"No hay agente para el área: {area}"})
        return

    # ── Step 5: Inject user memory context ───────────────────────────────────
    user_context = ""
    if current_user:
        try:
            user_context = await memory_service.get_user_context(current_user.id, db)
        except Exception:
            pass  # Non-blocking

    # ── Step 6: Build messages array ─────────────────────────────────────────
    messages: list[dict] = [{"role": "system", "content": agent.system_prompt}]

    if context:
        messages.append({"role": "system", "content": f"CONTEXTO NORMATIVO RELEVANTE:\n{context}"})

    if user_context:
        messages.append({"role": "system", "content": user_context})

    for hist_msg in conversation_history:
        messages.append({"role": hist_msg["role"], "content": hist_msg["content"]})

    messages.append({"role": "user", "content": body.message})

    yield _sse({"type": "status", "content": f"El especialista en {area} está analizando tu caso..."})
    yield _sse({"type": "agent", "agent_used": agent.name, "legal_area": area})

    # ── Step 7: Stream primary LLM response ───────────────────────────────────
    # BYOK: Use the user's own provider key for the main response generation.
    # Classification, evaluation, and RAG retrieval use platform keys internally.
    full_text = ""
    citations: list[dict] = []
    agent_name = agent.name

    try:
        response = await llm_service.completion(
            messages=messages,
            model=model,
            stream=True,
            user_api_key=user_api_key,  # BYOK
        )
        stream = response["stream"]

        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_text += delta
                yield _sse({"type": "token", "content": delta})

        # Extract citations from primary response
        citations = agent._extract_citations(full_text)

        # ── Step 8: META-REASONING — Evaluate primary response ─────────────
        yield _sse({"type": "status", "content": "Evaluando si se necesitan más especialistas..."})

        eval_state = {
            "query": body.message,
            "primary_response": {"response": full_text, "agent_used": agent_name},
            "primary_area": area,
            "model": model,
            "user_api_key": user_api_key,
        }
        evaluation = await evaluate_response(eval_state)

        # ── Step 9: If needs more agents — ENRICHMENT LOOP ─────────────────
        if evaluation.get("needs_enrichment") and evaluation.get("secondary_areas"):
            secondary_areas = evaluation["secondary_areas"]
            reason = evaluation.get("evaluation_reason", "")

            # Status message: let the user know we're consulting more specialists
            areas_names = ", ".join(secondary_areas)
            yield _sse({
                "type": "orchestrator_thinking",
                "content": (
                    f"He notado que tu consulta también involucra {areas_names}. "
                    f"Estoy consultando con más especialistas para darte una respuesta completa. "
                    f"Un momento por favor..."
                ),
                "reason": reason,
            })

            secondary_responses = []
            for sec_area in secondary_areas:
                yield _sse({"type": "status", "content": f"Consultando al especialista en {sec_area}..."})

                sec_agent = get_agent(sec_area)
                if not sec_agent:
                    continue

                # Retrieve RAG for secondary area
                sec_context = ""
                try:
                    sec_context = await rag_service.retrieve(
                        query=body.message,
                        legal_area=sec_area,
                        limit=4,
                    )
                except Exception as exc:
                    logger.warning(f"RAG failed for secondary area={sec_area}: {exc}")

                # Secondary agent processes (non-streaming for speed)
                sec_result = await sec_agent.process(
                    query=(
                        f"En relación a esta consulta, proporciona tu análisis desde la perspectiva "
                        f"del {sec_agent.name}. Sé específico con la normativa aplicable.\n\n"
                        f"Consulta: {body.message}"
                    ),
                    context=sec_context,
                    model=model,
                    conversation_history=conversation_history,
                    user_api_key=user_api_key,
                )
                secondary_responses.append(sec_result)

            # ── Step 10: SYNTHESIZE all responses ──────────────────────────
            yield _sse({"type": "status", "content": "Integrando análisis de todos los especialistas..."})

            synth_state = {
                "query": body.message,
                "primary_response": {"response": full_text, "agent_used": agent_name, "citations": citations},
                "primary_area": area,
                "secondary_responses": secondary_responses,
                "secondary_areas": secondary_areas,
                "evaluation_reason": reason,
                "citations": citations,
                "model": model,
                "user_api_key": user_api_key,
            }
            synthesis = await synthesize_response(synth_state)

            # Signal the frontend to REPLACE the streamed content with the synthesis
            yield _sse({
                "type": "synthesis",
                "content": synthesis["response"],
                "agent_used": synthesis.get("agent_used", ""),
                "is_multi_area": True,
            })

            # Update for persistence
            full_text = synthesis["response"]
            agent_name = synthesis.get("agent_used", agent.name)
            citations = synthesis.get("citations", citations)

        # ── Step 11: Extract and compute final metadata ───────────────────
        latency_ms = int((time.time() - start) * 1000)

        # ── Step 12: Persist via ORM ──────────────────────────────────────
        conv = None
        msg_id: uuid.UUID | None = None

        if current_user:
            try:
                if body.conversation_id:
                    try:
                        conv_uuid = uuid.UUID(body.conversation_id)
                        conv = await get_conversation_with_messages(db, conv_uuid, current_user.id)
                    except (ValueError, Exception):
                        conv = None

                if conv is None:
                    # New conversation
                    conv = await create_conversation(
                        db,
                        user_id=current_user.id,
                        title=body.message[:100],
                        legal_area=area,
                        model_used=model,
                    )

                await add_message(db, conv.id, "user", body.message)

                assistant_msg = await add_message(
                    db,
                    conv.id,
                    "assistant",
                    full_text,
                    agent_used=agent_name,
                    legal_area=area,
                    model=model,
                    citations=citations if citations else None,
                    tokens_used=None,
                    latency_ms=latency_ms,
                )
                msg_id = assistant_msg.id

                # Commit the ORM session now — the SSE generator is ending
                await db.commit()

            except Exception as persist_err:
                logger.warning(f"Persistence failed (non-blocking): {persist_err}")
                try:
                    await db.rollback()
                except Exception:
                    pass

        # ── Step 13: Extract and save memories (non-blocking) ─────────────
        if current_user and conv is not None:
            try:
                # Pass both user message AND assistant response for richer extraction
                extraction_msgs = [
                    {"role": "user", "content": body.message},
                    {"role": "assistant", "content": full_text[:1000]},  # cap to avoid huge prompts
                ]
                new_mems = await memory_service.extract_memories(
                    current_user.id,
                    conv.id,
                    extraction_msgs,
                    db,
                )
                if new_mems:
                    await memory_service.save_memories(
                        current_user.id, new_mems, conv.id, db
                    )
            except Exception:
                pass  # Non-blocking

        # ── Step 14: Send "done" event ─────────────────────────────────────
        conv_id_out = str(conv.id) if conv else (body.conversation_id or str(uuid.uuid4()))
        yield _sse({
            "type": "done",
            "citations": citations,
            "model_used": model,
            "latency_ms": latency_ms,
            "conversation_id": conv_id_out,
            "message_id": str(msg_id) if msg_id else None,
        })

    except Exception as e:
        logger.exception("Stream generation error")
        yield _sse({"type": "error", "message": str(e)})


def _sse(data: dict) -> str:
    """Format dict as SSE event."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/stream")
async def chat_stream(
    body: StreamRequest,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream a legal query response via Server-Sent Events.

    The endpoint implements a full deliberative orchestration loop:
    classify → retrieve → primary_agent (streaming) → evaluate → [enrich → synthesize]

    Events:
    - status: Processing step info (shown in status bar)
    - classification: Legal area detected
    - agent: Which primary agent is responding
    - token: Incremental text token (primary response streaming)
    - orchestrator_thinking: Meta-reasoning message ("consulting more specialists")
    - synthesis: REPLACES streamed content with multi-area integrated response
    - done: Final metadata (citations, latency, conversation_id)
    - error: Error message
    """
    # BYOK: Resolve the user's API key before streaming starts.
    # We do this here (outside the generator) so we can raise HTTP 400
    # before the SSE stream is opened — cleaner error handling.
    user_api_key: str | None = None
    if current_user is not None and body.model:
        user_api_key = await get_user_keys_for_model(current_user.id, body.model, db)
        if not user_api_key:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No tienes una API key configurada para el modelo '{body.model}'. "
                    "Ve a Configuración → Mis API Keys para agregar tu clave del proveedor."
                ),
            )

    # Daily query limit enforcement — checked before opening the stream
    if current_user is not None:
        limit_check = await usage_service.check_daily_limit(current_user.id, current_user.plan)
        if not limit_check["allowed"]:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Has alcanzado tu límite diario de {limit_check['daily_limit']} consultas. "
                    f"Actualiza tu plan para continuar. "
                    f"Usado: {limit_check['used_today']}/{limit_check['daily_limit']}"
                ),
                headers={
                    "X-Daily-Limit": str(limit_check["daily_limit"]),
                    "X-Daily-Used": str(limit_check["used_today"]),
                },
            )

    return StreamingResponse(
        _generate_stream(body, current_user=current_user, db=db, user_api_key=user_api_key),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
