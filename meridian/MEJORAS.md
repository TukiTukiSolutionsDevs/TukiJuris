# Mejoras aplicadas y pendientes

## Mejoras YA aplicadas (esta sesión)

### Shim (`~/.config/opencode/meridian-opencode-shim.js`)

| # | Mejora | Detalle |
|---|--------|---------|
| 1 | `/health` propio | Endpoint que no proxea a Meridian; reporta `healthy`/`degraded` con stats |
| 2 | Logging estructurado | `[timestamp] [SHIM] LEVEL: msg {extra}` con reqId por request |
| 3 | Graceful shutdown | Handlers SIGTERM/SIGINT con timeout 5s para cerrar conexiones |
| 4 | System prompt configurable | Via env `OPENCODE_MERIDIAN_SYSTEM_PROMPT` |
| 5 | Body limit | 50MB max, respuesta 413 si se excede |
| 6 | Error codes | 502 (proxy error), 413 (too large), WARN en JSON parse fail |
| 7 | Stats en /health | Contador de requests, rewrites y errors en runtime |

### Wrapper (`~/.local/bin/opencode-anthropic`)

| # | Mejora | Detalle |
|---|--------|---------|
| 1 | `--restart` | Stop + start en un solo comando |
| 2 | `--tail` | `tail -f` de ambos logs en vivo |
| 3 | `--help` | Documentación inline con comandos y env vars |
| 4 | Log rotation | Rota a `.old` al pasar 5MB (`MAX_LOG_SIZE`) |
| 5 | PID tracking | Guarda PIDs en `~/.local/state/opencode-anthropic/pids/` |
| 6 | Meridian CLI fix | Invocación directa sin `bash -lc` frágil |
| 7 | Stop mejorado | Mata por PID primero, fallback a `lsof` si PID file es stale |

---

## Pendientes

### P1 — Alta prioridad

- [ ] **Verificar conflicto plugin Meridian**
  - `opencode.json` línea 209-211 tiene el plugin de Meridian cargado
  - Puede generar requests duplicados o interferencia con el shim
  - **Test**: quitar el plugin, correr `opencode-anthropic run "Reply only with OK"`, verificar que sigue OK
  - **Si falla sin plugin**: Meridian necesita el plugin para detectar `adapter=opencode`
  - **Si funciona sin plugin**: removerlo limpia la arquitectura

- [ ] **Monitorear cambios de Meridian**
  - Suscribirse a releases de `rynfar/meridian` (`gh release watch rynfar/meridian`)
  - Si actualizan el adapter de OpenCode, revisar si afecta al shim

### P2 — Media prioridad

- [ ] **LaunchAgent de macOS**
  - Crear `~/Library/LaunchAgents/com.opencode.meridian-stack.plist`
  - Que levante Meridian + shim al login
  - Que `opencode-anthropic` detecte si ya están vivos y no duplique

- [ ] **Monitor de auth**
  - Check periódico de `claude auth status`
  - Si `loggedIn: false`, notificar y no levantar stack

- [ ] **Rotación de logs mejorada**
  - Mantener N archivos históricos (no solo 1 `.old`)
  - Opción: usar `newsyslog` de macOS

### P3 — Baja prioridad

- [ ] **Preservar contexto parcial en system prompt**
  - Hoy el shim reemplaza TODO el system por una línea mínima
  - Podríamos preservar directorio de trabajo y git status sin activar detección
  - **Riesgo**: cualquier marker de más puede reactivar el gating

- [ ] **Dashboard local**
  - Stats del shim accesibles via browser
  - `/health` ya expone stats, solo falta un HTML frontend

- [ ] **Tests automáticos del shim**
  - Smoke test: `curl` a Meridian con system prompt branded → debe ser reescrito
  - Regression: si Anthropic cambia markers, detectar rápido

- [ ] **Alias en .zshrc**
  - `alias opencode="opencode-anthropic"` para el usuario
  - Solo si decide que siempre quiere Anthropic por defecto

---

## Notas sobre el wrapper que NO hay que cambiar

### ¿Por qué `ANTHROPIC_API_KEY=x`?
El wrapper exporta `ANTHROPIC_API_KEY=x` como dummy. OpenCode necesita que la env var exista
para activar el provider Anthropic. El valor real no importa porque Meridian inyecta el token
de Claude CLI. **No cambiar a un valor real.**

### ¿Por qué no tocar el binario de OpenCode?
Investigamos el binario nativo (`opencode-darwin-arm64`) buscando strings del system prompt.
El prompt se arma en runtime, no está hardcodeado en el binario. Por eso el shim HTTP
fue suficiente sin parchear OpenCode.

### ¿Por qué el plugin `experimental.chat.system.transform` no alcanzó?
Lo probamos. El hook se ejecuta pero NO modifica el request HTTP outbound real.
OpenCode loguea "transform applied" pero el request sale con el prompt original.
El shim HTTP intercepta DESPUÉS de que OpenCode arma el request final.
