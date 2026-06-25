"""Chat routes — the core of the legal AI assistant."""

import asyncio
import json
import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.orchestrator import _emit_event, legal_orchestrator
from app.api.deps import RateLimitBucket, RateLimitGuard, get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.services import conversations as conv_service
from app.services.llm_adapter import llm_service
from app.services.llm_key_service import get_user_keys_for_model
from app.services.memory_service import memory_service
from app.services.usage import usage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# --- Schemas ---


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None
    model: str | None = None  # Override default model
    legal_area: str | None = None  # Optional hint for routing
    # Case-analysis state carried across turns by the client.
    # First turn: omit or pass {} → triggers intake.
    # Subsequent turns: send the `case_state` returned by the previous response.
    case_state: dict | None = None


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: str
    agent_used: str
    legal_area: str
    citations: list[dict] | None = None
    model_used: str
    tokens_used: int | None = None
    latency_ms: int
    # Updated case state — client should persist and return on next turn.
    # Contains: case_phase, case_facts, case_pending, case_turn_count, case_area_hint.
    case_state: dict | None = None


class AvailableModelsResponse(BaseModel):
    models: list[dict]


# --- Routes ---


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Send a legal query to the orchestrator.
    The orchestrator classifies, routes to the right agent, and returns a cited response.
    Injects user memory context when the user is authenticated.
    """
    start_time = time.time()

    # Load user memory context (authenticated users only)
    # FIX 5: user_context is passed as a separate parameter — NOT prepended to the query.
    # This keeps the classifier working on the clean query so area routing is accurate.
    user_context: str | None = None
    if current_user is not None:
        try:
            user_context = await memory_service.get_user_context(current_user.id, db)
        except Exception as exc:
            # Memory failure must never block the main response
            logger.warning(f"Failed to load memory context for user {current_user.id}: {exc}")

    # Load conversation history if continuing an existing conversation
    conversation_history: list[dict] = []
    if body.conversation_id is not None and current_user is not None:
        try:
            existing_conv = await conv_service.get_conversation_with_messages(
                db, body.conversation_id, current_user.id
            )
            if existing_conv and existing_conv.messages:
                conversation_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in existing_conv.messages[-20:]
                ]
        except Exception as exc:
            logger.warning("Failed to load conversation history for %s: %s", body.conversation_id, exc)

    # ── Query limit enforcement (unified daily) ─────────────────────────────
    if current_user is not None:
        plan = current_user.plan or "free"
        limit_check = await usage_service.check_daily_limit(current_user.id, plan)
        if not limit_check["allowed"]:
            from app.schemas.quota import QuotaExceededDetail
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=QuotaExceededDetail(
                    plan=plan,
                    used=limit_check["used_today"],
                    limit=limit_check["limit"],
                    reset_at=limit_check["reset_at"],
                    upgrade_url="/planes",
                ).model_dump(mode="json"),
            )

    # ── Model + API key resolution ───────────────────────────────────────────
    # Priority: BYOK key (if plan allows) → platform key → reject
    user_api_key: str | None = None
    resolved_model = body.model
    if current_user is not None:
        plan = current_user.plan or "free"
        is_byok = False

        if body.model:
            # Try BYOK first (only if plan allows)
            from app.services.plan_service import PlanService
            try:
                byok_enabled = PlanService.get_config(plan).byok_enabled
            except ValueError:
                byok_enabled = False
            if byok_enabled:
                user_api_key = await get_user_keys_for_model(current_user.id, body.model, db)
                if user_api_key:
                    is_byok = True
            else:
                # Defense in depth: BYOK not enabled for this plan.
                # Retained rows from prior plans are gated — do NOT use them.
                logger.warning(
                    "byok.plan_gate: user=%s plan=%s model=%s — BYOK disabled by plan, using platform key",
                    current_user.id,
                    plan,
                    body.model,
                )

            if not is_byok:
                # Use platform key — check tier limit first
                tier_check = await usage_service.check_tier_limit(current_user.id, plan, body.model)
                if not tier_check["allowed"]:
                    if tier_check["limit"] == 0:
                        raise HTTPException(
                            status_code=403,
                            detail=(
                                f"El modelo '{body.model}' (Tier {tier_check['tier']}) no está disponible "
                                f"en tu plan {plan}. Actualizá tu plan para acceder."
                            ),
                        )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=(
                                f"Has alcanzado tu límite de {tier_check['limit']} consultas "
                                f"con modelos Tier {tier_check['tier']} por {tier_check['period']}. "
                                f"Usado: {tier_check['used']}/{tier_check['limit']}"
                            ),
                        )
                # Resolve platform key
                free_resolved = await llm_service.resolve_free_tier(body.model)
                if free_resolved:
                    resolved_model, user_api_key = free_resolved
                else:
                    # Try getting platform key directly
                    platform_key = await llm_service._get_platform_key(body.model)
                    if platform_key:
                        user_api_key = platform_key
                        resolved_model = body.model
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Modelo '{body.model}' no disponible en la plataforma.",
                        )
        else:
            # No model specified — use the plan's recommended default.
            # Replaces the prior FREE_TIER_MODELS chain that ignored
            # paid-plan preferences entirely.
            from app.services.plan_service import PlanService
            try:
                default_model = PlanService.get_config(plan).default_model
            except ValueError:
                default_model = "groq/llama-3.3-70b-versatile"
            platform_key = await llm_service._get_platform_key(default_model)
            if platform_key:
                resolved_model = default_model
                user_api_key = platform_key
            else:
                # Plan's preferred default isn't keyed up on this platform —
                # fall through to any free model that IS available.
                free_resolved = await llm_service.resolve_free_tier()
                if free_resolved:
                    resolved_model, user_api_key = free_resolved

    try:
        result = await legal_orchestrator.process_query(
            query=body.message,  # FIX 5: clean query — no memory prepended
            model=resolved_model,
            legal_area_hint=body.legal_area,
            conversation_history=conversation_history,
            user_context=user_context,  # FIX 5: injected separately at agent level
            user_api_key=user_api_key,  # BYOK or free tier platform key
            case_state=body.case_state,  # Case-analysis state across turns
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

    latency_ms = int((time.time() - start_time) * 1000)

    # ── Post-success usage increment ─────────────────────────────────────────
    # Only reached on successful LLM completion — exception path raises before here.
    # Failed LLM calls do NOT increment usage (correct per spec §2).
    if current_user is not None:
        try:
            await usage_service.increment_daily_usage(
                user_id=current_user.id,
                org_id=getattr(current_user, "organization_id", None),
                query_count=1,
                token_count=result.get("tokens_used", 0) if isinstance(result, dict) else 0,
            )
        except Exception as exc:
            logger.warning(
                "increment_daily_usage failed for user %s: %s", current_user.id, exc
            )

    # Extract and persist memories from this message (fire-and-best-effort)
    if current_user is not None:
        try:
            new_memories = await memory_service.extract_memories(
                user_id=current_user.id,
                conversation_id=body.conversation_id,
                messages=[{"role": "user", "content": body.message}],
                db=db,
            )
            if new_memories:
                await memory_service.save_memories(
                    user_id=current_user.id,
                    memories=new_memories,
                    conversation_id=body.conversation_id,
                    db=db,
                )
        except Exception as exc:
            logger.warning(f"Memory extraction failed for user {current_user.id}: {exc}")

    # Persist conversation and messages to DB (authenticated users only)
    final_conversation_id: uuid.UUID = body.conversation_id or uuid.uuid4()
    if current_user is not None:
        try:
            if body.conversation_id is not None:
                # Load existing conversation owned by this user
                existing = await conv_service.get_conversation_with_messages(
                    db, body.conversation_id, current_user.id
                )
                if existing:
                    final_conversation_id = existing.id
                else:
                    # conversation_id provided but not found/owned — create new
                    conv = await conv_service.create_conversation(
                        db=db,
                        user_id=current_user.id,
                        title=body.message[:80],
                        legal_area=result["legal_area"],
                        model_used=result["model_used"],
                    )
                    final_conversation_id = conv.id
            else:
                # No conversation_id — create new conversation
                conv = await conv_service.create_conversation(
                    db=db,
                    user_id=current_user.id,
                    title=body.message[:80],
                    legal_area=result["legal_area"],
                    model_used=result["model_used"],
                )
                final_conversation_id = conv.id

            # Save user message
            await conv_service.add_message(
                db=db,
                conversation_id=final_conversation_id,
                role="user",
                content=body.message,
            )

            # Save assistant message with full metadata
            await conv_service.add_message(
                db=db,
                conversation_id=final_conversation_id,
                role="assistant",
                content=result["response"],
                agent_used=result.get("agent_used"),
                legal_area=result.get("legal_area"),
                model=result.get("model_used"),
                citations=result.get("citations"),
                tokens_used=result.get("tokens_used"),
                latency_ms=latency_ms,
            )

            # Snapshot the latest case-analysis state so the user can resume
            # this case from /historial → /analizar?conversation=<id>.
            await conv_service.update_case_state(
                db=db,
                conversation_id=final_conversation_id,
                case_state=result.get("case_state"),
            )
        except Exception as exc:
            # Persistence failure must never break the response
            logger.warning("Conversation persistence failed for user %s: %s", current_user.id, exc)

    return ChatResponse(
        conversation_id=final_conversation_id,
        message=result["response"],
        agent_used=result["agent_used"],
        legal_area=result["legal_area"],
        citations=result.get("citations"),
        model_used=result["model_used"],
        tokens_used=result.get("tokens_used"),
        latency_ms=latency_ms,
        case_state=result.get("case_state"),
    )


@router.post("/stream-case")
async def chat_stream_case(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """
    Streaming variant of /chat/query for the case-analysis flow.

    Emits Server-Sent Events as the orchestrator progresses through
    intake → investigation → analysis. Final payload is delivered as a
    `done` event whose `data` matches the ChatResponse schema. The frontend
    uses this to drive a real reasoning panel instead of simulating steps.

    Events:
      - phase_start: {phase: intake|investigation|analysis, ...}
      - step:        {node, status: start|done, phase, ...}
      - done:        full chat response payload
      - error:       {message}
    """
    start_time = time.time()

    # ── User context + conversation history (same as /query) ───────────────
    user_context: str | None = None
    if current_user is not None:
        try:
            user_context = await memory_service.get_user_context(current_user.id, db)
        except Exception as exc:
            logger.warning(f"Failed to load memory context for user {current_user.id}: {exc}")

    conversation_history: list[dict] = []
    if body.conversation_id is not None and current_user is not None:
        try:
            existing_conv = await conv_service.get_conversation_with_messages(
                db, body.conversation_id, current_user.id
            )
            if existing_conv and existing_conv.messages:
                conversation_history = [
                    {"role": msg.role, "content": msg.content}
                    for msg in existing_conv.messages[-20:]
                ]
        except Exception as exc:
            logger.warning("Failed to load conversation history for %s: %s", body.conversation_id, exc)

    # ── Quota check (same as /query) ──────────────────────────────────────
    if current_user is not None:
        plan = current_user.plan or "free"
        limit_check = await usage_service.check_daily_limit(current_user.id, plan)
        if not limit_check["allowed"]:
            from app.schemas.quota import QuotaExceededDetail
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=QuotaExceededDetail(
                    plan=plan,
                    used=limit_check["used_today"],
                    limit=limit_check["limit"],
                    reset_at=limit_check["reset_at"],
                    upgrade_url="/planes",
                ).model_dump(mode="json"),
            )

    # ── Model + API key resolution (mirrors /query — TODO: extract helper) ─
    user_api_key: str | None = None
    resolved_model = body.model
    if current_user is not None:
        plan = current_user.plan or "free"
        is_byok = False
        if body.model:
            from app.services.plan_service import PlanService
            try:
                byok_enabled = PlanService.get_config(plan).byok_enabled
            except ValueError:
                byok_enabled = False
            if byok_enabled:
                user_api_key = await get_user_keys_for_model(current_user.id, body.model, db)
                if user_api_key:
                    is_byok = True
            if not is_byok:
                tier_check = await usage_service.check_tier_limit(current_user.id, plan, body.model)
                if not tier_check["allowed"]:
                    if tier_check["limit"] == 0:
                        raise HTTPException(
                            status_code=403,
                            detail=(
                                f"El modelo '{body.model}' (Tier {tier_check['tier']}) no está disponible "
                                f"en tu plan {plan}. Actualizá tu plan para acceder."
                            ),
                        )
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=(
                            f"Has alcanzado tu límite de {tier_check['limit']} consultas "
                            f"con modelos Tier {tier_check['tier']} por {tier_check['period']}. "
                            f"Usado: {tier_check['used']}/{tier_check['limit']}"
                        ),
                    )
                free_resolved = await llm_service.resolve_free_tier(body.model)
                if free_resolved:
                    resolved_model, user_api_key = free_resolved
                else:
                    platform_key = await llm_service._get_platform_key(body.model)
                    if platform_key:
                        user_api_key = platform_key
                        resolved_model = body.model
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Modelo '{body.model}' no disponible en la plataforma.",
                        )
        else:
            # No model specified — use the plan's recommended default.
            from app.services.plan_service import PlanService
            try:
                default_model = PlanService.get_config(plan).default_model
            except ValueError:
                default_model = "groq/llama-3.3-70b-versatile"
            platform_key = await llm_service._get_platform_key(default_model)
            if platform_key:
                resolved_model = default_model
                user_api_key = platform_key
            else:
                free_resolved = await llm_service.resolve_free_tier()
                if free_resolved:
                    resolved_model, user_api_key = free_resolved

    queue: asyncio.Queue = asyncio.Queue()

    async def emit_cb(event_type: str, data: dict) -> None:
        await queue.put((event_type, data))

    async def run_pipeline() -> None:
        try:
            result = await legal_orchestrator.process_query(
                query=body.message,
                model=resolved_model,
                legal_area_hint=body.legal_area,
                conversation_history=conversation_history,
                user_context=user_context,
                user_api_key=user_api_key,
                case_state=body.case_state,
            )
            latency_ms = int((time.time() - start_time) * 1000)

            # ── Post-success persistence (same as /query) ─────────────────
            final_conversation_id: uuid.UUID = body.conversation_id or uuid.uuid4()
            if current_user is not None:
                try:
                    await usage_service.increment_daily_usage(
                        user_id=current_user.id,
                        org_id=getattr(current_user, "organization_id", None),
                        query_count=1,
                        token_count=result.get("tokens_used", 0) if isinstance(result, dict) else 0,
                    )
                except Exception as exc:
                    logger.warning("increment_daily_usage failed for user %s: %s", current_user.id, exc)

                try:
                    new_memories = await memory_service.extract_memories(
                        user_id=current_user.id,
                        conversation_id=body.conversation_id,
                        messages=[{"role": "user", "content": body.message}],
                        db=db,
                    )
                    if new_memories:
                        await memory_service.save_memories(
                            user_id=current_user.id,
                            memories=new_memories,
                            conversation_id=body.conversation_id,
                            db=db,
                        )
                except Exception as exc:
                    logger.warning(f"Memory extraction failed for user {current_user.id}: {exc}")

                try:
                    if body.conversation_id is not None:
                        existing = await conv_service.get_conversation_with_messages(
                            db, body.conversation_id, current_user.id
                        )
                        if existing:
                            final_conversation_id = existing.id
                        else:
                            conv = await conv_service.create_conversation(
                                db=db,
                                user_id=current_user.id,
                                title=body.message[:80],
                                legal_area=result["legal_area"],
                                model_used=result["model_used"],
                            )
                            final_conversation_id = conv.id
                    else:
                        conv = await conv_service.create_conversation(
                            db=db,
                            user_id=current_user.id,
                            title=body.message[:80],
                            legal_area=result["legal_area"],
                            model_used=result["model_used"],
                        )
                        final_conversation_id = conv.id

                    await conv_service.add_message(
                        db=db,
                        conversation_id=final_conversation_id,
                        role="user",
                        content=body.message,
                    )
                    await conv_service.add_message(
                        db=db,
                        conversation_id=final_conversation_id,
                        role="assistant",
                        content=result["response"],
                        agent_used=result.get("agent_used"),
                        legal_area=result.get("legal_area"),
                        model=result.get("model_used"),
                        citations=result.get("citations"),
                        tokens_used=result.get("tokens_used"),
                        latency_ms=latency_ms,
                    )
                    await conv_service.update_case_state(
                        db=db,
                        conversation_id=final_conversation_id,
                        case_state=result.get("case_state"),
                    )
                except Exception as exc:
                    logger.warning("Conversation persistence failed for user %s: %s", current_user.id, exc)

            done_payload = {
                "conversation_id": str(final_conversation_id),
                "message": result["response"],
                "agent_used": result["agent_used"],
                "legal_area": result["legal_area"],
                "citations": result.get("citations"),
                "model_used": result["model_used"],
                "tokens_used": result.get("tokens_used"),
                "latency_ms": latency_ms,
                "case_state": result.get("case_state"),
            }
            await queue.put(("done", done_payload))
        except Exception as exc:
            logger.exception("stream-case pipeline failed")
            await queue.put(("error", {"message": str(exc)}))
        finally:
            await queue.put(None)

    async def event_stream():
        token = _emit_event.set(emit_cb)
        task = asyncio.create_task(run_pipeline())
        # Heartbeat keeps the SSE socket alive during long-running LLM nodes
        # (e.g. gpt-5.5 with max_tokens=4096 can block 30-60s without emitting
        # any event). Without this, Chrome / proxies cut the idle connection
        # and the frontend never sees the final `done`.
        KEEPALIVE_INTERVAL = 10.0
        try:
            while True:
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=KEEPALIVE_INTERVAL)
                except asyncio.TimeoutError:
                    # SSE comment line — ignored by EventSource but resets idle timers.
                    yield ": keepalive\n\n"
                    continue
                if item is None:
                    break
                event_type, data = item
                yield f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"
        finally:
            _emit_event.reset(token)
            if not task.done():
                task.cancel()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/models", response_model=AvailableModelsResponse)
async def list_models():
    """List available LLM models the user can select."""
    models = llm_service.get_available_models()
    return AvailableModelsResponse(models=models)


@router.post("/models/ping")
async def ping_model(
    body: dict,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Ping a model to check if it's reachable with the user's API key.

    Sends a minimal completion request ("ping") and returns latency + status.
    """
    model_id = body.get("model")
    if not model_id:
        raise HTTPException(status_code=400, detail="model is required")

    # Resolve BYOK key
    user_api_key: str | None = None
    if current_user is not None:
        user_api_key = await get_user_keys_for_model(current_user.id, model_id, db)

    start = time.time()
    try:
        result = await llm_service.completion(
            messages=[{"role": "user", "content": "Responde SOLO 'pong'."}],
            model=model_id,
            max_tokens=5,
            temperature=0.0,
            stream=False,
            user_api_key=user_api_key,
        )
        latency_ms = int((time.time() - start) * 1000)
        content = result.get("content", "").strip()
        return {
            "model": model_id,
            "status": "active",
            "latency_ms": latency_ms,
            "response": content[:20],
        }
    except Exception as e:
        latency_ms = int((time.time() - start) * 1000)
        error_msg = str(e)[:200]
        logger.warning(f"Ping failed for {model_id}: {error_msg}")
        return {
            "model": model_id,
            "status": "error",
            "latency_ms": latency_ms,
            "error": error_msg,
        }


