"""
Base Agent — Foundation for all specialized legal domain agents.

Each domain agent inherits from this and provides its own:
- System prompt with domain-specific legal knowledge
- RAG filter criteria (which documents to search)
- Citation formatting rules
"""

import logging
from abc import ABC, abstractmethod

from app.services.llm_adapter import llm_service

logger = logging.getLogger(__name__)

# Base legal system prompt that ALL agents share
BASE_LEGAL_SYSTEM_PROMPT = """Eres un asistente jurídico especializado en el derecho peruano. 
Tu función es orientar al usuario sobre temas legales basándote EXCLUSIVAMENTE en la normativa 
peruana vigente y la jurisprudencia relevante.

REGLAS FUNDAMENTALES:
1. SOLO responde basándote en normativa peruana. Si no conoces la norma específica, dilo.
2. SIEMPRE cita las fuentes: número de ley, decreto, artículo específico.
3. NUNCA inventes normas, artículos o jurisprudencia que no existan.
4. Si la consulta requiere asesoría legal personalizada, indica que el usuario debe consultar 
   con un abogado.
5. Responde en español, usando terminología jurídica peruana.
6. Si la consulta involucra otra rama del derecho, indícalo al usuario.

FORMATO DE CITACIÓN:
- Leyes: "Art. [número], [Nombre de la norma] ([Número de ley/decreto])"
- Jurisprudencia: "Exp. N° [número]-[año]-[tipo], [Tribunal], [fecha]"
- Constitución: "Art. [número] de la Constitución Política del Perú de 1993"

DISCLAIMER: Siempre incluye al final: "Esta información es de carácter orientativo y no 
constituye asesoría legal. Para casos específicos, consulte con un abogado colegiado."
"""


class BaseLegalAgent(ABC):
    """Abstract base class for specialized legal domain agents."""

    def __init__(self):
        self.name = self.get_agent_name()
        self.legal_area = self.get_legal_area()
        self.system_prompt = self._build_system_prompt()

    @abstractmethod
    def get_agent_name(self) -> str:
        """Human-readable name of this agent."""
        ...

    @abstractmethod
    def get_legal_area(self) -> str:
        """Legal area identifier (e.g., 'civil', 'penal', 'laboral')."""
        ...

    @abstractmethod
    def get_domain_prompt(self) -> str:
        """Domain-specific system prompt additions."""
        ...

    @abstractmethod
    def get_rag_filter(self) -> dict:
        """Metadata filter for RAG retrieval (limits to relevant documents)."""
        ...

    def _build_system_prompt(self) -> str:
        """Combine base + domain-specific prompts."""
        return f"{BASE_LEGAL_SYSTEM_PROMPT}\n\n{self.get_domain_prompt()}"

    async def process(
        self,
        query: str,
        context: str = "",
        model: str | None = None,
        conversation_history: list[dict] | None = None,
        user_api_key: str | None = None,
        reasoning_effort: str | None = None,
    ) -> dict:
        """
        Process a legal query through this specialized agent.

        Args:
            query: The user's legal question
            context: RAG-retrieved context (relevant legal documents)
            model: LLM model to use
            conversation_history: Prior messages for multi-turn context
            user_api_key: BYOK — the user's own LLM provider key.
            reasoning_effort: "low", "medium", "high" — thinking depth.

        Returns:
            dict with response, citations, and metadata
        """
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]

        if context:
            messages.append({
                "role": "system",
                "content": f"CONTEXTO NORMATIVO RELEVANTE:\n{context}",
            })

        # Inject conversation history (last 20 messages to avoid context overflow)
        if conversation_history:
            recent = conversation_history[-20:]
            for msg in recent:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": query})

        logger.info(f"Agent [{self.name}] processing query: {query[:100]}...")

        result = await llm_service.completion(
            messages=messages,
            model=model,
            user_api_key=user_api_key,
            reasoning_effort=reasoning_effort,
        )

        return {
            "response": result["content"],
            "agent_used": self.name,
            "legal_area": self.legal_area,
            "model_used": result["model"],
            "tokens_used": result.get("tokens_used"),
            "citations": self._extract_citations(result["content"]),
        }

    def _extract_citations(self, text: str) -> list[dict]:
        """Extract legal citations from the response text using regex patterns."""
        import re

        citations = []
        seen = set()

        patterns = [
            # "Art. 196 del Código Penal" / "Art. 38, DS 003-97-TR" / "Artículo 2"
            (
                r"Art(?:ículo|\.)\s*(\d+[\w\-]*)"
                r"(?:[,\s]+(?:del?\s+)?([A-ZÁ-Ú][\w\s\-°ºª]+?)(?=[\.\,\;\)\n]|$))?",
                "article",
            ),
            # "Ley N° 27735" / "Ley 29783" / "Ley General de Sociedades"
            (r"Ley\s+(?:N[°º]?\s*)?(\d{4,5}(?:[\-\w]*)?)", "law"),
            # "DS 003-97-TR" / "Decreto Supremo N° 179-2004-EF"
            (
                r"(?:DS|Decreto\s+Supremo)\s*(?:N[°º]?\s*)?(\d{1,3}[\-]\d{2,4}[\-]\w{1,4})",
                "decree",
            ),
            # "DL 728" / "Decreto Legislativo 635"
            (r"(?:DL|Decreto\s+Legislativo)\s*(?:N[°º]?\s*)?(\d{2,5})", "legislative_decree"),
            # "Exp. N° 0006-2006-PC/TC"
            (r"Exp\.?\s*(?:N[°º]?\s*)?(\d{2,5}[\-]\d{4}[\-][\w/]+)", "case"),
            # "Constitución" reference
            (r"Constituci[oó]n\s+(?:Pol[ií]tica\s+)?(?:del\s+Per[uú])?", "constitution"),
        ]

        for pattern, citation_type in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                full_match = match.group(0).strip().rstrip(".,;)")
                if full_match not in seen and len(full_match) > 3:
                    seen.add(full_match)
                    citation = {
                        "type": citation_type,
                        "text": full_match,
                        "reference": match.group(1) if match.lastindex else full_match,
                    }
                    citations.append(citation)

        return citations
