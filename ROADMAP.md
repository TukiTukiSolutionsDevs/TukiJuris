# TUKIJURIS — Roadmap de Progreso

> Actualizado: 4 de Abril, 2026 — Fase 3: Preparación Beta Comercial completada
> Dominio: tukijuris.net.pe | Deploy: VPS

---

## Fase 3: Preparación Beta Comercial (Sprints 30-33) ✅

### Sprint 30 — Auth Hardening ✅
- Página /auth/reset-password (flujo completo con validación real-time)
- Fix validación de password (UI↔backend sincronizados: 8+ chars, upper, lower, digit)
- Fix CSRF en OAuth (state en Redis, verificación en callback)
- Fix política de password en reset confirm
- .env.example completado con todas las variables
- Docstring JWT corregido (7 days → 60 minutes)

### Sprint 31 — MercadoPago + Culqi Integration ✅
- PaymentService con providers abstractos (MercadoPago + Culqi)
- Billing routes reescritas (0 Stripe en codebase)
- Webhooks separados /webhook/mp y /webhook/culqi
- Modelos DB: stripe_* → payment_* + payment_provider
- Migración SQL 014 para renombrar columnas
- Planes actualizados: Free (beta), Base S/70, Enterprise (contactar)
- Frontend billing con precios en soles, logos de pago, botones activos

### Sprint 32 — Flujo Comercial Completo ✅
- Páginas billing/success y billing/cancel
- Email de confirmación de pago
- Límite diario de consultas (100/día plan Base)
- Check de límite en chat.py + stream.py (429)
- Plan badge en sidebar (Beta/Base/Enterprise)
- /auth/reset-password en PUBLIC_PATHS del middleware

### Sprint 33 — Production Hardening ✅
- docker-compose.prod.yml con TODAS las migraciones (14)
- Version bump a 1.0.0-beta
- CORS con dominio de producción
- Daily usage tracking conectado
- Deployment checklist documentado

---

## ESTADO ACTUAL: Fase 3 completada — Lista para beta comercial

```
FASE 1 (Sprints 1-24)
████████████████████  100%  — Plataforma construida

FASE 2 (Sprints 25-28) — AUDITORÍA FUNCIONAL PROFUNDA
████████████████████  100%  (4/4 sprints)

FASE 3 (Sprints 29-33) — PREPARACIÓN BETA COMERCIAL
████████████████████  100%  (5/5 sprints)

✅ BYOK model implementado (sin Stripe, con MercadoPago + Culqi)
✅ Auth hardening completo (reset-password, CSRF, OAuth)
✅ Flujo comercial completo (pagos, emails, límites diarios)
✅ Production hardening — versión 1.0.0-beta lista para deploy
```

---

## ESTADO ANTERIOR: Fase 2 en progreso — Sprints 25-28

```
FASE 1 (Sprints 1-24)
████████████████████  100%  — Plataforma construida

FASE 2 (Sprints 25-28) — AUDITORÍA FUNCIONAL PROFUNDA
████████████████████  100%  (4/4 sprints)

✅ Auditoría funcional completada — todos los hallazgos corregidos:
✅ El LLM ahora ve historial de conversación (últimos 20 mensajes)
✅ Frontend envía auth + conversation_id al stream
✅ Agentes secundarios reciben RAG context
✅ File upload implementado (PDF, DOCX, imágenes, TXT)
✅ stream.py unificado con orquestador (usa classify+retrieve del orchestrator)
✅ Síntesis multi-área con LLM (no concatenación)
✅ KEYWORD_MAP completo (11/11 áreas)
```

---

## FASE 2 — PLAN DE SPRINTS (25-28)

