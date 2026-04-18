# ROADMAP DE FIXES PRE-PRODUCCIÓN — TukiJuris

> Última actualización: 14 de Abril 2026

---

## ESTADO GENERAL

```
FASE 0 — Bloqueantes     ████████████████████  100%  COMPLETA
FASE 1 — Estabilidad     ████████████████████   95%  (4/5 done — falta dashboard)
MEJORAS                   ████████████████████  100%  COMPLETA
```

---

## FASE 0 — BLOQUEANTES

| # | Tarea | Estado | Detalle |
|---|-------|:------:|---------|
| 0-B | Fix rate limiter CORS | ✅ DONE | Headers CORS en respuesta 429 |
| 0-F | Volumen uploads docker-compose | ✅ DONE | dev + prod compose con `api_uploads` volume |
| 0-G | JWT secret safety + expiry 24h | ✅ DONE | Validación en startup prod + 60min→24h |
| 0-M | Aplicar migraciones faltantes (003-014) | ✅ DONE | 21 tablas en DB |
| 0-A1 | Ingestar KB (seeders) | ✅ DONE | 74 docs, 378 chunks, 378 embeddings |
| 0-A2 | Generar embeddings | ✅ DONE | 100% cobertura |
| 0-C | Auth resilience (authFetch + 401→login) | ✅ DONE | authFetch() en lib/auth.ts + redirect automático |
| 0-D | Páginas /terminos y /privacidad | ✅ DONE | 271 + 348 líneas, Ley 29733 completo |
| 0-E | Webhook signature verification | ✅ DONE | HMAC-SHA256 para MercadoPago + Culqi |
| 0-X | Dev compose monta TODAS las migraciones | ✅ DONE | 14 SQL files |
| 0-Y | Sentry + google-generativeai | ✅ DONE | Dependencias agregadas |
| 0-Z | Services/ montado en container | ✅ DONE | Pipeline accesible |

## FASE 1 — ESTABILIDAD

| # | Tarea | Estado | Detalle |
|---|-------|:------:|---------|
| 1-A | Error boundaries Next.js | ✅ DONE | error.tsx + not-found.tsx Lex Aurum |
| 1-B | Global exception handler FastAPI | ✅ DONE | core/exception_handlers.py |
| 1-C | Free tier con Gemini Flash | ✅ DONE | chat.py + stream.py fallback chain |
| 1-D | Dashboard del cliente | ⬜ PENDIENTE | Pantalla home con resumen de uso |
| 1-E | Pricing S/39 + S/99 | ✅ DONE | billing + landing + onboarding |

---

## DEUDA TÉCNICA RESUELTA (verificado — no eran bugs)

| # | Tarea | Estado |
|---|-------|:------:|
| 2-A | /v1/usage devuelve zeros | ✅ Ya cuenta desde messages table |
| 2-B | chat.py no persiste | ✅ Ya crea conversation + messages |
| 2-C | memory/settings fake | ✅ Ya persiste en user.preferences JSONB |

## DEUDA TÉCNICA REAL (baja prioridad)

| # | Tarea | Severidad |
|---|-------|-----------|
| 2-D | APIKey.organization_id nunca se setea | Media |
| 2-F | Matrix pruebas modelos x razonamiento | Baja |

---

## PENDIENTE PARA GO-LIVE

```
[ ] Configurar GOOGLE_API_KEY en .env para free tier
[ ] Dashboard del cliente (1-D)
[ ] Provisionar VPS + DNS
[ ] Deploy final
```

---

*TukiJuris — Plataforma Jurídica Inteligente para Derecho Peruano*
