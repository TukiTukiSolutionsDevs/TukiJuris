"""Folders routes — CRUD for conversation folders."""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RateLimitBucket, RateLimitGuard, get_current_user
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.tag import Folder
from app.models.user import User

router = APIRouter(tags=["folders"])

MAX_FOLDERS_PER_USER = 10


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class FolderOut(BaseModel):
    id: uuid.UUID
    name: str
    icon: str
    position: int
    conversation_count: int
    created_at: str

    model_config = {"from_attributes": True}


class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    icon: str = Field(default="folder", max_length=50)


class FolderUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    icon: str | None = Field(None, max_length=50)
    position: int | None = None


# ---------------------------------------------------------------------------
# Folder CRUD
# ---------------------------------------------------------------------------


@router.get("/folders/", response_model=list[FolderOut])
async def list_folders(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.READ)),
):
    """List all folders for the authenticated user with conversation counts."""
    result = await db.execute(
        select(Folder)
        .where(Folder.user_id == user.id)
        .order_by(Folder.position, Folder.name)
    )
    folders = result.scalars().all()

    output = []
    for f in folders:
        count_result = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.folder_id == f.id,
                Conversation.user_id == user.id,
            )
        )
        count = count_result.scalar_one() or 0
        output.append(
            FolderOut(
                id=f.id,
                name=f.name,
                icon=f.icon,
                position=f.position,
                conversation_count=count,
                created_at=f.created_at.isoformat(),
            )
        )
    return output


@router.post("/folders/", response_model=FolderOut, status_code=201)
async def create_folder(
    body: FolderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Create a new folder. Max 10 folders per user."""
    # Enforce limit
    count_result = await db.execute(
        select(func.count(Folder.id)).where(Folder.user_id == user.id)
    )
    folder_count = count_result.scalar_one() or 0
    if folder_count >= MAX_FOLDERS_PER_USER:
        raise HTTPException(
            status_code=400,
            detail=f"Maximo {MAX_FOLDERS_PER_USER} carpetas por usuario",
        )

    # Check duplicate name
    existing = await db.execute(
        select(Folder).where(Folder.user_id == user.id, Folder.name == body.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Ya existe una carpeta con ese nombre")

    folder = Folder(
        user_id=user.id,
        name=body.name,
        icon=body.icon,
        position=folder_count,  # append at end
    )
    db.add(folder)
    await db.flush()
    await db.commit()
    await db.refresh(folder)

    return FolderOut(
        id=folder.id,
        name=folder.name,
        icon=folder.icon,
        position=folder.position,
        conversation_count=0,
        created_at=folder.created_at.isoformat(),
    )


@router.put("/folders/{folder_id}", response_model=FolderOut)
async def update_folder(
    folder_id: uuid.UUID,
    body: FolderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Update a folder's name, icon, or position."""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    if body.name is not None:
        # Check duplicate name (excluding itself)
        dup = await db.execute(
            select(Folder).where(
                Folder.user_id == user.id,
                Folder.name == body.name,
                Folder.id != folder_id,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Ya existe una carpeta con ese nombre")
        folder.name = body.name

    if body.icon is not None:
        folder.icon = body.icon

    if body.position is not None:
        folder.position = body.position

    await db.flush()
    await db.commit()
    await db.refresh(folder)

    count_result = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.folder_id == folder.id,
            Conversation.user_id == user.id,
        )
    )
    count = count_result.scalar_one() or 0

    return FolderOut(
        id=folder.id,
        name=folder.name,
        icon=folder.icon,
        position=folder.position,
        conversation_count=count,
        created_at=folder.created_at.isoformat(),
    )


@router.delete("/folders/{folder_id}", status_code=204)
async def delete_folder(
    folder_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Delete a folder. Conversations in the folder get folder_id=NULL."""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id)
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    # Unassign conversations (SET NULL handled by FK, but we do it explicitly for clarity)
    await db.execute(
        update(Conversation)
        .where(Conversation.folder_id == folder_id, Conversation.user_id == user.id)
        .values(folder_id=None)
    )

    await db.delete(folder)
    await db.commit()


# ---------------------------------------------------------------------------
# Move conversation to/from folder
# ---------------------------------------------------------------------------


@router.put("/conversations/{conversation_id}/folder/{folder_id}")
async def move_conversation_to_folder(
    conversation_id: uuid.UUID,
    folder_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Move a conversation into a folder."""
    # Verify conversation ownership
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    # Verify folder ownership
    folder_result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == user.id)
    )
    if not folder_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    conv.folder_id = folder_id
    await db.flush()
    await db.commit()

    return {"detail": "Conversacion movida a la carpeta"}


@router.delete("/conversations/{conversation_id}/folder", status_code=204)
async def remove_conversation_from_folder(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    _rl: None = Depends(RateLimitGuard(RateLimitBucket.WRITE)),
):
    """Remove a conversation from its folder (set folder_id to NULL)."""
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = conv_result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    conv.folder_id = None
    await db.flush()
    await db.commit()
