# AUDITORÍA INTEGRAL — TukiJuris v1.0.0-beta
## Plataforma Jurídica Inteligente para Derecho Peruano

> **Fecha**: 8 de Abril, 2026
> **Auditor**: Arquitecto Senior — Revisión pre-producción
> **Alcance**: Producto, Negocio, Paneles, Pricing, Infraestructura, Seguridad
> **Veredicto global**: 🟡 NO LISTO para producción — requiere correcciones críticas

---

## RESUMEN EJECUTIVO

TukiJuris tiene una **base técnica sólida y ambiciosa**. El orquestador multi-agente con LangGraph es real (no marketing), el modelo BYOK es innovador para LATAM, y la cobertura funcional (25 páginas, 90+ endpoints, 11 agentes IA) es impresionante para un solo desarrollador.

**Sin embargo**, la plataforma tiene **brechas críticas** que impedirían una operación comercial real:

| Categoría | Estado | Bloqueante |
|-----------|--------|:----------:|
| Base de conocimiento | ❌ VACÍA (0 docs, 0 chunks) | **SÍ** |
| Rate limiter + CORS | ❌ 429 sin headers CORS | **SÍ** |
| Token expirado sin redirect | ❌ UX rota silenciosamente | **SÍ** |
| Páginas legales inexistentes | ❌ /terms, /privacy → 404 | **SÍ** |
| Webhook signature verification | ⚠️ Ausente | **SÍ** |
| Deploy pipeline (CD) | ❌ Placeholder | **SÍ** |
| Panel admin | ⚠️ MVP, 1 sola vista | No |
| Error boundaries (Next.js) | ❌ No existen | No |
| Observabilidad | ⚠️ Solo in-memory | No |
| i18n | ⚠️ Preparación, no real | No |

---

## I. AUDITORÍA DE PRODUCTO

### 1.1 Inventario funcional completo

**Frontend: 25 páginas, 7 componentes compartidos**

| Módulo | Páginas | Estado | Observación |
|--------|---------|--------|-------------|
| **Chat principal** | `/` (1513 líneas) | ✅ Completo | Core del producto. Streaming SSE, orquestador, BYOK, file upload |
| **Auth** | Login, Register, Reset, OAuth callbacks (5 págs) | ✅ Completo | JWT + Google + Microsoft SSO |
| **Onboarding** | 5-step wizard (1029 líneas) | ✅ Completo | Perfil → Org → API Key → Modelo → Tips |
| **Historial** | Conversaciones + folders + tags (1180 líneas) | ✅ Completo | Pin, archive, share, bulk ops |
| **Búsqueda** | Búsqueda avanzada normativa (1067 líneas) | ✅ Completo | Filtros, suggestions, saved searches |
| **Analytics** | Overview + costos + top queries (1297 líneas) | ✅ Completo | Export CSV |
| **Configuración** | Perfil + Password + Org + Memoria + API Keys (1326 líneas) | ✅ Completo | BYOK management completo |
| **Billing** | Planes + Checkout + Success/Cancel | ⚠️ Parcial | Planes hardcodeados en frontend |
| **Organización** | Crear + miembros + invitar | ✅ Completo | Multi-tenant |
| **Marcadores** | Mensajes guardados por área | ✅ Completo | Filtro + paginación |
| **Analizar** | Análisis estructurado de caso | ✅ Completo | Módulo simple pero funcional |
| **Buscar docs** | Visor de documento + TOC | ✅ Completo | Búsqueda dentro del doc |
| **Landing** | Página comercial pública | ✅ Completo | Features, pricing, stats dinámicos |
| **Admin** | Panel administrativo | ⚠️ MVP | 1 sola vista, sidebar promete más |
| **Status** | Estado del sistema | ⚠️ Parcial | Incidentes son placeholder fake |
| **Guía** | FAQ + tips + soporte | ✅ Completo | 15 FAQ |
| **API Docs** | Documentación para developers | ✅ Completo | Auth, endpoints, ejemplos |
| **Design System** | Página interna de diseño | ⚠️ Interna | "Pendiente aprobación" |
| **Compartido** | Link público de conversación | ✅ Completo | SSR + OG tags |

**Backend: 22 routers, 90+ endpoints, 12 servicios**

