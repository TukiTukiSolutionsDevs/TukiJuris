"""
Memory Service — extract, store, and retrieve user context memories.

V1 uses regex-based extraction for reliability.
The extracted facts persist across conversations to personalise responses.
"""

import logging
import re
import uuid
from collections import defaultdict

from sqlalchemy import and_, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.memory import UserMemory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Regex-based extraction patterns (V1 — no LLM required)
# ---------------------------------------------------------------------------

_PROFESSION_PATTERNS = [
    (r"\bsoy\s+(abogad[oa]|notari[oa]|juez|jueza|fiscal|magistrad[oa])\b", "profession"),
    (r"\bsoy\s+abogad[oa]\s+(?:especialista\s+en\s+|de\s+)?(\w[\w\s]{2,40})", "profession"),
    (r"\btrabajo\s+(?:en|como)\s+([^,.]{5,60})", "profession"),
    (r"\bme\s+desempe[nñ]o\s+como\s+([^,.]{5,50})", "profession"),
    (r"\bejercemos?\s+en\s+(?:el\s+estudio\s+)?([^,.]{5,60})", "profession"),
    (r"\bestudio\s+(?:jur[ií]dico\s+|de\s+abogados?\s+)?([A-Z][^,.]{3,50})", "profession"),
]

_INTERESTS_PATTERNS = [
    (r"\bme\s+(?:interesa|especializo\s+en|dedico\s+a)\s+(?:el\s+|la\s+|los\s+|las\s+)?([^,.]{5,60})", "interests"),
    (r"\bes(?:toy\s+especializad[oa]|pecialidad)\s+en\s+([^,.]{5,60})", "interests"),
    (r"\btema(?:s)?\s+de\s+([^,.]{5,50})", "interests"),
]

_CASES_PATTERNS = [
    (r"\btengo\s+un\s+caso\s+(?:de\s+)?([^,.]{5,80})", "cases"),
    (r"\bmi\s+cliente\s+(?:tiene\s+un\s+caso\s+de\s+|fue\s+)?([^,.]{5,80})", "cases"),
    (r"\bexpediente\s+(?:n[uo]?\.\s*)?([A-Z0-9][\w\-/]{3,30})", "cases"),
    (r"\bproceso\s+(?:judicial\s+)?(?:de\s+|por\s+)?([^,.]{5,60})", "cases"),
    (r"\bdemand[ao]\s+(?:por\s+|de\s+)?([^,.]{5,60})", "cases"),
]

_PREFERENCES_PATTERNS = [
    (r"\bprefiero\s+(?:respuestas?\s+)?([^,.]{5,60})", "preferences"),
    (r"\bnecesito\s+(?:que\s+(?:seas|sea[sn])\s+)?([^,.]{5,50})", "preferences"),
    (r"\bpor\s+favor\s+(?:siempre\s+)?([^,.]{5,50})", "preferences"),
]

_CONTEXT_PATTERNS = [
    (r"\bopero\s+(?:desde\s+|en\s+)([A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)?)", "context"),
    (r"\bestoy\s+(?:ubicad[oa]\s+)?en\s+([A-Z][a-záéíóúñ]+(?:\s+[A-Z][a-záéíóúñ]+)?)", "context"),
    (r"\bmis\s+clientes?\s+(?:son\s+|trabajan?\s+en\s+)?([^,.]{5,60})", "context"),
    (r"\btrabajamos?\s+(?:principalmente\s+)?con\s+([^,.]{5,60})", "context"),
    (r"\bzona\s+(?:norte|sur|este|oeste|centro)\b", "context"),
]

_ALL_PATTERNS = (
    _PROFESSION_PATTERNS
    + _INTERESTS_PATTERNS
    + _CASES_PATTERNS
    + _PREFERENCES_PATTERNS
    + _CONTEXT_PATTERNS
)

# Category labels for the formatted context string
_CATEGORY_LABELS = {
    "profession": "Profesion",
    "interests": "Intereses",
    "cases": "Casos activos",
    "preferences": "Preferencias",
    "context": "Contexto",
}

VALID_CATEGORIES = set(_CATEGORY_LABELS.keys())


def _extract_from_text(text: str) -> list[dict]:
    """Apply all patterns to a single text string. Returns list of {category, content}."""
    found = []
    text_lower = text.lower()
    for pattern, category in _ALL_PATTERNS:
        for match in re.finditer(pattern, text_lower, re.IGNORECASE):
            # Use the full match or first group if present
            if match.lastindex:
                content = match.group(1).strip()
            else:
                content = match.group(0).strip()
            if len(content) >= 5:
                found.append({"category": category, "content": content})
    return found


