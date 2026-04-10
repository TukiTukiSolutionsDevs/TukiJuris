# ROADMAP DE FIXES PRE-PRODUCCIÓN — TukiJuris

> Actualizado en tiempo real mientras avanzo. Refresh para ver progreso.
> Última actualización: 8 de Abril 2026 — 08:18 UTC

---

## ESTADO GENERAL

```
FASE 0 — Bloqueantes     ████████████████████  100%  COMPLETA
FASE 1 — Estabilidad     ████████████████░░░░   80%  (4/5 done)
MEJORAS                   ████████████████░░░░   80%  Modelos sync, Config API Keys
```

---

## FASE 0 — BLOQUEANTES (sin esto no se puede lanzar)

| # | Tarea | Estado | Detalle |
|---|-------|:------:|---------|
| 0-B | Fix rate limiter CORS | ✅ DONE | Headers CORS en respuesta 429 |
| 0-F | Volumen uploads docker-compose | ✅ DONE | dev + prod compose con `api_uploads` volume |
| 0-G | JWT secret safety + expiry 24h | ✅ DONE | Validación en startup prod + 60min→24h |
| 0-M | Aplicar migraciones faltantes (003-014) | ✅ DONE | 21 tablas en DB — todas las migraciones aplicadas |
| 0-A1 | Ingestar KB (seeders) | ✅ DONE | 24 documentos, 251 chunks en 12 áreas del derecho |
| 0-A2 | Generar embeddings | ⏸️ BLOQUEADO | Google API key sin permiso de embeddings. Esperando decisión del usuario |
| 0-C | Auth resilience (authFetch + 401→login) | ✅ DONE | authFetch() en lib/auth.ts + redirect automático |
| 0-D | Páginas /terminos y /privacidad | 🔄 EN CURSO | Subagente trabajando |
| 0-E | Webhook signature verification | 🔄 EN CURSO | Subagente trabajando (MP + Culqi HMAC-SHA256) |
| 0-X | Dev compose monta TODAS las migraciones | ✅ DONE | 14 SQL files en docker-entrypoint-initdb.d |
| 0-Y | Sentry + google-generativeai en pyproject.toml | ✅ DONE | Dependencias faltantes agregadas |
| 0-Z | Services/ montado en container dev | ✅ DONE | Ingestion pipeline accesible desde API container |

## FASE 1 — ESTABILIDAD (beta profesional)

| # | Tarea | Estado | Detalle |
|---|-------|:------:|---------|
| 1-A | Error boundaries Next.js | 🔄 EN CURSO | Subagente trabajando (error.tsx, not-found.tsx, global-error.tsx) |
| 1-B | Global exception handler FastAPI | 🔄 EN CURSO | Subagente trabajando |
| 1-C | Free tier con gemini-flash | ⬜ PENDIENTE | Eliminar barrera BYOK |
| 1-D | Dashboard del cliente | ⬜ PENDIENTE | Pantalla home con resumen |
| 1-E | Actualizar pricing S/39 + S/99 | ⬜ PENDIENTE | Landing + billing + onboarding |

---

## VERIFICACIONES EN VIVO

| Test | Resultado | Fecha |
|------|-----------|-------|
| CORS en 429 | ✅ `access-control-allow-origin` presente | 08/04 08:14 UTC |
| KB ingesta | ✅ 24 docs, 251 chunks, 12 áreas | 08/04 08:13 UTC |
| Console errors | ✅ 0 errores en browser | 08/04 08:16 UTC |
| API health | ✅ `{"status":"ok"}` | 08/04 08:14 UTC |
| DB tables | ✅ 21 tablas presentes | 08/04 08:10 UTC |
| Login funcional | ✅ jaimeandre17@... logueado | 08/04 08:16 UTC |

---

*Última actualización: Sprint en curso*