| Router | Endpoints | Auth | Estado |
|--------|:---------:|------|--------|
| auth | 4 | Mixto | ✅ |
| emails | 2 | Público | ✅ |
| oauth | 5 | Público | ✅ |
| chat | 3 | Opcional | ✅ |
| stream | 1 | Opcional | ✅ |
| conversations | 7 | JWT | ✅ |
| documents | 4 | Público | ✅ |
| feedback | 2 | Mixto | ✅ |
| bookmarks | 3 | JWT | ✅ |
| analysis | 1 | Opcional | ✅ |
| organizations | 7 | JWT | ✅ |
| billing | 7 | Mixto | ⚠️ Webhooks sin verificación |
| admin | 4 | Admin | ✅ |
| analytics | 7 | JWT+Org | ✅ |
| api_keys | 8 | JWT | ✅ |
| notifications | 5 | JWT | ✅ |
| search | 6 | Mixto | ✅ |
| export | 3 | JWT | ✅ |
| shared | 1 | Público | ✅ |
| tags | 7 | JWT | ✅ |
| folders | 6 | JWT | ✅ |
| memory | 6 | JWT | ✅ |
| upload | 3 | JWT | ✅ |
| health | 6 | Público | ✅ |
| v1 (API pública) | 6 | API Key | ✅ |

### 1.2 Bugs y problemas activos encontrados

#### 🔴 CRÍTICOS (bloqueantes para producción)

1. **KB vacía** — `documents = 0, chunks = 0, embeddings = 0`. Sin ingesta de datos, el RAG no funciona. El chat no puede responder nada sobre derecho peruano.

2. **Rate limiter rompe CORS** — Cuando el `RateLimitMiddleware` devuelve 429, la respuesta NO incluye headers `Access-Control-Allow-Origin`. El browser bloquea silenciosamente TODAS las llamadas y la app se vuelve inutilizable sin ningún error visible para el usuario.

3. **Token expirado = app zombie** — JWT vence en 60 minutos. El frontend NO detecta 401s globalmente para redirigir a login. El usuario ve la app "normal" pero todas las llamadas fallan silenciosamente. No hay refresh tokens.

4. **Páginas legales 404** — Landing linkea `/terms` y `/privacy`. Register linkea `/terminos` y `/privacidad`. Ninguna de las 4 rutas existe. Esto es un **requisito legal** para operar un SaaS con pagos.

5. **Webhook payment sin verificación criptográfica** — MercadoPago y Culqi webhooks parsean JSON pero NO verifican firma. Un atacante podría fabricar webhooks falsos para activar planes sin pagar.

6. **Deploy pipeline es placeholder** — `deploy.yml` solo imprime "TODO". No hay CD real.

7. **Uploads perdidos al reiniciar** — Files se guardan en `/app/uploads` dentro del container pero NO hay volumen montado. Al reconstruir/reiniciar el container, todos los archivos subidos desaparecen.

#### 🟡 IMPORTANTES (necesarios antes de beta pública)

8. **No hay error boundaries** — No existen `error.tsx`, `not-found.tsx`, `loading.tsx`, `global-error.tsx`. Un crash en cualquier página muestra pantalla blanca.

9. **JWT_SECRET placeholder** — Default es `"change-this-in-production"`. Si se despliega sin cambiarlo, cualquiera puede fabricar tokens.

10. **No hay exception handlers globales** — Errores no capturados devuelven stacktraces de Python al cliente.

11. **OAuth state fail-open** — Si Redis cae durante OAuth, la validación de state se saltea, abriendo vector CSRF.

12. **Sentry declarado pero no instalado** — `sentry-sdk` no está en `pyproject.toml` aunque el código lo importa.

13. **Admin sidebar promete más de lo que hay** — Links a `?section=users|orgs|subscriptions` pero la página no lee query params. Solo muestra una vista.

14. **Status page con incidentes fake** — Placeholder hardcodeado que dice "Sin incidentes" pero no viene de ningún endpoint.

15. **Versión hardcodeada v0.3.0** en i18n/help mientras el roadmap dice v1.0.0-beta.

16. **`console.log` en producción** — 9 console.log/error en código frontend que no deberían estar.

17. **Inconsistencia en infraestructura de gateway** — `docker-compose.prod.yml` asume gateway externo pero scripts/nginx/certbot asumen nginx local. Son contradictorios.

---

## II. AUDITORÍA DE PANELES