def _is_duplicate(new_content: str, existing_contents: list[str], threshold: float = 0.7) -> bool:
    """Simple fuzzy dedup: check if new_content overlaps significantly with any existing one."""
    new_words = set(new_content.lower().split())
    if not new_words:
        return False
    for existing in existing_contents:
        existing_words = set(existing.lower().split())
        if not existing_words:
            continue
        intersection = new_words & existing_words
        union = new_words | existing_words
        if len(union) > 0 and len(intersection) / len(union) >= threshold:
            return True
    return False


class MemoryService:
    """Service for extracting, storing, and serving user context memories."""

    async def extract_memories(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        messages: list[dict],
        db: AsyncSession,
    ) -> list[dict]:
        """
        Extract key facts about the user from conversation messages.
        Uses LLM extraction (platform key) with regex fallback.

        Args:
            user_id: The user's UUID
            conversation_id: Source conversation (for provenance)
            messages: List of {"role": str, "content": str} dicts
            db: Async database session

        Returns:
            List of new {category, content} dicts that were NOT already known.
        """
        # Look at user messages AND assistant responses (to extract case context)
        all_texts = [m["content"] for m in messages if m.get("content")]
        user_texts = [m["content"] for m in messages if m.get("role") == "user"]
        if not all_texts:
            return []

        # --- Strategy 1: LLM extraction (platform key, internal operation) ---
        candidates = await self._extract_with_llm(all_texts)

        # --- Strategy 2: Regex fallback ---
        if not candidates:
            for text in user_texts:
                candidates.extend(_extract_from_text(text))

        if not candidates:
            logger.debug("No memories extracted from %d messages", len(messages))
            return []

        logger.info("Extracted %d memory candidates from conversation", len(candidates))

        # Load existing active memories to deduplicate
        result = await db.execute(
            select(UserMemory).where(
                and_(UserMemory.user_id == user_id, UserMemory.is_active.is_(True))
            )
        )
        existing = result.scalars().all()
        existing_by_category: dict[str, list[str]] = defaultdict(list)
        for mem in existing:
            existing_by_category[mem.category].append(mem.content)

        # Deduplicate
        new_memories: list[dict] = []
        seen_in_batch: dict[str, list[str]] = defaultdict(list)
        for candidate in candidates:
            cat = candidate["category"]
            content = candidate["content"]
            existing_pool = existing_by_category[cat] + seen_in_batch[cat]
            if not _is_duplicate(content, existing_pool):
                new_memories.append(candidate)
                seen_in_batch[cat].append(content)

        return new_memories

    async def _extract_with_llm(self, texts: list[str]) -> list[dict]:
        """Use a lightweight LLM call to extract user facts from messages."""
        import json as _json

        try:
            from app.services.llm_adapter import llm_service
        except ImportError:
            return []

        combined = "\n---\n".join(t[:500] for t in texts[-6:])  # last 6 messages, 500 chars each

        prompt = f"""Analiza los siguientes mensajes de un chat legal y extrae HECHOS concretos sobre el usuario.

MENSAJES:
{combined}

Extrae SOLO información factual y concreta. NO extraigas preguntas ni saludos genéricos.
Si no hay hechos concretos sobre el usuario, responde con un array vacío [].

Categorías válidas:
- profession: profesión, lugar de trabajo, estudio jurídico
- interests: áreas de interés legal, temas que consulta frecuentemente
- cases: casos activos, expedientes, situaciones legales mencionadas
- preferences: cómo prefiere las respuestas, idioma, formato
- context: ubicación geográfica, tipo de clientes, sector

Responde SOLO con un array JSON, sin explicación:
[{{"category": "cases", "content": "Problema de discoteca cerca a colegio en Cerro Colorado, Arequipa"}}]

Si no hay hechos concretos, responde: []"""

        try:
            result = await llm_service.completion(
                messages=[{"role": "user", "content": prompt}],
                model=None,  # platform default (cheapest)
                temperature=0.0,
                max_tokens=500,
                # No user_api_key → uses platform key (internal operation)
            )
            content = result.get("content", "").strip()

            # Parse JSON array from response
            # Try to find JSON array in the response
            import re as _re
            json_match = _re.search(r'\[.*\]', content, _re.DOTALL)
            if json_match:
                parsed = _json.loads(json_match.group())
                if isinstance(parsed, list):
                    # Validate each item
                    valid = []
                    for item in parsed:
                        if (isinstance(item, dict)
                                and item.get("category") in VALID_CATEGORIES
                                and isinstance(item.get("content"), str)
                                and len(item["content"]) >= 5):
                            valid.append({
                                "category": item["category"],
                                "content": item["content"][:200],  # cap length
                                "confidence": 0.85,
                            })
                    return valid
        except Exception as e:
            logger.warning("LLM memory extraction failed (falling back to regex): %s", e)

        return []

    async def save_memories(
        self,
        user_id: uuid.UUID,
        memories: list[dict],
        conversation_id: uuid.UUID | None,
        db: AsyncSession,
    ) -> int:
        """
        Persist extracted memories to the database.

        Returns:
            Count of memories saved.
        """
        if not memories:
            return 0

        count = 0
        for mem in memories:
            category = mem.get("category", "context")
            if category not in VALID_CATEGORIES:
                category = "context"
            record = UserMemory(
                user_id=user_id,
                category=category,
                content=mem["content"],
                source_conversation_id=conversation_id,
                confidence=mem.get("confidence", 0.8),
                is_active=True,
            )
            db.add(record)
            count += 1

        if count:
            await db.commit()
            logger.info(f"Saved {count} new memories for user {user_id}")

        return count

    async def get_user_context(
        self,
        user_id: uuid.UUID,
        db: AsyncSession,
        limit: int = 20,
    ) -> str:
        """
        Build a context string from the user's active memories for LLM injection.

        Returns formatted markdown string or empty string if no memories.
        """
        result = await db.execute(
            select(UserMemory)
            .where(and_(UserMemory.user_id == user_id, UserMemory.is_active.is_(True)))
            .order_by(UserMemory.created_at.desc())
            .limit(limit)
        )
        memories = result.scalars().all()

        if not memories:
            return ""

        grouped: dict[str, list[str]] = defaultdict(list)
        for mem in memories:
            grouped[mem.category].append(mem.content)

        lines = ["## Contexto del Usuario"]
        for category in ["profession", "interests", "cases", "preferences", "context"]:
            if category in grouped:
                label = _CATEGORY_LABELS[category]
                contents = ", ".join(grouped[category])
                lines.append(f"**{label}**: {contents}")

        return "\n".join(lines)

    async def list_memories(
        self,
        user_id: uuid.UUID,
        db: AsyncSession,
    ) -> list[UserMemory]:
        """Return all memories for a user (active and inactive), newest first."""
        result = await db.execute(
            select(UserMemory)
            .where(UserMemory.user_id == user_id)
            .order_by(UserMemory.created_at.desc())
        )
        return list(result.scalars().all())

    async def toggle_memory(
        self,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
        is_active: bool,
        db: AsyncSession,
    ) -> UserMemory | None:
        """Toggle a memory's active state. Returns updated record or None if not found."""
        result = await db.execute(
            select(UserMemory).where(
                and_(UserMemory.id == memory_id, UserMemory.user_id == user_id)
            )
        )
        memory = result.scalar_one_or_none()
        if not memory:
            return None

        memory.is_active = is_active
        await db.commit()
        await db.refresh(memory)
        return memory

    async def delete_memory(
        self,
        user_id: uuid.UUID,
        memory_id: uuid.UUID,
        db: AsyncSession,
    ) -> bool:
        """Hard delete a specific memory. Returns True if deleted, False if not found."""
        result = await db.execute(
            select(UserMemory).where(
                and_(UserMemory.id == memory_id, UserMemory.user_id == user_id)
            )
        )
        memory = result.scalar_one_or_none()
        if not memory:
            return False

        await db.delete(memory)
        await db.commit()
        return True

    async def clear_all_memories(
        self,
        user_id: uuid.UUID,
        db: AsyncSession,
    ) -> int:
        """Hard delete ALL memories for a user. Returns count deleted."""
        result = await db.execute(
            select(UserMemory).where(UserMemory.user_id == user_id)
        )
        memories = result.scalars().all()
        count = len(memories)

        await db.execute(
            delete(UserMemory).where(UserMemory.user_id == user_id)
        )
        await db.commit()
        logger.info(f"Cleared {count} memories for user {user_id}")
        return count


# Singleton instance
memory_service = MemoryService()
