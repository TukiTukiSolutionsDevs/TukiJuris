"""
Agente Derecho — FastAPI Application Entry Point.

Peruvian Legal AI Platform with specialized domain agents
coordinated by a LangGraph-powered orchestrator.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from app.api.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from app.api.routes import (
    admin,
    admin_invoices,
    admin_saas,
    analysis,
    rbac_admin,
    analytics,
    api_keys,
    auth,
    billing,
    bookmarks,
    chat,
    conversations,
    documents,
    emails,
    export,
    feedback,
    folders,
    health,
    me_invoices,
    memory,
    upload,
    notifications,
    oauth,
    organizations,
    plans,
    rbac_admin,
    search,
    shared,
    stream,
    tags,
    v1,
)
from app.config import settings
from app.core.monitoring import init_sentry
from app.core.startup_validation import validate_production_config

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.app_debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    # Refuse to start in production with insecure or incomplete config.
    # Centralised in app.core.startup_validation — see tests/test_startup_validation.py
    # for the full set of invariants enforced.
    validate_production_config(settings)

    init_sentry()
    logger.info(f"Starting {settings.app_name} API...")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Default LLM: {settings.default_llm_provider}/{settings.default_llm_model}")
    yield
    logger.info(f"Shutting down {settings.app_name} API...")


app = FastAPI(
    title="TukiJuris API",
    description="""
## TukiJuris — Plataforma Juridica Inteligente

Plataforma juridica inteligente especializada en derecho peruano.
Sistema de agentes especializados por rama del derecho, coordinados por un orquestador LangGraph.

### Autenticacion

Todos los endpoints protegidos aceptan dos metodos de autenticacion:

- **JWT Bearer**: Usa `POST /api/auth/login` para obtener un token, luego incluye
  `Authorization: Bearer <token>` en cada request.
- **API Key**: Crea una clave en `POST /api/keys/`, luego usa el header `X-API-Key: ak_...`
  o `Authorization: Bearer ak_...`. Las API keys tienen scopes que restringen que endpoints pueden llamar.
- **SSO**: Google y Microsoft OAuth2 disponibles en `/api/auth/oauth/`.

### Limites de Velocidad (Rate Limits)

Los limites se aplican por IP (anonimos) o por usuario/key (autenticados):

| Plan        | Requests / minuto |
|-------------|-------------------|
| Anonimo     | 10                |
| Free        | 30                |
| Pro         | 120               |
| Enterprise  | 600               |

Cuando se excede el limite, la API retorna `429 Too Many Requests`.

### Areas del Derecho

La plataforma cubre 11 areas del derecho peruano:
`civil`, `penal`, `laboral`, `tributario`, `administrativo`, `corporativo`,
`constitucional`, `registral`, `competencia`, `compliance`, `comercio_exterior`

### Public API v1

Endpoints versionados en `/api/v1/` para integraciones de terceros.
Requieren autenticacion via JWT o API key con los scopes correspondientes.

### Interactive Docs

- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
""",
    version="0.5.0",
    contact={"name": "TukiJuris", "url": "https://tukijuris.net.pe"},
    license_info={"name": "Proprietary"},
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "health", "description": "Liveness, readiness probes y metricas del sistema"},
        {"name": "auth", "description": "Autenticacion — registro, login, JWT"},
        {"name": "oauth", "description": "SSO — Google y Microsoft OAuth2"},
        {"name": "chat", "description": "Chat legal — consulta y streaming de respuestas"},
        {"name": "conversations", "description": "Historial de conversaciones"},
        {"name": "stream", "description": "Streaming SSE de respuestas del chat"},
        {"name": "documents", "description": "Busqueda y navegacion de la base de conocimiento legal"},
        {"name": "organizations", "description": "Gestion multi-tenant de organizaciones"},
        {"name": "billing", "description": "Planes, suscripciones y pagos"},
        {"name": "admin", "description": "Administracion del sistema (solo admins)"},
        {"name": "analytics", "description": "Analiticas de uso y metricas"},
        {"name": "api-keys", "description": "Gestion de API keys para desarrolladores"},
        {"name": "public-api-v1", "description": "API publica versionada v1 para integraciones externas"},
        {"name": "feedback", "description": "Feedback sobre la calidad de las respuestas"},
        {"name": "bookmarks", "description": "Marcadores de mensajes importantes"},
        {"name": "emails", "description": "Reseteo de contrasena y notificaciones"},
        {"name": "analysis", "description": "Analisis de casos legales"},
        {"name": "notifications", "description": "Centro de notificaciones in-app"},
        {"name": "search", "description": "Busqueda avanzada con filtros, historial y busquedas guardadas"},
        {"name": "export", "description": "Exportacion de consultas y conversaciones en formato PDF"},
        {"name": "shared", "description": "Vistas publicas de conversaciones compartidas (sin autenticacion)"},
        {"name": "tags", "description": "Etiquetas para organizar conversaciones"},
        {"name": "folders", "description": "Carpetas para agrupar conversaciones"},
        {"name": "memory", "description": "Memoria de contexto — hechos recordados entre sesiones"},
        {"name": "upload", "description": "Carga de archivos — PDF, DOCX, imagenes para analisis en chat"},
    ],
)

# Middleware stack — order matters: last registered = outermost layer
# GZip (outermost) -> CORS -> Security Headers -> Rate Limit (innermost)
if settings.gzip_enabled:
    app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=settings.cors_max_age,
)

# Global exception handlers — consistent JSON errors, no raw 500 HTML
from app.core.exception_handlers import register_exception_handlers
register_exception_handlers(app)

# Routes
app.include_router(health.router, prefix="/api")
app.include_router(plans.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(emails.router, prefix="/api")
app.include_router(oauth.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(stream.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(feedback.router, prefix="/api")
app.include_router(bookmarks.router, prefix="/api")
app.include_router(analysis.router, prefix="/api")
app.include_router(organizations.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(me_invoices.router, prefix="/api/billing")
app.include_router(admin.router, prefix="/api")
app.include_router(admin_saas.router, prefix="/api")
app.include_router(admin_invoices.router, prefix="/api")
app.include_router(rbac_admin.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(api_keys.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(shared.router, prefix="/api")
app.include_router(tags.router, prefix="/api")
app.include_router(folders.router, prefix="/api")
app.include_router(memory.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(v1.router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.4.0",
        "description": "Plataforma Jurídica Inteligente — Derecho Peruano",
        "docs": "/docs",
        "health": "/api/health",
    }
