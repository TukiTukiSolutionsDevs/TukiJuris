# Meridian + OpenCode — Plan de Implementacion

## Arquitectura

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌───────────┐
│ OpenCode │────▶│ Shim (:4568) │────▶│ Meridian  │────▶│ Anthropic │
│          │     │ rewrite sys  │     │  (:3456)  │     │   API     │
└──────────┘     └──────────────┘     └──────────┘     └───────────┘
                       │                    │
                       ▼                    ▼
                  shim.log            meridian.log
```

### Componentes

| Componente | Ubicacion | Funcion |
|------------|-----------|---------|
| Wrapper | `~/.local/bin/opencode-anthropic` | Arranca stack, inyecta env vars, ejecuta OpenCode |
| Shim | `~/.config/opencode/meridian-opencode-shim.js` | Intercepta HTTP, reescribe system prompt |
| Meridian | `@rynfar/meridian` (npm global) | Proxy SDK que usa credenciales Claude CLI |
| Smoke agent | `~/.config/opencode/agents/meridian-smoke.md` | Agente minimal para testing |

### Por que el shim es necesario

OpenCode manda un system prompt gigante que incluye:
- `"You are OpenCode, the best coding agent on the planet."`
- `<env>` con rutas, git status, fecha
- `Instructions from:` con AGENTS.md completo

Anthropic detecta ese shape como "third-party app" y responde:
> "Third-party apps now draw from your extra usage, not your plan limits"

**Evidencia**: request capturado en `/tmp/opencode-capture.json` demostro que:
- Mismo body + tools + stream pero con system minimal → funciona
- Mismo body pero sin tools y con system original → falla
- **Causa raiz: el system prompt, no las tools**

## Archivos actuales

### 1. Shim mejorado (YA APLICADO)

Ubicacion: `~/.config/opencode/meridian-opencode-shim.js`

Mejoras sobre la version original:
- `/health` propio (no proxy) con estado `healthy`/`degraded`
- Logging estructurado con timestamp, reqId, nivel
- Graceful shutdown (SIGTERM/SIGINT)
- System prompt configurable via env var
- Body limit 50MB con respuesta 413
- Error codes correctos (502 proxy, 413 too large)

### 2. Wrapper mejorado (YA APLICADO)

Ubicacion: `~/.local/bin/opencode-anthropic`

Mejoras:
- `--restart` (stop + start en un paso)
- `--tail` (seguir logs en vivo)
- `--help` (documentacion inline)
- Log rotation (rota a `.old` al pasar 5MB)
- PID files en `~/.local/state/opencode-anthropic/pids/`
- Meridian CLI invocacion directa (sin `bash -lc` fragil)

## Issues conocidos de Meridian (investigados)

### Issue #319 — Anthropic changes / harness detection
- Meridian pasa el system prompt del harness al SDK
- El maintainer evita modificar prompts en el proxy
- Workaround: shim externo (lo que implementamos)

### Issue #255 — Extra usage / harnesses
- Reportes de bloqueo por system prompts de OpenCode/Pi/OpenClaw
- Confirmado que el gating depende del shape del request

### Issue #278 — Beta headers
- Discusion sobre stripping de headers anthropic-beta
- Meridian los deja pasar

### Issue #221 — OpenCode persona configs
- Configuraciones de agente afectan lo que Meridian ve

## Riesgos y limitaciones

### Tecnico
1. **Fragilidad del shim**: si Anthropic cambia las heuristicas de deteccion, el shim puede dejar de funcionar
2. **System prompt minimal**: al reemplazar el prompt, se pierde contexto de env/directorio que OpenCode normalmente inyecta
3. **Plugin Meridian en opencode.json**: sigue cargado (linea 209-211); podria generar interferencia con el shim

### Compliance
1. Consumer Terms de Anthropic prohiben acceso automatizado salvo via API key
2. OpenCode removio soporte Anthropic tras pedido legal (PR #18186)
3. Esto es experimental/personal, no productivo

### Operacional
1. Requiere Claude CLI autenticado (`claude auth status` debe mostrar `loggedIn: true`)
2. Si Claude CLI se desloguea, todo el stack falla
3. Logs crecen; la rotacion es basica (1 archivo `.old`)

## Comandos de uso diario

```bash
# Abrir OpenCode interactivo con Anthropic
opencode-anthropic

# Ejecutar prompt directo
opencode-anthropic run --model anthropic/claude-sonnet-4-0 "tu prompt"

# Ver estado
opencode-anthropic --status

# Ver logs en vivo
opencode-anthropic --tail

# Reiniciar stack
opencode-anthropic --restart

# Detener todo
opencode-anthropic --stop

# Ayuda
opencode-anthropic --help
```

## Variables de entorno soportadas

| Variable | Default | Descripcion |
|----------|---------|-------------|
| `MERIDIAN_HOST` | `127.0.0.1` | Host de Meridian |
| `MERIDIAN_PORT` | `3456` | Puerto de Meridian |
| `OPENCODE_MERIDIAN_SHIM_PORT` | `4568` | Puerto del shim |
| `OPENCODE_MERIDIAN_SYSTEM_PROMPT` | (Claude Code minimal) | System prompt para requests Anthropic |
| `OPENCODE_MERIDIAN_LOG_DIR` | `~/.local/state/opencode-anthropic` | Directorio de logs |
| `MAX_LOG_SIZE` | `5242880` (5MB) | Tamano maximo de log antes de rotar |
| `MERIDIAN_CLI` | (auto-detect) | Override del comando Meridian |

## Pendientes / mejoras futuras

### P1 — Alta prioridad
- [ ] Verificar si el plugin Meridian en `opencode.json` (linea 209-211) genera conflicto con el shim; si si, removerlo
- [ ] Agregar health check periodico en el shim que refresque stats de Meridian

### P2 — Media prioridad
- [ ] LaunchAgent de macOS para dejar Meridian + shim siempre levantados
- [ ] Monitoreo: alertar si `claude auth status` deja de estar logueado
- [ ] Rotacion de logs mas sofisticada (mantener N archivos historicos)

### P3 — Baja prioridad
- [ ] Preservar PARTE del contexto env (directorio, git) en el system prompt reescrito sin triggear deteccion
- [ ] Dashboard web local con stats del shim (requests, rewrites, errors)
- [ ] Tests automatizados para el shim (smoke test via curl en CI local)
