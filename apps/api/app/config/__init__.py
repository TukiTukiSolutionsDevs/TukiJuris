"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    # App
    app_name: str = "TukiJuris"
    app_env: str = "development"
    app_debug: bool = True
    api_port: int = 8000
    app_base_url: str = "https://tukijuris.net.pe"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/agente_derecho"
    database_url_sync: str = "postgresql://postgres:postgres@db:5432/agente_derecho"

    # Redis
    redis_url: str = "redis://redis:6379/0"
    redis_key_prefix: str = "tukijuris:"  # Namespace prefix for all Redis keys

    # Auth
    jwt_secret: str = "dev-only-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15  # 15 min default — override with ACCESS_TOKEN_EXPIRE_MINUTES env var

    # Encryption — BYOK
    # Dedicated Fernet key for encrypting BYOK LLM keys at rest.
    # Decoupled from JWT_SECRET so JWT rotation does NOT corrupt saved BYOK rows.
    # Must be a valid Fernet key (44-char url-safe base64 of 32 bytes). Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # Required in production (APP_DEBUG=false). Dev falls back to JWT_SECRET-derived key.
    byok_encryption_key: str | None = None

    # LLM
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    deepseek_api_key: str = ""
    groq_api_key: str = ""
    xai_api_key: str = ""
    openrouter_api_key: str = ""
    default_llm_provider: str = "google"
    default_llm_model: str = "gemini/gemini-2.5-flash"

    # Free Tier — platform-provided models for users without BYOK keys
    free_tier_enabled: bool = True
    free_tier_model: str = "gemini/gemini-2.5-flash"
    free_tier_fallback_models: list[str] = [
        "groq/llama-3.3-70b-versatile",
        "openrouter/z-ai/glm-4.5-air:free",
    ]
    free_tier_daily_limit: int = 10

    # Embeddings
    embedding_model: str = "text-embedding-004"          # Google model (primary)
    embedding_dimensions: int = 768                       # Google 768-dim; OpenAI 1536-dim
    embedding_provider: str = "google"                    # google | openai

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "https://tukijuris.net.pe", "https://www.tukijuris.net.pe"]
    frontend_url: str = "http://localhost:3000"
    cors_allow_credentials: bool = True
    cors_max_age: int = 600  # Cache preflight responses for 10 minutes

    # Security
    password_min_length: int = 8
    max_login_attempts: int = 5   # per IP per 15-minute window
    session_timeout_minutes: int = 60

    # OAuth2 — Google
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_redirect_uri: str = "http://localhost:3000/auth/callback/google"

    # OAuth2 — Microsoft
    microsoft_oauth_client_id: str = ""
    microsoft_oauth_client_secret: str = ""
    microsoft_oauth_redirect_uri: str = "http://localhost:3000/auth/callback/microsoft"
    microsoft_oauth_tenant_id: str = "common"  # "common" for multi-tenant

    # Reranking
    reranking_enabled: bool = True
    reranking_model: str = "gemini/gemini-2.0-flash"  # fast + cheap for scoring
    reranking_candidates: int = 16                     # over-retrieve count
    reranking_top_k: int = 6                           # final results after reranking
    reranking_timeout_seconds: float = 5.0

    # Payment — MercadoPago
    mp_access_token: str = ""            # TEST-xxx or APP_USR-xxx
    mp_public_key: str = ""              # TEST-xxx or APP_USR-xxx
    mp_webhook_secret: str = ""          # for signature verification

    # Payment — Culqi
    culqi_public_key: str = ""           # pk_test_xxx or pk_live_xxx
    culqi_secret_key: str = ""           # sk_test_xxx or sk_live_xxx
    culqi_webhook_secret: str = ""       # for webhook signature verification

    # Payment — General
    payment_portal_return_url: str = "http://localhost:3000/billing"

    # Monitoring
    sentry_dsn: str = ""
    app_version: str = "1.0.0-beta"
    log_level: str = "INFO"
    log_format: str = "json"  # json or text

    # Email
    email_provider: str = "console"       # resend | smtp | console (dev)
    resend_api_key: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "TukiJuris <noreply@tukijuris.net.pe>"
    email_enabled: bool = False           # Set True when provider is configured

    # Feature flags
    # BETA_MODE=True unlocks all features for all users EXCEPT:
    #   (a) free tier stays capped at 10 msg/day
    #   (b) byok_enabled stays restricted to pro/studio
    # Default True for dev/staging. MUST be explicit in production (startup fail-fast enforces this).
    beta_mode: bool = True

    # Trials feature flag — default False until staging validates end-to-end flow.
    # Set TRIALS_ENABLED=true in staging/production to enable trial creation and scheduler ticks.
    trials_enabled: bool = False

    # Scheduler — set False on secondary API containers so only one instance schedules jobs.
    # See deploy runbook: docs/scheduler-runbook.md
    scheduler_enabled: bool = True

    # Internal tick token — shared secret for POST /internal/trials/tick.
    # Must be a long random string in production. Dev default is intentionally weak.
    internal_tick_token: str = "dev-internal-tick-token"

    # Cache
    cache_enabled: bool = True
    cache_default_ttl: int = 300          # 5 minutes (general purpose)
    cache_rag_ttl: int = 600              # 10 minutes (legal content rarely changes)
    cache_stats_ttl: int = 60            # 1 minute (more dynamic counters)

    # Cookies
    cookie_domain: str = ""  # e.g. ".tukijuris.net.pe" for cross-subdomain; empty = host-only (localhost)

    # Performance
    gzip_enabled: bool = True
    gzip_minimum_size: int = 1000        # bytes — skip compressing small responses
    db_pool_size: int = 20
    db_max_overflow: int = 10

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

# Startup validation: BYOK_ENCRYPTION_KEY is mandatory in production.
# Dev/test environments use APP_DEBUG=true and fall back to JWT_SECRET-derived key.
if not (settings.byok_encryption_key or "").strip() and not settings.app_debug:
    raise RuntimeError(
        "BYOK_ENCRYPTION_KEY must be set in production (APP_DEBUG=false). "
        "An empty or whitespace-only value is not accepted. "
        "Generate with: python -c 'from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())'"
    )
