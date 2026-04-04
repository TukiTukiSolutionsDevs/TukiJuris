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


# Available models configuration
AVAILABLE_MODELS = [
    {
        "id": "gpt-4o-mini",
        "provider": "openai",
        "name": "GPT-4o Mini",
        "description": "Rápido y económico. Bueno para consultas simples.",
        "tier": "free",
        "cost_per_1k_tokens": 0.00015,
    },
    {
        "id": "gpt-4o",
        "provider": "openai",
        "name": "GPT-4o",
        "description": "Modelo avanzado. Mejor análisis y razonamiento legal.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.005,
    },
    {
        "id": "claude-sonnet-4-20250514",
        "provider": "anthropic",
        "name": "Claude Sonnet 4",
        "description": "Excelente para análisis legal detallado y largo.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.003,
    },
    {
        "id": "claude-3-5-haiku-20241022",
        "provider": "anthropic",
        "name": "Claude 3.5 Haiku",
        "description": "Rápido y preciso. Buena relación calidad-precio.",
        "tier": "free",
        "cost_per_1k_tokens": 0.0008,
    },
    {
        "id": "gemini/gemini-2.0-flash",
        "provider": "google",
        "name": "Gemini 2.0 Flash",
        "description": "Rápido, potente y gratuito. Excelente para consultas legales.",
        "tier": "free",
        "cost_per_1k_tokens": 0.0,
    },
    {
        "id": "gemini/gemini-1.5-pro",
        "provider": "google",
        "name": "Gemini 1.5 Pro",
        "description": "Gran contexto. Ideal para documentos largos.",
        "tier": "pro",
        "cost_per_1k_tokens": 0.00125,
    },
]


class LLMService:
    """Unified interface for all LLM providers via LiteLLM."""

    def __init__(self):
        self._configure_api_keys()

    def _configure_api_keys(self):
        """Set platform-level API keys from settings (used for internal operations)."""
        if settings.openai_api_key:
            litellm.openai_key = settings.openai_api_key
        if settings.anthropic_api_key:
            litellm.anthropic_key = settings.anthropic_api_key
        if settings.google_api_key:
            litellm.google_key = settings.google_api_key

    def _get_platform_key(self, model: str) -> str | None:
        """
        Return the platform's own API key for a given model.

        Used ONLY for internal operations (classification, reranking, memory extraction)
        that are not user-facing. User-facing responses must use the user's own key.
        """
        model_lower = (model or "").lower()
        if any(x in model_lower for x in ["gpt", "o1", "o3", "openai"]):
            return settings.openai_api_key or None
        elif any(x in model_lower for x in ["claude", "anthropic", "sonnet", "haiku", "opus"]):
            return settings.anthropic_api_key or None
        elif any(x in model_lower for x in ["gemini", "google", "palm"]):
            return settings.google_api_key or None
        return None

    async def completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
        stream: bool = False,
        user_api_key: str | None = None,  # BYOK: user's own provider key
    ) -> dict:
        """
        Send a completion request to any supported LLM.

        Args:
            messages: Chat messages in OpenAI format [{"role": "...", "content": "..."}]
            model: Model ID (e.g., "gpt-4o-mini", "claude-sonnet-4-20250514")
            temperature: Sampling temperature (low for legal accuracy)
            max_tokens: Maximum response tokens
            stream: Whether to stream the response
            user_api_key: BYOK — the user's own provider API key.
                If None, falls back to the platform's key (for internal operations only).

        Returns:
            dict with 'content', 'model', 'tokens_used'
        """
        model = model or settings.default_llm_model

        # BYOK key resolution:
        # 1. Use user's key if provided (user-facing responses)
        # 2. Fall back to platform key (internal ops: classification, reranking, etc.)
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

            response = await litellm.acompletion(**call_kwargs)

            if stream:
                return {"stream": response, "model": model}

            return {
                "content": response.choices[0].message.content,
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
                return {
                    "content": response.choices[0].message.content,
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
