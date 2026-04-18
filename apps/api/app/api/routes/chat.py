"""Chat routes — the core of the legal AI assistant."""

import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.services.llm_adapter import llm_service
from app.services.llm_key_service import get_user_keys_for_model
from app.agents.orchestrator import legal_orchestrator
from app.services.memory_service import memory_service
from app.services import conversations as conv_service
from app.services.usage import usage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


# --- Schemas ---


class ChatRequest(BaseModel):
    message: str
    conversation_id: uuid.UUID | None = None
    model: str | None = None  # Override default model
    legal_area: str | None = None  # Optional hint for routing


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: str
    agent_used: str
    legal_area: str
    citations: list[dict] | None = None
    model_used: str
    tokens_used: int | None = None
    latency_ms: int


class AvailableModelsResponse(BaseModel):
    models: list[dict]


# --- Routes ---


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
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

    # ── Query limit enforcement ─────────────────────────────────────────────
    # Free plan: weekly limit. Paid plans: daily limit.
    if current_user is not None:
        plan = current_user.plan or "free"
        from app.services.usage import PLAN_LIMITS
        plan_config = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])

        if plan == "free":
            limit_check = await usage_service.check_weekly_limit(current_user.id, plan)
            if not limit_check["allowed"]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Has alcanzado tu límite semanal de {limit_check['weekly_limit']} consultas. "
                        f"Se reinicia el lunes. Actualizá a Profesional para 30 consultas/día. "
                        f"Usado: {limit_check['used_week']}/{limit_check['weekly_limit']}"
                    ),
                )
        else:
            limit_check = await usage_service.check_daily_limit(current_user.id, plan)
            if not limit_check["allowed"]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"Has alcanzado tu límite diario de {limit_check['daily_limit']} consultas. "
                        f"Usado: {limit_check['used_today']}/{limit_check['daily_limit']}"
                    ),
                )

    # ── Model + API key resolution ───────────────────────────────────────────
    # Priority: BYOK key (if plan allows) → platform key → reject
    user_api_key: str | None = None
    resolved_model = body.model
    if current_user is not None:
        plan = current_user.plan or "free"
        plan_config = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])
        is_byok = False

        if body.model:
            # Try BYOK first (only if plan allows)
            if plan_config.get("byok_enabled", False):
                user_api_key = await get_user_keys_for_model(current_user.id, body.model, db)
                if user_api_key:
                    is_byok = True

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
                free_resolved = llm_service.resolve_free_tier(body.model)
                if free_resolved:
                    resolved_model, user_api_key = free_resolved
                else:
                    # Try getting platform key directly
                    platform_key = llm_service._get_platform_key(body.model)
                    if platform_key:
                        user_api_key = platform_key
                        resolved_model = body.model
                    else:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Modelo '{body.model}' no disponible en la plataforma.",
                        )
        else:
            # No model specified — use default free tier
            free_resolved = llm_service.resolve_free_tier()
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
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI processing error: {str(e)}")

    latency_ms = int((time.time() - start_time) * 1000)

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