### 2.1 Panel del Cliente (estado actual)

Lo que EXISTE hoy:

```
SIDEBAR ACTUAL:
├── PRINCIPAL
│   ├── Chat (core del producto)
│   └── Buscar (búsqueda en normativa)
├── ORGANIZACIÓN
│   ├── Historial (conversaciones)
│   └── Marcadores (mensajes guardados)
├── GESTIÓN
│   ├── Analytics (métricas de uso)
│   ├── Organización (team management)
│   └── Facturación (planes/pagos)
└── CONFIGURACIÓN
    ├── Configuración (perfil + API keys)
    ├── Guía (FAQ + tips)
    └── API Docs (developer docs)
```

### 2.2 Lo que FALTA en el Panel del Cliente

| Módulo | Prioridad | Justificación |
|--------|:---------:|---------------|
| **Dashboard / Home** | 🔴 Alta | El cliente entra directo al chat. No hay una pantalla resumen con: consultas recientes, uso del mes, estado del plan, tips rápidos |
| **Notificaciones (página)** | 🟡 Media | Existe el bell dropdown pero no hay `/notificaciones` como página completa |
| **Centro de Ayuda / Soporte** | 🔴 Alta | No hay canal de soporte: no hay chat de soporte, no hay ticket system, no hay email visible de contacto (solo `ventas@`) |
| **Términos y Privacidad** | 🔴 Alta | Inexistentes — requisito legal |
| **Perfil público / Avatar** | 🟡 Media | `avatar_url` existe en el modelo pero no hay UI para subirlo |
| **Exportación masiva de datos** | 🟡 Media | GDPR compliance: el usuario debería poder exportar todo su contenido |
| **Uso diario visible** | 🟡 Media | TODO en el código: indicador de consultas diarias restantes |
| **Changelog / Novedades** | 🟢 Baja | Para comunicar actualizaciones al usuario |

### 2.3 Panel de Administración (estado actual)

Lo que EXISTE hoy:

```
/admin — UNA sola página con:
├── Stats globales (usuarios, consultas, feedback)
├── Health del sistema
├── Tabla de usuarios (email, plan, fecha)
├── Actividad reciente (queries)
└── KB stats por área
```

**AdminSidebar** promete secciones que NO están implementadas:
- Usuarios (con CRUD) → solo tabla readonly
- Organizaciones → no implementado
- Suscripciones → no implementado

### 2.4 Lo que NECESITA el Panel de Administración

| Módulo | Prioridad | Descripción |
|--------|:---------:|-------------|
| **Dashboard operativo** | 🔴 Alta | Métricas en tiempo real: usuarios activos, queries/hora, errores, latencia, uso de modelos |
| **Gestión de usuarios** | 🔴 Alta | CRUD completo: activar/desactivar, cambiar plan, ver uso, impersonar, resetear password |
| **Gestión de organizaciones** | 🔴 Alta | Ver todas las orgs, planes activos, miembros, consumo |
| **Gestión de suscripciones** | 🔴 Alta | Ver pagos, estados, cancelaciones, revenue |
| **Knowledge Base admin** | 🟡 Media | Ver documentos ingresados, re-ingestar, agregar documentos manuales, ver coverage por área |
| **Logs / Auditoría** | 🟡 Media | Registro de acciones críticas: logins, cambios de plan, pagos |
| **Configuración del sistema** | 🟡 Media | Feature flags, límites de planes, mantenimiento programado |
| **Gestión de feedback** | 🟡 Media | Ver todos los 👍/👎 por área, identificar problemas del LLM |
| **Email / Comunicaciones** | 🟢 Baja | Enviar anuncios a usuarios, templates de email |
| **Monitoreo de costos IA** | 🟡 Media | Cuánto cuesta operar la plataforma (tokens de embeddings, reranking) |

---

## III. ARQUITECTURA DE IA — EVALUACIÓN

### 3.1 Lo que está BIEN (y es genuinamente diferenciador)

1. **Orquestador LangGraph real** — No es un wrapper de chat. Es un grafo con nodos: classify → retrieve → primary_agent → evaluate → (enrich → synthesize) | format_simple. Esto ES deliberativo.

2. **11 agentes especializados** — civil, penal, laboral, tributario, constitucional, administrativo, corporativo, registral, competencia, compliance, comercio_exterior. Cada uno con prompt y filtro RAG específico.

