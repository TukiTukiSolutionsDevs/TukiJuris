"""
LLM Adapter Layer — Model-agnostic interface using LiteLLM.

Supports OpenAI, Anthropic, Google, and local models via Ollama.

BYOK Model:
  - User-facing queries: always use the user's own provider API key.
  - Internal operations (classification, reranking, secondary enrichment):
    fall back to the platform's configured keys.
  - The `user_api_key` parameter in `completion()` drives this distinction.
"""

import logging

import litellm

from app.config import settings

logger = logging.getLogger(__name__)

# Configure LiteLLM
litellm.set_verbose = settings.app_debug
litellm.drop_params = True  # Allow models not yet in LiteLLM's catalog (e.g. gemini-3.1-pro-preview)


# ─── Available models — April 2026 catalog ─────────────────────────────────
# ALL model IDs use LiteLLM prefix format so routing works out of the box.
# Verified against official provider docs: 2026-04-08
AVAILABLE_MODELS = [
    # --- Free / Ultra-cheap tier ---
    {
        "id": "gemini/gemini-2.5-flash",
        "provider": "google",
        "name": "Gemini 2.5 Flash",
        "description": "Rápido y gratuito. Último Flash estable de Google.",
        "tier": "free",
        "cost_per_1k_tokens": 0.0,
    },
    {
        "id": "deepseek/deepseek-chat",
        "provider": "deepseek",
        "name": "DeepSeek V3.2",
        "description": "Ultra económico ($0.28/M). Excelente razonamiento.",
        "tier": "free",
        "cost_per_1k_tokens": 0.00028,
    },
    {
        "id": "groq/llama-3.1-8b-instant",
        "provider": "groq",
        "name": "Llama 3.1 8B — Groq",
        "description": "Ultra rápido (560 t/s). Respuestas instantáneas.",
        "tier": "free",
        "cost_per_1k_tokens": 0.00005,
    },
    {
        "id": "groq/llama-3.3-70b-versatile",
        "provider": "groq",
        "name": "Llama 3.3 70B — Groq",
        "description": "Rápido y versátil (280 t/s). Buena calidad.",
        "tier": "free",
        "cost_per_1k_tokens": 0.00059,
    },
    # --- Standard tier ---
    {
        "id": "openai/gpt-5.4-nano",
        "provider": "openai",
        "name": "GPT-5.4 Nano",
        "description": "El más barato de OpenAI ($0.20/M). Tareas simples.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.0002,
    },
    {
        "id": "anthropic/claude-haiku-4-5",
        "provider": "anthropic",
        "name": "Claude Haiku 4.5",
        "description": "El más rápido de Anthropic ($1/M). Near-frontier.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.001,
    },
    {
        "id": "groq/qwen/qwen3-32b",
        "provider": "groq",
        "name": "Qwen3 32B — Groq",
        "description": "Modelo potente en Groq (400 t/s). Buen razonamiento.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.00029,
    },
    {
        "id": "deepseek/deepseek-reasoner",
        "provider": "deepseek",
        "name": "DeepSeek Reasoner",
        "description": "Razonamiento profundo (thinking mode). Análisis complejo.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.00028,
    },
    {
        "id": "gemini/gemini-2.5-pro",
        "provider": "google",
        "name": "Gemini 2.5 Pro",
        "description": "Gran contexto (1M tokens). Ideal para documentos largos.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.00125,
    },
    # --- Pro tier ---
    {
        "id": "openai/gpt-5.4-mini",
        "provider": "openai",
        "name": "GPT-5.4 Mini",
        "description": "Mejor relación calidad/precio de OpenAI ($0.75/M). 400K ctx.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.00075,
    },
    {
        "id": "anthropic/claude-sonnet-4-6",
        "provider": "anthropic",
        "name": "Claude Sonnet 4.6",
        "description": "Velocidad + inteligencia ($3/M). 1M contexto.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.003,
    },
    {
        "id": "gemini/gemini-3.1-flash-lite-preview",
        "provider": "google",
        "name": "Gemini 3.1 Flash-Lite",
        "description": "Alta eficiencia ($0.25/M). Ideal para tareas de alto volumen.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.00025,
    },
    {
        "id": "gemini/gemini-3.1-pro-preview",
        "provider": "google",
        "name": "Gemini 3.1 Pro",
        "description": "Flagship de Google ($2/M). Deep Think, 1M contexto, agentic.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.002,
    },
    {
        "id": "groq/openai/gpt-oss-120b",
        "provider": "groq",
        "name": "GPT-OSS 120B — Groq",
        "description": "OpenAI open-weight en Groq (500 t/s). Potente.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.00015,
    },
    {
        "id": "openai/gpt-5.4",
        "provider": "openai",
        "name": "GPT-5.4",
        "description": "Flagship OpenAI ($2.50/M). 1M contexto, 128K output.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.0025,
    },
    {
        "id": "anthropic/claude-opus-4-6",
        "provider": "anthropic",
        "name": "Claude Opus 4.6",
        "description": "El más inteligente de Anthropic ($5/M). Agentes y coding.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.005,
    },
    # --- xAI Grok (prefix: xai/) ─────────────────────────────
    {
        "id": "xai/grok-3-mini-fast-latest",
        "provider": "xai",
        "name": "Grok 3 Mini Fast",
        "description": "Ultra económico ($0.30/M). 131K ctx. Rápido y eficiente.",
        "tier": "free",
        "cost_per_1k_tokens": 0.0003,
    },
    {
        "id": "xai/grok-3-fast-latest",
        "provider": "xai",
        "name": "Grok 3 Fast",
        "description": "Rápido con razonamiento ($3/M). 131K ctx.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.003,
    },
    {
        "id": "xai/grok-4-1-fast-reasoning",
        "provider": "xai",
        "name": "Grok 4.1 Fast",
        "description": "Mejor valor xAI ($0.20/M). 2M ctx. Reasoning + tool-calling.",
        "tier": "standard",
        "cost_per_1k_tokens": 0.0002,
    },
    {
        "id": "xai/grok-4-0709",
        "provider": "xai",
        "name": "Grok 4",
        "description": "Flagship xAI ($3/M). 256K ctx. Reasoning profundo.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.003,
    },
    {
        "id": "xai/grok-4.20-reasoning-latest",
        "provider": "xai",
        "name": "Grok 4.20 Reasoning",
        "description": "Lo último de xAI ($2/M). 2M ctx. Menor alucinación del mercado.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.002,
    },
]

