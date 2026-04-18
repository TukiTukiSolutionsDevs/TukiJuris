# ROADMAP TukiJuris 2026 — Plan Completo

> Actualizado: 9 de Abril 2026
> Incluye: estado real, deuda técnica, expansión de modelos, plan free tier

---

## RESUMEN EJECUTIVO

```
COMPLETADO                ████████████████████  ~80%
PENDIENTE TÉCNICO         ████░░░░░░░░░░░░░░░░  ~10%   (solo 2-D, 2-F)
EXPANSIÓN MODELOS + FREE  ████████████████████  ~90%   Free tier ACTIVADO (14/Abr)
PRODUCTO COMERCIAL        ████████████░░░░░░░░  ~60%   Pricing done, falta dashboard
```

---

## FASE 0 — BLOQUEANTES (pre-producción)

| # | Tarea | Estado | Notas |
|---|-------|:------:|-------|
| 0-B | Fix rate limiter CORS | ✅ | Headers CORS en 429 |
| 0-F | Volumen uploads docker-compose | ✅ | dev + prod con `api_uploads` |
| 0-G | JWT secret safety + expiry 24h | ✅ | Validación startup + 24h |
| 0-M | Migraciones aplicadas | ✅ | 21 tablas |
| 0-A1 | Ingestar KB | ✅ | 74 docs, 378 chunks, 378 embeddings |
| 0-A2 | Generar embeddings | ✅ | 100% cobertura |
| 0-C | Auth resilience | ✅ | authFetch + 401→login |
| 0-X | Dev compose monta migraciones | ✅ | 14 SQL files |
| 0-Y | Dependencias (sentry, google-generativeai) | ✅ | pyproject.toml |
| 0-Z | services/ montado en container | ✅ | Pipeline accesible |
| 0-D | Páginas /terminos y /privacidad | ✅ | 271 + 348 líneas, Ley 29733, RUC, ARCO |
| 0-E | Webhook signature verification | ✅ | HMAC-SHA256 para MP + Culqi |

### Extras completados (no previstos)
- ✅ Rediseño completo Lex Aurum (27 pantallas + 4 componentes)
- ✅ Admin: sección Respaldo & Base de Conocimiento
- ✅ Makefile: db-backup, db-restore, db-seed-full
- ✅ Scrapers: fix DB URL (localhost→db en Docker)
- ✅ Frontend SSE audit: 4 bugs corregidos (citations, labels, errors, model_used)
- ✅ Rebrand Agente Derecho → TukiJuris
- ✅ BYOK multi-provider: 8 providers, 22 modelos, UI completa

---

## FASE 1 — ESTABILIDAD

| # | Tarea | Estado | Impacto | Esfuerzo |
|---|-------|:------:|---------|----------|
| 1-A | Error boundaries Next.js | ✅ | error.tsx + not-found.tsx Lex Aurum | Bajo |
| 1-B | Global exception handler FastAPI | ✅ | HTTP + validation + catch-all JSON | Bajo |
| 1-C | Free tier con Gemini Flash | ✅ | chat.py + stream.py fallback chain | Alto |
| 1-D | Dashboard del cliente | ❌ | UX | Medio |
| 1-E | Pricing S/39 + S/99 | ✅ | billing + landing + onboarding | Medio |

---

## FASE 2 — DEUDA TÉCNICA (del backend audit #571)

Bugs y deudas encontrados en auditoría que siguen sin resolver:

| # | Tarea | Severidad | Detalle |
|---|-------|-----------|---------|
| 2-A | `/v1/usage` devuelve zeros | Alta | Endpoint placeholder, no reporta uso real |
| 2-B | chat.py no persiste conversación a DB | Alta | Solo stream.py persiste |
| 2-C | memory/settings endpoint es fake | Media | No guarda nada server-side |
| 2-D | `APIKey.organization_id` nunca se setea | Media | Multi-org roto |
| 2-E | `get_current_user_with_org` sin usar | Baja | Código muerto |
| 2-F | Matrix pruebas modelos×razonamiento | Media | Solo 1/88 probado |