```
Sprint 25: Chat Core — El Chat Funciona de Verdad ✅ COMPLETADO
  ✅ Frontend envía Authorization: Bearer al /stream
  ✅ Frontend envía conversation_id en body
  ✅ Frontend captura conversation_id del "done" event
  ✅ orchestrator.py: conversation_history en process_query()
  ✅ base_agent.py: historial inyectado en messages[] (últimos 20)
  ✅ chat.py: carga historial antes del orquestador
  ✅ stream.py: recibe auth + conversation_id + carga historial

Sprint 26: Unificación del Stream ✅ COMPLETADO
  ✅ stream.py reescrito: usa classify/retrieve del orchestrator
  ✅ asyncpg raw reemplazado por ORM service (conversations.py)
  ✅ Memoria de usuario inyectada (get_user_context)
  ✅ Memorias extraídas post-respuesta (non-blocking)
  ✅ db: AsyncSession via Depends(get_db)
  ✅ Formato SSE idéntico preservado

Sprint 27: Calidad del Orquestador ✅ COMPLETADO
  ✅ Agentes secundarios reciben RAG context (retrieve por área)
  ✅ Síntesis multi-área con LLM (no concatenación)
  ✅ KEYWORD_MAP completo (11/11 áreas: +registral, competencia, compliance, comercio_exterior)
  ✅ get_rag_filter() usado en retrieval (sub-áreas incluidas)
  ✅ classification_confidence < 0.5 → nota de baja confianza
  ✅ user_context separado de query en clasificación
  ✅ Reranker truncación 200→500 chars

Sprint 28: File Upload ✅ COMPLETADO
  ✅ Modelo UploadedDocument + migración 012
  ✅ Upload service (PDF/DOCX/TXT extracción, imagen placeholder)
  ✅ 3 endpoints: POST/GET/DELETE /api/upload/
  ✅ Frontend: botón Paperclip, preview, dismiss, context injection
  ✅ Max 10MB, 6 MIME types soportados

Sprint 29: BYOK — Bring Your Own Key ✅ COMPLETADO
  MODELO DE NEGOCIO: TukiJuris cobra SOLO por acceso a la plataforma.
  Los usuarios traen sus propias API keys de proveedores de IA.
  ✅ Modelo UserLLMKey + migración 013 + Fernet encryption
  ✅ LLM Key Service (encrypt/decrypt, provider mapping, catalogue)
  ✅ 4 endpoints BYOK: list/add/delete keys + list providers
  ✅ LLM Adapter: user_api_key propagado (platform key para ops internas)
  ✅ chat.py + stream.py: resuelven key del usuario antes de llamar LLM
  ✅ orchestrator.py + base_agent.py: user_api_key en toda la cadena
  ✅ v1/usage: sin monthly_limit/remaining
  ✅ Billing: planes sin queries ni modelos (solo acceso)
  ✅ deps.py: rate limit anti-abuse plano (60/min auth, 10/min anon)
  ✅ Config → API Keys: UI completa (4 providers, colores, add/delete)
  ✅ Billing page: planes con features de plataforma, banner BYOK
  ✅ Landing: sin claims de modelos incluidos
  ✅ Chat: model dropdown filtra por keys configuradas + warning banner
  ✅ Guía: FAQ BYOK actualizado
  ✅ Onboarding: Step 4 → "Conectá tu IA" (provider + key + model)
```

---

---

## SPRINT 24 — RESUMEN (Go-Live Ready)

Sprint 24 es operativo — toda la funcionalidad de desarrollo esta completada.
Los scripts de deploy, backup, restore y monitor ya existen desde Sprint 18.
Las migraciones 009-011 estan listas. CI/CD esta verde.

**El app esta 100% production-ready. Solo falta provisionar VPS + DNS + go-live.**

---

## SPRINT 23 — RESUMEN (UX Polish + Flujo Completo)