3. **Búsqueda híbrida** — BM25 + pgvector + cross-encoder reranking. Esto es state-of-the-art para documentos legales.

4. **Memoria de contexto** — Extracción de hechos entre sesiones, inyección en prompts.

5. **BYOK bien implementado** — Encriptación Fernet de API keys, resolución por provider, catálogo de modelos.

### 3.2 Lo que está DÉBIL

1. **KB VACÍA** — Todo el RAG pipeline está construido pero sin datos. Es como un motor Ferrari sin gasolina.

2. **Clasificación frágil** — Depende de parsear output libre del LLM. Si el modelo cambia formato de respuesta, la clasificación se rompe.

3. **Citaciones no grounded** — Las citas se extraen con regex del texto generado, no están vinculadas a chunks reales del RAG. El LLM puede inventar artículos y el sistema no lo detectaría.

4. **Embedding dimension mismatch risk** — Google genera 768-dim, OpenAI 1536-dim. Si se cambia de proveedor, hay que re-generar todos los embeddings y cambiar la dimensión del vector en la DB.

5. **Scrapers parcialmente funcionales** — El peruano, TC e INDECOPI tienen scrapers pero mucha data es curada manualmente. El scheduler guarda estado solo en memoria.

---

## IV. AUDITORÍA DE SEGURIDAD

### 4.1 Lo que está BIEN

| Control | Implementación |
|---------|---------------|
| JWT auth | HS256, 60 min expiry |
| OAuth2 (Google, Microsoft) | State en Redis, callbacks validados |
| Password hashing | bcrypt, 12 rounds |
| API keys | SHA-256 hash, solo prefijo visible |
| LLM keys | Fernet encryption at rest |
| Rate limiting | Redis sliding window (60/min auth, 10/min anon) |
| Security headers | CSP, HSTS, X-Frame-Options, Referrer-Policy |
| Brute force | 5 intentos / 15 min en login |
| CORS | Configurado correctamente (pero roto por rate limiter) |

### 4.2 Lo que FALTA

| Brecha | Severidad | Detalle |
|--------|:---------:|---------|
| Refresh tokens | 🔴 Alta | Sin refresh tokens, el usuario debe re-loguearse cada 60 min |
| Token revocation | 🔴 Alta | No hay blacklist. Si comprometen un token, no se puede invalidar |
| Webhook signatures | 🔴 Alta | MercadoPago y Culqi no verifican firma criptográfica |
| MFA / 2FA | 🟡 Media | No hay opción de segundo factor |
| Global exception handler | 🟡 Media | Stacktraces pueden filtrarse al cliente |
| Audit trail | 🟡 Media | No hay registro de acciones sensibles (login, cambio plan, etc.) |
| Request/Correlation ID | 🟡 Media | Imposible trazar un request entre frontend y backend |
| Rate limiter CORS | 🔴 Alta | 429 respuestas no tienen headers CORS, rompe browser |
| TrustedHost middleware | 🟢 Baja | Acepta cualquier Host header |
| CSRF protection | 🟡 Media | Solo en OAuth state, no en forms de billing |

---

## V. AUDITORÍA DE INFRAESTRUCTURA

### 5.1 Estado actual

| Componente | Dev | Prod | Estado |
|------------|:---:|:----:|--------|
| Docker Compose | ✅ | ✅ | Funcional pero con inconsistencias |
| PostgreSQL 17 + pgvector | ✅ | ✅ | Healthy |
| Redis 7 | ✅ | ✅ | Healthy (sin password en dev) |
| Nginx + SSL | — | ⚠️ | Existe config pero contradice prod compose |
| CI (GitHub Actions) | ✅ | — | Lint + Test + Build + Docker |
| CD (Deploy) | — | ❌ | Placeholder "TODO" |
| Backups | — | ⚠️ | Solo DB local, sin offsite, sin verificación |
| Monitoring | — | ⚠️ | In-memory metrics, Sentry sin instalar |
| Logging | ⚠️ | ⚠️ | Plain text, sin structured logging |
| Healthchecks | ⚠️ | ⚠️ | Solo DB tiene healthcheck en prod |

### 5.2 Problemas de infraestructura

1. **Contradicción gateway/nginx**: prod compose asume external `shared-gateway` network pero los scripts asumen nginx local. Esto VA A FALLAR en deploy.