# ─── Model tier classification — controls access per plan ────────────────
# Tier 1: Economic ($0.001-0.01/query) — available on all plans
# Tier 2: Standard ($0.01-0.03/query) — limited on free, unlimited on paid
# Tier 3: Premium ($0.03-0.07/query) — only on paid plans (limited)
# Tier 4: Ultra ($0.08-0.12/query) — only on enterprise
MODEL_TIERS: dict[str, int] = {
    # Tier 1 — Economic
    "gemini/gemini-2.5-flash": 1,
    "groq/llama-3.1-8b-instant": 1,
    "groq/llama-3.3-70b-versatile": 1,
    "deepseek/deepseek-chat": 1,
    "xai/grok-4-1-fast-reasoning": 1,
    "openai/gpt-5.4-nano": 1,
    "xai/grok-3-mini-fast-latest": 1,
    # Tier 2 — Standard (alto razonamiento)
    "anthropic/claude-haiku-4-5": 2,
    "openai/gpt-5.4-mini": 2,
    "deepseek/deepseek-reasoner": 2,
    "gemini/gemini-2.5-pro": 2,
    "groq/qwen/qwen3-32b": 2,
    "gemini/gemini-3.1-flash-lite-preview": 2,
    # Tier 3 — Premium
    "anthropic/claude-sonnet-4-6": 3,
    "openai/gpt-5.4": 3,
    "gemini/gemini-3.1-pro-preview": 3,
    "xai/grok-4.20-reasoning-latest": 3,
    "xai/grok-4-0709": 3,
    "groq/openai/gpt-oss-120b": 3,
    "xai/grok-3-fast-latest": 3,
    # Tier 4 — Ultra
    "anthropic/claude-opus-4-6": 4,
}


def get_model_tier(model_id: str) -> int:
    """Return the tier (1-4) for a model ID. Defaults to 2 if unknown."""
    return MODEL_TIERS.get(model_id, 2)


