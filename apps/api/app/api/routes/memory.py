"""Memory routes — manage user context memories."""

import uuid
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.memory_service import VALID_CATEGORIES, memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class MemoryOut(BaseModel):
    id: uuid.UUID
    category: str
    content: str
    confidence: float
    is_active: bool
    source_conversation_id: uuid.UUID | None
    created_at: str

    model_config = {"from_attributes": True}


class MemoryGroup(BaseModel):
    category: str
    label: str
    memories: list[MemoryOut]


class MemoriesResponse(BaseModel):
    groups: list[MemoryGroup]
    total: int
    active_count: int


class ToggleBody(BaseModel):
    is_active: bool


class MemorySettingsOut(BaseModel):
    memory_enabled: bool
    auto_extract: bool


class MemorySettingsIn(BaseModel):
    memory_enabled: bool | None = None
    auto_extract: bool | None = None


_CATEGORY_LABELS = {
    "profession": "Profesion",
    "interests": "Intereses",
    "cases": "Casos activos",
    "preferences": "Preferencias",
    "context": "Contexto",
}

_CATEGORY_ORDER = ["profession", "interests", "cases", "preferences", "context"]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("/", response_model=MemoriesResponse)
async def list_memories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all memories for the current user, grouped by category."""
    memories = await memory_service.list_memories(user.id, db)

    grouped: dict[str, list] = defaultdict(list)
    for mem in memories:
        grouped[mem.category].append(mem)

    groups = []
    for cat in _CATEGORY_ORDER:
        if cat in grouped:
            groups.append(
                MemoryGroup(
                    category=cat,
                    label=_CATEGORY_LABELS.get(cat, cat.title()),
                    memories=[
                        MemoryOut(
                            id=m.id,
                            category=m.category,
                            content=m.content,
                            confidence=m.confidence,
                            is_active=m.is_active,
                            source_conversation_id=m.source_conversation_id,
                            created_at=m.created_at.isoformat(),
                        )
                        for m in grouped[cat]
                    ],
                )
            )
    # Add any unexpected categories at the end
    for cat, mems in grouped.items():
        if cat not in _CATEGORY_ORDER:
            groups.append(
                MemoryGroup(
                    category=cat,
                    label=cat.title(),
                    memories=[
                        MemoryOut(
                            id=m.id,
                            category=m.category,
                            content=m.content,
                            confidence=m.confidence,
                            is_active=m.is_active,
                            source_conversation_id=m.source_conversation_id,
                            created_at=m.created_at.isoformat(),
                        )
                        for m in mems
                    ],
                )
            )

    total = len(memories)
    active_count = sum(1 for m in memories if m.is_active)

    return MemoriesResponse(groups=groups, total=total, active_count=active_count)


@router.put("/{memory_id}/toggle", response_model=MemoryOut)
async def toggle_memory(
    memory_id: uuid.UUID,
    body: ToggleBody,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate a specific memory."""
    memory = await memory_service.toggle_memory(user.id, memory_id, body.is_active, db)
    if not memory:
        raise HTTPException(status_code=404, detail="Memoria no encontrada")

    return MemoryOut(
        id=memory.id,
        category=memory.category,
        content=memory.content,
        confidence=memory.confidence,
        is_active=memory.is_active,
        source_conversation_id=memory.source_conversation_id,
        created_at=memory.created_at.isoformat(),
    )


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(
    memory_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hard delete a specific memory."""
    deleted = await memory_service.delete_memory(user.id, memory_id, db)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memoria no encontrada")


@router.delete("/", status_code=200)
async def clear_all_memories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Hard delete ALL memories for the current user."""
    count = await memory_service.clear_all_memories(user.id, db)
    return {"deleted": count, "message": f"Se eliminaron {count} memorias"}


@router.get("/settings", response_model=MemorySettingsOut)
async def get_memory_settings(
    user: User = Depends(get_current_user),
):
    """Get memory feature settings for the current user (persisted in user.preferences)."""
    prefs = user.preferences or {}
    return MemorySettingsOut(
        memory_enabled=prefs.get("memory_enabled", True),
        auto_extract=prefs.get("auto_extract", True),
    )


@router.put("/settings", response_model=MemorySettingsOut)
async def update_memory_settings(
    body: MemorySettingsIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update memory feature settings — persisted in user.preferences JSONB column."""
    if user.preferences is None:
        user.preferences = {}
    user.preferences = {
        **user.preferences,
        "memory_enabled": body.memory_enabled if body.memory_enabled is not None else user.preferences.get("memory_enabled", True),
        "auto_extract": body.auto_extract if body.auto_extract is not None else user.preferences.get("auto_extract", True),
    }
    await db.flush()
    return MemorySettingsOut(
        memory_enabled=user.preferences["memory_enabled"],
        auto_extract=user.preferences["auto_extract"],
    )