@router.get("/agents")
async def list_agents():
    """List available legal domain agents."""
    return {
        "agents": [
            {"id": "civil", "name": "Derecho Civil", "description": "Código Civil, CPC, Familia, Sucesiones, Contratos, Obligaciones"},
            {"id": "penal", "name": "Derecho Penal", "description": "Código Penal, NCPP, Ejecución Penal"},
            {"id": "laboral", "name": "Derecho Laboral", "description": "LPCL, Seguridad y Salud, Relaciones Colectivas"},
            {"id": "tributario", "name": "Derecho Tributario", "description": "Código Tributario, IR, IGV, SUNAT"},
            {"id": "administrativo", "name": "Derecho Administrativo", "description": "LPAG, Contrataciones del Estado"},
            {"id": "corporativo", "name": "Derecho Corporativo", "description": "LGS, Mercado de Valores, MYPE"},
            {"id": "constitucional", "name": "Derecho Constitucional", "description": "Constitución 1993, Procesos Constitucionales, TC"},
            {"id": "registral", "name": "Derecho Registral", "description": "SUNARP, Registros Públicos"},
            {"id": "competencia", "name": "Competencia y PI", "description": "INDECOPI, Marcas, Patentes, Consumidor"},
            {"id": "compliance", "name": "Compliance", "description": "Datos Personales, Anticorrupción, Lavado de Activos"},
            {"id": "comercio_exterior", "name": "Comercio Exterior", "description": "Aduanas, TLC, MINCETUR"},
        ]
    }