# ─── Free tier models — available without BYOK keys ──────────────────────
# These are provided by the platform at zero cost to the user.
# Order matters: first model is the primary, rest are fallbacks.
FREE_TIER_MODELS = [
    {
        "id": "gemini/gemini-2.5-flash",
        "provider": "google",
        "name": "Gemini 2.5 Flash",
        "description": "Modelo gratuito incluido. Rápido y capaz.",
        "tier": "free",
        "cost_per_1k_tokens": 0.0,
        "is_platform_provided": True,
    },
    {
        "id": "groq/llama-3.3-70b-versatile",
        "provider": "groq",
        "name": "Llama 3.3 70B — Groq",
        "description": "Modelo gratuito incluido. 280 t/s, versátil.",
        "tier": "free",
        "cost_per_1k_tokens": 0.0,
        "is_platform_provided": True,
    },
    {
        "id": "groq/llama-3.1-8b-instant",
        "provider": "groq",
        "name": "Llama 3.1 8B — Groq",
        "description": "Modelo gratuito incluido. Ultra rápido.",
        "tier": "free",
        "cost_per_1k_tokens": 0.0,
        "is_platform_provided": True,
    },
]


class LLMService:
    """Unified interface for all LLM providers via LiteLLM."""

    def __init__(self):
        self._configure_api_keys()

    def _configure_api_keys(self):
        """Set platform-level API keys from settings (used for internal operations)."""
        import os

        if settings.openai_api_key:
            litellm.openai_key = settings.openai_api_key
        if settings.anthropic_api_key:
            litellm.anthropic_key = settings.anthropic_api_key
        if settings.xai_api_key:
            os.environ["XAI_API_KEY"] = settings.xai_api_key
        if settings.openrouter_api_key:
            os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key

    def _provider_from_model(self, model: str) -> str | None:
        """Map a model string to its provider name for BYOK key resolution.

        Checks LiteLLM-style prefix first (e.g. ``openai/gpt-5.4``),
        then falls back to keyword matching for bare model names.
        """
        model_lower = (model or "").lower()

        # ── 1. Explicit LiteLLM prefix (highest priority) ──────────────
        if model_lower.startswith("openai/"):
            return "openai"
        if model_lower.startswith("anthropic/"):
            return "anthropic"
        if model_lower.startswith("gemini/"):
            return "google"
        if model_lower.startswith("deepseek/"):
            return "deepseek"
        if model_lower.startswith("groq/"):
            return "groq"
        if model_lower.startswith("xai/"):
            return "xai"
        if model_lower.startswith("openrouter/"):
            return "openrouter"

        # ── 2. Keyword fallback for bare model names ───────────────────
        if any(x in model_lower for x in ["gpt", "o1-", "o3-", "o4-"]):
            return "openai"
        if any(x in model_lower for x in ["claude", "sonnet", "haiku", "opus"]):
            return "anthropic"
        if any(x in model_lower for x in ["gemini", "palm"]):
            return "google"
        if "deepseek" in model_lower:
            return "deepseek"
        if any(x in model_lower for x in ["llama", "qwen", "mixtral"]):
            return "groq"
        return None

    def _get_platform_key(self, model: str) -> str | None:
        """
        Return ONLY the platform-owned API key for a model.

        CRITICAL SECURITY RULE:
        Platform operations and free tier resolution MUST NEVER reuse keys
        uploaded by other users. Cross-tenant key reuse would mean one user's
        provider account pays for another user's traffic.

        Therefore this method reads exclusively from server-side settings/.env.
        """
        provider = self._provider_from_model(model)
        env_keys = {
            "openai": settings.openai_api_key,
            "anthropic": settings.anthropic_api_key,
            "google": settings.google_api_key,
            "deepseek": settings.deepseek_api_key,
            "groq": settings.groq_api_key,
            "xai": settings.xai_api_key,
            "openrouter": settings.openrouter_api_key,
        }
        env_key = env_keys.get(provider or "", "") or ""
        if env_key:
            return env_key

        return None

    async def completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
        user_api_key: str | None = None,  # BYOK: user's own provider key
        reasoning_effort: str | None = None,  # "low", "medium", "high"
    ) -> dict:
        """
        Send a completion request to any supported LLM.

        Args:
            messages: Chat messages in OpenAI format
            model: Model ID with LiteLLM prefix
            temperature: Sampling temperature (low for legal accuracy)
            max_tokens: Maximum response tokens
            stream: Whether to stream the response
            user_api_key: BYOK — the user's own provider API key.
            reasoning_effort: "low", "medium", "high" — controls thinking depth.
                LiteLLM maps this to each provider's native parameter:
                - Anthropic: output_config.effort / thinking.budget_tokens
                - Gemini: thinking budget
                - OpenAI: reasoning_effort
                - xAI: selects reasoning vs non-reasoning variant

        Returns:
            dict with 'content', 'model', 'tokens_used'
        """
        model = model or settings.default_llm_model

        # BYOK key resolution
        api_key = user_api_key or self._get_platform_key(model)

        try:
            call_kwargs: dict = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream,
            )
            if api_key:
                call_kwargs["api_key"] = api_key

            # Pass reasoning_effort if specified — LiteLLM handles provider mapping
            if reasoning_effort and reasoning_effort in ("low", "medium", "high"):
                call_kwargs["reasoning_effort"] = reasoning_effort

            response = await litellm.acompletion(**call_kwargs)

            if stream:
                return {"stream": response, "model": model}

            # Extract content — thinking models may return None in .content
            content = response.choices[0].message.content
            if content is None:
                # Some thinking models put all output in reasoning/thinking blocks
                # Try to extract from thinking_content or reasoning_content
                msg = response.choices[0].message
                content = (
                    getattr(msg, "reasoning_content", None)
                    or getattr(msg, "thinking_content", None)
                    or getattr(msg, "thinking", None)
                    or ""
                )
                if content:
                    logger.info(f"Extracted content from thinking block ({len(content)} chars)")
                else:
                    logger.warning(f"Model {model} returned None content with no thinking fallback")

            return {
                "content": content or "",
                "model": model,
                "tokens_used": response.usage.total_tokens if response.usage else None,
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
            }

        except Exception as e:
            logger.error(f"LLM completion error with model {model}: {e}")
            # Try fallback model (only for internal platform calls — no user_api_key)
            if user_api_key:
                # Don't silently swap the user's model to a platform model
                raise
            fallback = settings.default_llm_model
            logger.info(f"Attempting fallback to {fallback}")
            try:
                fallback_kwargs: dict = dict(
                    model=fallback,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                fallback_key = self._get_platform_key(fallback)
                if fallback_key:
                    fallback_kwargs["api_key"] = fallback_key
                response = await litellm.acompletion(**fallback_kwargs)
                fallback_content = response.choices[0].message.content or ""
                return {
                    "content": fallback_content,
                    "model": fallback,
                    "tokens_used": response.usage.total_tokens if response.usage else None,
                    "fallback": True,
                }
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise

    async def embed(self, text: str | list[str]) -> list[list[float]]:
        """Generate embeddings for text using the configured embedding model."""
        if isinstance(text, str):
            text = [text]

        response = await litellm.aembedding(
            model=settings.embedding_model,
            input=text,
        )

        return [item["embedding"] for item in response.data]

    def resolve_free_tier(self, requested_model: str | None = None) -> tuple[str, str] | None:
        """Resolve a model + API key for free tier usage.

        Tries the requested model first (if it's a free tier model),
        then falls back through FREE_TIER_MODELS in order.

        Returns:
            (model_id, api_key) tuple, or None if no free tier key is available.
        """
        # Build ordered candidate list: requested model first, then fallbacks
        candidates = []
        if requested_model:
            free_ids = {m["id"] for m in FREE_TIER_MODELS}
            if requested_model in free_ids:
                candidates.append(requested_model)
        candidates.extend(m["id"] for m in FREE_TIER_MODELS if m["id"] not in candidates)

        for model_id in candidates:
            key = self._get_platform_key(model_id)
            if key:
                logger.info(f"Free tier resolved: {model_id}")
                return (model_id, key)

        logger.warning("No free tier key available — all platform keys are empty")
        return None

    def get_free_tier_models(self) -> list[dict]:
        """Return free tier models that have a working platform key."""
        if not settings.free_tier_enabled:
            return []
        result = []
        for model in FREE_TIER_MODELS:
            key = self._get_platform_key(model["id"])
            if key:
                result.append({**model, "available": True})
        return result

    def get_available_models(self) -> list[dict]:
        """
        Return list of available models with their metadata.

        BYOK: All models are listed as available — availability depends on whether
        the user has configured their own API key for that provider, not on
        platform-level keys. The 'available' flag is always True since users
        bring their own keys.
        """
        return [{**model, "available": True} for model in AVAILABLE_MODELS]


# Singleton instance
llm_service = LLMService()