2. **Sin puertos publicados en prod**: prod compose no expone ports de api/web, pero `deploy.sh` y `monitor.sh` hacen `curl localhost:8000`. Incompatible.

3. **Uploads sin volumen**: archivos subidos se pierden al reiniciar container.

4. **Migrations split**: 14 SQL files + 2 Alembic versions. Estrategia mixta que puede causar drift.

5. **No hay zero-downtime deploy**: el script hace `docker compose down` + `up`. Downtime guaranteed.

6. **.env examples incompletos**: faltan ~20 variables vs `config.py`.

---

## VI. ANÁLISIS DE PANELES — PROPUESTA DE ESTRUCTURA

### 6.1 Panel del Cliente (propuesta completa)

```
┌─────────────────────────────────────────────────┐
│ PANEL DEL CLIENTE — TukiJuris                   │
├─────────────────────────────────────────────────┤
│                                                  │
│ PRINCIPAL                                        │
│ ├── 🏠 Dashboard (NUEVO)                        │
│ │    Resumen: queries hoy, plan, uso, tips      │
│ ├── 💬 Chat                                     │
│ │    Consulta legal con IA + orquestador        │
│ ├── 🔍 Buscar                                   │
│ │    Búsqueda en normativa peruana              │
│ └── 📋 Analizar                                 │
│      Análisis estructurado de caso              │
│                                                  │
│ ORGANIZACIÓN                                     │
│ ├── 📜 Historial + Carpetas + Tags             │
│ ├── 📑 Marcadores                               │
│ └── 👥 Mi Organización                          │
│      Equipo, invitaciones, uso compartido       │
│                                                  │
│ GESTIÓN                                          │
│ ├── 📊 Analytics (uso, costos, top queries)     │
│ ├── 💳 Facturación (plan, pagos, facturas)      │
│ └── 🔑 API Keys (BYOK + developer keys)        │
│                                                  │
│ CONFIGURACIÓN                                    │
│ ├── ⚙️  Perfil + Password + Preferencias        │
│ ├── 🧠 Memoria (contexto recordado)             │
│ ├── 📖 Guía + FAQ                               │
│ ├── 📚 API Docs                                 │
│ └── 🛟 Soporte (NUEVO)                          │
│                                                  │
│ FOOTER                                           │
│ ├── Estado del sistema                           │
│ ├── Términos de servicio (NUEVO)                │
│ └── Política de privacidad (NUEVO)              │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 6.2 Panel de Administración (propuesta completa)

```
┌─────────────────────────────────────────────────┐
│ PANEL ADMIN — TukiJuris                         │
├─────────────────────────────────────────────────┤
│                                                  │
│ OVERVIEW                                         │
│ └── 📊 Dashboard Operativo                      │
│      KPIs: DAU, queries/h, revenue, errores     │
│                                                  │
│ USUARIOS                                         │
│ ├── 👤 Lista de usuarios (CRUD)                 │
│ │    Buscar, filtrar, activar/desactivar         │
│ ├── 🏢 Organizaciones                           │
│ │    Lista, miembros, planes, consumo            │
│ └── 💰 Suscripciones                            │
│      Pagos activos, MRR, churn, facturas        │
│                                                  │
│ CONTENIDO                                        │
│ ├── 📚 Knowledge Base                           │
│ │    Documentos, chunks, coverage, re-ingesta    │
│ ├── 💬 Conversaciones                           │
│ │    Monitoreo de calidad, flagged content       │
│ └── 👍 Feedback                                 │
│      Análisis de satisfacción por área           │
│                                                  │
│ OPERACIONES                                      │
│ ├── 🔧 Sistema                                  │
│ │    Health, Redis, DB, feature flags            │
│ ├── 📋 Logs / Auditoría                         │
│ │    Acciones sensibles, login history           │
│ └── 💸 Costos IA                                │
│      Consumo de plataforma (embeddings, etc.)    │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## VII. ANÁLISIS DE MERCADO

### 7.1 Competidores directos en Perú