| Feature | Detalle |
|---------|---------|
| SSO en Register | Google + Microsoft SSO buttons (copiado patrón de login) |
| Password Reset | Link "¿Olvidaste tu contraseña?" en login con modal de recovery |
| Auth Redirects | Login y Register redirigen a / si ya logueado |
| SSO → Onboarding | Callbacks Google/Microsoft detectan usuario nuevo (sin full_name) → /onboarding |
| Onboarding → API | Step 2 llama PUT /api/auth/me, Step 3 llama POST /api/organizations/ |
| Markdown Shared | renderMarkdown() extraído a lib/markdown.ts, usado en analizar, compartido, marcadores |
| Landing Stats | Stats dinámicos desde /api/health/knowledge (chunks, docs, áreas) |
| Status Español | Todas las strings traducidas (operativo, degradado, caído, etc.) |
| Docs Update | SDKs "Coming Soon" → "Disponible" con install commands y ejemplos |
| Guía Update | PDF export → "Disponible", API Keys → "Próximamente", versión v0.4.0 |
| Document Viewer | Búsqueda dentro del documento + TOC sidebar + "Consultar artículo →" |
| Marcadores | Paginación (10/página) + búsqueda/filtro |
| v1/usage | Endpoint con datos reales (queries today/month, plan, remaining) |
| v1/areas | Descripciones reales copiadas de /chat/agents |

### Archivos Sprint 23:
```
NUEVOS (1 archivo):
  apps/web/src/lib/markdown.ts              — Shared markdown renderer

FRONTEND MODIFICADOS (12 archivos):
  apps/web/src/app/auth/register/page.tsx   — SSO + redirect
  apps/web/src/app/auth/login/page.tsx      — password reset + redirect
  apps/web/src/app/auth/callback/google/page.tsx     — → onboarding si nuevo
  apps/web/src/app/auth/callback/microsoft/page.tsx  — → onboarding si nuevo
  apps/web/src/app/onboarding/page.tsx      — conectado a APIs reales
  apps/web/src/app/page.tsx                 — import renderMarkdown de lib/
  apps/web/src/app/analizar/page.tsx        — markdown rendering
  apps/web/src/app/compartido/[id]/page.tsx — markdown rendering
  apps/web/src/app/marcadores/page.tsx      — markdown + paginación + búsqueda
  apps/web/src/app/landing/page.tsx         — stats dinámicos
  apps/web/src/app/status/page.tsx          — traducción completa español
  apps/web/src/app/docs/page.tsx            — SDKs disponible + ejemplos
  apps/web/src/app/guia/page.tsx            — FAQ actualizado
  apps/web/src/app/documento/[id]/page.tsx  — search + TOC + consultar link

BACKEND MODIFICADOS (2 archivos):
  apps/api/app/api/routes/v1.py             — /usage real + /areas con descripciones
  apps/api/app/api/deps.py                  — TODO comment en código orphan
```

---

## SPRINT 22 — RESUMEN (Fixes Criticos + Sidebar Global + Auth)

| Feature | Detalle |
|---------|---------|
| Sidebar Global | AppSidebar + AppLayout componentes compartidos, sidebar persistente en 12 paginas autenticadas |
| Auth Fixes | Fix localStorage key en 6 paginas (org, billing, config, admin, analytics, buscar), middleware.ts, auth guard |
| Chat Persistence | chat.py ahora persiste conversaciones y mensajes a DB (removia el TODO critico) |
| Stream Security | Credenciales hardcodeadas removidas de stream.py, usa settings.database_url |
| Message Model | Columnas legal_area + model agregadas al modelo Message (analytics SQL ahora funciona) |
| Feedback | Botones 👍/👎 conectados al backend, satisfaction_rate usa Message.feedback real |
| Auth Endpoints | GET/PUT /api/auth/me creados con UpdateProfileBody |
| Memory Persist | User.preferences JSONB column, memory settings persistidos server-side |
| Plan Sync | _sync_member_plans() en billing webhooks (user.plan = org.plan para todos los miembros) |
| URL Params | Chat procesa ?conversation=, ?conv=, ?q= desde historial/marcadores/onboarding |
| Dead Links | /developer→/docs, /notificaciones arreglado, /auth→/auth/login en marcadores |
| Analytics Org | Removido DEMO_ORG_ID, fetch dinamico de org del usuario |