---

## FASE 3 — EXPANSIÓN DE MODELOS LLM (INVESTIGACIÓN)

### Catálogo actual: 22 modelos, 6 providers

| Provider | Modelos | Tier |
|----------|---------|------|
| Google (Gemini) | 2.5 Flash, 2.5 Pro, 3.1 Flash-Lite, 3.1 Pro | free/std/pro |
| Groq | Llama 3.3 70B, Llama 3.1 8B, Qwen3 32B, GPT-OSS 120B | free/std/pro |
| DeepSeek | V3.2, Reasoner | free/std |
| OpenAI | GPT-5.4 Nano/Mini/Full | std/pro |
| Anthropic | Haiku 4.5, Sonnet 4.6, Opus 4.6 | std/pro |
| xAI | Grok 3 Mini, 3 Fast, 4.1 Fast, 4, 4.20 | free/std/pro |

### Nuevos providers a investigar e integrar

Todos estos son compatibles con LiteLLM (tienen provider entry o API OpenAI-compatible):

#### Chinos con API abierta

| Provider | Modelos clave | LiteLLM | Precio/1M input | Free tier |
|----------|---------------|---------|------------------|-----------|
| **Z.AI (GLM/Zhipu)** | GLM-5.1 (744B MoE), GLM-4.7, GLM-4.5-Air, GLM-4.5-Flash | ✅ `zai/` | $0.20-$1.00 | GLM-4.5-Flash gratis; GLM-4.5-Air $0 en OpenRouter |
| **Moonshot (Kimi)** | Kimi K2.5 (262K ctx), moonshot-v1 | ✅ `moonshot/` | $0.38-$0.60 | Free tier ~30-50 msgs/día |
| **Alibaba (Qwen)** | Qwen3-Max, Qwen-Plus, Qwen-Flash, Qwen-Coder | ✅ via OpenAI-compat | $0.40 | 1M tokens gratis x 90 días |
| **MiniMax** | M2.5, M2-Stable | ✅ `minimax/` | $0.30 | **M2.5 GRATIS en OpenRouter** |
| **StepFun** | Step-3.5-Flash (256K ctx) | ✅ `stepfun/` | $0.10 | **Gratis en OpenRouter** |
| **ByteDance (Doubao)** | Doubao-1.5-Pro (256K), Doubao-1.5-Lite | ⚠️ OpenAI-compat | ~$0.15 | No confirmado |
| **Tencent (Hunyuan)** | Hunyuan-A13B (131K ctx) | ⚠️ OpenAI-compat | $0.10 | No confirmado |
| **Baichuan** | Baichuan-4 (128K ctx) | ⚠️ OpenAI-compat | $2.78 | No confirmado |

#### Globales con free tier o muy baratos

| Provider | Modelos clave | LiteLLM | Free tier |
|----------|---------------|---------|-----------|
| **Cerebras** | Llama 4 Scout, Llama 70B | ✅ OpenAI-compat | **1M tokens/día GRATIS** |
| **SambaNova** | Llama 405B, DeepSeek, Qwen | ✅ OpenAI-compat | Developer tier (cambiante) |
| **Mistral** | Mistral Large, Small, Codestral | ✅ `mistral/` | Experiment tier (1 req/s, sin tarjeta) |
| **Together AI** | Llama 4, Mixtral, Qwen | ✅ `together_ai/` | $100 créditos iniciales |
| **Fireworks AI** | Llama, Mixtral, custom | ✅ `fireworks_ai/` | $1 crédito inicial |
| **Cohere** | Command R+, Embed | ✅ `cohere/` | 1,000 calls/mes trial |
| **Hyperbolic** | Varios open-source | ✅ `hyperbolic/` | No confirmado |
| **Novita AI** | Varios open-source | ✅ `novita/` | No confirmado |
| **OpenRouter** | 200+ modelos (gateway) | ✅ `openrouter/` | **Modelos gratis: GLM-4.5-Air, MiniMax-M2.5, Step-3.5-Flash** |
| **AI21 Labs** | Jamba 2 | ✅ `ai21/` | No confirmado |