| Competidor | Precio | Usuarios | Fortaleza | Debilidad vs TukiJuris |
|------------|--------|----------|-----------|------------------------|
| **DOXS.AI** 🔴 | S/20/mes (Pro) | Desconocido | Peru-nativo, TC/Corte Suprema/SCIJ/El Peruano, voz | No tiene orquestador multi-agente |
| **Magnar** 🔴 | USD 50/mes | 6,000+ en Perú | Chile→Perú, jurisprudencia multi-país | No es especializado en derecho peruano |
| **vLex + Vincent AI** 🟡 | Enterprise (quote) | Institucional | Marca, cobertura global, Vincent AI | Caro, genérico, no es Peru-first |
| **Thomson Reuters Peru** 🟡 | Enterprise (quote) | Corporativo | HighQ, marca, integrado | Solo grandes estudios/empresas |
| **Fuentes oficiales gratuitas** 🟠 | Gratis | Todos | PJ, TC, SCIJ, El Peruano | El "competidor real" — investigación manual |

> ⚠️ **DOXS.AI cobra S/20/mes** — tu plan actual de S/70/mes es **3.5x más caro** que tu competidor directo más comparable.

### 7.2 Contexto del mercado peruano

| Dato | Valor | Fuente |
|------|-------|--------|
| Abogados activos en Lima (CAL) | **53,029** | Colegio de Abogados de Lima, Enero 2026 |
| Salario promedio abogado Perú | **S/2,317/mes** | Computrabajo Perú, Abril 2026 |
| % del salario que S/70 representa | **3.0%** | Cálculo directo |
| % del salario que S/20 representa | **0.9%** | Zona de confort para adopción |
| Zona de pricing óptima | **S/20-S/49/mes** | Alineado con DOXS, Magnar convertido |
| LegalTech global proyectado | **USD 47B para 2029** | Research and Markets |
| CAGR AI legal LATAM | **~18.8%** | Grand View Research |

### 7.3 Hallazgo clave: BYOK NO es estándar en LegalTech

**Ningún competidor verificado usa BYOK como modelo de pricing.** 

El mercado usa:
- Suscripciones bundled (IA incluida)
- Enterprise seats
- Credits/usage-based con overages

Harvey menciona "BYOK" pero en contexto de seguridad/crypto, no como "traé tu propia API key de OpenAI".

**Implicación**: Tu modelo BYOK es innovador pero genera fricción. Un abogado peruano promedio NO sabe qué es una API key.

---

## VIII. MODELO DE NEGOCIO Y PRICING — EVALUACIÓN

### 8.1 Análisis del modelo BYOK actual

**Concepto**: TukiJuris cobra por acceso a la plataforma. El usuario paga su propia IA.

**Ventajas**:
- ✅ Costos operativos predecibles para ti (no pagás tokens de LLM)
- ✅ Sin techo de uso artificial — el cliente puede usar cuanto quiera
- ✅ Flexibilidad de proveedores — el usuario elige su modelo
- ✅ Alineado con tendencia enterprise (empresas ya tienen cuentas OpenAI/Anthropic)

**Desventajas / Riesgos**:
- ❌ **Fricción altísima** para usuario no-técnico: ¿un abogado peruano sabe qué es una API key de OpenAI?
- ❌ **Barrera de entrada** que reduce conversión: el usuario tiene que ir a otro sitio, crear cuenta, generar key, volver
- ❌ **Soporte de billing doble**: "¿por qué me cobra OpenAI $20 si ya pago TukiJuris?"
- ❌ **No podés controlar la experiencia**: si el key del usuario tiene rate limits o se queda sin crédito, TukiJuris se "rompe" y el usuario te culpa a vos
- ❌ **Nadie más lo hace**: sin precedente en LegalTech, los usuarios no lo entienden

### 8.2 Recomendación de pricing (MODELO HÍBRIDO)

Basado en el análisis de mercado peruano:

```
┌─────────────────────────────────────────────────────────────┐
│ PLAN GRATUITO — "Explorar"                                  │
│ S/0                                                          │
│ ─────────────────────────────────────────────────────────── │
│ • 5 consultas/día con modelo INCLUIDO (gemini-flash)        │
│ • NO necesita API key para empezar                           │
│ • 3 áreas del derecho (civil, laboral, penal)               │
│ • Historial 7 días                                           │
│ • Sin analytics, sin export, sin org                         │
│                                                              │
│ Objetivo: ELIMINAR fricción de entrada                      │
│ Costo para ti: ~$0.001/query × 5 × DAU = negligible        │
├─────────────────────────────────────────────────────────────┤
│ PLAN PROFESIONAL — "Profesional"                            │
│ S/39/mes                                                     │
│ ─────────────────────────────────────────────────────────── │
│ • Consultas ilimitadas con TU API key (BYOK)                │
│ • Las 11 áreas del derecho                                   │
│ • Analytics completo + export CSV/PDF                        │
│ • Memoria de contexto + marcadores + carpetas               │
│ • Búsqueda avanzada en normativa                            │
│ • Historial ilimitado                                        │
│                                                              │
│ Posicionamiento: 2x DOXS.AI pero con orquestador multi-    │
│ agente + BYOK ilimitado. Compite por valor, no por precio.  │
├─────────────────────────────────────────────────────────────┤
│ PLAN ESTUDIO — "Estudio"                                    │
│ S/99/mes                                                     │
│ ─────────────────────────────────────────────────────────── │
│ • Todo Profesional + organización multi-usuario              │
│ • API keys compartidas a nivel org                           │
│ • Hasta 10 miembros incluidos                                │
│ • Soporte prioritario                                        │
│ • 200 consultas/mes con modelo INCLUIDO                      │
│   (para miembros que no configuren key propia)              │
│                                                              │
│ Precio por usuario: S/9.9/mes — irresistible para estudios │
├─────────────────────────────────────────────────────────────┤
│ ENTERPRISE — "Corporativo"                                  │
│ Contactar                                                    │
│ ─────────────────────────────────────────────────────────── │
│ • SSO/SAML + SLA + on-premise option                         │
│ • Usuarios ilimitados                                        │
│ • API keys a nivel empresa                                   │
│ • Custom ingesta de normativa interna                        │
│ • Soporte dedicado + capacitación                            │
└─────────────────────────────────────────────────────────────┘
```

**¿Por qué este pricing y no el actual (S/70)?**

| Factor | S/70 actual | S/39 propuesto |
|--------|:-----------:|:--------------:|
| vs DOXS.AI (S/20) | 3.5x más caro | 2x más caro (justificable por features) |
| vs salario promedio (S/2,317) | 3.0% del salario | 1.7% del salario |
| Zona psicológica | "Es caro" | "Es razonable" |
| Free tier incluido | No | Sí → elimina fricción |
| Barrera BYOK | Total | Parcial (free tier no necesita key) |

### 8.3 Comunicación del modelo BYOK

**Problema actual**: El usuario no entiende por qué necesita "otra cuenta en otro lado".

**Solución**: Reemplazar el lenguaje técnico:

| ❌ Actual | ✅ Propuesto |
|-----------|-------------|
| "Configura tu API key de OpenAI" | "Conectá tu cuenta de inteligencia artificial" |
| "BYOK — Bring Your Own Key" | "Usá tu propia IA — sin límites" |
| "sk-..." | "Copiá tu clave privada desde tu panel de OpenAI" |
| Banner: "Sin modelo" | "Activá tu IA para empezar a consultar" |
| "No tenés claves de IA configuradas" | "Probá gratis o conectá tu IA para uso ilimitado" |

### 8.4 Estrategia free tier — análisis de viabilidad

| Métrica | Estimación |
|---------|-----------|
| Costo por query (gemini-2.0-flash) | ~$0.0015 |
| Queries free/día/usuario | 5 |
| Si 100 DAU free | 500 queries/día = ~$0.75/día = **~$22/mes** |
| Si 500 DAU free | **~$112/mes** |
| Si 1000 DAU free | **~$225/mes** |

**Conclusión**: El free tier es BARATO de mantener. Con 10 usuarios pagos a S/39 (≈$10 USD) cubrís el costo de 1000 usuarios free. Es una inversión en adquisición, no un costo.

---

## VIII. HOJA DE RUTA PRE-PRODUCCIÓN

### Fase 0 — Bloqueantes (1-2 semanas)