### Archivos Sprint 22:
```
NUEVOS (4 archivos):
  apps/web/src/components/AppSidebar.tsx         — Sidebar global reutilizable
  apps/web/src/components/AppLayout.tsx           — Layout wrapper con auth guard
  apps/web/src/middleware.ts                      — Next.js middleware (PUBLIC_PATHS)
  infrastructure/sql/migration_011_message_columns.sql — messages.legal_area/model + users.preferences

BACKEND MODIFICADOS (11 archivos):
  apps/api/app/api/routes/stream.py       — creds fix + auth + legal_area/model
  apps/api/app/api/routes/chat.py         — persistencia real de conversaciones
  apps/api/app/api/routes/feedback.py     — auth en POST, optional en GET
  apps/api/app/api/routes/analysis.py     — auth opcional
  apps/api/app/api/routes/analytics.py    — satisfaction_rate fix (Message.feedback)
  apps/api/app/api/routes/auth.py         — GET/PUT /me endpoints
  apps/api/app/api/routes/memory.py       — settings persisten en user.preferences
  apps/api/app/api/routes/billing.py      — _sync_member_plans() en webhooks
  apps/api/app/models/conversation.py     — +legal_area, +model en Message
  apps/api/app/models/user.py             — +preferences JSONB
  apps/api/app/services/conversations.py  — +legal_area, +model en add_message()

FRONTEND MODIFICADOS (15 archivos):
  apps/web/src/app/page.tsx               — URL params, feedback, /developer→/docs
  apps/web/src/app/organizacion/page.tsx  — token fix + AppLayout
  apps/web/src/app/billing/page.tsx       — token fix + AppLayout
  apps/web/src/app/configuracion/page.tsx — token fix + AppLayout
  apps/web/src/app/admin/page.tsx         — token fix + AppLayout
  apps/web/src/app/analytics/page.tsx     — token fix + DEMO_ORG_ID removed + AppLayout
  apps/web/src/app/buscar/page.tsx        — token fix (removed local getToken) + AppLayout
  apps/web/src/app/historial/page.tsx     — AppLayout
  apps/web/src/app/marcadores/page.tsx    — /auth fix + ?conv→?conversation + AppLayout
  apps/web/src/app/analizar/page.tsx      — AppLayout
  apps/web/src/app/status/page.tsx        — AppLayout
  apps/web/src/app/docs/page.tsx          — AppLayout
  apps/web/src/app/guia/page.tsx          — AppLayout
  apps/web/src/components/NotificationBell.tsx — removed dead /notificaciones link
```

---

## SPRINT 21 — RESUMEN (Post-Launch Improvements III)

| Feature | Detalle |
|---------|---------|
| Analytics avanzado | 3 nuevos endpoints: costos por modelo, top queries, export CSV + frontend con tabs Costos y Consultas Frecuentes |
| Tags y carpetas | Modelo Tag/Folder/ConversationTag, 13 endpoints CRUD, sidebar con carpetas y etiquetas en historial |
| Memoria de contexto | Modelo UserMemory, servicio de extraccion regex V1, inyeccion de contexto en chat, tab Memoria en configuracion |

### Archivos Sprint 21:
```
NUEVOS (8 archivos):
  apps/api/app/models/tag.py                — Tag, Folder, ConversationTag ORM (75 lineas)
  apps/api/app/models/memory.py             — UserMemory ORM (45 lineas)
  apps/api/app/api/routes/tags.py           — CRUD tags + assign/remove (297 lineas)
  apps/api/app/api/routes/folders.py        — CRUD folders + move conversations (272 lineas)
  apps/api/app/api/routes/memory.py         — Memory CRUD + settings (204 lineas)
  apps/api/app/services/memory_service.py   — Extraction + context injection (321 lineas)
  infrastructure/sql/migration_009_tags_folders.sql     — Tags, folders, conversation_tags tables (63 lineas)
  infrastructure/sql/migration_010_context_memory.sql   — User memories table + indexes (37 lineas)

MODIFICADOS (8 archivos):
  apps/api/app/api/routes/analytics.py      — +255 lineas (3 endpoints: costs, top-queries, export CSV)
  apps/api/app/api/routes/conversations.py  — +45 lineas (tags/folder en ConversationSummary)
  apps/api/app/api/routes/chat.py           — +40 lineas (memory injection + extraction)
  apps/api/app/models/conversation.py       — +5 lineas (folder_id FK + relationships)
  apps/api/app/models/user.py               — +3 lineas (tags, folders, memories relationships)
  apps/api/app/models/__init__.py           — +4 lineas (register Tag, Folder, ConversationTag, UserMemory)
  apps/api/app/main.py                      — +9 lineas (register 3 new routers + openapi tags, bump v0.4.0)
  apps/web/src/app/analytics/page.tsx       — +392 lineas (tabs Costos + Consultas Frecuentes + Export CSV)
  apps/web/src/app/historial/page.tsx       — +681 lineas (sidebar carpetas/etiquetas, pills, folder submenu)
  apps/web/src/app/configuracion/page.tsx   — +259 lineas (tab Memoria con toggle, lista, delete)
```

