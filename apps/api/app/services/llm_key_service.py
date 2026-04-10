"""
LLM Key Service — BYOK (Bring Your Own Key) management.

Users store their own API keys for LLM providers here.
TukiJuris does NOT resell AI model usage — platform only provides access and tooling.

Keys are encrypted at rest with Fernet symmetric encryption, derived from JWT_SECRET.
"""

import base64
import hashlib
import logging

from cryptography.fernet import Fernet
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.llm_key import UserLLMKey

logger = logging.getLogger(__name__)

# Derive a valid Fernet key from JWT_SECRET using SHA-256.
# SHA-256 always produces 32 bytes → base64url-encode → valid 44-char Fernet key.
_key_bytes = hashlib.sha256(settings.jwt_secret.encode()).digest()
_fernet = Fernet(base64.urlsafe_b64encode(_key_bytes))


# ---------------------------------------------------------------------------
# Crypto helpers
# ---------------------------------------------------------------------------


def encrypt_key(api_key: str) -> str:
    """Encrypt an API key with Fernet (AES-128-CBC + HMAC-SHA256)."""
    return _fernet.encrypt(api_key.encode()).decode()


def decrypt_key(encrypted: str) -> str:
    """Decrypt a Fernet-encrypted API key."""
    return _fernet.decrypt(encrypted.encode()).decode()


def make_hint(api_key: str) -> str:
    """
    Create a safe display hint like 'sk-...3kF2'.
    Shows the first 3 chars and last 4 chars — never the full key.
    """
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:3]}...{api_key[-4:]}"


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------


async def get_user_key_for_provider(
    user_id,
    provider: str,
    db: AsyncSession,
) -> str | None:
    """
    Get the user's decrypted API key for a specific provider.

    Returns the most recently added active key, or None if not found.
    """
    result = await db.execute(
        select(UserLLMKey)
        .where(
            UserLLMKey.user_id == user_id,
            UserLLMKey.provider == provider,
            UserLLMKey.is_active == True,  # noqa: E712
        )
        .order_by(UserLLMKey.created_at.desc())
        .limit(1)
    )
    key_row = result.scalar_one_or_none()
    if not key_row:
        return None
    try:
        return decrypt_key(key_row.api_key_encrypted)
    except Exception:
        logger.warning(
            "Failed to decrypt LLM key for user %s provider %s — key may be corrupted",
            user_id,
            provider,
        )
        return None


async def get_user_keys_for_model(
    user_id,
    model: str,
    db: AsyncSession,
) -> str | None:
    """
    Map a model name to its provider, then return the user's decrypted key.

    Used at request time to inject the user's own key into LLM calls.
    Returns None if the model is unknown or the user has no key configured.
    """
    provider = _model_to_provider(model)
    if not provider:
        logger.warning("Could not map model '%s' to a known provider", model)
        return None
    return await get_user_key_for_provider(user_id, provider, db)


# ---------------------------------------------------------------------------
# Model → Provider mapping
# ---------------------------------------------------------------------------


def _model_to_provider(model: str) -> str | None:
    """
    Map a model name/ID to a provider slug.

    Checks LiteLLM-style prefix first (e.g. ``openai/gpt-5.4``,
    ``groq/llama-3.1-8b-instant``), then falls back to keyword matching.
    """
    model_lower = model.lower() if model else ""

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
    if "grok" in model_lower:
        return "xai"
    return None


# ---------------------------------------------------------------------------
# Provider catalogue
# ---------------------------------------------------------------------------


def get_available_providers() -> list[dict]:
    """
    Return the list of LLM providers supported for BYOK.

    Each entry includes:
    - id:           slug used in `provider` column
    - name:         human-readable name
    - models:       model IDs available from this provider
    - key_prefix:   expected prefix of the API key (for UI validation hints)
    - docs_url:     where users can generate their own keys
    - setup_guide:  short instructions for getting a key
    - pricing_note: brief pricing info
    """
    return [
        {
            "id": "google",
            "name": "Google AI (Gemini)",
            "models": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-3.1-flash-lite-preview", "gemini-3.1-pro-preview"],
            "key_prefix": "AI",
            "docs_url": "https://aistudio.google.com/apikey",
            "setup_guide": "Entrá a aistudio.google.com/apikey y generá tu clave. 100% gratis para empezar.",
            "pricing_note": "Gemini Flash es GRATIS. 3.1 Pro: $2/M input, $12/M output.",
        },
        {
            "id": "groq",
            "name": "Groq",
            "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "qwen/qwen3-32b", "openai/gpt-oss-120b"],
            "key_prefix": "gsk_",
            "docs_url": "https://console.groq.com/keys",
            "setup_guide": "Registrate gratis en console.groq.com y generá tu API key. Tiene tier gratuito.",
            "pricing_note": "Desde $0.05/millón tokens. Inferencia ultra rápida (hasta 1000 t/s).",
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "models": ["deepseek-chat", "deepseek-reasoner"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.deepseek.com/api_keys",
            "setup_guide": "Registrate en platform.deepseek.com, recargá desde $2 USD y creá tu API key.",
            "pricing_note": "$0.28/millón tokens (cache hit: $0.028/M). V3.2 con 128K contexto.",
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "models": ["gpt-5.4-nano", "gpt-5.4-mini", "gpt-5.4"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.openai.com/api-keys",
            "setup_guide": "Registrate en platform.openai.com, cargá créditos y creá tu API key.",
            "pricing_note": "Desde $0.20/M (Nano). Flagship GPT-5.4 con 1M contexto.",
        },
        {
            "id": "anthropic",
            "name": "Anthropic (Claude)",
            "models": ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"],
            "key_prefix": "sk-ant-",
            "docs_url": "https://console.anthropic.com/settings/keys",
            "setup_guide": "Registrate en console.anthropic.com. Obtené créditos iniciales gratis.",
            "pricing_note": "Desde $1/M (Haiku 4.5). Opus 4.6: el más inteligente, 1M contexto.",
        },
        {
            "id": "xai",
            "name": "xAI (Grok)",
            "models": ["grok-3-mini-fast-latest", "grok-3-fast-latest", "grok-4-1-fast-reasoning", "grok-4-0709", "grok-4.20-reasoning-latest"],
            "key_prefix": "xai-",
            "docs_url": "https://console.x.ai",
            "setup_guide": "Registrate en console.x.ai, cargá créditos y creá tu API key.",
            "pricing_note": "Desde $0.20/M (Grok 4.1 Fast). Grok 4.20: menor alucinación del mercado, 2M ctx.",
        },
    ]