| # | Tarea | Esfuerzo | Impacto |
|---|-------|:--------:|---------|
| 1 | **Ingestar KB completa** — correr seeders + generate_embeddings | 2h | ❌→✅ Core del producto |
| 2 | **Fix rate limiter CORS** — agregar CORS headers al 429 response | 30min | ❌→✅ App usable |
| 3 | **Auth token refresh** — implementar refresh tokens o extender expiry + auto-redirect en 401 | 4h | ❌→✅ Sesiones que no mueren |
| 4 | **Crear /terminos y /privacidad** | 2h | ❌→✅ Requisito legal |
| 5 | **Webhook signature verification** — MercadoPago + Culqi | 3h | ❌→✅ Pagos seguros |
| 6 | **Volumen para uploads** — montar en docker-compose | 15min | ❌→✅ Archivos persisten |
| 7 | **Cambiar JWT_SECRET default** y documentar en .env.example | 30min | ❌→✅ Seguridad básica |

### Fase 1 — Estabilidad (2-3 semanas)

| # | Tarea | Esfuerzo | Impacto |
|---|-------|:--------:|---------|
| 8 | Error boundaries — `error.tsx`, `not-found.tsx`, `global-error.tsx` | 3h | UX resiliente |
| 9 | Global exception handler en FastAPI | 2h | Sin stacktraces al cliente |
| 10 | Unificar infra: elegir gateway externo O nginx local | 4h | Deploy que funciona |
| 11 | Deploy pipeline real en GitHub Actions | 4h | CD automatizado |
| 12 | Completar .env examples con TODAS las variables | 1h | Onboarding devops |
| 13 | Free tier con modelo incluido (gemini-flash) | 4h | Elimina barrera de entrada |
| 14 | Dashboard del cliente (nueva página) | 6h | Primera impresión profesional |

### Fase 2 — Profesionalización (3-4 semanas)

| # | Tarea | Esfuerzo | Impacto |
|---|-------|:--------:|---------|
| 15 | Admin panel completo (CRUD usuarios, orgs, subs) | 16h | Operabilidad del negocio |
| 16 | Observabilidad: Sentry real + structured logging + alerts | 8h | Detectar problemas |
| 17 | Centro de soporte (al menos email + FAQ mejorado) | 4h | Customer success |
| 18 | Consolidar migraciones en Alembic (eliminar SQL sueltos) | 6h | Mantenibilidad |
| 19 | Testing: agregar tests de integración para chat/stream/billing | 12h | Confianza en deploys |
| 20 | SEO: metadata por página, sitemap, robots.txt | 4h | Visibilidad orgánica |

### Fase 3 — Growth (ongoing)

| # | Tarea | Esfuerzo | Impacto |
|---|-------|:--------:|---------|
| 21 | Landing page profesional (rediseño con propuesta de valor clara) | 12h | Conversión |
| 22 | Onboarding para no-técnicos (tutoriales interactivos) | 8h | Reducir abandono |
| 23 | API SDKs publicados (npm + pypi) | 4h | Developer adoption |
| 24 | i18n real (quechua, inglés) | 16h | Mercado expandido |
| 25 | Integraciones: Google Docs, Word export, calendar legal | 24h | Stickiness |

---

## IX. CONCLUSIÓN

### Lo que tenés es BUENO

Hermano, no te voy a mentir: lo que construiste es **impresionante** para una sola persona. Un orquestador multi-agente con LangGraph, búsqueda híbrida con reranking, 25 páginas, 90+ endpoints, BYOK real, auth completo con SSO. Eso no es poco.

### Lo que falta para ser un PRODUCTO

Pero hay una diferencia enorme entre "código que funciona" y "producto que se vende". Y ahí es donde estás flojo:

1. **La KB está vacía** — Es como abrir un restaurante sin comida
2. **No hay resiliencia** — Un token vencido mata la experiencia sin aviso
3. **No hay observabilidad** — ¿Cómo vas a saber si algo falla en producción?
4. **El panel admin es un esqueleto** — ¿Cómo vas a gestionar clientes sin herramientas?
5. **El modelo BYOK puro es friction hell** — Un abogado peruano no sabe qué es una API key

### Mi veredicto

🟡 **NO LISTO para producción comercial, pero a 2-3 semanas de estarlo.**

La Fase 0 (bloqueantes) son correcciones de 1-2 días de trabajo concentrado. La Fase 1 es otra semana. Con eso tenés un beta funcional y vendible.

Lo que NO deberías hacer es seguir agregando features. **Ponete las pilas con lo que falta, no con lo nuevo.**

---

*Auditoría realizada el 8 de Abril, 2026*
*TukiJuris v1.0.0-beta — Plataforma Jurídica Inteligente para Derecho Peruano*