---

## SPRINT 20 — RESUMEN (Post-Launch Improvements II)

| Feature | Detalle |
|---------|---------|
| Chat markdown | Renderer regex puro para respuestas legales formateadas |
| Bookmarks | Modelo + 3 endpoints + pagina /marcadores agrupada por area |
| Query templates | Templates por area legal con prefill en chat |
| Formatting toolbar | Barra de herramientas de formato en chat input |
| Conversation management | Pin, archive, share, rename, hard-delete + historial page con tabs y bulk ops |
| Shared conversations | Share links publicos (12-char, SSR + OG tags) |
| Keyboard shortcuts | 8 shortcuts + modal (Ctrl+K buscar, Ctrl+Enter enviar, etc.) |
| Accessibility | ARIA labels, roles, focus rings, skip-to-content |
| i18n preparation | 70+ keys es/en, funcion t() |
| Help popover | Boton ? en footer con shortcuts, guia, status |

---

## SPRINT 19 — RESUMEN (Post-Launch Improvements I)

| Feature | Detalle |
|---------|---------|
| Alembic | Migration system async para PostgreSQL (env.py, NullPool, baseline) |
| Notification center | Bell con badge + dropdown + 5 endpoints + polling 30s |
| Advanced search | 6 endpoints, filtros, autocomplete, saved searches, history + rewrite de /buscar (1070 lineas) |
| PDF export | ReportLab A4 profesional + 3 endpoints (conversacion, mensaje, bulk) |

---

## NUMEROS ACTUALES — TUKIJURIS