#### Sin datos suficientes (investigar manualmente)
- **Baidu (Ernie)** — sin info de API pública internacional
- **SenseTime (SenseChat)** — sin info
- **Reka** — sin info
- **01.AI (Yi)** — restricción comercial, requiere permiso

---

## FASE 4 — PLAN FREE TIER (estrategia)

### El problema
Hoy TukiJuris es 100% BYOK: el usuario TIENE que traer su API key para usar la app.
Eso mata la conversión: nadie se registra si tiene que configurar una key antes de probar.

### La solución: modelo gratuito de plataforma

#### Opción A — OpenRouter Free Models (RECOMENDADA)
```
Pros: Sin costo, permanente, LiteLLM nativo, múltiples modelos
Cons: Depende de disponibilidad de OpenRouter, rate limits variables
Modelos: GLM-4.5-Air, MiniMax-M2.5, Step-3.5-Flash (todos $0)
```
**Implementación**: Una sola API key de OpenRouter → acceso a todos los modelos free.
El usuario free NO configura nada. La plataforma rutea a estos modelos automáticamente.

#### Opción B — Cerebras Free Tier
```
Pros: 1M tokens/día, rápido (2600 t/s), OpenAI-compatible
Cons: Solo modelos Llama, un solo provider
Modelos: Llama 3.3 70B, Llama 4 Scout
```

#### Opción C — Gemini Flash (actual)
```
Pros: Ya integrado, Google gratis para low-volume
Cons: Requiere API key de Google (¿la pone la plataforma?)
Modelos: Gemini 2.5 Flash
```

#### Opción D — Combo (máxima resiliencia)
```
Primary:   OpenRouter free (GLM-4.5-Air)
Fallback1: Cerebras free (Llama 70B)
Fallback2: Gemini 2.5 Flash (platform key)
```
Si uno cae → fallback automático. El usuario free NUNCA se queda sin servicio.

### Arquitectura propuesta para free tier

```
Usuario Free → TukiJuris API → LiteLLM
                                  ├─ openrouter/z-ai/glm-4.5-air:free     (primary)
                                  ├─ cerebras/llama-3.3-70b                (fallback)
                                  └─ gemini/gemini-2.5-flash               (fallback)

Usuario BYOK → TukiJuris API → LiteLLM → provider con SU key
```

### Límites sugeridos para plan free

| Límite | Valor | Razón |
|--------|-------|-------|
| Consultas/día | 10 | Suficiente para probar, no para producción |
| Tokens/consulta | 4,096 | Respuesta completa sin abusar |
| Modelos disponibles | Solo free tier | GLM-4.5-Air, MiniMax-M2.5, Llama |
| Historial | Últimas 10 conversaciones | Motivar upgrade |
| Áreas del derecho | Todas | No limitar funcionalidad core |
| Reasoning/thinking | No | Solo para planes pagos |

---

## FASE 5 — PRODUCTO COMERCIAL

| # | Tarea | Prioridad | Detalle |
|---|-------|-----------|---------|
| 5-A | Definir pricing final | P0 | S/39 (Profesional) + S/99 (Firma) |
| 5-B | Implementar free tier | P0 | Ver Fase 4 |
| 5-C | Landing page actualizada | P1 | Reflejar pricing + free tier |
| 5-D | Billing + Stripe/Culqi | P1 | Planes reales, no placeholder |
| 5-E | Onboarding sin BYOK | P1 | Free → usa modelo gratis, skip config |
| 5-F | Dashboard cliente | P2 | Home con uso, historial, accesos rápidos |
| 5-G | Uso diario visible | P2 | Barra de progreso consultas restantes |
| 5-H | Centro de ayuda real | P3 | FAQ + soporte + contacto |
| 5-I | Estado del sistema real | P3 | No placeholder |

