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

    Supports LiteLLM-style prefixes (e.g. 'gemini/gemini-2.0-flash',
    'groq/llama-3.1-8b-instant', 'deepseek/deepseek-chat') as well as plain names.
    """
    model_lower = model.lower() if model else ""

    if any(x in model_lower for x in ["gpt", "o1", "o3", "openai"]):
        return "openai"
    elif any(x in model_lower for x in ["claude", "anthropic", "sonnet", "haiku", "opus"]):
        return "anthropic"
    elif any(x in model_lower for x in ["gemini", "google", "palm"]):
        return "google"
    elif any(x in model_lower for x in ["deepseek"]):
        return "deepseek"
    elif any(x in model_lower for x in ["groq", "llama-3", "llama"]) and "groq" in model_lower:
        return "groq"
    elif any(x in model_lower for x in ["llama"]) and "groq" not in model_lower:
        return "meta"
    elif any(x in model_lower for x in ["mistral", "mixtral"]):
        return "mistral"
    elif any(x in model_lower for x in ["moonshot", "kimi"]):
        return "moonshot"
    elif any(x in model_lower for x in ["qwen", "dashscope"]):
        return "qwen"
    elif any(x in model_lower for x in ["zhipu", "glm"]):
        return "zhipu"
    elif any(x in model_lower for x in ["minimax"]):
        return "minimax"
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
            "name": "Google AI",
            "models": ["gemini-2.0-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
            "key_prefix": "AI",
            "docs_url": "https://aistudio.google.com/apikey",
            "setup_guide": "Entrá a aistudio.google.com/apikey y generá tu clave. 100% gratis para empezar.",
            "pricing_note": "Gemini Flash es GRATIS. Pro desde $1.25/millón tokens.",
        },
        {
            "id": "groq",
            "name": "Groq",
            "models": ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "qwen-qwq-32b", "moonshotai/kimi-k2-instruct"],
            "key_prefix": "gsk_",
            "docs_url": "https://console.groq.com/keys",
            "setup_guide": "Registrate gratis en console.groq.com y generá tu API key. Tiene tier gratuito.",
            "pricing_note": "Desde $0.05/millón tokens. Inferencia ultra rápida en hardware dedicado.",
        },
        {
            "id": "deepseek",
            "name": "DeepSeek",
            "models": ["deepseek-chat", "deepseek-reasoner"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.deepseek.com/api_keys",
            "setup_guide": "Registrate en platform.deepseek.com, recargá desde $2 USD y creá tu API key.",
            "pricing_note": "Desde $0.28/millón de tokens. Uno de los más baratos del mercado.",
        },
        {
            "id": "openai",
            "name": "OpenAI",
            "models": ["gpt-4o", "gpt-4o-mini", "o1-mini", "o3-mini"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.openai.com/api-keys",
            "setup_guide": "Registrate en platform.openai.com, cargá créditos y creá tu API key.",
            "pricing_note": "Desde $0.15/millón tokens (GPT-4o-mini). Pay-as-you-go.",
        },
        {
            "id": "anthropic",
            "name": "Anthropic",
            "models": ["claude-sonnet-4-20250514", "claude-3-5-haiku-20241022"],
            "key_prefix": "sk-ant-",
            "docs_url": "https://console.anthropic.com/settings/keys",
            "setup_guide": "Registrate en console.anthropic.com. Obtené créditos iniciales gratis.",
            "pricing_note": "Desde $0.25/millón tokens (Haiku). Pay-as-you-go.",
        },
        {
            "id": "moonshot",
            "name": "Moonshot AI (Kimi)",
            "models": ["moonshot-v1-8k", "moonshot-v1-32k"],
            "key_prefix": "sk-",
            "docs_url": "https://platform.moonshot.cn/console/api-keys",
            "setup_guide": "Registrate en platform.moonshot.cn (disponible en inglés). Creá tu API key.",
            "pricing_note": "Desde $1.00/millón tokens. Modelo chino con buen rendimiento en español.",
        },
        {
            "id": "qwen",
            "name": "Qwen (Alibaba)",
            "models": ["qwen-turbo", "qwen-plus", "qwen-max"],
            "key_prefix": "sk-",
            "docs_url": "https://dashscope.console.aliyun.com/apiKey",
            "setup_guide": "Registrate en dashscope.aliyun.com. Obtené tu API key de DashScope.",
            "pricing_note": "Desde $0.35/millón tokens. Modelos de Alibaba Cloud, open source.",
        },
        {
            "id": "zhipu",
            "name": "Zhipu AI (GLM)",
            "models": ["glm-4-plus", "glm-4-flash"],
            "key_prefix": "",
            "docs_url": "https://open.bigmodel.cn/usercenter/apikeys",
            "setup_guide": "Registrate en open.bigmodel.cn. Generá tu API key desde el panel.",
            "pricing_note": "Desde $0.70/millón tokens. GLM-4, fuerte en razonamiento.",
        },
    ]