| Categoria | Valor |
|-----------|-------|
| **API** | v0.4.0, 64+ endpoints, 22 routers |
| **Frontend** | 21 paginas + sidebar GLOBAL persistente (AppLayout) + markdown compartido |
| **AI** | 11 agentes especializados, LangGraph orchestrator + context memory |
| **Search** | Hybrid (BM25 + pgvector + cross-encoder reranking) |
| **KB** | ~306+ chunks, 17 seeders, 4 scrapers, 251 articles en pipeline |
| **Testing** | 103 pytest tests + Locust load testing |
| **Auth** | JWT + OAuth2 (Google, Microsoft) + API keys |
| **Billing** | Stripe real (checkout, portal, webhooks) |
| **Email** | 3 providers, 4 templates |
| **Monitoring** | Sentry + in-memory metrics + status page |
| **Performance** | Redis cache + GZip + DB pool optimization |
| **Security** | 4 middlewares, validators, brute-force, password policy |
| **CI/CD** | GitHub Actions (lint + test + build + docker) |
| **SDKs** | Python (sync+async) + JavaScript/TypeScript |
| **Docs** | OpenAPI enriched + developer guide + user guide + 15 FAQ |
| **Deploy** | Docker prod (Gunicorn + Nginx + Let's Encrypt) + VPS scripts |
| **Mobile** | 10 paginas responsive polished |
| **Onboarding** | 5-step wizard para nuevos usuarios |
| **Operations** | Backup diario, deploy script, monitor, restore |
| **Organization** | Tags, carpetas, bookmarks, conversation management, shared links |
| **Analytics** | Overview, areas, models, costs, top queries, CSV export |
| **Context Memory** | Extraction regex V1, user memories, context injection |

---

## DEPLOYMENT CHECKLIST (VPS)

```
[ ] 1. Provision VPS (Ubuntu 22.04, 4CPU/8GB/100GB)
[ ] 2. SSH into server + run: make setup-server
[ ] 3. Clone repo: git clone <repo> /opt/tukijuris/app
[ ] 4. Copy .env: cp .env.production.example .env.production
[ ] 5. Edit .env.production with real values (DB pass, Stripe, OAuth, etc.)
[ ] 6. Configure DNS: A record tukijuris.net.pe -> server IP
[ ] 7. Wait DNS propagation: dig tukijuris.net.pe
[ ] 8. Get SSL cert: bash infrastructure/certbot/init-letsencrypt.sh
[ ] 9. Build: make prod-build
[ ] 10. Start: make prod-up
[ ] 11. Run migrations: migration_009 + migration_010
[ ] 12. Ingest data: docker exec api python -m services.ingestion.ingest
[ ] 13. Generate embeddings: docker exec api python -m services.ingestion.generate_embeddings
[ ] 14. Run scrapers: docker exec api python -m services.ingestion.scrapers.scheduler
[ ] 15. Verify: curl -I https://tukijuris.net.pe
[ ] 16. Setup crons: make setup-cron (backup 2am + SSL renewal 3am)
[ ] 17. Check status: https://tukijuris.net.pe/status
[ ] 18. Go-live!
```

---

## MILESTONES — TODOS COMPLETADOS

```
MILESTONE 1 — "Funciona" .................. COMPLETADO (Sprint 2)
MILESTONE 2 — "Es util" .................. COMPLETADO (Sprint 4)
MILESTONE 3 — "MVP interno" .............. COMPLETADO (Sprint 8)
MILESTONE 4 — "Beta privada" ............. COMPLETADO (Sprint 13)
MILESTONE 5 — "Beta publica" ............. COMPLETADO (Sprint 16)
MILESTONE 6 — "Launch" ................... 95% (Sprint 18)
   Solo falta: VPS + DNS + go-live
MILESTONE 7 — "Post-Launch Polish" ....... COMPLETADO (Sprint 24)
   ✅ Sprints 19-24 completados
   ✅ AUDITORIA: 18 bugs criticos identificados y corregidos
   ✅ ROADMAP 100% — PRODUCTION-READY
```

---

## AUDITORIA INTEGRAL (Post Sprint 21)

Se realizo una auditoria completa del sistema (21 paginas frontend, 22 routers backend,
~90 endpoints, 14 tablas DB). Se identificaron bugs criticos, inconsistencias y
deuda tecnica que deben resolverse ANTES del go-live.

### Hallazgos Criticos

```
FRONTEND (8 criticos):
  🔴 localStorage key inconsistency — 5 paginas leen token con key incorrecta
  🔴 URL params no procesados — /?conversation=, ?q=, ?conv= ignorados
  🔴 Sin sidebar compartida — 20 paginas son islas sin navegacion lateral
  🔴 Dead links: /developer→404, /notificaciones→404, /auth→404
  🔴 DEMO_ORG_ID hardcodeado en analytics
  🔴 Onboarding no llama APIs — solo localStorage
  🔴 Feedback 👍/👎 son TODO sin conexion
  🔴 Sin middleware.ts de auth

BACKEND (10 criticos):
  🔴 stream.py tiene credenciales hardcodeadas en codigo
  🔴 Message model falta columnas legal_area y model (analytics SQL falla)
  🔴 chat.py POST /chat/query NO persiste (TODO en codigo)
  🔴 analytics feedback query referencia tabla inexistente
  🔴 stream.py, feedback.py, analysis.py sin autenticacion
  🔴 memory/settings no persiste (acepta PUT pero no guarda)
  🔴 v1/usage siempre retorna zeros
  🔴 User.plan vs Organization.plan sin sync
  🔴 usage_service.track_query() nunca se llama
  🔴 Markdown inconsistente (solo chat lo renderiza)
```

---

## SPRINTS RESTANTES (22-24) — REPLANTEADOS POST-AUDITORIA

```
Sprint 22: Fixes Criticos + Sidebar Global + Auth ✅ COMPLETADO
  ✅ Fix credenciales hardcodeadas en stream.py
  ✅ Agregar columnas legal_area + model a Message model + migracion
  ✅ Implementar persistencia en chat.py
  ✅ Agregar auth a feedback.py, analysis.py, stream.py
  ✅ Fix satisfaction_rate con Message.feedback
  ✅ Crear GET/PUT /api/auth/me
  ✅ Sync user.plan ↔ org.plan via _sync_member_plans()
  ✅ Persistir memory settings en User.preferences JSONB
  ✅ Fix localStorage key en 6 paginas
  ✅ AppLayout + AppSidebar global (12 paginas)
  ✅ middleware.ts de auth
  ✅ Fix dead links (/developer, /notificaciones, /auth)
  ✅ URL params ?conversation=, ?q= en chat
  ✅ Fix DEMO_ORG_ID en analytics
  ✅ Feedback 👍/👎 conectado al backend

Sprint 23: UX Polish + Flujo Completo ✅ COMPLETADO
  ✅ SSO en register (Google + Microsoft)
  ✅ "Olvide mi contraseña" en login
  ✅ Redirect si ya logueado en /login y /register
  ✅ SSO → onboarding para usuarios nuevos
  ✅ Onboarding conectado a APIs reales
  ✅ Markdown rendering consistente (analizar, compartido, marcadores)
  ✅ Landing stats desde backend
  ✅ Status page traducido a español
  ✅ Docs actualizados (SDKs disponibles)
  ✅ Guia actualizada (PDF disponible, API Keys proximo)
  ✅ Busqueda dentro de documentos + TOC + "Consultar artículo"
  ✅ Paginacion + busqueda en marcadores
  ✅ /api/v1/usage con datos reales
  ✅ /api/v1/areas con descripciones
  ✅ Cleanup codigo orphan

Sprint 24: Go-Live Ready ✅ COMPLETADO
  ✅ Todo el desarrollo completado (24/24 sprints)
  ✅ Migraciones 009-011 listas para deploy
  ✅ Scripts de deploy/backup/restore/monitor desde Sprint 18
  ✅ CI/CD configurado (GitHub Actions)
  ✅ Sentry configurado para monitoring
  ⬜ Pendiente: Provisionar VPS + DNS + go-live (operativo)
  🚀 LISTO PARA LANZAMIENTO
```

---

## STACK COMPLETO

```
Frontend:   Next.js 15 (App Router) + Tailwind CSS + Lucide React
Backend:    FastAPI + Python 3.12 + Gunicorn + Uvicorn (4 workers)
AI:         LangGraph + LiteLLM + 11 domain agents + cross-encoder reranker + context memory
Search:     BM25 + pgvector HNSW + Hybrid search + Redis cache
Database:   PostgreSQL 17 + pgvector 0.8.2
Cache:      Redis 7 (rate limit + query cache + sessions)
Proxy:      Nginx (SSL/TLS 1.3 + rate limiting + gzip + SSE)
Auth:       JWT + OAuth2 (Google, Microsoft) + API keys (SHA-256)
Billing:    Stripe (checkout, portal, webhooks, plans)
Email:      Resend / SMTP / Console (4 HTML templates)
Monitoring: Sentry + RequestMetrics + /status page
CI/CD:      GitHub Actions (lint + test + build + docker)
Deploy:     Docker multi-stage + VPS scripts (setup, deploy, backup, restore)
SDKs:       Python (httpx) + TypeScript (native fetch)
Security:   4 middlewares + validators + brute-force + HSTS + CSP
```

---

*TukiJuris — Plataforma Juridica Inteligente para Derecho Peruano*
*Repo: Agente-Derecho | Dominio: tukijuris.net.pe*
