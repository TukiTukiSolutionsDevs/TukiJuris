"""Streaming chat endpoint — Server-Sent Events (SSE) with deliberative orchestration.

ARCHITECTURE (v2 — single final stream):
The entire orchestration pipeline runs INTERNALLY (no tokens sent to user).
The user only sees narrative status events in the orchestrator panel.
Once ALL agents finish, ONE final response is streamed token-by-token.

Pipeline: classify → RAG → primary_agent (internal) → evaluate →
          [secondary_agents (internal) → synthesize (internal)] →
          final_stream_start → stream final response
"""

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
    reasoning_effort: str | None = None  # "low", "medium", "high" — controls thinking depth


async def _generate_stream(
    body: StreamRequest,
    current_user: User | None,
    db: AsyncSession,
    user_api_key: str | None = None,
) -> AsyncGenerator[str, None]:
    """Generate SSE events for a legal query — full deliberative orchestration loop.

    KEY DESIGN: All agent work is INTERNAL (non-streaming).  The user only
    sees narrative status events.  After all processing completes, a single
    ``final_stream_start`` event is emitted, followed by the actual response
    tokens streamed via ``final_token`` events.
    """
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
            pass  # History load failure must not block streaming

    # ── Step 2: Classify WITH history ────────────────────────────────────────
    yield _sse({
        "type": "status",
        "step": "classify",
        "content": "🧠 Analizando tu consulta para determinar qué especialistas necesitás...",
    })

    reasoning = body.reasoning_effort  # "low", "medium", "high", or None

    classify_state = {
        "query": body.message,
        "model": model,
        "legal_area_hint": body.legal_area,
        "primary_area": "",
        "secondary_areas": [],
        "classification_confidence": 0.0,
        "conversation_history": conversation_history,
        "user_api_key": user_api_key,
        "reasoning_effort": reasoning,
    }
    try:
        classification = await classify_query(classify_state)
    except Exception as classify_err:
        logger.exception("Classification failed")
        yield _sse({"type": "error", "message": f"Error al clasificar la consulta: {classify_err}"})
        return
    area = classification["primary_area"]
    confidence = classification["classification_confidence"]

    yield _sse({
        "type": "classification",
        "legal_area": area,
        "confidence": confidence,
    })
    yield _sse({
        "type": "status",
        "step": "classify_done",
        "content": f"🎯 Área identificada: {area.capitalize()} ({int(confidence * 100)}% confianza)",
    })

    # ── Step 3: RAG Retrieve ──────────────────────────────────────────────────
    agent_preview = get_agent(area)
    agent_label = agent_preview.name if agent_preview else area

    yield _sse({
        "type": "status",
        "step": "rag",
        "content": "📚 Buscando normativa peruana relevante en la base de conocimiento...",
    })

    retrieve_state = {**classify_state, **classification}
    try:
        retrieval = await retrieve_context(retrieve_state)
    except Exception as rag_err:
        logger.warning(f"RAG retrieval failed: {rag_err}")
        retrieval = {"retrieved_context": ""}
    context = retrieval.get("retrieved_context", "")
    rag_found = bool(context and len(context) > 50)

    if rag_found:
        yield _sse({
            "type": "status",
            "step": "rag_done",
            "content": "📖 Normativa encontrada. Preparando análisis especializado...",
        })
    else:
        yield _sse({
            "type": "status",
            "step": "rag_done",
            "content": "📖 Sin normativa específica. Se usará conocimiento especializado del agente.",
        })

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

    yield _sse({
        "type": "status",
        "step": "primary_working",
        "content": f"⚖️ El {agent.name} está analizando tu caso...",
    })
    yield _sse({"type": "agent", "agent_used": agent.name, "legal_area": area})

    # ── Step 7: PRIMARY AGENT — INTERNAL (non-streaming) ──────────────────────
    # The key architectural change: completion WITHOUT streaming.
    # The user does NOT see tokens yet — only narrative status events.
    full_text = ""
    citations: list[dict] = []
    agent_name = agent.name

    try:
        primary_result = await llm_service.completion(
            messages=messages,
            model=model,
            stream=False,  # ← INTERNAL — no tokens to user
            user_api_key=user_api_key,
            reasoning_effort=reasoning,
        )
        full_text = primary_result.get("content", "")

        # Extract citations from primary response
        citations = agent._extract_citations(full_text)

        yield _sse({
            "type": "status",
            "step": "primary_done",
            "content": f"✅ El {agent.name} completó su análisis.",
        })

        # ── Step 8: META-REASONING — Evaluate primary response ─────────────
        yield _sse({
            "type": "status",
            "step": "evaluating",
            "content": "🔍 El orquestador está verificando si tu consulta necesita más especialistas...",
        })

        eval_state = {
            "query": body.message,
            "primary_response": {"response": full_text, "agent_used": agent_name},
            "primary_area": area,
            "model": model,
            "user_api_key": user_api_key,
            "reasoning_effort": reasoning,
        }
        evaluation = await evaluate_response(eval_state)

        # ── Step 9: If needs more agents — ENRICHMENT LOOP ─────────────────
        if evaluation.get("needs_enrichment") and evaluation.get("secondary_areas"):
            secondary_areas = evaluation["secondary_areas"]
            reason = evaluation.get("evaluation_reason", "")

            # Narrative status: the "meeting of lawyers" moment
            sec_agent_names = []
            for sa in secondary_areas:
                sec_a = get_agent(sa)
                sec_agent_names.append(sec_a.name if sec_a else sa)
            areas_display = " y ".join(sec_agent_names)

            yield _sse({
                "type": "orchestrator_thinking",
                "content": (
                    f"📋 Reunión de especialistas convocada. "
                    f"El {agent.name} detectó que tu caso también involucra a {areas_display}. "
                    f"Motivo: {reason}"
                ),
                "reason": reason,
                "secondary_areas": secondary_areas,
            })

            secondary_responses = []
            for sec_area in secondary_areas:
                sec_agent = get_agent(sec_area)
                if not sec_agent:
                    continue

                sec_name = sec_agent.name
                yield _sse({
                    "type": "status",
                    "step": "secondary_working",
                    "content": f"👨‍⚖️ El {sec_name} está revisando tu caso y complementando el análisis del {agent.name}...",
                })

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

                # ── KEY CHANGE: Secondary agents receive the primary response ──
                # They don't work blind — they COMPLEMENT the primary analysis.
                sec_result = await sec_agent.process(
                    query=(
                        f"Otro especialista ({agent.name}) ya analizó esta consulta. "
                        f"Tu rol es COMPLEMENTAR su análisis desde tu perspectiva como {sec_name}. "
                        f"NO repitas lo que ya dijo — enfocate en lo que falta o difiere.\n\n"
                        f"CONSULTA ORIGINAL: {body.message}\n\n"
                        f"ANÁLISIS PREVIO DEL {agent.name.upper()}:\n"
                        f"{full_text[:2500]}\n\n"
                        f"Ahora da tu análisis complementario desde {sec_name}. "
                        f"Sé específico con normativa y artículos aplicables."
                    ),
                    context=sec_context,
                    model=model,
                    conversation_history=conversation_history,
                    user_api_key=user_api_key,
                    reasoning_effort=reasoning,
                )
                secondary_responses.append(sec_result)

                yield _sse({
                    "type": "status",
                    "step": "secondary_done",
                    "content": f"✅ El {sec_name} completó su análisis complementario.",
                })

            # ── Step 10: SYNTHESIZE all responses ──────────────────────────
            all_agent_names = [agent.name] + sec_agent_names
            yield _sse({
                "type": "status",
                "step": "synthesizing",
                "content": f"🔄 Integrando los análisis de {', '.join(all_agent_names)} en una respuesta unificada...",
            })

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
                "reasoning_effort": reasoning,
            }
            synthesis = await synthesize_response(synth_state)

            # Update for final streaming
            full_text = synthesis["response"]
            agent_name = synthesis.get("agent_used", agent.name)
            citations = synthesis.get("citations", citations)

            yield _sse({
                "type": "status",
                "step": "synthesis_done",
                "content": "✅ Síntesis integrada. Preparando respuesta final...",
            })
        else:
            # Single-agent: evaluation passed, no enrichment needed
            yield _sse({
                "type": "status",
                "step": "eval_pass",
                "content": f"✅ La respuesta del {agent.name} cubre completamente tu consulta.",
            })

        # ── Step 11: FINAL STREAM — The ONLY response the user sees ──────────
        # Signal the frontend: "now show tokens"
        yield _sse({
            "type": "final_stream_start",
            "agent_used": agent_name,
            "legal_area": area,
            "is_multi_area": bool(evaluation.get("needs_enrichment")),
        })
        yield _sse({
            "type": "status",
            "step": "streaming",
            "content": "✨ Respuesta lista — mostrando resultado final...",
        })

        # Now stream the final response (already computed) token-by-token
        # We re-call the LLM with stream=True to get natural token-by-token delivery
        # OR if we already have the complete text, we simulate streaming with chunks.
        # Using real re-streaming for the best UX:
        try:
            final_stream = await llm_service.completion(
                messages=[
                    {"role": "system", "content": (
                        "Eres un asistente legal peruano. "
                        "Reproduce EXACTAMENTE el siguiente análisis legal, sin modificar NADA — "
                        "ni agregar, ni quitar, ni reformular. Cópialo textualmente:"
                    )},
                    {"role": "user", "content": full_text},
                ],
                model=model,
                stream=True,
                user_api_key=user_api_key,
                reasoning_effort="low",  # Re-stream is just copying — no thinking needed
            )
            stream = final_stream["stream"]
            streamed_text = ""
            async for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    streamed_text += delta
                    yield _sse({"type": "final_token", "content": delta})

            # If the re-stream produced something reasonable, use it
            # Otherwise fall back to the original computed response
            if len(streamed_text) < len(full_text) * 0.5:
                # Re-stream was too short — fall back to chunk-based simulation
                logger.warning(
                    "Re-stream produced truncated output (%d vs %d chars). "
                    "Falling back to simulated streaming.",
                    len(streamed_text),
                    len(full_text),
                )
                # Send the missing part as chunks
                remaining = full_text[len(streamed_text):]
                for i in range(0, len(remaining), 12):
                    yield _sse({"type": "final_token", "content": remaining[i:i + 12]})
            else:
                # Re-stream was complete; use its output as the persisted response
                full_text = streamed_text

        except Exception as stream_err:
            # Fallback: simulate streaming by chunking the pre-computed text
            logger.warning(f"Final re-stream failed ({stream_err}). Using simulated streaming.")
            for i in range(0, len(full_text), 12):
                yield _sse({"type": "final_token", "content": full_text[i:i + 12]})

        # ── Step 12: Extract and compute final metadata ───────────────────
        latency_ms = int((time.time() - start) * 1000)

        # ── Step 13: Persist via ORM ──────────────────────────────────────
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

        # ── Step 14: Extract and save memories (non-blocking) ─────────────
        if current_user and conv is not None:
            try:
                extraction_msgs = [
                    {"role": "user", "content": body.message},
                    {"role": "assistant", "content": full_text[:1000]},
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

        # ── Step 15: Send "done" event ─────────────────────────────────────
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

    Architecture (v2 — single final stream):
    The entire pipeline runs INTERNALLY — the user only sees status events
    in the orchestrator panel.  After all agents complete, a single
    ``final_stream_start`` event is emitted, followed by ``final_token``
    events with the actual response.

    Events:
    - status: Processing step info (shown in orchestrator timeline panel)
    - classification: Legal area detected
    - agent: Which primary agent is working
    - orchestrator_thinking: Meta-reasoning ("consulting more specialists")
    - final_stream_start: Signals frontend to start showing tokens
    - final_token: Incremental text token (the ONLY response the user sees)
    - done: Final metadata (citations, latency, conversation_id)
    - error: Error message
    """
    # BYOK: Resolve the user's API key before streaming starts.
    # Free tier: if user has no BYOK key, use platform-provided free model.
    user_api_key: str | None = None
    free_tier_active = False
    if current_user is not None and body.model:
        user_api_key = await get_user_keys_for_model(current_user.id, body.model, db)
        if not user_api_key:
            # No BYOK key — try free tier if enabled and user is on free plan
            if settings.free_tier_enabled and current_user.plan == "free":
                resolved = llm_service.resolve_free_tier(body.model)
                if resolved:
                    body.model, user_api_key = resolved
                    free_tier_active = True
                    logger.info(f"Free tier activated for user {current_user.id}: {body.model}")
                else:
                    raise HTTPException(
                        status_code=503,
                        detail="El servicio gratuito no está disponible en este momento. Intenta más tarde.",
                    )
            else:
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