---

## FASE 6 — OPERACIÓN ADMIN

| # | Tarea | Prioridad | Detalle |
|---|-------|-----------|---------|
| 6-A | CRUD de usuarios | P1 | Ver, editar, suspender usuarios |
| 6-B | Gestión de organizaciones | P2 | Crear, editar, asignar usuarios |
| 6-C | Gestión de suscripciones | P1 | Ver planes activos, cancelar, upgrade |
| 6-D | KB admin real | P2 | Reingesta, ver docs, coverage, último backup |

---

## ORDEN DE EJECUCIÓN RECOMENDADO

```
SPRINT A (inmediato) — Cierre legal + estabilidad
  1. /terminos y /privacidad
  2. Webhook signature verification
  3. Error boundaries Next.js
  4. Exception handlers FastAPI

SPRINT B (semana 2) — Modelos + Free Tier
  1. Investigar y probar: OpenRouter free, Cerebras, MiniMax
  2. Agregar providers nuevos al catálogo (chinos + globales)
  3. Implementar free tier con fallback chain
  4. Onboarding sin BYOK para plan free

SPRINT C (semana 3) — Producto comercial
  1. Pricing final S/39 + S/99
  2. Landing actualizada
  3. Billing real (Stripe o Culqi)
  4. Dashboard cliente

SPRINT D (semana 4) — Deuda técnica + admin
  1. /v1/usage real
  2. chat.py persistencia
  3. memory/settings real
  4. Admin: CRUD usuarios + suscripciones
```

---

## PROVIDERS COMPATIBLES CON LITELLM — REFERENCIA RÁPIDA

Para agregar un nuevo provider al `llm_adapter.py`, solo se necesita:

```python
# 1. Agregar el modelo a AVAILABLE_MODELS
{"id": "zai/glm-4.5-air", "provider": "zai", "name": "GLM-4.5 Air", ...}

# 2. Agregar el prefix en _provider_from_model()
if model_lower.startswith("zai/"):
    return "zai"

# 3. Agregar la env key en _configure_api_keys() y env_keys
if settings.zai_api_key:
    os.environ["ZAI_API_KEY"] = settings.zai_api_key

# 4. Agregar al frontend en models.ts
{id: "zai/glm-4.5-air", name: "GLM-4.5 Air", provider: "zai", tier: "free"}
```

### Prefijos LiteLLM confirmados
| Provider | Prefix | Env var |
|----------|--------|---------|
| Z.AI (GLM) | `zai/` | `ZAI_API_KEY` |
| Moonshot (Kimi) | `moonshot/` | `MOONSHOT_API_KEY` |
| MiniMax | `minimax/` | `MINIMAX_API_KEY` |
| StepFun | `stepfun/` | `STEP_API_KEY` |
| Cerebras | `cerebras/` | `CEREBRAS_API_KEY` |
| Mistral | `mistral/` | `MISTRAL_API_KEY` |
| Together AI | `together_ai/` | `TOGETHERAI_API_KEY` |
| Fireworks | `fireworks_ai/` | `FIREWORKS_AI_API_KEY` |
| Cohere | `cohere/` | `COHERE_API_KEY` |
| Hyperbolic | `hyperbolic/` | `HYPERBOLIC_API_KEY` |
| Novita | `novita/` | `NOVITA_API_KEY` |
| OpenRouter | `openrouter/` | `OPENROUTER_API_KEY` |
| AI21 | `ai21/` | `AI21_API_KEY` |

---

*Generado con investigación Tavily + auditoría de código + engram memory*
*Última actualización: 9 de Abril 2026*
